import discord
from typing import Callable, Optional
from discord.ext import commands
from utils.errors import NotInBanBattle, ArgumentBaseError
from utils.format import get_command_name

def has_permissions_or_role(**perms):
        perms = commands.has_guild_permissions(**perms).predicate
        async def predicate(ctx):
            if ctx.guild is None:
                raise commands.NoPrivateMessage()
            if ctx.author.id == 321892489470410763 or ctx.author.id == 650647680837484556:
                return True
            roles = await ctx.bot.pool_pg.fetch("SELECT role_id, whitelist FROM rules WHERE guild_id=$1 AND command=$2", ctx.guild.id, get_command_name(ctx.command))
            if not roles:
                return await perms(ctx)
            for role in roles:
                if not role.get('whitelist'):
                    if discord.utils.get(ctx.author.roles, id=role.get('role_id')):
                        return False
                else:
                    if discord.utils.get(ctx.author.roles, id=role.get('role_id')):
                        return True
            return await perms(ctx)
        return commands.check(predicate=predicate)

def is_owner_or_perms(**perms):
    base_check = commands.has_guild_permissions(**perms).predicate
    async def predicate(ctx):
        if ctx.guild is None and ctx.author.id != 321892489470410763 or ctx.guild is None and ctx.author.id != 650647680837484556:
            raise commands.NoPrivateMessage()
        if ctx.author.id == 321892489470410763 or ctx.author.id == 650647680837484556:
            return True
        return await base_check(ctx)
    return commands.check(predicate=predicate)

def in_beta() -> Callable:
    async def predicate(ctx):
        if ctx.author.id in [515725341910892555, 366069251137863681, 650647680837484556, 321892489470410763,
                                 602066975866355752]:
            return True
        else:
            raise ArgumentBaseError(message="This feature is still in development and is not available to the public at the moment. Be sure to check it again soon!")
    return commands.check(predicate)

def dev() -> callable:
    async def predicate(ctx):
        if ctx.message.author.id in [321892489470410763, 650647680837484556]:
            return True
        else:
            raise ArgumentBaseError(message="Only developers can use this command.")
    return commands.check(predicate)

def admoon() -> Callable:
    async def predicate(ctx):
        if (ctx.message.author.id == 321892489470410763) or (ctx.message.author.id == 515725341910892555) or (ctx.message.author.id == 650647680837484556):
            return True
        else:
            raise commands.NotOwner()
    return commands.check(predicate)

def is_dvbm(silent: Optional[bool] = False) -> Callable:
    async def predicate(ctx):
        if ctx.guild and ctx.guild.id == 813865065593176145:
            return True
        else:
            if not silent:
                raise NotInBanBattle()
    return commands.check(predicate)

def is_bav_or_mystic() -> Callable:
    async def predicate(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if ctx.author.id in [719890992723001354, 542447261658120221]:
            return True
        if ctx.author.guild_permissions.manage_roles == True:
            return True
        raise ArgumentBaseError(message="You need to be a `mystic` or `bav` or have the required permissions to use this command.")
    return commands.check(predicate)