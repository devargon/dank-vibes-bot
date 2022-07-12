import asyncio
from typing import Optional

import asyncpg
import discord
from discord.ext import commands
from main import dvvt
from utils import checks
from utils.context import DVVTcontext
from utils.format import generate_loadbar
from utils.time import humanize_timedelta


def is_payout_channel(channel: discord.TextChannel):
    if ("dank" in channel.name or "nitro" in channel.name or "ticket" in channel.name or "closed" in channel.name) and channel.category is None or channel.category_id == 608506105835814933:
        return True

SQL_CREATION = "CREATE TABLE IF NOT EXISTS payoutchannels(channel_id BIGINT PRIMARY KEY, ticket_user_id BIGINT, staff BIGINT)"

class PayoutManagement(commands.Cog):
    def __init__(self, client: dvvt):
        self.client = client

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        if isinstance(channel, discord.TextChannel):
            if is_payout_channel(channel):
                def check(m: discord.Message):
                    return m.author.id == 557628352828014614 and len(m.mentions) > 0 and "follow the instructions" in m.content
                try:
                    m = await self.client.wait_for('message', check=check, timeout=30)
                except asyncio.TimeoutError:
                    pass
                else:
                    ticket_user = m.mentions[0]
                    try:
                        await self.client.db.execute("INSERT INTO payoutchannels VALUES($1, $2, $3)", channel.id, ticket_user.id, None)
                    except asyncpg.exceptions.UniqueViolationError:
                        pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if isinstance(channel, discord.TextChannel):
            if is_payout_channel(channel):
                await self.client.db.execute("DELETE FROM payoutchannels WHERE channel_id = $1", channel.id)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if is_payout_channel(message.channel):
            if not message.author.bot:
                row = await self.client.db.fetchrow("SELECT * FROM payoutchannels WHERE channel_id = $1", message.channel.id)
                if row is not None:
                    if discord.utils.get(message.author.roles, id=608495204399448066) is not None or discord.utils.get(message.author.roles, id=608500355973644299):
                        await self.client.db.execute("UPDATE payoutchannels SET staff = $1 WHERE channel_id = $2", message.author.id, message.channel.id)
                else:
                    await self.client.db.execute("INSERT INTO payoutchannels(channel_id, staff) VALUES($1, $2)", message.channel.id, message.author.id)


    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command()
    async def dankgw(ctx):
        await ctx.message.delete()
        if "dankgw" in ctx.channel.name:
            pass
        else:
            old_name = ctx.channel.name.replace('ticket-', '')
            await ctx.channel.edit(name=f"dankgw-{old_name}")

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command()
    async def dankevent(ctx):
        await ctx.message.delete()
        if "dankevent" in ctx.channel.name:
            pass
        else:
            old_name = ctx.channel.name.replace('ticket-', '')
            await ctx.channel.edit(name=f"dankevent-{old_name}")

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command()
    async def nitro(ctx):
        await ctx.message.delete()
        old_name = ctx.channel.name.replace('ticket-', '')
        await ctx.channel.edit(name=f"nitro-{old_name}")

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command()
    async def tickets(self, ctx: DVVTcontext, channel: Optional[discord.TextChannel] = None):
        if channel is None:
            channel = ctx.channel
        if is_payout_channel(channel):
            categories = []
            if "ticket" in channel.name:
                categories.append("Uncategorised")
            else:
                if "dankgw" in channel.name:
                    categories.append("Dank Giveaway")
                if "dankevent" in channel.name:
                    categories.append("Dank Event")
                if "nitro" in channel.name:
                    categories.append("Nitro Giveaway/Event")

            description = [" | ".join(categories)]
            row = await self.client.db.fetchrow("SELECT * FROM payoutchannels WHERE channel_id = $1", channel.id)
            staff = ctx.guild.get_member(row.get("staff")) if row is not None else None
            description.append(f"Claimed by: {staff or 'No one'}")
            description.append(f"Open for: {humanize_timedelta(seconds=round(discord.utils.utcnow().timestamp() - channel.created_at.timestamp()))}")
            embed = discord.Embed(title=channel.name, description="\n".join(description), color=self.client.embed_color)
        else:
            all_channels = await self.client.db.fetch("SELECT * FROM payoutchannels")
            if len(all_channels) == 0:
                await ctx.send("No payout channels found.")
                return
            channels = []
            dankgw_channels = []
            dankevent_channels = []
            nitro_channels = []
            claimed_channels = {}
            for row in all_channels:
                channel = self.client.get_channel(row.get("channel_id"))
                if channel is not None:
                    channels.append(channel)
                if "dankgw" in channel.name:
                    dankgw_channels.append(channel)
                if "dankevent" in channel.name:
                    dankevent_channels.append(channel)
                if "nitro" in channel.name:
                    nitro_channels.append(channel)
                if row.get('staff') is not None:
                    staff = ctx.guild.get_member(row.get('staff'))
                    if staff is not None:
                        claimed_channels[channel] = staff
            descriptions = []
            descriptions.append(f"DankGw Channels: **{len(dankgw_channels)}**")
            descriptions.append(f"Dankevent Channels: **{len(dankevent_channels)}**")
            descriptions.append(f"Nitro Channels: **{len(nitro_channels)}**")
            descriptions.append(f"Claimed Channels: [{len(claimed_channels.items())}/{len(channels)}]")
            oldest_channel, oldest_time = channels[0], channels[0].created_at.timestamp()
            for channel in channels:
                if channel.created_at.timestamp() < oldest_time:
                    oldest_channel, oldest_time = channel, channel.created_at.timestamp()
            descriptions.append(f"Oldest Channel: {oldest_channel.name} (Created **{humanize_timedelta(seconds=round(discord.utils.utcnow().timestamp() - oldest_time))}** ago)")

            embed = discord.Embed(title="Payout Channels Summary", color=self.client.embed_color)
            capacity = 500 - (len(ctx.guild.channels) - len(channels))
            loadbar = generate_loadbar(len(channels)/capacity, 20)
            embed.add_field(name="Ticket Capacity", value=f"`[{len(channels)}/{capacity}]`{loadbar}", inline=False)
            #dankgw_channels_mention = " ".join([c.mention for c in dankgw_channels])
            #dankevent_channels_mention = " ".join([c.mention for c in dankevent_channels])
            #nitro_channels_mention = " ".join([c.mention for c in nitro_channels])
            if len(channels) - len(claimed_channels) > 0:
                unclaimed_channels = [c.mention for c in channels if c not in claimed_channels.items()]
                embed.add_field(name="Unclaimed Channels", value="\n".join(unclaimed_channels), inline=False)
        await ctx.send(embed=embed)
