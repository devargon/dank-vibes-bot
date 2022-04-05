import discord
from discord.ext import commands, tasks

class AutoStatus(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.status = None

    @tasks.loop(minutes=1.0)
    async def change_status(self):
        try:
            await self.client.wait_until_ready()
            statuses = await self.client.db.fetch("SELECT * FROM maintenance")
            not_under_maintenance = []
            under_maintenance = []
            for status in statuses:
                if status.get('enabled') == True:
                    under_maintenance.append(status.get('cog_name'))
                else:
                    not_under_maintenance.append(status.get('cog_name'))
            if len(under_maintenance) > 0:
                if len(not_under_maintenance) == 0:
                    self.status = discord.Game(f"Under maintenance")
                    um = discord.Status.dnd
                else:
                    list_of_cogs = ""
                    if len(under_maintenance) > 3:
                        mm = f"{under_maintenance[0]}, {under_maintenance[1]}, {under_maintenance[2]} and another {len(under_maintenance) - 3} categories"
                    else:
                        mm = ', '.join(under_maintenance)
                    self.status = discord.Game(f"Partially Under Maintenance: {mm}")
                    um = discord.Status.idle
            else:
                self.status = discord.Game(f"discord.gg/dankmemer | dv.help")
                um = discord.Status.online
            await self.client.change_presence(status=um, activity=self.status)
        except Exception as e:
            print(f"status task caught a error: {e}")
