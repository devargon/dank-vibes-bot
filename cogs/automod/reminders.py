import os

import discord
from discord.ext import commands, tasks

from utils.format import print_exception
from utils.time import humanize_timedelta
import time
from utils.specialobjects import Reminder
import asyncio
class reminders_(commands.Cog):
    def __init__(self, client):
        self.client = client


    @tasks.loop(seconds=1)
    async def reminder_check(self):
        await self.client.wait_until_ready()
        try:
            reminders = await self.client.db.fetch("SELECT * FROM reminders WHERE time <= $1", round(time.time()))
            if len(reminders) == 0:
                return
            else:
                for reminder in reminders:
                    reminder: Reminder = Reminder(record=reminder)
                    user = self.client.get_user(reminder.user)
                    chan_id = reminder.channel
                    guild_id = reminder.guild
                    msg_id = reminder.message
                    time_end = reminder.time
                    time_created = reminder.created_time
                    channel = self.client.get_channel(chan_id)
                    msg_link = f"https://discord.com/channels/{guild_id}/{chan_id}/{msg_id}"
                    embed = discord.Embed(title=f"Reminder #{reminder.id}", description=f"You asked to be reminded for {reminder.name} [{humanize_timedelta(seconds=time_end - time_created)} ago]({msg_link}).", color=self.client.embed_color)
                    text = f"Your reminder ended: **{reminder.name}**"
                    if reminder.repeat is True and reminder.interval and reminder.interval > 0:
                        text += f"\nThis reminder will repeat again at <t:{time_end+reminder.interval}> (every {humanize_timedelta(seconds=reminder.interval)})."
                        await self.client.db.execute("UPDATE reminders SET time = $1, created_time = $2 WHERE id = $3", time_end+reminder.interval, time_end, reminder.id)
                    if user is not None:
                        try:
                            await user.send(text, embed=embed)
                        except Exception as e:
                            if channel is not None:
                                await channel.send(f"{user.mention} {text}", embed=embed)
                            else:
                                pass
                    else:
                        pass
                    if not reminder.repeat is True:
                        await self.client.db.execute("DELETE FROM reminders WHERE id = $1", reminder.id)
        except Exception as error:
            if isinstance(error, ConnectionRefusedError):
                os.system("sudo service postgresql restart")
                time.sleep(2.0)
                os.system("pm2 restart dv_bot")
            traceback_error = print_exception(f'Ignoring exception in RealReminder task', error)
            embed = discord.Embed(color=0xffcccb, description=f"Error encountered on a OfficialReminders.\n```py\n{traceback_error}```", timestamp=discord.utils.utcnow())
            await self.client.get_guild(871734809154707467).get_channel(871737028105109574).send(embed=embed)