import discord
from discord.ext import commands, tasks
from time import time

class Freezenick(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.freezenick.start()

    @tasks.loop(seconds=5.0)
    async def freezenick(self):
        await self.client.wait_until_ready()
        try:
            timenow = time()
            result = await self.client.db.fetch("SELECT * FROM freezenick")
            for row in result:
                guild = self.client.get_guild(row.get('guild_id'))
                if guild is not None:
                    member = guild.get_member(row.get('user_id'))
                    if row.get('time') < timenow:
                        if member:
                            try:
                                await member.edit(nick=row.get('old_nickname'))
                            except:
                                pass
                            else:
                                try:
                                    await member.send("Your nickname has been restored and is no longer frozen.")
                                except:
                                    pass
                        await self.client.db.execute("DELETE FROM freezenick WHERE id = $1", row.get('id'))
                    elif member and member.display_name != row.get('nickname'):
                        try:
                            await member.edit(nick=row.get('nickname'))
                        except:
                            pass
                else:
                    await self.client.db.execute("DELETE FROM freezenick WHERE id = $1", row.get('id'))
        except Exception as e:
            errormsg = f"Error in Freezenick function: {e}"
            if len(errormsg) > 2000:
                print(errormsg)
                await self.client.get_channel(871737028105109574).send("There was an error in freezenick function, check the log for details.")
            else:
                await self.client.get_channel(871737028105109574).send(errormsg)
