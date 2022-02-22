import discord
from discord.ext import commands, tasks
import time

class timedrole(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.timedrole.start()

    @tasks.loop(seconds=5.0)
    async def timedrole(self):
        try:
            await self.client.wait_until_ready()
            timenow = round(time.time())  # Gets the time now
            result = await self.client.pool_pg.fetch("SELECT * FROM autorole WHERE time < $1", timenow)
            if len(result) == 0:
                return
            for row in result:
                guild = self.client.get_guild(row.get('guild_id'))
                if guild is not None:
                    member = guild.get_member(row.get('member_id'))
                    if member is not None:
                        role = guild.get_role(row.get('role_id'))
                        if role is not None:
                            try:
                                await member.remove_roles(role, reason="Delayed role removal")  # removes the vibing dankster role
                            except discord.Forbidden:
                                pass
                await self.client.pool_pg.execute("DELETE FROM autorole WHERE member_id = $1 and guild_id = $2 and role_id = $3 and time = $4", row.get('member_id'), row.get('guild_id'), row.get('role_id'), row.get('time'))
        except Exception as e:
            print(e)