import logging
from datetime import datetime

import discord
from redbot.core import commands

from .core import Core, apicheck

log = logging.getLogger("predeactor.cleverbot")


class CleverBot(Core):
    """Ask questions to Cleverbot or even start a Conversation with her!"""

    @apicheck()
    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ask(self, ctx: commands.Context, *, question: str):
        """Ask an unique question to Cleverbot.

        You won't have a discussion with Cleverbot, you're just
        asking a single question."""
        async with ctx.typing():
            session = await self._make_cleverbot_session()
            answer, answered = await self.ask_question(session, question, ctx.author.id)
            if answered:
                message = "{user}, {answer}".format(user=ctx.author.name, answer=answer)
            else:
                message = answer
            await session.close()
            await ctx.send(message)

    @apicheck()
    @commands.command()
    async def conversation(self, ctx: commands.Context):
        """Start a conversation with Cleverbot
        You don't need to use a prefix or the command using this mode."""

        if str(ctx.author.id) in self.conversation:
            await ctx.send("There's already a conversation running. Say `close` to " "stop it.")
            return

        session = await self._make_cleverbot_session()
        data = {
            "session": session,
            "channel": ctx.channel.id,
            "timer": datetime.now(),
            "typing": False,
        }
        self.conversation[str(ctx.author.id)] = data

        await ctx.send(
            "Starting a new Cleverbot session!\n\nSay `close` to stop the conversation"
            " with me !\n\nYour conversation will be automatically closed if CleverBot"
            " receive no answer.\nThis conversation is only available in this channel."
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """The CleverBot listener that will send a message in case a user is in a conversation."""
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        ctx = await self.bot.get_context(message)

        # If user is not using conversation
        if str(ctx.author.id) not in self.conversation:
            return
        session = self.conversation[str(ctx.author.id)]["session"]
        timer = self.conversation[str(ctx.author.id)]["timer"]
        channel = self.conversation[str(ctx.author.id)]["channel"]
        # If the timer is exceeded.
        if (datetime.now() - timer).seconds > 300:
            channel = self.bot.get_channel(channel)
            await channel.send(self._message_by_timeout())
            await session.close()
            del self.conversation[str(ctx.author.id)]
            return
        # If message is not in the good channel
        if ctx.channel.id is not channel:
            return
        # If bot is typing
        if self.conversation[str(ctx.author.id)]["typing"]:
            return
        # If the string start with a prefix
        if message.content.startswith(tuple(await self.bot.get_valid_prefixes())):
            return
        # If user is closing
        if message.content.lower() == "close":
            await session.close()
            del self.conversation[str(ctx.author.id)]
            await ctx.send("Session closed!")
            return
        # if all checks pass
        async with ctx.typing():
            self.conversation[str(ctx.author.id)]["typing"] = True
            answer, answered = await self.ask_question(session, message.content, ctx.author.id)
            if answered:
                message = "{user}, {answer}".format(user=ctx.author.mention, answer=answer)
                self.conversation[str(ctx.author.id)]["timer"] = datetime.now()
                exiting = False
            else:
                message = answer
                exiting = True
            await ctx.send(message)
            self.conversation[str(ctx.author.id)]["typing"] = False
            if exiting:
                await session.close()
