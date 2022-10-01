import discord
from discord.ext import commands
from main import dvvt
import asyncio

from utils.format import plural
from utils.helper import get_channel_capacity


class PrivChannelTags(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    async def get_owner_channel(self, owner: discord.Member) -> discord.TextChannel:
        channel = await self.client.db.fetchval("SELECT channel_id FROM channels WHERE owner_id = $1 AND active = TRUE", owner.id)
        channel = self.client.get_channel(channel)
        return channel

    pvcGroup = discord.SlashCommandGroup(name="privchannel", description="Manage your private channel.", default_member_permissions=discord.Permissions(administrator=True))

    @pvcGroup.command(name="rename")
    @commands.cooldown(2, 600, commands.BucketType.user)
    async def rename(self, ctx: discord.ApplicationContext, channel_name: discord.Option(str, "Your private channel's new name", min_length=1, max_length=32)):
        """
        Rename your private channel.
        """
        channel = await self.get_owner_channel(ctx.author)
        if channel is None:
            return await ctx.respond(embed=discord.Embed(title="<:DVB_False:887589731515392000> Channel rename failed", description="You don't own a private channel.", color=discord.Color.red()))
        old_channel_name = channel.name
        await channel.edit(name=channel_name)
        await ctx.respond(embed=discord.Embed(title="<:DVB_True:887589686808309791> Channel renamed", description=f"Your private channel has been renamed from **{old_channel_name}** to {channel.mention}.", color=discord.Color.green()))

    @pvcGroup.command(name="add")
    async def add(self, ctx: discord.ApplicationContext, member: discord.Option(discord.Member, "A friend you want to add to your private channel.")):
        """
        Add a friend to your private channel.
        """
        channel = await self.get_owner_channel(ctx.author)
        if channel is None:
            return await ctx.respond(embed=discord.Embed(title="<:DVB_False:887589731515392000> Failed", description="You don't own a private channel.", color=discord.Color.red()))
        if member in channel.overwrites:
            return await ctx.respond(embed=discord.Embed(title="<:DVB_False:887589731515392000> Failed", description=f"{member.mention} is already in your private channel {channel.mention}.", color=discord.Color.red()))
        members = [overwriteobject for overwriteobject in channel.overwrites if isinstance(overwriteobject, discord.Member) and not overwriteobject.bot]
        members.remove(ctx.author)
        if len(members) >= get_channel_capacity(ctx.author):
            minimum_removal = len(members) - get_channel_capacity(ctx.author) + 1
            return await ctx.respond(embed=discord.Embed(title="<:DVB_False:887589731515392000> Failed", description=f"Your private channel {channel.mention} is full.\n\nYou need to remove **{plural(minimum_removal):member}** from your channel via </privchannel remove:1020235323785105418>.\nSee your channel capacity and members via </privchannel view:1020235323785105418>.", color=discord.Color.red()))
        overwrite = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            add_reactions=True,
            use_external_emojis=True,
            manage_messages=True,
            read_message_history=True
        )
        await channel.set_permissions(member, overwrite=overwrite)
        await ctx.respond(embed=discord.Embed(title="<:DVB_True:887589686808309791> Success", description=f"{member.mention} has been added to your private channel {channel.mention}.", color=discord.Color.green()))

    @pvcGroup.command(name="remove")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def remove(self, ctx: discord.ApplicationContext, member: discord.Option(discord.Member, "A friend you want to remove from your private channel.")):
        """
        Add a friend to your private channel.
        """
        channel = await self.get_owner_channel(ctx.author)
        if channel is None:
            return await ctx.respond(embed=discord.Embed(title="<:DVB_False:887589731515392000> Failed", description="You don't own a private channel.", color=discord.Color.red()))
        if member not in channel.overwrites:
            return await ctx.respond(embed=discord.Embed(title="<:DVB_False:887589731515392000> Failed", description=f"{member.mention} is not in your private channel {channel.mention}.", color=discord.Color.red()))
        await channel.set_permissions(member, overwrite=None)
        await ctx.respond(embed=discord.Embed(title="<:DVB_True:887589686808309791> Success", description=f"{member.mention} has been removed from your private channel {channel.mention}.", color=discord.Color.green()))

    @pvcGroup.command(name="view")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def view(self, ctx: discord.ApplicationContext):
        """
        View your private channel details, including your friends in your private channel.
        """
        channel = await self.get_owner_channel(ctx.author)
        if channel is None:
            return await ctx.respond(embed=discord.Embed(title="<:DVB_False:887589731515392000> Failed", description="You don't own a private channel.", color=discord.Color.red()))
        owner = ctx.author
        members = [overwriteobject for overwriteobject in channel.overwrites if isinstance(overwriteobject, discord.Member) and not overwriteobject.bot] # gets all members who have some sort of overwrite in that channel
        membersin = []
        for member in members:
            if owner is not None:
                if member.id == owner.id:
                    continue
            permissions = channel.permissions_for(member)
            if permissions.view_channel == True:
                membersin.append(f"**{member}** {member.mention}")
        if owner is not None:
            owner_str = f"**{owner}** {owner.mention}"
            if not (channel.permissions_for(owner).send_messages and channel.permissions_for(owner).view_channel):
                owner_str += "\n<:DVB_False:887589731515392000>  Not in channel"
        else:
            owner_str = "Unknown"

        membermsg = "".join(f"`{count}.` {i}\n" for count, i in enumerate(membersin, start=1))
        embed = discord.Embed(title=f"Private Channel Details of #{channel.name}", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.add_field(name="Owner 🧑‍⚖️", value=owner_str, inline=True)
        embed.add_field(name="Members", value=membermsg if len(membermsg) > 0 else "No one is in this channel.", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Member Count", value=f"`{len(membersin)}` of **{get_channel_capacity(ctx.author)}**", inline=True)
        embed.add_field(name="Created at", value=channel.created_at.strftime("%a, %b %d, %Y") if channel.created_at is not None else 'Unknown')
        category = discord.utils.get(ctx.guild.categories, id=channel.category_id)
        embed.add_field(name="Under Category", value=category.name or "Unknown")
        await ctx.respond(embed=embed)

    @pvcGroup.command(name="topic")
    @commands.cooldown(2, 600, commands.BucketType.user)
    async def topic(self, ctx: discord.ApplicationContext, channel_topic: discord.Option(str, "Your private channel's new topic", min_length=1, max_length=1024)):
        """
        Change your private channel's topic.
        """
        channel = await self.get_owner_channel(ctx.author)
        if channel is None:
            return await ctx.respond(embed=discord.Embed(title="<:DVB_False:887589731515392000> Channel rename failed", description="You don't own a private channel.", color=discord.Color.red()))
        await channel.edit(topic=channel_topic)
        await ctx.respond(embed=discord.Embed(title="<:DVB_True:887589686808309791> Channel topic changed", description=f"Your private channel {channel.mention}'s topic has been changed.", color=discord.Color.green()))