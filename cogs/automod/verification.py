import discord
from discord.ext import commands, tasks
from time import time

class Verification(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.check_verification.start()

    @tasks.loop(minutes=30.0)
    async def check_verification(self):
        await self.client.wait_until_ready()
        for guild in self.client.guilds:
            is_enabled = await self.client.pool_pg.fetchval("SELECT enabled FROM serverconfig WHERE settings = $1 and guild_id = $2", 'verification', guild.id)
            if is_enabled:
                has_not_verified = []
                for member in guild.members:
                    if member.bot:
                        pass
                    elif member.pending == True:
                        if time() - member.joined_at.timestamp() > 86400:
                            has_not_verified.append(member)
                    elif member.pending == False:
                        if len(member.roles) == 0:
                            roleids = [837591810389442600, 671426678807068683, 671426686100963359, 671426692077584384, 649499248320184320]
                            roles = [guild.get_role(roleid) for roleid in roleids]
                            await member.add_roles(*roles, reason="Member finished Membership Screening")
                embed = discord.Embed(title="Verify in Dank Vibes", description="Remember to click on the **Verify** Button in <#910425487103365160> to gain access to the server!", color=5763312)
                embed.set_thumbnail(url="https://cdn.discordapp.com/icons/595457764935991326/a_fba2b3f7548d99cd344931e27930ec4d.gif?size=1024")
                embed.set_footer(text="Dank Vibes", icon_url="https://cdn.discordapp.com/icons/595457764935991326/a_fba2b3f7548d99cd344931e27930ec4d.gif?size=1024")
                for member in has_not_verified:
                    try:
                        await member.send(embed=embed)
                    except:
                        await self.client.get_channel(910425487103365160).send(f"{member.mention}", delete_after = 1.0)
                    await self.client.get_channel(616007729718231161).send(f"{member} ({member.id}) has been reminded about verifying. *This will be removed at a later date, am just using it to monitor*")

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

    def cog_unload(self) -> None:
        self.check_verification.stop()