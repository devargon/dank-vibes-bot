import discord
from discord.ext import commands, tasks
import time
import os

modchannel = 743174564778868796 if os.getenv('state') == '0' else 871737314831908974

class RemovingAccess(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.remind_perk_removal.start()
        self.command_removal.start()

    @tasks.loop(seconds=30.0)
    async def remind_perk_removal(self):
        await self.client.wait_until_ready()
        expired_perks = await self.client.pool_pg.fetch("SELECT * FROM perkremoval WHERE until < $1", round(time.time()))
        for perk in expired_perks:
            member = self.client.get_user(perk.get('member_id'))
            if member is not None:
                member = f"{member.mention} ({member.id})"
            else:
                member = f"{perk.get('member_id')}"
            await self.client.get_channel(modchannel).send(f"{member}'s **{perk.get('perk')}** is over.")
            await self.client.pool_pg.execute("DELETE FROM perkremoval WHERE until = $1 AND member_id = $2 AND perk = $3", perk.get('until'), perk.get('member_id'), perk.get('perk'))

    @tasks.loop(seconds=30.0)
    async def command_removal(self):
        await self.client.wait_until_ready()
        try:
            expired_commands = await self.client.pool_pg.fetch("SELECT * FROM commandaccess WHERE until < $1", round(time.time()))
            for commandperk in expired_commands:
                member = self.client.get_user(commandperk.get('member_id'))
                if member is not None:
                    member = f"{member.mention} ({member.id})"
                else:
                    member = f"{commandperk.get('member_id')}"
                await self.client.get_channel(modchannel).send(f"{member}'s **{commandperk.get('command')}** is over.\n*Just tracking, no need to do anything about this*")
                await self.client.pool_pg.execute("DELETE FROM commandaccess WHERE until = $1 AND member_id = $2 AND command = $3", commandperk.get('until'), commandperk.get('member_id'), commandperk.get('command'))
        except:
            pass

    def cog_unload(self) -> None:
        self.remind_perk_removal.stop()
        self.command_removal.stop()