from .akinatorcog import Akinator


def setup(bot):
    cog = Akinator(bot)
    bot.add_cog(cog)
