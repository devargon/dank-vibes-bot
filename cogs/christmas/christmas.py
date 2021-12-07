import discord
from discord.ext import commands
from utils import checks
from utils.format import human_join
from typing import Optional

def format_channel(list_of_channels, split:Optional[bool] = False):
    """
    Formats a list of channels into a string.
    """
    if split == False:
        if len(list_of_channels) > 70:
            return ", ".join(list_of_channels[:70]) + f" and {len(list_of_channels) - 70}"
        else:
            return human_join(list_of_channels, ', ', 'and')
    else:
        if len(list_of_channels) > 35:
            return "\n".join(list_of_channels[:35]) + f"\n**And {len(list_of_channels) - 35} more...**"
        else:
            return "\n".join(list_of_channels)


class Christmas(commands.Cog, name="christmas"):
    """
    Christmas Celebration Features
    """
    def __init__(self, client):
        self.client = client
        self.rate = {}
        self.ignoredchannels = {}
        self.ignoredcategories = {}

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name='christmasconfig', aliases=['xmasconfig'], invoke_without_command=True)
    async def christmasconfig(self, ctx):
        """
        Shows the configuration for Christmas games or changes it.

        An accepted rate is between 0 (0%) to 1 (100%), but the lowest rate must have a maximum of 2 decimal points, otherwise the bot may read the rate as 0 instead.
        """
        extrasummary = ""
        guildid = str(ctx.guild.id)
        if guildid not in self.rate:
            rate = await self.client.pool_pg.fetchval("SELECT percentage FROM christmaseventconfig WHERE guild_id = $1", ctx.guild.id)
            if rate is None:
                rate = 0
            self.rate[guildid] = rate
        else:
            rate = self.rate[guildid]
        if rate > 1:
            result = "**spawn on every message sent**"
        elif rate == 0:
            result = "**not spawn**"
        else:
            result = f"have a **{round(rate*100, 2)}**% of spawning when a message is sent"
        embed = discord.Embed(title="Christmas Event Config for {}".format(ctx.guild.name), description=f"Chistmas game events will {result}.")
        array = []
        cached_channels = []
        deleted_channels = []
        if guildid not in self.ignoredchannels:
            ignoredchannels = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmaschan WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredchannels) == 0:
                ignoredchannels = []
                self.ignoredchannels[guildid] = ignoredchannels
                array = ["None"]
                deleted_channels = []
            else:
                extrasummary = ""
                ids = [entry.get('channel_id') for entry in ignoredchannels]
        else:
            ids = [channel_id for channel_id in self.ignoredchannels[guildid]]
        if array != ["None"]:
            for channel_id in ids:
                channel = ctx.guild.get_channel(channel_id)
                if channel is not None:
                    print(array)
                    array.append(channel.mention)
                    cached_channels.append(channel.id)
                else:
                    await self.client.pool_pg.execute("DELETE FROM ignoredchristmaschan WHERE channel_id = $1", channel_id)
                    deleted_channels.append(channel_id)
            if guildid not in self.ignoredchannels or cached_channels != self.ignoredchannels[guildid]:
                self.ignoredchannels[guildid] = cached_channels
        embed.add_field(name="Ignored Channels", value=format_channel(array, split=True) if len(array) > 0 else "None")
        if len(deleted_channels) > 0:
            extrasummary += f"\n\n**These channels do not exist and were deleted from the list of ignored channels:** {', '.join(deleted_channels)}"
        array = []
        cached_categories = []
        deleted_categories = []
        if guildid not in self.ignoredcategories:
            ignoredcategories = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmascat WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredcategories) == 0:
                ignoredcategories = []
                self.ignoredcategories[guildid] = ignoredcategories
                array = ["None"]
            else:
                array = []
                categoryids = [entry.get('category_id') for entry in ignoredcategories]
                for entry in ignoredcategories:
                    category_id = entry.get('category_id')
                    category = ctx.guild.get_channel(category_id)
                    if category is not None and isinstance(category, discord.CategoryChannel):
                        array.append(category.name)
                        cached_categories.append(category.id)
                    else:
                        await self.client.pool_pg.execute("DELETE FROM ignoredchristmascat WHERE category_id = $1", category_id)
                        deleted_categories.append(category_id)
        else:
            categoryids = [category_id for category_id in self.ignoredcategories[guildid]]
        if array != ["None"]:
            for category_id in self.ignoredcategories[guildid]:
                category = ctx.guild.get_channel(category_id)
                if category is not None and isinstance(category, discord.CategoryChannel):
                    array.append(category.name)
                    cached_categories.append(category.id)
                else:
                    await self.client.pool_pg.execute("DELETE FROM ignoredchristmascat WHERE category_id = $1", category_id)
                    deleted_categories.append(category_id)
            if guildid not in self.ignoredcategories or cached_categories != self.ignoredcategories[guildid]:
                self.ignoredcategories[guildid] = cached_categories
        embed.add_field(name="Ignored Categories", value=format_channel(array, split=True) if len(array) > 0 else "None")
        if len(deleted_categories) > 0:
            extrasummary += f"\n\n**These categories are invalid and were deleted from the list of ignored categories:** {', '.join(deleted_categories)}"
        if extrasummary:
            embed.add_field(name="Also..", value=extrasummary, inline=False)
        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @christmasconfig.command(name="rate", aliases=["r"])
    async def rate_config(self, ctx, rate:str = None):
        """
        Sets the percentage that events will have a chance to spawn.
        """
        if rate is None:
            return await ctx.send("Please specify a rate between 0 and 1. To see the current rate set, use `dv.xmasconfig`.")
        try:
            rate = float(rate)
        except ValueError:
            await ctx.send("The rate must be a number between 0 to 100.")
        else:
            if rate > 1:
                rate = 1
            elif rate < 0:
                rate = 0
            if rate >= 1:
                additional = "**Events will now spawn on each message sent.**"
            elif rate <= 0:
                additional = "**Events will not spawn.**"
            else:
                additional = ""
            await self.client.pool_pg.execute("UPDATE christmaseventconfig SET PERCENTAGE = $1 WHERE guild_id = $2", rate, ctx.guild.id)
            guildid = str(ctx.guild.id)
            self.rate[guildid] = rate
            await ctx.send(f"The rate has been set to {rate * 100}%.\n{additional}")

    @checks.has_permissions_or_role(manage_roles=True)
    @christmasconfig.command(name="ignorechannel", aliases=["ichan"])
    async def ignore_channel_config(self, ctx, channels: commands.Greedy[discord.TextChannel]):
        """
        This adds channels that Dank Vibes Bot will not spawn events in. You can specify multiple channels in this command.
        """
        guildid = str(ctx.guild.id)
        if guildid not in self.ignoredchannels:
            ignoredchannels = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmaschan WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredchannels) == 0:
                ignoredchannels = []
                self.ignoredchannels[guildid] = ignoredchannels
            else:
                ids = [entry.get('channel_id') for entry in ignoredchannels]
                self.ignoredchannels[guildid] = ids
        if len(channels) == 0:
            await ctx.send("You must specify at least one channel.")
            return
        if guildid not in self.ignoredchannels:
            self.ignoredchannels[guildid] = []
        ignoredchannels = self.ignoredchannels[guildid]
        added_channels = []
        already_added = []
        for channel in channels:
            if channel.id in ignoredchannels:
                already_added.append(channel.mention)
            else:
                await self.client.pool_pg.execute("INSERT INTO ignoredchristmaschan (guild_id, channel_id) VALUES ($1, $2)", ctx.guild.id, channel.id)
                ignoredchannels.append(channel.id)
                added_channels.append(channel.mention)
        self.ignoredchannels[guildid] = ignoredchannels
        if len(added_channels) > 0:
            added_channel_string = format_channel(added_channels)
        else:
            added_channel_string = ""
        if len(already_added) > 0:
            already_added_string = format_channel(already_added)
        else:
            already_added_string = ""
        embed = discord.Embed(title="Success!", description=f"{added_channel_string} will now be ignored by the bot." if len(added_channel_string) > 0 else "", color=discord.Color.green())
        if already_added_string:
            embed.add_field(name="Already Added", value=f"{already_added_string} was aleady in the list of ignored channels.", inline=False)
            embed.color = discord.Color.yellow()
        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @christmasconfig.command(name="unignorechannel", aliases=["uichan"])
    async def unignore_channel_config(self, ctx, channels: commands.Greedy[discord.TextChannel]):
        """
        This removes channels from the list of channels that Dank Vibes Bot will not spawn events in. You can specify multiple channels in this command.
        """
        guildid = str(ctx.guild.id)
        if guildid not in self.ignoredchannels:
            ignoredchannels = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmaschan WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredchannels) == 0:
                ignoredchannels = []
                self.ignoredchannels[guildid] = ignoredchannels
            else:
                ids = [entry.get('channel_id') for entry in ignoredchannels]
                self.ignoredchannels[guildid] = ids
        if len(channels) == 0:
            await ctx.send("You must specify at least one channel.")
            return
        if guildid not in self.ignoredchannels:
            self.ignoredchannels[guildid] = []
        ignoredchannels = self.ignoredchannels[guildid]
        removed_channels = []
        not_exist = []
        for channel in channels:
            if channel.id not in ignoredchannels:
                not_exist.append(channel.mention)
            else:
                await self.client.pool_pg.execute("DELETE FROM ignoredchristmaschan WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, channel.id)
                ignoredchannels.remove(channel.id)
                removed_channels.append(channel.mention)
        self.ignoredchannels[guildid] = ignoredchannels
        if len(removed_channels) > 0:
            added_channel_string = format_channel(removed_channels)
        else:
            added_channel_string = ""
        if len(not_exist) > 0:
            already_added_string = format_channel(not_exist)
        else:
            already_added_string = ""
        embed = discord.Embed(title="Success!", description=f"{added_channel_string} has been removed from the list of ignored channels." if len(added_channel_string) > 0 else "", color=discord.Color.green())
        if already_added_string:
            embed.add_field(name="Already Revmoed", value=f"{already_added_string} were not in the list of ignored channels.", inline=False)
            embed.color = discord.Color.yellow()
        await ctx.send(embed=embed)












