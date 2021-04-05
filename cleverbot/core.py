from typing import Literal, Mapping, Optional

from redbot.core import checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list

from .asynccleverbot import cleverbot as ac

seems_ok = None


class Core(commands.Cog):

    __author__ = ["Predeactor"]
    __version__ = "v1.0.7"

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        """
        Nothing to delete...
        """
        pass

    # Nothing to delete, I assume that if the user was previously in self.conversation,
    # then it will automatically removed after cog reload/bot restart.

    def __init__(self, bot: Red):
        self.bot = bot
        self.conversation = {}
        super().__init__()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return "{pre_processed}\n\nAuthor: {authors}\nCog Version: {version}".format(
            pre_processed=pre_processed,
            authors=humanize_list(self.__author__),
            version=self.__version__,
        )

    @commands.Cog.listener()
    async def on_red_api_tokens_update(self, service_name: str, api_tokens: Mapping):
        global seems_ok
        if service_name == "travitia":
            seems_ok = None

    async def _get_api_key(self):
        travitia = await self.bot.get_shared_api_tokens("travitia")
        # No need to check if the API key is not registered, the
        # @apicheck() do it automatically.
        return travitia.get("api_key")

    async def _make_cleverbot_session(self):
        return ac.Cleverbot(await self._get_api_key())

    @staticmethod
    async def ask_question(session, question: str, user_id: Optional[int] = None):
        try:
            answer = await session.ask(question, user_id if user_id is not None else "00")
            answered = True
        except Exception as e:
            answer = "An error happened: {error}\nPlease try again later. Session closed.".format(
                error=str(e)
            )
            answered = False
        return answer, answered

    @staticmethod
    def _message_by_timeout():
        return "I have closed the conversation since I had no answers."

    # Commands for settings

    @checks.is_owner()
    @commands.command()
    async def travitiaapikey(self, ctx: commands.Context, *, api_key: str):
        """Set the API key for Travitia API.

        To set the API key:
        1. Go to [this server](https://discord.gg/s4fNByu).
        2. Go to #playground and use `> api`.
        3. Say yes and follow instructions.
        4. When you receive your key, use this command again with your API key.
        """
        message = (
            "To set the API key:\n1. Go to [this server](https://discord.gg/s4fNByu).\n"
            "2. Go to #playground and use `> api`.\n3. Say yes and follow instructions.\n"
            "3. Use `[p]set api travitia api_key <Your token>` "
        )
        await ctx.send(message)


def apicheck():
    """
    Check for hidding commands if the API key is not registered.
    Taken from
    https://github.com/PredaaA/predacogs/blob/75a2d0e2561da8f3415e0859c9f540794e6a72b4/nsfw/core.py#L200
    """

    async def predicate(ctx: commands.Context):
        global seems_ok
        if seems_ok is not None:
            return seems_ok
        travitia_keys = await ctx.bot.get_shared_api_tokens("travitia")
        not_key = travitia_keys.get("api_key") is None
        if ctx.invoked_with == "help" and not_key:
            seems_ok = False
            return seems_ok
        if not_key:
            seems_ok = False
            raise commands.UserFeedbackCheckFailure(
                "The API key is not registered, the command is unavailable."
            )
        seems_ok = True
        return seems_ok

    return commands.check(predicate)
