import discord
from discord.ext import commands, tasks

from time import time
from datetime import datetime
from utils.time import humanize_timedelta

class timer(commands.Cog):
    def __init__(self, client):
        self.client = client

    @tasks.loop(seconds=4)
    async def timer_loop(self):

        timers = await self.client.pool_pg.fetch("SELECT * FROM timers")
        if len(timers) == 0:
            return
        for timer_record in timers:
            guild = self.client.get_guild(timer_record.get('guild_id'))
            if guild is None:
                if timer_record.get('time') < round(time()):
                    await self.client.pool_pg.execute("DELETE FROM timers WHERE message_id = $1", timer_record.get('message_id'))
            chan_id = timer_record.get('channel_id')
            channel = guild.get_channel(int(chan_id))
            if channel is None:
                if timer_record.get('time') < round(time()):
                    await self.client.pool_pg.execute("DELETE FROM timers WHERE message_id = $1", timer_record.get('message_id'))
            else:
                message = channel.get_partial_message(timer_record.get('message_id'))
                author = self.client.get_user(timer_record.get('user_id'))
                title = timer_record.get('title')
                if author is None:
                    if title is None:
                        title = "Timer"
                    else:
                        title = f"{title} Timer"
                else:
                    if title is None:
                        title = f"{author.name}'s Timer"
                    else:
                        title = f"{author.name}'s {title} Timer"
                endtime = timer_record.get('time')
                embed = discord.Embed(color=self.client.embed_color, timestamp=datetime.fromtimestamp(endtime)).set_author(name=title, icon_url=guild.icon.url)
                embed.set_footer(text=f"Timer ends at")
                if endtime < round(time()):
                    await self.client.pool_pg.execute("DELETE FROM timers WHERE message_id = $1", timer_record.get('message_id'))
                    embed.title="Timer is over! 🎊"
                    try:
                        await message.edit(embed=embed)
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                        pass
                    try:
                        usermention = author.mention if author is not None else None
                        if usermention is None:
                            await channel.send(f"The {title} is over! 🎊")
                        else:
                            await channel.send(f"{usermention}'s {title} is over! 🎊")
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                        pass
                else:
                    embed.title = f"{humanize_timedelta(seconds=endtime - round(time()))} remaining..."
                    try:
                        await message.edit(embed=embed)
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                        pass

    @timer_loop.before_loop
    async def before_timer_loop(self):
        await self.client.wait_until_ready()
