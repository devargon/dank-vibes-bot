import os
from typing import Optional, Union

import asyncpg
import discord
import typing
from discord.ext import commands

import time
from datetime import datetime, timezone
import asyncio

from custom_emojis import DVB_TRUE
from main import dvvt
from utils.buttons import confirm
from utils.context import DVVTcontext
from utils.converters import TimedeltaConverter, BetterTimeConverter
from utils.errors import ArgumentBaseError
from utils.time import humanize_timedelta, UserFriendlyTime
from utils import checks
from utils.specialobjects import Reminder

class RemindersViewModeSelect(discord.ui.Select):
    def __init__(self, selected_mode: typing.Literal['all', 'repeating'] = "all"):
        options = [
            discord.SelectOption(label="All reminders", value="all", emoji="⏰", default=selected_mode == "all"),
            discord.SelectOption(label="Repeating reminders", value="repeating", emoji="🔁", default=selected_mode == "repeating")
        ]

        super().__init__(placeholder="Show...", min_values=1, max_values=1, options=options, custom_id="reminders_view_mode_select")

    async def callback(self, interaction: discord.Interaction):
        view: RemindersView = self.view
        if view is None:
            return await interaction.response.send_message("An error occurred while processing this interaction. Please try again.", ephemeral=True)
        selected_value = self.values[0]
        view.list_mode = selected_value
        view.page_num = 0
        await view.render_layout()
        await interaction.response.edit_message(view=view)

class DeleteReminderButton(discord.ui.Button):
    def __init__(self, reminder_id: int, emoji="🗑️", label=None):
        super().__init__(
            emoji=emoji,
            label=label,
            style=discord.ButtonStyle.danger,
            custom_id=f"reminders:delete:{reminder_id}",
        )

        self.reminder_id = reminder_id

    async def callback(self, interaction: discord.Interaction):
        self.view: RemindersView = self.view
        await self.view.initiate_delete_reminder(interaction, self.reminder_id)

class InteractionConfirm(discord.ui.View):
    def __init__(self, author: Union[discord.User, discord.Member], client, timeout):
        self.timeout = timeout
        self.author = author
        self.response = None
        self.client = client
        self.returning_value = None
        self.interaction = None
        super().__init__(timeout=30.0)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.interaction = interaction
        self.returning_value = True
        for b in self.children:
            if b != button:
                b.style = discord.ButtonStyle.grey
            b.disabled = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.interaction = interaction
        self.returning_value = False
        for b in self.children:
            if b != button:
                b.style = discord.ButtonStyle.grey
            b.disabled = True
        await interaction.response.defer()
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        author = self.author
        if interaction.user != author:
            await interaction.response.send_message("These buttons aren't for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        self.returning_value = None
        for b in self.children:
            b.disabled = True
        if isinstance(self.response, discord.Message) or isinstance(self.response, discord.WebhookMessage):
            await self.response.edit(view=self)
        elif isinstance(self.response, discord.Interaction):
            await self.response.edit_original_response(view=self)

class RemindersView(discord.ui.DesignerView):
    def __init__(self, client, ctx):
        self.ctx: DVVTcontext = ctx
        self.client: dvvt = client
        self.list_mode: typing.Literal['all', 'repeating'] = "all"
        self.page_num = 0
        self.reminders_per_page = 7
        super().__init__(timeout=60, disable_on_timeout=True)

    async def fetch_reminders(self):
        # fetch based on self.page_num, and self.reminders_per_page
        offset = self.page_num * self.reminders_per_page
        if self.list_mode == "all":
            reminders = await self.client.db.fetch("SELECT * FROM reminders WHERE user_id=$1 AND guild_id=$2 ORDER BY time LIMIT $3 OFFSET $4", self.ctx.author.id, self.ctx.guild.id, self.reminders_per_page, offset)
        else:
            reminders = await self.client.db.fetch("SELECT * FROM reminders WHERE user_id=$1 AND guild_id=$2 AND repeat=true ORDER BY time LIMIT $3 OFFSET $4", self.ctx.author.id, self.ctx.guild.id, self.reminders_per_page, offset)
        return reminders

    async def render_layout(self):
        reminders = await self.fetch_reminders()
        self.clear_items()
        container = discord.ui.Container(
            discord.ui.TextDisplay(f"## Your Reminders\nPage {self.page_num+1}"),
            discord.ui.ActionRow(RemindersViewModeSelect(selected_mode=self.list_mode)),
            discord.ui.Separator(divider=True, spacing=discord.SeparatorSpacingSize.small),
            color=self.client.embed_color
        )
        for reminder in reminders:
            container.add_item(self.build_reminder(reminder))

        self.add_item(container)

    def build_reminder(self, reminder: asyncpg.Record):
        reminder_id = reminder.get('id')
        guild_id = reminder.get('guild_id')
        channel_id = reminder.get('channel_id')
        message_id = reminder.get('message_id')
        name = reminder.get('name')
        time = reminder.get('time')
        repeating = reminder.get('repeat')
        repeating_interval = reminder.get('interval')
        url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

        text = f"**#{reminder_id}**: {name}\n<t:{time}:f>"
        if repeating:
            text += f"\n-# 🔁 Repeats every **{humanize_timedelta(seconds=repeating_interval)}**"

        row = discord.ui.Section(discord.ui.TextDisplay(text), accessory=DeleteReminderButton(reminder_id=reminder_id))
        return row

    async def initiate_delete_reminder(self, interaction: discord.Interaction, reminder_id: int):
        confirmview = InteractionConfirm(interaction.user, self.client, 30.0)
        confirmembed = discord.Embed(
            description=f"Are you sure you want to delete reminder **#{reminder_id}**? This action is irreversible!",
            color=discord.Color.orange())
        confirmview.response = await interaction.response.send_message(embed=confirmembed, view=confirmview)
        await confirmview.wait()
        if confirmview.returning_value is not True:
            if confirmview.interaction:
                confirmembed.color = discord.Color.red()
                confirmembed.description = "Deletion cancelled."
                await confirmview.interaction.edit_original_response(embed=confirmembed, view=confirmview)
            return

        reminder = await self.client.db.fetchrow("SELECT * FROM reminders WHERE id=$1 AND user_id=$2 AND guild_id=$3",
                                                 reminder_id, self.ctx.author.id, self.ctx.guild.id)
        if not reminder:
            confirmembed.color = discord.Color.red()
            confirmembed.description = "You don't have a reminder with that ID. It may have already been deleted."
            await confirmview.interaction.edit_original_response(embed=confirmembed, view=confirmview)
            return

        await self.client.db.execute("DELETE FROM reminders WHERE id=$1 AND user_id=$2 AND guild_id=$3", reminder_id,
                                     self.ctx.author.id, self.ctx.guild.id)
        confirmembed.color = discord.Color.green()
        confirmembed.description += f"\n\n{DVB_TRUE} **Success!**"
        await confirmview.interaction.edit_original_response(embed=confirmembed, view=confirmview)
        await self.render_layout()
        await self.message.edit(view=self)


class ReminderCreatedView(discord.ui.DesignerView):
    def __init__(self, client, ctx, reminder_id: int, reminder_name: str, remind_time: int):
        self.ctx: DVVTcontext = ctx
        self.client: dvvt = client
        self.reminder_id = reminder_id
        self.reminder_name = reminder_name
        self.remind_time = remind_time
        super().__init__(timeout=30, disable_on_timeout=True)

        self.add_item(discord.ui.Container(
            discord.ui.TextDisplay(f"## {DVB_TRUE} Reminder #{reminder_id} Created!\nI will remind you about **{reminder_name}** in **{humanize_timedelta(seconds=round(remind_time - time.time()))}** (at <t:{round(remind_time)}:f>)."),
            discord.ui.ActionRow(DeleteReminderButton(reminder_id=reminder_id, label="Delete Reminder")),
            color=discord.Color.green(),
        ))

    async def initiate_delete_reminder(self, interaction: discord.Interaction, reminder_id: int):
        confirmview = InteractionConfirm(interaction.user, self.client, 30.0)
        confirmembed = discord.Embed(
            description=f"Are you sure you want to delete reminder **#{reminder_id}**? This action is irreversible!",
            color=discord.Color.orange())
        confirmview.response = await interaction.response.send_message(embed=confirmembed, view=confirmview)
        await confirmview.wait()
        if confirmview.returning_value is not True:
            if confirmview.interaction:
                confirmembed.color = discord.Color.red()
                confirmembed.description = "Deletion cancelled."
                await confirmview.interaction.edit_original_response(embed=confirmembed, view=confirmview)
            return

        reminder = await self.client.db.fetchrow(
            "SELECT * FROM reminders WHERE id=$1 AND user_id=$2 AND guild_id=$3",
            reminder_id, self.ctx.author.id, self.ctx.guild.id)
        if not reminder:
            confirmembed.color = discord.Color.red()
            confirmembed.description = "You don't have a reminder with that ID. It may have already been deleted."
            await confirmview.interaction.edit_original_response(embed=confirmembed, view=confirmview)
            return

        await self.client.db.execute("DELETE FROM reminders WHERE id=$1 AND user_id=$2 AND guild_id=$3",
                                     reminder_id,
                                     self.ctx.author.id, self.ctx.guild.id)
        confirmembed.color = discord.Color.green()
        confirmembed.description += f"\n\n{DVB_TRUE} **Success!**"
        await confirmview.interaction.edit_original_response(embed=confirmembed, view=confirmview)
        self.disable_all_items()
        await self.message.edit(view=self)
        self.stop()


class reminders(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    class ReminderConverter(commands.Converter):
        async def convert(self, ctx, argument):
            try:
                argument = int(argument)
            except ValueError:
                raise ArgumentBaseError(message='You did not provide a valid reminder ID.')
            reminder = await ctx.bot.db.fetchrow("SELECT * FROM reminders WHERE id=$1 AND guild_id=$2", argument, ctx.guild.id)
            if not reminder:
                raise ArgumentBaseError(message="You don't have a reminder with that ID.")
            return Reminder(record=reminder)

    class OwnReminderConverter(commands.Converter):
        async def convert(self, ctx, argument):
            try:
                argument = int(argument)
            except ValueError:
                raise ArgumentBaseError(message='You did not provide a valid reminder ID.')
            reminder = await ctx.bot.db.fetchrow("SELECT * FROM reminders WHERE id=$1 AND user_id=$2 AND guild_id=$3", argument, ctx.author.id, ctx.guild.id)
            if not reminder:
                raise ArgumentBaseError(message="You don't have a reminder with that ID.")
            return Reminder(record=reminder)

    async def add_reminder(self, user_id, guild_id, channel_id, message_id, name, end_time, repeat: Optional[bool] = False):
        now = round(time.time())
        rm_id = await self.client.db.fetchval("INSERT INTO reminders(user_id, guild_id, channel_id, message_id, name, time, created_time) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id", user_id, guild_id, channel_id, message_id, name, end_time, round(time.time()), column='id')
        return rm_id

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.group(name='remind', aliases=['reminder', 'remindme', 'rm'], invoke_without_command=True)
    async def remind(self, ctx, *, when_and_what_to_remind: UserFriendlyTime(commands.clean_content, default='\u2026') = None):
        """Reminds you of something after a certain amount of time.
        The input can be any direct date (e.g. YYYY-MM-DD) or a human
        readable offset. Examples:
        - "next thursday at 3pm do something funny"
        - "do the dishes tomorrow"
        - "in 3 days do the thing"
        - "2d unmute someone"
        Times are in UTC.
        """
        # Check out https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/reminder.py#L210-L232 on how it's used
        if when_and_what_to_remind is None:
            return await ctx.send("You need to specify a time and what you want to be reminded for.")
        remind_dt = when_and_what_to_remind.dt
        if remind_dt is None:
            return await ctx.send(f'Invalid time provided.')
        reminder = when_and_what_to_remind.arg
        if reminder == '…':
            reminder = "something"
        if len(reminder) > 256:
            return await ctx.send("You can only provide a message of up to 256 characters for your reminder.")
        rm_id = await self.add_reminder(ctx.author.id, ctx.guild.id, ctx.channel.id, ctx.message.id, reminder, remind_dt.timestamp())
        view = ReminderCreatedView(self.client, ctx, rm_id, reminder, remind_dt.timestamp())
        try:
            await ctx.message.reply(view=view)
        except Exception as e:
            await ctx.send(view=view)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @remind.command(name='repeat', aliases=['loop'])
    async def remind_repeat(self, ctx, reminder_id: OwnReminderConverter, repeating_interval: Optional[Union[int, BetterTimeConverter]] = None):
        """
        Repeats/loops a reminder, making it reoccuring with a set interval
        If no interval is provided, the reminder will repeat based on its original duration.

        To stop a reminder from repeating, use `remind repeat <id> -1`.
        """
        reminder: Reminder = reminder_id
        if reminder is None:
            return await ctx.send("You need to specify the ID of the reminder that you'd want to repeat.")
        if repeating_interval is None:
            repeating_interval = reminder.time - reminder.created_time + 1
        if isinstance(repeating_interval, int) and repeating_interval == -1:
            await self.client.db.execute("UPDATE reminders SET repeat = $1, interval = $2 WHERE id = $3", False, 0, reminder.id)
            return await ctx.send(f"Alright, I won't repeat this reminder (**{reminder.name}**) anymore.")
        minimum_interval = 1 if os.getenv('state') == '1' else 300
        if repeating_interval < minimum_interval:
            return await ctx.send("Repeating reminders require a minimum of 5 minutes between each reminder.")
        else:
            await self.client.db.execute("UPDATE reminders SET repeat = $1, interval = $2 WHERE id = $3", True, repeating_interval, reminder.id)
            await ctx.send(f"Alright! Your reminder **{reminder.name}** will repeat **every {humanize_timedelta(seconds=repeating_interval)}**. This will take place only after you get reminded about this reminder.")

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @remind.command(name='list', aliases=['mine', 'show', 'display'])
    async def remind_list(self, ctx):
        """Lists all of your reminders."""
        view = RemindersView(self.client, ctx=ctx)
        await view.render_layout()
        view.message = await ctx.send(view=view)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @remind.command(name='delete', aliases=['remove', 'del', 'rm'])
    async def remind_delete(self, ctx, *, reminder_id: OwnReminderConverter = None):
        """Deletes a reminder."""
        if reminder_id is None:
            return await ctx.send("You need to specify a reminder's ID to delete.")
        reminder: Reminder = reminder_id
        await self.client.db.execute("DELETE FROM reminders WHERE id=$1 AND user_id=$2 AND guild_id=$3", reminder.id, ctx.author.id, ctx.guild.id)
        await ctx.send(f"Your reminder **{reminder.name}** with ID `{reminder.id}` has been deleted.")

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @remind.command(name='clear', aliases=['clean', 'purge', 'reset'])
    async def remind_clear(self, ctx):
        """Completely clears your reminder list."""
        is_existing = await self.client.db.fetch("SELECT * FROM reminders WHERE user_id = $1 AND guild_id = $2", ctx.author.id, ctx.guild.id)
        if not is_existing:
            return await ctx.send("You don't have any reminders to clear lol �")
        confirmview = confirm(ctx, self.client, 30)
        embed = discord.Embed(title="Dangerous Action!", description="**Are you sure you want to reset and clear all your reminders in this server??** This action is irreversible!", color=discord.Color.orange())
        confirmview.response = await ctx.send(embed=embed, view=confirmview)
        await confirmview.wait()
        if confirmview.returning_value is not True:
            embed.color, embed.description = discord.Color.red(), "Action cancelled. Your reminders have not been reset."
            return await confirmview.response.edit(embed=embed)
        embed.color, embed.description = discord.Color.green(), "Clearing your reminders for {}...".format(ctx.guild.name)
        await confirmview.response.edit(embed=embed)
        await self.client.db.execute("DELETE FROM reminders WHERE user_id=$1 AND guild_id=$2", ctx.author.id, ctx.guild.id)
        await ctx.send(f"Your {len(is_existing)} reminders have been removed.")

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @remind.command(name='when', aliases=['what', 'details'])
    async def remind_when(self, ctx, *, reminder_id: OwnReminderConverter = None):
        """
        Shows you details about a reminder and when it ends.
        """
        if reminder_id is None:
            return await ctx.send("You need to specify a reminder's ID to show.")
        reminder: Reminder = reminder_id
        channel_id = reminder.channel
        message_id = reminder.message
        url = f"https://discord.com/channels/{ctx.guild.id}/{channel_id}/{message_id}"
        embed = discord.Embed(title=f"{reminder.name}", description=f"In **{humanize_timedelta(seconds=round(reminder.time - time.time()))}**\nAt **<t:{reminder.time}:d> <t:{reminder.time}:t>**\n<:Reply:871808167011549244> [Jump to message]({url})", color=self.client.embed_color, timestamp=datetime.utcfromtimestamp(reminder.created_time))
        embed.set_author(icon_url=ctx.author.avatar.url, name=f"{ctx.author.name}'s Reminder #{reminder.id}")
        embed.set_footer(text="Reminder created")
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @remind.command(name='subscribe', aliases=['sub', 'clone'])
    async def remind_subscribe(self, ctx, *, reminder_id: ReminderConverter = None):
        """
        Copy another person's reminder and make it your own reminder!
        """
        reminder: Reminder = reminder_id
        if reminder is None:
            return await ctx.send("You need to specify a reminder to copy.")
        remind_time = reminder.time
        name = reminder.name
        if reminder.user == ctx.author.id:
            return await ctx.send("You can't subscribe to your own reminder.")
        reminder_id = await self.add_reminder(ctx.author.id, ctx.guild.id, ctx.channel.id, ctx.message.id, name, remind_time)
        await ctx.send(f"Alright! I have cloned the reminder **{name}**. You will be reminded about it in **{humanize_timedelta(seconds=round(remind_time-time.time()))}** (at <t:{round(remind_time)}:f>).\nThis reminder's ID is `{reminder_id}`.")

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @remind.command(name='edit', aliases=['change'])
    async def remind_edit(self, ctx: DVVTcontext, reminder_id: OwnReminderConverter, *,
                     when_and_what_to_remind: UserFriendlyTime(commands.clean_content, default='\u2026', optional_time=True) = None):
        """Edits a reminder with the specified ID. You can change the time and the message of the reminder.
        Follow the format allowed by the original "remind" command.
        Times are in UTC.
        """
        reminder: Reminder = reminder_id
        if reminder is None:
            return await ctx.send("You need to specify the ID of the reminder that you'd want to repeat.")
        if when_and_what_to_remind is None:
            return await ctx.send("Unexpected parsing, please try again later.")
        new_remind_dt = when_and_what_to_remind.dt
        new_reminder = when_and_what_to_remind.arg

        if new_remind_dt is None or new_remind_dt == "...":
            new_remind_dt = reminder.time
        else:
            new_remind_dt = new_remind_dt.timestamp()

        if new_reminder is None:
            new_reminder = reminder.name

            if len(new_reminder) > 256:
                return await ctx.send("You can only provide a message of up to 256 characters for your reminder.")

        await self.client.db.execute("UPDATE reminders SET time = $1, name = $2 WHERE id = $3", new_remind_dt, new_reminder, reminder.id)
        return await ctx.maybe_reply(f"Alright! I have updated your reminder (#{reminder.id}) **{reminder.name}** to be in **{humanize_timedelta(seconds=round(new_remind_dt - time.time()))}** (at <t:{round(new_remind_dt)}:f>).")

