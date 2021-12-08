import discord
from discord.ext import commands, menus, tasks
from utils import checks
from utils.format import human_join
from utils.menus import CustomMenu
from typing import Optional
import random
import time
import os
from .removingaccess import RemovingAccess

modchannel = 743174564778868796 if os.getenv('state') == '0' else 871737314831908974

something = ["Custom Role", "Free Odd Eye Raffle Entry", "+1 Amari Level", "+2 Amari Level", "+3 Amari Level",
             "Access to reaction snipe", "Access to #general-spam (25x/50x multi)", "Create a private channel",
             "1x/2x role multiplier", "Access to #reaction-logs", "Access to #dyno-message-logs",
             "Join a surprise heist", "Use slash commands", "Access to `dv.dm`", "Access to `-paint`",
             "Use Color roles", "Access to `dv.es`"]
weights = [1, 2, 2, 2, 1, 3, 2, 2, 2, 3, 3, 3, 2, 3, 3, 3, 3, ]

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

class ListPerks(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=10)

    async def format_page(self, menu, page):
        embed = discord.Embed(color=menu.ctx.bot.embed_color, title=self.title, timestamp=discord.utils.utcnow())
        for entry in page:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        return embed

class ChoosePrize(discord.ui.View):
    def __init__(self, prizes, member):
        self.member = member
        self.prizes = prizes
        self.prize = None
        self.response = None
        super().__init__(timeout=15.0)

        async def manage_prize(label):
            self.prize = label
            for b in self.children:
                b.disabled = True
            await self.response.edit(view=self)
            self.stop()

        class Prize(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await manage_prize(self.label)

        for prize in self.prizes:
            self.add_item(Prize(label=prize, style=discord.ButtonStyle.blurple))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.member:
            await interaction.response.send_message("These aren't your prizes to claim 😑", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        for b in self.children:
            b.disabled = True
        await self.response.edit(content="You failed to claim your prize.", view=self)




class Christmas(RemovingAccess, commands.Cog, name="christmas"):
    """
    Christmas Celebration Features
    """
    def __init__(self, client):
        self.client = client
        self.rate = {}
        self.ignoredchannels = {}
        self.ignoredcategories = {}
        self.remind_perk_removal.start()
        self.command_removal.start()

    async def manage_prize(self, message, prize, member):
        if prize == "Custom Role":
            await message.channel.send("You chose the **Custom Role**!\nYou will be able to keep this Custom Role for 2 days. Please wait until an admin DMs you with more information.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a custom role for 2 days\n{message.jump_url}")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, "Custom Role Perk", round(time.time()) + 172800)

        elif prize == "Free Odd Eye Raffle Entry":
            await message.channel.send("You chose the **Free Odd Eye Raffle Entry**!\nYou can redeem a free Odd Eye entry.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) can get a free odd eye raffle entry.\n{message.jump_url}")

        elif prize == "+1 Amari Level":
            await message.channel.send("You chose the **+1 Amari Level**!\nYour extra level will be added to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won **+1 Amari Level**.\n{message.jump_url}")

        elif prize == "+2 Amari Level":
            await message.channel.send("You chose the **+2 Amari Level**!\nYour extra level will be added to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won **+2 Amari Level**\n{message.jump_url}")

        elif prize == "+3 Amari Level":
            await message.channel.send("You chose the **+3 Amari Level**!\nYour extra level will be added to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **+3 Amari Level**\n{message.jump_url}")

        elif prize == "Access to reaction snipe":
            await message.channel.send("You chose the **Access to reaction snipe**!\nYou can start using `dv.rs` until your access is automatically removed in 2 days.")
            await self.client.pool_pg.execute("INSERT INTO commandaccess(member_id, command, until) VALUES($1, $2, $3)", member.id, "reactionsnipe", round(time.time()) + 172800)

        elif prize == "Access to #general-spam (25x/50x multi)":
            await message.channel.send("You chose the **Access to #general-spam (25x/50x multi)**!\nYour access to the channel will be given as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won **Access to #general-spam\n{message.jump_url}")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Create a private channel":
            await message.channel.send("You chose the **Create a private channel**!\nYou will be given access to create a private channel in <#763458133116059680> as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Create a private channel**\n{message.jump_url}")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "1x/2x role multiplier":
            await message.channel.send("You chose the **1x/2x role multiplier**!\nMessages you sent will have an additional multiplier in AmariBot for 2 days. This perk will be given to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **1x/2x role multiplier**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Access to #reaction-logs":
            await message.channel.send("You chose the **Access to #reaction-logs**!\nYou will be given access to <#847710145001029672> as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Access to #reaction-logs**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize,round(time.time()) + 172800)

        elif prize == "Access to #dyno-message-logs":
            await message.channel.send("You chose the **Access to #dyno-message-logs**!\nYou will be given access to <#880990535282724926> as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Access to #dyno-message-logs**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize,round(time.time()) + 172800)

        elif prize == "Join a surprise heist":
            await message.channel.send("You chose the **Join a surprise heist**!\nYou can join a surprise heist xxx")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Join a surprise heist**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Use slash commands":
            await message.channel.send("You chose the **Use slash commands**!You will be able to use bots' Slash Commands for 2 days. This access will be given to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Use slash commands**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Access to `dv.dm`":
            await message.channel.send("You chose the **Access to `dv.dm`**!\nActing like a messenger, Dank Vibes Bot anonymously will DM your target on your behalf. You can do so for two days!")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Access to `dv.dm`**")
            await self.client.pool_pg.execute("INSERT INTO commandaccess VALUES($1, $2, $3)", member.id, "dm", round(time.time()) + 172800)

        elif prize == "Access to `-paint`":
            await message.channel.send("You chose the **Access to `-paint`**!\nYou will be able to make other peoples' color roles change for a short period of time! This access will be given to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Access to `-paint`**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Use Color roles":
            await message.channel.send("You chose the **Use Color roles**!\nYou will be able to grab exclusive color roles in <#641497978112180235>.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Use Color roles**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Access to `dv.es`":
            await message.channel.send("You chose the **Access to `dv.es`**!\nYou will be able to see what a user's message was before they edited it for two days!")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Access to `dv.es`**")
            await self.client.pool_pg.execute("INSERT INTO commandaccess VALUES($1, $2, $3)", member.id, "editsnipe", round(time.time()) + 172800)

    @tasks.loop()

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Main event handler for christmas games.
        """
        guildid = str(message.guild.id)
        """
        Caching the rate for the guild.
        """
        if guildid not in self.rate:
            rate = await self.client.pool_pg.fetchval("SELECT percentage FROM christmaseventconfig WHERE guild_id = $1", message.guild.id)
            if rate is None:
                rate = 0
            self.rate[guildid] = rate
        """
        Caching the ignored categories for the guild
        """
        if guildid not in self.ignoredcategories:
            ignoredcategories = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmascat WHERE guild_id = $1", message.guild.id)
            if len(ignoredcategories) == 0:
                ignoredcategories = []
                self.ignoredcategories[guildid] = ignoredcategories
            else:
                ids = [entry.get('category_id') for entry in ignoredcategories]
                self.ignoredcategories[guildid] = ids
        """
        Caching the ignored channels for the guild
        """
        if guildid not in self.ignoredchannels:
            ignoredchannels = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmaschan WHERE guild_id = $1", message.guild.id)
            if len(ignoredchannels) == 0:
                ignoredchannels = []
                self.ignoredchannels[guildid] = ignoredchannels
            else:
                ids = [entry.get('channel_id') for entry in ignoredchannels],
                self.ignoredchannels[guildid] = ids
        if message.author.bot:
            return



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
                    deleted_channels.append(str(channel_id))
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
                        array.append(f"{category.name} ({category_id})")
                        cached_categories.append(category.id)
                    else:
                        await self.client.pool_pg.execute("DELETE FROM ignoredchristmascat WHERE category_id = $1", category_id)
                        deleted_categories.append(category_id)
        else:
            categoryids = [category_id for category_id in self.ignoredcategories[guildid]]
            if guildid in self.ignoredcategories or array != ["None"]:
                for category_id in categoryids:
                    category = ctx.guild.get_channel(category_id)
                    if category is not None and isinstance(category, discord.CategoryChannel):
                        array.append(category.name)
                        cached_categories.append(category.id)
                    else:
                        await self.client.pool_pg.execute("DELETE FROM ignoredchristmascat WHERE category_id = $1", category_id)
                        deleted_categories.append(str(category_id))
            if guildid not in self.ignoredcategories or cached_categories != self.ignoredcategories[guildid]:
                self.ignoredcategories[guildid] = cached_categories
        embed.add_field(name="Ignored Categories", value=format_channel(array, split=True) if len(array) > 0 else "None")
        if len(deleted_categories) > 0:
            extrasummary += f"\n\n**These categories are invalid and were deleted from the list of ignored categories:** {', '.join(deleted_categories)}"
        if extrasummary:
            embed.add_field(name="Also..", value=extrasummary, inline=False)
        embed.set_thumbnail(url=random.choice(['https://cdn.discordapp.com/emojis/568124063675973632.gif?size=96',
                                                'https://cdn.discordapp.com/emojis/893450958326091777.png?size=96',
                                                'https://cdn.discordapp.com/emojis/817909791287934986.png?size=96',
                                                'https://cdn.discordapp.com/emojis/694973517862666360.png?size=96',
                                                'https://cdn.discordapp.com/emojis/694973517816397824.png?size=96',
                                                'https://cdn.discordapp.com/emojis/694973517677985792.png?size=96',
                                                'https://cdn.discordapp.com/emojis/733017031493943718.gif?size=96',
                                                'https://cdn.discordapp.com/emojis/706107990024913007.gif?size=96',
                                                'https://cdn.discordapp.com/emojis/643747917017907240.gif?size=96',
                                                'https://cdn.discordapp.com/emojis/766099048217313281.png?size=96',
                                                'https://cdn.discordapp.com/emojis/722195328799080459.png?size=96',
                                                'https://cdn.discordapp.com/emojis/679800699625799740.png?size=96',
                                                'https://cdn.discordapp.com/emojis/706107989047771239.gif?size=96',
                                                'https://cdn.discordapp.com/emojis/893449040421855242.png?size=96']))

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
            embed.add_field(name="Already Removed", value=f"{already_added_string} were not in the list of ignored channels.", inline=False)
            embed.color = discord.Color.yellow()
        await ctx.send(embed=embed)


    @checks.has_permissions_or_role(manage_roles=True)
    @christmasconfig.command(name="ignorecategory", aliases=["icat"])
    async def ignore_category_config(self, ctx, categories: commands.Greedy[discord.CategoryChannel]):
        """
        sets categories which channels inside will be ignored. You can provide a name, or the ID of the category.
        """
        guildid = str(ctx.guild.id)
        if guildid not in self.ignoredcategories:
            ignoredcategories = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmascat WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredcategories) == 0:
                ignoredcategories = []
                self.ignoredcategories[guildid] = ignoredcategories
            else:
                ids = [entry.get('category_id') for entry in ignoredcategories]
                self.ignoredcategories[guildid] = ids
        if len(categories) == 0:
            await ctx.send("You must specify at least one category.")
            return
        ignoredcategories = self.ignoredcategories[guildid]
        added_categories = []
        already_added = []
        for category in categories:
            if category.id not in ignoredcategories:
                await self.client.pool_pg.execute("INSERT INTO ignoredchristmascat (guild_id, category_id) VALUES ($1, $2)", ctx.guild.id, category.id)
                ignoredcategories.append(category.id)
                added_categories.append(category.name)
            else:
                already_added.append(category.mention)
        self.ignoredcategories[guildid] = ignoredcategories
        if len(added_categories) > 0:
            added_category_string = format_channel(added_categories)
        else:
            added_category_string = ""
        if len(already_added) > 0:
            already_added_string = format_channel(already_added)
        else:
            already_added_string = ""
        embed = discord.Embed(title="Success!", description=f"Channels inside **{added_category_string}** will be ignored by the bot.", color=discord.Color.green())
        if already_added_string:
            embed.add_field(name="Already Added", value=f"**{already_added_string}** were already in the list of ignored categories.", inline=False)
            embed.color = discord.Color.yellow()
        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @christmasconfig.command(name="unignorecategory", aliases=["uicat"])
    async def unignore_category_config(self, ctx, categories: commands.Greedy[discord.CategoryChannel]):
        """
        Removes categories set in the list of ignored categories.
        """
        guildid = str(ctx.guild.id)
        if guildid not in self.ignoredcategories:
            ignoredcategories = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmascat WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredcategories) == 0:
                ignoredcategories = []
                self.ignoredcategories[guildid] = ignoredcategories
            else:
                ids = [entry.get('category_id') for entry in ignoredcategories]
                self.ignoredcategories[guildid] = ids
        if len(categories) == 0:
            await ctx.send("You must specify at least one category.")
            return
        ignoredcategories = self.ignoredcategories[guildid]
        removed_categories = []
        not_exist = []
        for category in categories:
            if category.id in ignoredcategories:
                await self.client.pool_pg.execute("DELETE FROM ignoredchristmascat WHERE guild_id = $1 AND category_id = $2", ctx.guild.id, category.id)
                ignoredcategories.remove(category.id)
                removed_categories.append(category.name)
            else:
                not_exist.append(category.name)
        self.ignoredcategories[guildid] = ignoredcategories
        if len(removed_categories) > 0:
            removed_category_string = format_channel(removed_categories)
        else:
            removed_category_string = ""
        if len(not_exist) > 0:
            not_exist_string = format_channel(not_exist)
        else:
            not_exist_string = ""
        embed = discord.Embed(title="Success!", description=f"**{removed_category_string}** has been removed from the list of ignored categories.", color=discord.Color.green())
        if not_exist_string:
            embed.add_field(name="Not Exist", value=f"**{not_exist_string}** were not in the list of ignored categories.", inline=False)
            embed.color = discord.Color.yellow()
        await ctx.send(embed=embed)

    @checks.dev()
    @commands.command(name="prizechoice", aliases=['pc'])
    async def set_prize_choice(self, ctx, member:discord.Member = None):
        """
        Manually allows someone to claim a prize.
        """
        message = ctx.message
        if member is None:
            return await message.add_reaction("❌")
        selected_prizes = random.choices(something, weights=weights, k=3)
        prizeview = ChoosePrize(selected_prizes, member)
        embed=discord.Embed(title="You won the minigame!", description=f"Choose one of the prizes to redeem below!", color=self.client.embed_color)
        prizeview.response = await message.channel.send(embed=embed, view=prizeview)
        print('baka')
        await prizeview.wait()
        print(prizeview.prize)
        await self.manage_prize(ctx.message, prizeview.prize, member)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="existingperks", aliases=['ep'])
    async def existing_perks(self, ctx):
        """
        List the perks that currently exist on members.
        """
        entries = await self.client.pool_pg.fetch("SELECT * FROM perkremoval")
        commandentries = await self.client.pool_pg.fetch("SELECT * FROM commandaccess")
        if len(entries) == 0 and len(commandentries) == 0:
            return await ctx.send("There are no existing perks that are currently in use.")
        something = []
        for entry in entries:
            member = ctx.guild.get_member(entry.get('member_id'))
            if member is None:
                displaymember = entry.get('member_id')
            else:
                displaymember = f"{member.mention} ({member.id})"
            something.append((f"External: {entry.get('perk')}", f"**User**: {displaymember}\n**Until**: <t:{entry.get('until')}>"))
        for entry in commandentries:
            member = ctx.guild.get_member(entry.get('member_id'))
            if member is None:
                displaymember = entry.get('member_id')
            else:
                displaymember = f"{member.mention} ({member.id})"
            something.append((f"Dank Vibes Bot: `{entry.get('command')}`", f"**User**: {displaymember}\n**Until**: <t:{entry.get('until')}>"))
        pages = CustomMenu(source=ListPerks(something, "Existing Perks"), clear_reactions_after=True, timeout=60)
        return await pages.start(ctx)


    def cog_unload(self) -> None:
        self.remind_perk_removal.stop()
        self.command_removal.stop()
