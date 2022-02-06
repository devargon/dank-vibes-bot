import discord
from discord.ext import commands

import time
from datetime import datetime, timezone
import asyncio

from main import dvvt
from utils.buttons import confirm
from utils.errors import ArgumentBaseError
from utils.time import humanize_timedelta, UserFriendlyTime
from utils import checks


class Reminder:
    __slots__ = ('time', 'name', 'channel', 'guild', 'message', 'id', 'user', 'created_time')

    def __init__(self, *, record):
        self.id = record.get('id')
        self.user = record.get('user_id')
        self.guild = record.get('guild_id')
        self.channel = record.get('channel_id')
        self.message = record.get('message_id')
        self.created_time = record.get('created_time')
        self.time = record.get('time')
        self.name = record.get('name')


class reminders(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    class ReminderConverter(commands.Converter):
        async def convert(self, ctx, argument):
            try:
                argument = int(argument)
            except ValueError:
                raise ArgumentBaseError(message='You did not provide a valid reminder ID.')
            reminder = await ctx.bot.pool_pg.fetchrow("SELECT * FROM reminders WHERE id=$1 AND guild_id=$2", argument, ctx.guild.id)
            if not reminder:
                raise ArgumentBaseError(message="You don't have a reminder with that ID.")
            return Reminder(record=reminder)

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        return content.strip('` \n')

    class OwnReminderConverter(commands.Converter):
        async def convert(self, ctx, argument):
            try:
                argument = int(argument)
            except ValueError:
                raise ArgumentBaseError(message='You did not provide a valid reminder ID.')
            reminder = await ctx.bot.pool_pg.fetchrow("SELECT * FROM reminders WHERE id=$1 AND user_id=$2 AND guild_id=$3", argument, ctx.author.id, ctx.guild.id)
            if not reminder:
                raise ArgumentBaseError(message="You don't have a reminder with that ID.")
            return Reminder(record=reminder)

    async def add_reminder(self, user_id, guild_id, channel_id, message_id, name, end_time):
        now = round(time.time())
        rm_id = await self.client.pool_pg.fetchval("INSERT INTO reminders(user_id, guild_id, channel_id, message_id, name, time, created_time) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id", user_id, guild_id, channel_id, message_id, name, end_time, round(time.time()), column='id')
        return rm_id

    @checks.requires_roles()
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
        await ctx.message.reply(f"Alright! I'll remind you about **{reminder}** in **{humanize_timedelta(seconds=round(remind_dt.timestamp()-time.time()))}** (at <t:{round(remind_dt.timestamp())}:f>).\nThis reminder's ID is `{rm_id}`.")

    @checks.requires_roles()
    @commands.guild_only()
    @remind.command(name='list', aliases=['mine', 'show', 'display'])
    async def remind_list(self, ctx):
        """Lists all of your reminders."""
        reminders = await self.client.pool_pg.fetch("SELECT id, channel_id, message_id, name, time FROM reminders WHERE user_id=$1 AND guild_id=$2 ORDER BY time", ctx.author.id, ctx.guild.id)
        if not reminders:
            return await ctx.send("You don't have any reminders set.")
        reminder_list = []
        for rm in reminders:
            reminder_id = rm.get('id')
            channel_id = rm.get('channel_id')
            message_id = rm.get('message_id')
            name = rm.get('name')
            time = rm.get('time')
            url = f"https://discord.com/channels/{ctx.guild.id}/{channel_id}/{message_id}"
            reminder_list.append(f"ID: `{reminder_id}`, <t:{time}:d> <t:{time}:t> | {name}")
        current = len(reminder_list)
        deleted = 0
        if len('\n'.join(reminder_list)) > 2000:
            while len('\n'.join(reminder_list)) > 2000:
                reminder_list = reminder_list[:-1]
                deleted += 1
            final = '\n'.join(reminder_list)
        else:
            final = '\n'.join(reminder_list)
        embed = discord.Embed(title="Your reminders", description=final, color=self.client.embed_color)
        footertext = f"You have {current} active reminders."
        if deleted > 0:
            footertext += f" {deleted} reminders were not shown due to the character limit."
        embed.set_footer(text=footertext)
        await ctx.send(embed=embed)

    @checks.requires_roles()
    @commands.guild_only()
    @remind.command(name='delete', aliases=['remove', 'del', 'rm'])
    async def remind_delete(self, ctx, *, reminder_id: OwnReminderConverter = None):
        """Deletes a reminder."""
        reminder: Reminder = reminder_id
        await self.client.pool_pg.execute("DELETE FROM reminders WHERE id=$1 AND user_id=$2 AND guild_id=$3", reminder.id, ctx.author.id, ctx.guild.id)
        await ctx.send(f"Your reminder **{reminder.name}** with ID `{reminder.id}` has been deleted.")

    @checks.requires_roles()
    @commands.guild_only()
    @remind.command(name='clear', aliases=['clean', 'purge', 'reset'])
    async def remind_clear(self, ctx):
        """Completely clears your reminder list."""
        is_existing = await self.client.pool_pg.fetch("SELECT * FROM reminders WHERE user_id = $1 AND guild_id = $2", ctx.author.id, ctx.guild.id)
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
        await self.client.pool_pg.execute("DELETE FROM reminders WHERE user_id=$1 AND guild_id=$2", ctx.author.id, ctx.guild.id)
        await ctx.send(f"Your {len(is_existing)} reminders have been removed.")

    @checks.requires_roles()
    @commands.guild_only()
    @remind.command(name='when', aliases=['what', 'details'])
    async def remind_when(self, ctx, *, reminder_id: OwnReminderConverter = None):
        """
        Shows you details about a reminder and when it ends.
        """
        reminder: Reminder = reminder_id
        channel_id = reminder.channel
        message_id = reminder.message
        url = f"https://discord.com/channels/{ctx.guild.id}/{channel_id}/{message_id}"
        embed = discord.Embed(title=f"{reminder.name}", description=f"In **{humanize_timedelta(seconds=round(reminder.time - time.time()))}**\nAt **<t:{reminder.time}:d> <t:{reminder.time}:t>**\n<:Reply:871808167011549244> [Jump to message]({url})", color=self.client.embed_color, timestamp=datetime.utcfromtimestamp(reminder.created_time))
        embed.set_author(icon_url=ctx.author.avatar.url, name=f"{ctx.author.name}'s Reminder (ID: {reminder.id})")
        embed.set_footer(text="Reminder created")
        await ctx.send(embed=embed)

    @checks.requires_roles()
    @commands.guild_only()
    @remind.command(name='subscribe', aliases=['sub', 'clone'])
    async def remind_subscribe(self, ctx, *, reminder_id: ReminderConverter = None):
        """
        Copy another person's reminder and make it your own reminder!
        """
        reminder: Reminder = reminder_id
        remind_time = reminder.time
        name = reminder.name
        if reminder.user == ctx.author.id:
            return await ctx.send("You can't subscribe to your own reminder.")
        reminder_id = await self.add_reminder(ctx.author.id, ctx.guild.id, ctx.channel.id, ctx.message.id, name, remind_time)
        await ctx.send(f"Alright! I have cloned the reminder **{name}**. You will be reminded about it in **{humanize_timedelta(seconds=round(remind_time-time.time()))}** (at <t:{round(remind_time)}:f>).\nThis reminder's ID is `{reminder_id}`.")

    @checks.requires_roles()
    @commands.guild_only()
    @remind.command(name='import')
    async def remind_import(self, ctx):
        """
        Imports your reminders from Carl-bot.
        """
        await ctx.send("**Step 1 of 2**\n**Send `-rm list` within the next 20 seconds. I will read your current Carl-bot reminders.**")

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content.lower() == '-rm list'

        try:
            msg = await self.client.wait_for('message', check=check, timeout=20)
        except asyncio.TimeoutError:
            return await ctx.send("**Timed out.** I could not detect you running `-rm list`, please try again.")

        def check(m):
            return m.author.id == 235148962103951360 and m.channel.id == ctx.channel.id and (m.content.startswith("User has no reminders") or m.content.startswith('```'))

        try:
            msg = await self.client.wait_for('message', check=check, timeout=20.0)
        except asyncio.TimeoutError:
            return await ctx.send("**Timed out.** I could not detect Carl-bot's response, please try again.")
        if msg.content.startswith("User has no reminders"):
            return await ctx.send("**You do not have any reminders in Carl-bot.** As such, there's nothing to import.")
        if not msg.content.startswith('```'):
            return await ctx.send("**I detected Carl-bot's response but it is not in the expected format.** As such, there's nothing to import.")
        raw_text = self.cleanup_code(msg.content)
        arg = raw_text
        reminders = []
        for um in arg.split('\n'):
            um = um.strip()
            um = um.split(' ')
            date = ' '.join(um[3:5])
            rm = ' '.join(um[6:])
            date_dt = datetime.strptime(date, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc)
            timestamp = round(date_dt.timestamp())
            reminders.append((timestamp, rm))
        if len(reminders) < 1:
            return await ctx.send("**I could not detect any reminders from Carl-bot's message.** As such, there's nothing to import.")
        embed = discord.Embed(title=f"These are the reminders that will be imported from Carl-bot to {self.client.user.name}.", color=self.client.embed_color)
        rm_text = []
        for remind in reminders:
            rm_text.append(f"<t:{remind[0]}>: {remind[1]}")
        embed.description = '\n'.join(rm_text)
        confirmview = confirm(ctx, self.client, 20.0)
        confirmview.response = await ctx.send("**Step 2 of 2**\n**Confirm that I have read your reminders correctly.** Click `yes` if you've ensured they're imported correctly.", embed=embed, view=confirmview)
        await confirmview.wait()
        if confirmview.returning_value is not True:
            return await ctx.send("**Your reminders will not be imported from Carl-bot.")
        else:
            exising_reminders = await self.client.pool_pg.fetch(
                "SELECT name, time FROM reminders WHERE user_id = $1 AND guild_id = $2", ctx.author.id, ctx.guild.id)
            if len(exising_reminders) > 0:
                existing_reminders = [(x.get('time'), x.get('name')) for x in exising_reminders]
            else:
                existing_reminders = []
            to_import = [
                (ctx.author.id, ctx.guild.id, ctx.channel.id, ctx.message.id, tup[1], tup[0], round(time.time()))
                for tup in reminders
                if tup not in existing_reminders]
            await self.client.pool_pg.executemany("INSERT INTO reminders(user_id, guild_id, channel_id, message_id, name, time, created_time) VALUES ($1, $2, $3, $4, $5, $6, $7)", to_import)
            await ctx.send("**Your reminders have been successfully imported from Carl-bot!**")





