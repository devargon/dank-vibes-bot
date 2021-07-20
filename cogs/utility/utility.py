import time
import discord
import humanize
import datetime
from abc import ABC
from .whois import Whois
from discord.ext import commands

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    pass

class Utility(Whois, commands.Cog, name='utility', metaclass=CompositeMetaClass):
    """
    Some basic utility commands.
    """
    def __init__(self, client):
        self.client = client

    @commands.guild_only()
    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """
        Shows the bot uptime from when it was started.
        """
        since = self.client.uptime.strftime("%b %d, %H:%M:%S")
        delta = datetime.datetime.utcnow() - self.client.uptime
        uptime_str = humanize.precisedelta(delta, format="%0.0f")
        embed = discord.Embed(color=self.client.embed_color, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Uptime", value=uptime_str, inline=False)
        embed.add_field(name='Since', value=since, inline=False)
        embed.set_author(name=ctx.me.name)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name='ping')
    async def ping(self, ctx):
        """
        Get bot's latency.
        """
        start = time.monotonic()
        message = await ctx.send("Ping?")
        end = time.monotonic()
        totalping = round((end - start) * 1000)
        embed = discord.Embed(title='Pong!', color=self.client.embed_color)
        embed.description = f"**API:** `{round(self.client.latency * 1000)}` ms\n**RoundTrip:** `{totalping}` ms"
        try:
            await message.edit(content=None, embed=embed)
        except discord.NotFound:
            await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name='prefix')
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx, prefix: str = None):
        if prefix is None:
            embed = discord.Embed(color=self.client.embed_color)
            current_prefix = self.client.get_guild_prefix(ctx.guild)
            embed.description = "<:greentick:806531672140283944> **Server's current prefix is :** `{}`".format(current_prefix)
            return await ctx.send(embed=embed)
        if "@everyone" in prefix or "@here" in prefix:
            return await ctx.send("You can't do that.")
        try:
            await self.client.set_prefix(ctx.guild, prefix)
            embed = discord.Embed(color=self.client.embed_color)
            embed.description = "<:greentick:806531672140283944> **Server's prefix changed to `{}`**".format(prefix)
            await ctx.send(embed=embed)
        except Exception:
            return await ctx.send_error()