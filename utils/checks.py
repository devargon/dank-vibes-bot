from typing import Callable

from discord.ext import commands

from utils.context import DVVTcontext
from utils.errors import ArgumentBaseError


def dev() -> callable:
    async def predicate(ctx: DVVTcontext):
        return ctx.author.id == 650647680837484556
        enabled = await ctx.bot.db.fetchval("SELECT enabled FROM devmode WHERE user_id = $1", ctx.author.id)
        if enabled != True:
            raise ArgumentBaseError(message="Only developers can use this command. If you are a developer, turn on Developer mode.")
        return True
    return commands.check(predicate)

def admoon() -> Callable:
    async def predicate(ctx: DVVTcontext):
        if (ctx.message.author.id == 321892489470410763) or (ctx.message.author.id == 515725341910892555) or (ctx.message.author.id == 650647680837484556):
            return True
        else:
            raise commands.NotOwner()
    return commands.check(predicate)
