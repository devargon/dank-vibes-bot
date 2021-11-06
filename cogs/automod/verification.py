import discord
from discord.ext import commands

class Verification(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_update(self, member_before, member_after):
        is_enabled = await self.client.pool_pg.fetchval("SELECT enabled FROM serverconfig WHERE settings = $1 and guild_id = $2", 'verification', member_after.guild.id)
        if is_enabled != True:
            return
        if member_before.pending != True or member_after.pending != False or member_before.bot:
            return
        if member_before.guild.id == 871734809154707467:
            guild = member_before.guild
            roleids = [905980107435442186, 905980108148461599, 905980109268324402, 905980110157541446, 905980110954455070]
            roles = [guild.get_role(roleid) for roleid in roleids]
        elif member_before.guild.id == 595457764935991326:
            guild = member_before.guild
            roleids = [837591810389442600, 671426678807068683, 671426686100963359, 671426692077584384, 649499248320184320]
            roles = [guild.get_role(roleid) for roleid in roleids]
        else:
            return
        await member_before.add_roles(*roles, reason="Member finished Membership Screening")