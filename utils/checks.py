from typing import Callable
from discord.ext import commands

def admoon() -> Callable:
    async def predicate(ctx):
        if (ctx.message.author.id == 321892489470410763) or (ctx.message.author.id == 515725341910892555):
            return True
        else:
            raise commands.NotOwner()
    return commands.check(predicate)