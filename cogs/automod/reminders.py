import discord
from discord.ext import commands, tasks

from utils.format import print_exception
from utils.time import humanize_timedelta
import time
import asyncio
class reminders_(commands.Cog):
    def __init__(self, client):
        self.client = client


    @tasks.loop(seconds=1)
    async def reminder_check(self):
        await self.client.wait_until_ready()
        try:
            reminders = await self.client.pool_pg.fetch("SELECT * FROM reminders WHERE time <= $1", round(time.time()))
            if len(reminders) == 0:
                return
            else:
                for reminder in reminders:
                    user = self.client.get_user(reminder.get('user_id'))
                    chan_id = reminder.get('channel_id')
                    guild_id = reminder.get('guild_id')
                    msg_id = reminder.get('message_id')
                    time_end = reminder.get('time')
                    time_created = reminder.get('created_time')
                    channel = self.client.get_channel(chan_id)
                    msg_link = f"https://discord.com/channels/{guild_id}/{chan_id}/{msg_id}"
                    embed = discord.Embed(title=f"Reminder #{reminder.get('id')}", description=f"You asked to be reminded for {reminder.get('name')} [{humanize_timedelta(seconds=time_end - time_created)} ago]({msg_link}).", color=self.client.embed_color)
                    text = f"Your reminder ended: **{reminder.get('name')}**"
                    if user is not None:
                        try:
                            await user.send(text, embed=embed)
                        except Exception as e:
                            if channel is not None:
                                text += f"\n{user.mention}"
                                await channel.send(f"{user.mention} {text}")

                            else:
                                pass
                    else:
                        pass
                    await self.client.pool_pg.execute("DELETE FROM reminders WHERE id = $1", reminder.get('id'))
        except Exception as error:
            traceback_error = print_exception(f'Ignoring exception in RealReminder task', error)
            embed = discord.Embed(color=0xffcccb, description=f"Error encountered on a OfficialReminders.\n```py\n{traceback_error}```", timestamp=discord.utils.utcnow())
            await self.client.get_guild(871734809154707467).get_channel(871737028105109574).send(embed=embed)