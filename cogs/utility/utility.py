import sys
import time
import discord
import humanize
import datetime
from abc import ABC
from .whois import Whois
from .l2lvc import L2LVC
from .nicknames import nicknames
from discord.ext import commands
from .teleport import Teleport

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    pass

class Utility(Whois, L2LVC, nicknames, Teleport, commands.Cog, name='utility', metaclass=CompositeMetaClass):
    """
    Utility commands
    """
    def __init__(self, client):
        self.client = client
        self.nickconfig = {}

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
        start = time.perf_counter()
        message = await ctx.send("Ping?")
        end = time.perf_counter()
        totalping = round((end - start) * 1000)
        embed = discord.Embed(title='Pong!', color=self.client.embed_color)
        embed.description = f"**API:** `{round(self.client.latency * 1000)}` ms\n**RoundTrip:** `{totalping}` ms"
        try:
            await message.edit(content=None, embed=embed)
        except discord.NotFound:
            await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name='prefix', usage='[prefix]')
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix(self, ctx, *, prefix: str = None):
        """
        Changes the server's prefix.
        """
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

    @commands.command(name='info')
    async def info(self, ctx):
        """
        Shows some information about this bot.
        """
        value_1 = []
        value_1.append(f'⚙ Commands: {len(self.client.commands)}')
        value_1.append(f'<:user_mention:868806554961453116> Users: `{len(self.client.users)}`')
        text = 0
        voice = 0
        stage = 0
        for guild in self.client.guilds:
            if guild.unavailable:
                continue
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text += 1
                elif isinstance(channel, discord.VoiceChannel):
                    voice += 1
                elif isinstance(channel, discord.StageChannel):
                    stage += 1
        value_1.append(f"<:text_channel:868806636230283314>  Text Channels: `{text}`")
        value_1.append(f'<:voice_channel:868806601123958834> Voice Channels: `{voice}`')
        if stage != 0:
            value_1.append(f'<:stage_channel:868806674452987924> Stage Channels: `{stage}`')
        py_version = "{}.{}.{}".format(*sys.version_info[:3])
        dpy_version = discord.__version__
        embed = discord.Embed(color=self.client.embed_color)
        embed.add_field(name='Stats', value="\n".join(value_1), inline=True)
        embed.add_field(name='Versions', value=f"<:python:868806455317393428> Python: `{py_version}`\n<:discordpy:868806486241992724> Discord.py: `{dpy_version}`", inline=True)
        embed.add_field(name='Developers', value=f"{str(self.client.get_user(650647680837484556))}\n{str(self.client.get_user(321892489470410763))}", inline=True)
        embed.add_field(name="Credits", value=f"{str(await self.client.fetch_user(727498137232736306))}", inline=True)
        embed.set_author(name=str(ctx.guild.me), icon_url=ctx.guild.me.avatar_url)
        embed.set_thumbnail(url=ctx.guild.me.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name='suggest', usage='<message>')
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def suggest(self, ctx, *, message: str = None):
        """
        Suggest something to the developers through the bot.
        """
        if message is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Hey! write something meaningful and try again.")
        if not await ctx.confirmation("Are you sure you wanna send this message to the developers?", cancel_message="Okay, we're not sending that message to the developers", delete_delay=5):
            ctx.command.reset_cooldown(ctx)
            return
        channel = self.client.get_channel(876346196564803614)
        query = "INSERT INTO suggestions VALUES(DEFAULT, $1, $2) RETURNING id"
        suggestion_id = await self.client.pool_pg.fetchval(query, ctx.author.id, message, column='id')
        await ctx.checkmark()
        author = f"Suggestion from {ctx.author} ({suggestion_id})"
        suggestionembed = discord.Embed(color=self.client.embed_color, description=message, timestamp=datetime.datetime.utcnow())
        suggestionembed.set_author(name=author, icon_url=ctx.author.avatar_url)
        suggestionembed.set_footer(text=ctx.author.id)
        return await channel.send(embed=suggestionembed)