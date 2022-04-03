import discord
from discord.ext import commands, tasks
import time
import os

disboardchannel = 871737314831908974 if os.getenv('state') == '1' else 630898540155240480

class TimedUnlock(commands.Cog):
    def __init__(self, client):
        self.client = client

    @tasks.loop(seconds=1)
    async def unlock(self):
        await self.client.wait_until_ready()
        try:
            now = int(round(time.time()))
            unlockingchannels = await self.client.pool_pg.fetch("SELECT * FROM timedunlock WHERE time <= $1", now)
            for row in unlockingchannels:
                guild = self.client.get_guild(row.get('guild_id'))
                if guild is not None:
                    channel = guild.get_channel(row.get('channel_id'))
                    if channel is not None:
                        moderator = self.client.get_user(row.get('responsible_moderator'))
                        if moderator is not None:
                            reason = "Automatic channel unlock from lock invoked by {}".format(moderator)
                        else:
                            reason = "Automatic channel unlock from lock invoked by {}".format(row.get('responsible_moderator'))
                        try:
                            overwrite = channel.overwrites_for(guild.default_role)
                            overwrite.send_messages = None
                            await channel.set_permissions(guild.default_role, overwrite=overwrite, reason=reason)
                            if channel.id == disboardchannel:
                                await channel.send(embed=discord.Embed(title="You can now bump the server!", description="Use the slash command `/bump` to bump the server!", color=0xffffff).set_image(url="https://cdn.discordapp.com/attachments/871737314831908974/960030629959970856/unknown.png"))
                        except:
                            pass
                await self.client.pool_pg.execute("DELETE FROM timedunlock WHERE channel_id = $1 AND time = $2", row.get('channel_id'), row.get('time'))
        except Exception as e:
            print(f"timedunlock task caught a error: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        self.unlock.start()