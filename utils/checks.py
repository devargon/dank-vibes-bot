import sqlite3
import discord
from typing import Callable, Optional
from discord.ext import commands
from utils.errors import NotInBanBattle

con = sqlite3.connect('databases/database.db', timeout=5.0)
cur = con.cursor()

def get_roles(guild, cmd):
    roles = cur.execute("SELECT role_id FROM rules WHERE guild_id=? AND command=?", (guild.id, cmd.name,)).fetchall()
    roles = [role[0] for role in roles if len(roles) != 0]
    return roles

def set_rule(guild, cmd, role):
    cur.execute("INSERT INTO rules VALUES (?, ?, ?)", (guild.id, cmd.name, role.id,))
    con.commit()

def remove_rule(guild, cmd, role):
    cur.execute("DELETE FROM rules WHERE guild_id=? AND command=? AND role_id=?", (guild.id, cmd.name, role.id,))
    con.commit()

def clear_rule(guild, cmd):
    cur.execute("DELETE FROM rules WHERE guild_id=? AND command=?", (guild.id, cmd.name,))
    con.commit()

def perms_or_role(**perms):
    base_check = commands.has_guild_permissions(**perms).predicate
    async def predictate(ctx):
        if ctx.author.id == 321892489470410763:
            return True
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        roles = get_roles(ctx.guild, ctx.command)
        if len(roles) == 0:
            return await base_check(ctx)
        for role in roles:
            if discord.utils.get(ctx.author.roles, id=role):
                return True
        return await base_check(ctx)
    return commands.check(predicate=predictate)

def owner_or_perms(**perms):
    base_check = commands.has_guild_permissions(**perms).predicate
    async def predicate(ctx):
        if ctx.guild is None and ctx.author.id != 321892489470410763:
            raise commands.NoPrivateMessage()
        if ctx.author.id == 321892489470410763:
            return True
        return await base_check(ctx)
    return commands.check(predicate=predicate)

def admoon() -> Callable:
    async def predicate(ctx):
        if (ctx.message.author.id == 321892489470410763) or (ctx.message.author.id == 515725341910892555):
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