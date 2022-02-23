import discord
from typing import Callable, Optional
from discord.ext import commands
from utils.errors import NotInBanBattle, ArgumentBaseError
from utils.format import get_command_name
from utils.context import DVVTcontext


def is_dory():
    async def predicate(ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        if ctx.author.id == 493063931191885825:
            return True
        else:
            raise ArgumentBaseError(message="You are not 🚪y")

    return commands.check(predicate=predicate)

def has_permissions_or_role(**perms):
        perms = commands.has_guild_permissions(**perms).predicate
        async def predicate(ctx: DVVTcontext):
            if ctx.guild is None:
                raise commands.NoPrivateMessage()
            enabled = await ctx.bot.pool_pg.fetchval("SELECT enabled FROM devmode WHERE user_id = $1", ctx.author.id)
            if enabled == True:
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


def perm_insensitive_roles() -> callable:
    async def predicate(ctx: DVVTcontext):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        enabled = await ctx.bot.pool_pg.fetchval("SELECT enabled FROM devmode WHERE user_id = $1", ctx.author.id)
        if enabled == True:
            return True
        roles = await ctx.bot.pool_pg.fetch("SELECT role_id, whitelist FROM rules WHERE guild_id=$1 AND command=$2", ctx.guild.id, get_command_name(ctx.command))
        if ctx.author.guild_permissions.manage_roles:
            return True
        if not roles:
            if ctx.command.parent:
                roles = await ctx.bot.pool_pg.fetch("SELECT role_id, whitelist FROM rules WHERE guild_id=$1 AND command=$2", ctx.guild.id, str(ctx.command.parent))
                if not roles:
                    return True
            else:
                return True
        rolenames = []
        for role in roles:
            roleobj = ctx.guild.get_role(role.get('role_id'))
            if roleobj is not None:
                rolenames.append(roleobj.name)
            if not role.get('whitelist'):
                if discord.utils.get(ctx.author.roles, id=role.get('role_id')):
                    parsed = True
                    return False
            else:
                if discord.utils.get(ctx.author.roles, id=role.get('role_id')):
                    parsed = True
                    return True
        if len(rolenames) > 0:
            raise ArgumentBaseError(message="You need to have one of the following roles to use this command: **{}**".format(", ".join(rolenames)))
        else:
            return True
    return commands.check(predicate=predicate)

def is_owner_or_perms(**perms):
    base_check = commands.has_guild_permissions(**perms).predicate
    async def predicate(ctx: DVVTcontext):
        if ctx.guild is None and ctx.author.id != 321892489470410763 or ctx.guild is None and ctx.author.id != 650647680837484556:
            raise commands.NoPrivateMessage()
        enabled = await ctx.bot.pool_pg.fetchval("SELECT enabled FROM devmode WHERE user_id = $1", ctx.author.id)
        if enabled == True:
            return True
        return await base_check(ctx)
    return commands.check(predicate=predicate)

def in_beta() -> Callable:
    async def predicate(ctx: DVVTcontext):
        if ctx.author.id in [515725341910892555, 366069251137863681, 650647680837484556, 321892489470410763,
                                 602066975866355752]:
            return True
        else:
            raise ArgumentBaseError(message="This feature is still in development and is not available to the public at the moment. Be sure to check it again soon!")
    return commands.check(predicate)

def is_not_blacklisted() -> callable:
    async def predicate(ctx: DVVTcontext):
        blacklisted_users = await ctx.bot.pool_pg.fetchrow("SELECT * FROM blacklist WHERE user_id = $1 and blacklist_active = $2", ctx.author.id, True)
        if blacklisted_users:
            if ctx.message.author.id in [321892489470410763, 650647680837484556, 515725341910892555]:
                return True
            raise ArgumentBaseError(message="You have been blacklisted from using this function.")
        return True
    return commands.check(predicate=predicate)

def base_dev() -> callable:
    async def predicate(ctx: DVVTcontext):
        if await ctx.is_bot_dev():
            return True
        else:
            raise ArgumentBaseError(message="Only developers can use this command.")
    return commands.check(predicate)

def dev() -> callable:
    async def predicate(ctx: DVVTcontext):
        enabled = await ctx.bot.pool_pg.fetchval("SELECT enabled FROM devmode WHERE user_id = $1", ctx.author.id)
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

def is_dvbm(silent: Optional[bool] = False) -> Callable:
    async def predicate(ctx: DVVTcontext):
        if ctx.guild and ctx.guild.id == 813865065593176145:
            return True
        else:
            if not silent:
                raise NotInBanBattle()
    return commands.check(predicate)

def is_bav_or_mystic() -> Callable:
    async def predicate(ctx: DVVTcontext):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if ctx.author.guild_permissions.manage_roles == True:
            return True
        raise ArgumentBaseError(message="You need to be a `mystic` or `bav` or have the required permissions to use this command.")
    return commands.check(predicate)

def not_in_gen():
    async def predicate(ctx: DVVTcontext):
        channel_id = 608498967474601995
        if ctx.guild:
            if not ctx.author.guild_permissions.manage_roles or await ctx.is_bot_dev():
                if ctx.channel.id == channel_id:
                    raise ArgumentBaseError(message="You can't use this command here! Use it in another channel.")
        return True
    return commands.check(predicate)