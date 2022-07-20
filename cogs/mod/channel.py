import asyncio

import discord
from discord import ChannelType
from discord.ext import commands
from main import dvvt
from utils import checks
from typing import Union, Optional

def get_non_category_channels(arg: Union[discord.abc.GuildChannel, discord.Guild]):
    if isinstance(arg, discord.abc.GuildChannel):
        guild = arg.guild
    else:
        guild = arg
    return [c for c in guild.channels if c.category is None and not isinstance(c, discord.CategoryChannel)]


class ChannelList(discord.ui.Select):
    def __init__(self, channels: list, is_category_channels: bool, target_channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel]):
        self.is_category_channels = is_category_channels
        self.target_channel = target_channel
        self.index = 0
        if is_category_channels:
            placeholder = "Select a category"
        else:
            placeholder = "Select a channel"
        options = []
        if is_category_channels:
            options.append(discord.SelectOption(label="No category", value="nil"))
        if len(channels) > 0:
            if len(channels) < 20:
                for channel in channels:
                    channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel]
                    if channel.type == ChannelType.text:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_TextChannel:997786423820288061>" if channel.permissions_for(channel.guild.default_role).view_channel else "<:DVB_TextChannelLock:997786422260023366>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.voice:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_GreyVoiceChannel:997786435853758546>" if channel.permissions_for(channel.guild.default_role).view_channel else "<:DVB_GreyVoiceChannelLock:997786434104729641>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.category:
                        label = channel.name
                        value = str(channel.id)
                        emoji = discord.PartialEmoji.from_str("<:DVB_ChannelCategory:997787503744516126>")
                    elif channel.type == ChannelType.news:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_AnnouncementChannel:997786427775529010>" if channel.permissions_for(channel.guild.default_role).view_channel else "<:DVB_AnnouncementChannelLock:997786425875517450>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.stage_voice and type(channel) == discord.StageChannel:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_GreyStageChannel:997786431982415874>" if channel.permissions_for(channel.guild.default_role).view_channel else "<:DVB_StageChannelLock:997786430195630100>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    else:
                        print(f"Unidentified channel with ID {channel.id} in guild {channel.guild.id}: {type(channel)}")
                        continue
                    if channel.id == target_channel.id:
                        description = "This is the channel you selected, do not choose this."
                    else:
                        description = None
                    if channel.type == ChannelType.category and channel.id == self.target_channel.id:
                        default = True
                    else:
                        default = False

                    options.append(discord.SelectOption(label=label, value=value, emoji=emoji, default=default, description=description))
            else:
                min_index, max_index = self.index*20, (self.index+1)*20-1
                for channel in channels[min_index:max_index+1]:
                    channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel]
                    if channel.type == ChannelType.text:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_TextChannel:997786423820288061>" if channel.permissions_for(
                            channel.guild.default_role).view_channel else "<:DVB_TextChannelLock:997786422260023366>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.voice:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_GreyVoiceChannel:997786435853758546>" if channel.permissions_for(
                            channel.guild.default_role).view_channel else "<:DVB_GreyVoiceChannelLock:997786434104729641>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.category:
                        label = channel.name
                        value = str(channel.id)
                        emoji = discord.PartialEmoji.from_str("<:DVB_ChannelCategory:997787503744516126>")
                    elif channel.type == ChannelType.news:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_AnnouncementChannel:997786427775529010>" if channel.permissions_for(
                            channel.guild.default_role).view_channel else "<:DVB_AnnouncementChannelLock:997786425875517450>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.stage_voice and type(channel) == discord.StageChannel:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_GreyStageChannel:997786431982415874>" if channel.permissions_for(
                            channel.guild.default_role).view_channel else "<:DVB_StageChannelLock:997786430195630100>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    else:
                        print(f"Unidentified channel with ID {channel.id} in guild {channel.guild.id}: {type(channel)}")
                        continue
                    if channel.id == target_channel.id:
                        description = "This is the channel you selected, do not choose this."
                    else:
                        description = None
                    if channel.type == ChannelType.category and channel.id == self.target_channel.id:
                        default = True
                    else:
                        default = False

                    options.append(discord.SelectOption(label=label, value=value, emoji=emoji, default=default,
                                                        description=description))
                options.append(discord.SelectOption(label="More channels...", value="morechannels", emoji="➡️", default=False, description=f"{min_index+1} to {max_index+1} out of {len(channels)} channels"))


        else:
            options.append(discord.SelectOption(label="No channels found", emoji=None, default=True))
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options, disabled=True if len(options) == 1 and options[0].label == "No channels found" else False)

    def regenerate_options(self, list_of_channels: list):
        self.options = []
        if len(list_of_channels) > 0:
            if self.view.move_category is True:
                self.options.append(discord.SelectOption(label="No category", value="nil", default=True if self.target_channel.category is None else False))
            if len(list_of_channels) <= 20:
                for channel in list_of_channels:
                    channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel]
                    if channel.type == ChannelType.text:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_TextChannel:997786423820288061>" if channel.overwrites_for(channel.guild.default_role).view_channel is True else "<:DVB_TextChannelLock:997786422260023366>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.voice:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_GreyVoiceChannel:997786435853758546>" if channel.overwrites_for(channel.guild.default_role).view_channel is True else "<:DVB_GreyVoiceChannelLock:997786434104729641>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.category:
                        label = channel.name
                        value = str(channel.id)
                        emoji = discord.PartialEmoji.from_str("<:DVB_ChannelCategory:997787503744516126>")
                    elif channel.type == ChannelType.news:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_AnnouncementChannel:997786427775529010>" if channel.overwrites_for(channel.guild.default_role).view_channel else "<:DVB_AnnouncementChannelLock:997786425875517450>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.stage_voice and type(channel) == discord.StageChannel:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_GreyStageChannel:997786431982415874>" if channel.overwrites_for(channel.guild.default_role).view_channel else "<:DVB_StageChannelLock:997786430195630100>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    else:
                        print(f"Unidentified channel with ID {channel.id} in guild {channel.guild.id}: {type(channel)}")
                        continue
                    if channel.type == ChannelType.category and self.target_channel.category is not None and channel.id == self.target_channel.category.id:
                        default = True
                    else:
                        default = False
                    self.options.append(discord.SelectOption(label=label, value=value, emoji=emoji, default=default))

            else:
                min_index, max_index = self.index*20, (self.index+1)*20-1
                for channel in list_of_channels[min_index:max_index+1]:
                    channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel]
                    if channel.type == ChannelType.text:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_TextChannel:997786423820288061>" if channel.permissions_for(
                            channel.guild.default_role).view_channel else "<:DVB_TextChannelLock:997786422260023366>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.voice:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_GreyVoiceChannel:997786435853758546>" if channel.permissions_for(
                            channel.guild.default_role).view_channel else "<:DVB_GreyVoiceChannelLock:997786434104729641>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.category:
                        label = channel.name
                        value = str(channel.id)
                        emoji = discord.PartialEmoji.from_str("<:DVB_ChannelCategory:997787503744516126>")
                    elif channel.type == ChannelType.news:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_AnnouncementChannel:997786427775529010>" if channel.permissions_for(
                            channel.guild.default_role).view_channel else "<:DVB_AnnouncementChannelLock:997786425875517450>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    elif channel.type == ChannelType.stage_voice and type(channel) == discord.StageChannel:
                        label = channel.name
                        value = str(channel.id)
                        emoji_str = "<:DVB_GreyStageChannel:997786431982415874>" if channel.permissions_for(
                            channel.guild.default_role).view_channel else "<:DVB_StageChannelLock:997786430195630100>"
                        emoji = discord.PartialEmoji.from_str(emoji_str)
                    else:
                        print(f"Unidentified channel with ID {channel.id} in guild {channel.guild.id}: {type(channel)}")
                        continue
                    if channel.id == self.target_channel.id:
                        description = "This is the channel you selected, do not choose this."
                    else:
                        description = None
                    if channel.type == ChannelType.category and channel.id == self.target_channel.id:
                        default = True
                    else:
                        default = False

                    self.options.append(discord.SelectOption(label=label, value=value, emoji=emoji, default=default,
                                                        description=description))
                self.options.append(discord.SelectOption(label="More channels...", value="morechannels", emoji="➡️", default=False, description=f"{min_index + 1} to {max_index + 1} out of {len(list_of_channels)} channels"))
        else:
            self.options.append(discord.SelectOption(label="No channels found", emoji=None, default=True))
        self.disabled = True if len(self.options) == 0 and self.options[0].label == "No channels found" else False

    async def callback(self, interaction: discord.Interaction):
        if self.view.active is True:
            return interaction.response.send_message("A channel move is in progress, you can't interact with this menu until it's over.", ephemeral=True)
        if self.values[0] == "morechannels":
            self.index += 1
            min_index, max_index = self.index*20, (self.index+1)*20-1
            if self.view.move_category is True:
                channels = interaction.guild.categories
            else:
                channels = interaction.channel.category.channels if interaction.channel.category is not None else get_non_category_channels(interaction.guild)
            if min_index >= len(channels):
                self.index = 0
            self.regenerate_options(channels)
            return await interaction.response.edit_message(view=self.view)
        if self.values[0].isdigit():
            if int(self.values[0]) == self.target_channel.id:
                return await interaction.response.send_message(
                    f"You cannot select that channel since it's the one you're planning to move...", ephemeral=True)
            else:
                self.view.selected_channel_id = int(self.values[0])
        else:
            self.view.selected_channel_id = None
        for option in self.options:
            if self.values[0] == option.value:
                option.default = True
            else:
                option.default = False
        if self.values[0].isdigit():
            self.view.selected_channel_id = int(self.values[0])
        else:
            self.view.selected_channel_id = None
        self.view.generate_embed()
        await interaction.response.edit_message(embed=self.view.embed, view=self.view)


class ChannelViewButton(discord.ui.Button):
    def __init__(self, move_category):
        self.move_category = move_category
        super().__init__(style=discord.ButtonStyle.blurple, label="Current Action: Move to another category" if self.move_category is True else "Current Action: Move channel within category")

    def format(self):
        if self.view.move_category is True:
            self.label = "Current Action: Move to another category"
            self.emoji = discord.PartialEmoji.from_str("<:DVB_TextChannel:997786423820288061>")
        else:
            self.label = "Current Action: Move channel within category"
            self.emoji = discord.PartialEmoji.from_str("<:DVB_ChannelCategory:997787503744516126>")

    async def callback(self, interaction: discord.Interaction):
        if self.view.active is True:
            return interaction.response.send_message("A channel move is in progress, you can't interact with this menu until it's over.", ephemeral=True)
        if self.view.move_category is True:
            self.view.selected_channel_id = None
            self.view.move_above = True
            self.view.move_category = False
            self.move_category = False
            self.format()
            self.view.format_items()
            if self.view.channel.category is not None:
                channels_for_options = self.view.channel.category.channels
            else:
                channels_for_options = get_non_category_channels(interaction.guild)
            self.view.select_menu.regenerate_options(channels_for_options)
        else:
            self.view.selected_channel_id = None
            self.view.move_category = True
            self.move_category = True
            self.format()
            self.view.format_items()
            self.view.select_menu.regenerate_options(interaction.guild.categories)
        self.view.generate_embed()
        await interaction.response.edit_message(view=self.view, embed=self.view.embed)


class SwitchAboveOrBelow(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Move channel above/below")

    def format(self):
        if self.view.move_category is True:
            self.disabled = True
        else:
            self.disabled = False

    async def callback(self, interaction: discord.Interaction):
        if self.view.active is True:
            return await interaction.response.send_message("A channel move is in progress, you can't interact with this menu until it's over.", ephemeral=True)
        if self.view.move_above is True:
            self.view.move_above = False
        else:
            self.view.move_above = True
        self.view.generate_embed()
        self.format()
        await interaction.response.edit_message(view=self.view, embed=self.view.embed)


class Confirm(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.red, label="Confirm")

    def format(self):
        if self.view.active is True:
            self.label = "Executing action..."
            self.disabled = True
            self.emoji = discord.PartialEmoji.from_str("<a:DVB_typing:955345484648710154>")
        else:
            self.label = "Confirm"
            self.disabled = False
            self.emoji = None

    async def callback(self, interaction: discord.Interaction):
        if self.view.active is True:
            return interaction.response.send_message("A channel move is in progress, you can't interact with this menu until it's over.", ephemeral=True)
        self.view.active = True
        self.format()
        await interaction.response.edit_message(view=self.view)
        if self.view.move_category is True:
            if self.view.selected_channel_id is None:
                await self.view.channel.edit(category=None)
                statusmsg = f"{self.view.channel.mention} is moved out of all categories."
            else:
                categorychannel = interaction.guild.get_channel(self.view.selected_channel_id)
                if categorychannel is not None:
                    await self.view.channel.edit(category=categorychannel)
                    statusmsg = f"{self.view.channel.mention} is moved to the **{categorychannel.name}** channel."
                else:
                    statusmsg = f"Category channel with ID {self.view.selected_channel_id} not found.\nNothing was done to {self.view.channel.mention}."
        else:
            if self.view.selected_channel_id is not None:
                channel = interaction.guild.get_channel(self.view.selected_channel_id)
                if channel is not None:
                    if self.view.move_above is True:
                        await self.view.channel.move(before=discord.Object(id=channel.id))
                        statusmsg = f"{self.view.channel.mention} is moved above {channel.mention}."
                    else:
                        await self.view.channel.move(after=discord.Object(id=channel.id))
                        statusmsg = f"{self.view.channel.mention} is moved below {channel.mention}."
                else:
                    statusmsg = f"Channel with ID {self.view.selected_channel_id} not found.\nNothing was done to {self.view.channel.mention}."
            else:
                statusmsg = f"Nothing was done to {self.view.channel.mention}."
        await asyncio.sleep(0.5)
        channel_refreshed = interaction.guild.get_channel(self.view.channel.id)
        self.view.select_menu.target_channel = channel_refreshed
        self.view.selected_channel_id = None
        self.view.generate_embed()
        self.view.channel = channel_refreshed
        self.view.selected_channel_id = None
        self.view.move_category = False
        if self.view.channel.category is not None:
            channels_for_options = self.view.channel.category.channels
        else:
            channels_for_options = get_non_category_channels(interaction.guild)
        self.view.select_menu.regenerate_options(channels_for_options)

        self.view.channelcategorybutton.format()
        self.view.abovebelowbutton.format()
        self.view.confirmbutton.format()
        self.view.active = False
        self.format()
        self.view.format_items()
        await interaction.followup.send(statusmsg)
        await interaction.edit_original_message(embed=self.view.embed, view=self.view)


class ChannelView(discord.ui.View):
    def __init__(self, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel], initial_embed: discord.Embed, author):
        self.active = False
        self.author = author
        self.channel = channel
        self.embed = initial_embed
        self.select_menu = ChannelList(channels=channel.category.channels if channel.category is not None else get_non_category_channels(channel), is_category_channels=False, target_channel=channel)
        self.selected_channel_id = None
        self.move_category = False
        self.channelcategorybutton = ChannelViewButton(self.move_category)
        self.abovebelowbutton = SwitchAboveOrBelow()
        self.confirmbutton = Confirm()
        self.move_above = True
        super().__init__(timeout=180)

        self.add_item(self.select_menu)
        self.add_item(self.channelcategorybutton)
        self.add_item(self.abovebelowbutton)
        self.add_item(self.confirmbutton)

    def format_items(self):
        self.abovebelowbutton.format()
        self.confirmbutton.format()
        self.channelcategorybutton.format()

    def show_channel_position(self):
        text = []
        if self.channel.category is not None:
            category_exists = True
            text.append(f"<:DVB_ChannelCategory:997787503744516126> **{self.channel.category.name}**")
        else:
            text.append(f"**No category**")
            category_exists = False
        position = self.channel.position

        category_channels = self.channel.category.channels if category_exists is True else [channel for channel in self.channel.guild.channels if channel.category is None]
        channel_at_bottom, channel_at_top = False, False
        if len(category_channels) > 0:
            a = category_channels[-1]
            b = a.position
            if category_channels[-1] == self.channel:  # channel is at bottom of category
                for index, disp_channel in enumerate(category_channels):
                    if category_channels.index(self.channel) - index <= 2:
                        if disp_channel.id == self.channel.id:
                            text.append(f"    → **{disp_channel.mention}** ←")
                        else:
                            text.append(f"    •  **{disp_channel.mention}**")
            elif category_channels[0] == self.channel:  # channel is at top of category
                for index, disp_channel in enumerate(category_channels):
                    if index - category_channels.index(self.channel) <= 2:
                        if disp_channel.id == self.channel.id:
                            text.append(f"    → **{disp_channel.mention}** ←")
                        else:
                            text.append(f"    •  **{disp_channel.mention}**")
            else:
                for index, disp_channel in enumerate(category_channels):
                    if -1 <= index - category_channels.index(self.channel) <= 1:
                        if disp_channel.id == self.channel.id:
                            text.append(f"    → **{disp_channel.mention}** ←")
                        else:
                            text.append(f"    •  **{disp_channel.mention}**")
        return "\n".join(text)



    def generate_embed(self):
        embed = discord.Embed(title=f"You're editing **{self.channel.name}**'s position")
        if self.move_category is True:
            if self.selected_channel_id is None:
                if len(self.select_menu.values) < 1:
                    description = f"Choose a category from the dropdown to move {self.channel.mention} to."
                else:
                    description = f"{self.channel.mention} will be moved out of all channels."
            else:
                category_chan = self.channel.guild.get_channel(self.selected_channel_id)
                if category_chan is None:
                    description = f"{self.channel.mention} will be moved to `Invalid channel ({self.selected_channel_id})`."
                else:
                    description = f"{self.channel.mention} will be moved to **{category_chan.name}** category."
        else:
            if self.selected_channel_id is not None:
                selected_channel = self.channel.guild.get_channel(self.selected_channel_id)
                if selected_channel is not None:
                    if self.move_above is True:
                        description = f"{self.channel.mention} will be moved **above** {selected_channel.mention}."
                    else:
                        description = f"{self.channel.mention} will be moved **below** {selected_channel.mention}."
                else:
                    description = f"{self.channel.mention} will be moved to `Invalid channel ({self.selected_channel_id})`."
            else:
                description = f"Select a channel to move {self.channel.mention} above/below."
        embed.add_field(name="Channel's current position", value=self.show_channel_position(), inline=False)
        embed.add_field(name="What I'll do: ", value=description, inline=False)
        self.embed = embed
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author.id != interaction.user.id:
            await interaction.response.send_message("This isn't for you.", ephemeral=True)
            return False
        else:
            return True

class ChannelUtils(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name="channel", invoke_without_command=True)
    async def channel_base(self, ctx):
        """
        Channel management
        """
        return await ctx.help()

    @checks.has_permissions_or_role(manage_roles=True)
    @channel_base.command(name="move")
    async def channel_move(self, ctx, channel: discord.TextChannel = None):
        """
        Move a channel to a different category
        """
        if channel is None:
            channel = ctx.channel

        view = ChannelView(channel=channel, initial_embed=None, author=ctx.author)
        view.initial_embed = view.generate_embed()
        await ctx.send(embed=view.initial_embed, view=view)
        await view.wait()


