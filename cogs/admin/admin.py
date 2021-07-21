from datetime import datetime
import discord
from abc import ABC
from utils import checks
from discord.ext import commands
from .serverrule import ServerRule

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    pass

class Admin(ServerRule, commands.Cog, name='admin', metaclass=CompositeMetaClass):
    """
    Server Commands
    """
    def __init__(self, client):
        self.client = client

    @commands.guild_only()
    @commands.command(name='cmdinfo', usage='<command> <content>')
    @checks.owner_or_perms(administrator=True)
    async def cmdinfo(self, ctx, cmd: str = None, *, content: str = None):
        """
        Change the description content of a commamd
        """
        if cmd is None:
            return await ctx.send("Command is a required argument.")
        if not (command := self.client.get_command(cmd)):
            return await ctx.send(f"Oops, looks like command \"{cmd}\" doesn't exist!")
        if content is None:
            return await ctx.send("Content is a required argument.")
        self.client.cur.execute("INSERT OR REPLACE INTO config VALUES (?, ?)", (command.name, content,))
        self.client.con.commit()
        command.help = content
        command.description = content
        embed = discord.Embed(title=f"Description for `{command.name}` set to:", description=content)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        embed.timestamp = datetime.utcnow()
        await ctx.checkmark()
        return await ctx.send(embed=embed)