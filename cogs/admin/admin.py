import asyncio
import discord
from abc import ABC
from datetime import datetime
from discord.ext import commands
from .serverrule import ServerRule
from .sticky import Sticky

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    pass
class Admin(Sticky, ServerRule, commands.Cog, name='admin', metaclass=CompositeMetaClass):
    """
    Server Commands
    """
    def __init__(self, client):
        self.client = client
        self.queue = []

    async def handle_toggle(self, guild, settings) -> bool:
        if (result := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", guild.id, settings)) is not None:
            result = result.get('enabled')
        else:
            await self.client.pool_pg.execute("INSERT INTO serverconfig VALUES ($1, $2, $3)", guild.id, settings, False)
            result = False
        if result:
            result = False
        else:
            result = True
        await self.client.pool_pg.execute("UPDATE serverconfig SET enabled=$1 WHERE guild_id=$2 AND settings=$3", result, guild.id, settings)
        return result

    @commands.command(name='leaderboards')
    @commands.has_guild_permissions(administrator=True)
    async def leaderboards(self, ctx):
        """
        Shows guild's leaderboard settings and also allows you to allow/disable them.
        """
        def get_emoji(enabled):
            if enabled:
                return "<:DVB_enabled:872003679895560193>"
            return "<:DVB_disabled:872003709096321024>"
        embed = discord.Embed(title=f"Leaderboard Settings For {ctx.guild.name}", color=self.client.embed_color, timestamp=datetime.utcnow())
        if (owodaily := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", ctx.guild.id, "owodailylb")) is not None:
            owodaily = owodaily.get('enabled')
        if (owoweekly := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", ctx.guild.id, "owoweeklylb")) is not None:
            owoweekly = owoweekly.get('enabled')
        if (votelb := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", ctx.guild.id, "votelb")) is not None:
            votelb = votelb.get('enabled')
        embed.add_field(name=f"{get_emoji(owodaily)} OwO Daily Leaderboard", value=f"{'Enabled' if owodaily else 'Disabled'}", inline=False)
        embed.add_field(name=f"{get_emoji(owoweekly)} OwO Weekly Leaderboard", value=f"{'Enabled' if owoweekly else 'Disabled'}", inline=False)
        embed.add_field(name=f"{get_emoji(votelb)} Vote Leaderboard", value=f"{'Enabled' if votelb else 'Disabled'}", inline=False)
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        message = await ctx.send(embed=embed)
        emojis = ['1⃣', '2⃣', '3⃣', 'ℹ']
        for emoji in emojis:
            await message.add_reaction(emoji)
        def check(payload):
                return payload.user_id == ctx.message.author.id and payload.channel_id == ctx.channel.id and payload.message_id == message.id and str(payload.emoji) in emojis
        while True:
            try:
                response = await self.client.wait_for('raw_reaction_add', timeout=15, check=check)
            except asyncio.TimeoutError:
                return await message.clear_reactions()
            if str(response.emoji) == emojis[0]:
                owodaily = await self.handle_toggle(ctx.guild, "owodailylb")
                embed.set_field_at(index=0, name=f"{get_emoji(owodaily)} OwO Daily Leaderboard", value=f"{'Enabled' if owodaily else 'Disabled'}", inline=False)
                await message.edit(embed=embed)
            elif str(response.emoji) == emojis[1]:
                owoweekly = await self.handle_toggle(ctx.guild, 'owoweeklylb')
                embed.set_field_at(index=1, name=f"{get_emoji(owoweekly)} OwO Weekly Leaderboard", value=f"{'Enabled' if owoweekly else 'Disabled'}", inline=False)
                await message.edit(embed=embed)
            elif str(response.emoji) == emojis[2]:
                votelb = await self.handle_toggle(ctx.guild, 'votelb')
                embed.set_field_at(index=2, name=f"{get_emoji(votelb)} Vote Leaderboard", value=f"{'Enabled' if votelb else 'Disabled'}", inline=False)
                await message.edit(embed=embed)
            elif str(response.emoji) == emojis[3]:
                tempembed = discord.Embed(title='Information', color=self.client.embed_color, description="React with the emojis to toggle leaderboards")
                tempembed.add_field(name='Reactions' ,value=f"{emojis[0]} Toggles OwO daily leaderboard\n{emojis[1]} Toggles OwO weekly leaderboard\n{emojis[2]} Toggles vote leaderboard\n{emojis[3]} Shows this infomation message.")
                await message.edit(embed=tempembed)
            await message.remove_reaction(response.emoji, ctx.author)
        
    @commands.command(name="setnickchannel", aliases = ["nickchannel"])
    @commands.has_guild_permissions(administrator=True)
    async def setchannel(self, ctx, channel:discord.TextChannel=None):
        """
        Set the channel for nickname requests to be sent to.
        """
        result = await self.client.pool_pg.fetch("SELECT * FROM channelconfigs where guild_id = $1", ctx.guild.id)
        if len(result) == 0:
            await self.client.pool_pg.execute("INSERT INTO channelconfigs(guild_id, nicknamechannel_id) VALUES($1, $2)", ctx.guild.id, channel.id)
            return await ctx.send(f"I will now send nickname requests to {channel.mention}.")
        else:
            await self.client.pool_pg.execute("UPDATE channelconfigs SET nicknamechannel_id = $1 where guild_id = $2", channel.id, ctx.guild.id)
            await self.client.pool_pg.execute("DELETE FROM nicknames")
            return await ctx.send(f"I will now send nickname requests to {channel.mention}.\nAll nickname requests sent in a previous channel have been forfeited.")

    @commands.command(name="setdmchannel", aliases = ["dmchannel"])
    @commands.has_guild_permissions(administrator=True)
    async def setdmchannel(self, ctx, channel:discord.TextChannel=None):
        """
        Set the channel for dmname requests to be sent to.
        """
        result = await self.client.pool_pg.fetch("SELECT * FROM channelconfigs where guild_id = $1", ctx.guild.id)
        if len(result) == 0:
            await self.client.pool_pg.execute("INSERT INTO channelconfigs(guild_id, dmchannel_id) VALUES($1, $2)", ctx.guild.id, channel.id)
            return await ctx.send(f"I will now send DM requests to {channel.mention}.")
        else:
            await self.client.pool_pg.execute("UPDATE channelconfigs SET dmchannel_id = $1 where guild_id = $2", channel.id, ctx.guild.id)
            await self.client.pool_pg.execute("DELETE FROM dmrequests")
            return await ctx.send(f"I will now send DM requests to {channel.mention}.\nAll DM requests sent in a previous channel have been forfeited.")

    @commands.command(name="viewconfig")
    @commands.has_guild_permissions(administrator=True)
    async def viewconfig(self, ctx, channel: discord.TextChannel = None):
        """
        Show configurations for nickname and DM requests.
        """
        result = await self.client.pool_pg.fetchrow("SELECT * FROM channelconfigs where guild_id = $1", ctx.guild.id)
        if len(result) == 0:
            return await ctx.send(f"No configuration for DM and nickname requests have been set yet. ")
        else:
            await ctx.send(embed=discord.Embed(title=f"Configurations for {ctx.guild.name}", description = f"Nickname requests: {ctx.guild.get_channel(result.get('nicknamechannel_id'))}\nDM requests: {ctx.guild.get_channel(result.get('dmchannel_id'))}", color = 0x57F0F0))