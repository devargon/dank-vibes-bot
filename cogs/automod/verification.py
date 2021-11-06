import discord
from discord.ext import commands, tasks
from time import time

class Verification(commands.Cog):
    def __init__(self, client):
        self.client = client

    @tasks.loop(minutes=30.0)
    async def check_verification(self):
        for guild in self.client.guilds:
            is_enabled = await self.client.pool_pg.fetchval("SELECT enabled FROM serverconfig WHERE settings = $1 and guild_id = $2", 'verification', guild.id)
            if is_enabled:
                has_not_verified = [member for member in guild.members if (not member.bot) and (member.pending == True)]
                str = ""
                for member in has_not_verified:
                    if time() - member.joined_at.timestamp() > 86400:
                        if len(str) < 1800:
                            str += f"{member.mention} has not verified **and is eligible to be kicked.**."
                        else:
                            await self.client.get_channel(616007729718231161).send(str)
                    else:
                        if len(str) < 1800:
                            str += f"{member.mention} has not verified but joined less than 24 hours ago."
                        else:
                            await self.client.get_channel(616007729718231161).send(str)
                await self.client.get_channel(616007729718231161).send(str)
                """try:
                    await member.send("You were automatically kicked from Dank Vibes as you have not agreed to the rules yet. To participate in the many giveaways/heists that Dank Vibes offers, come back and **agree to the rules** by pressing `Complete` at the bottom of your Discord client! https://cdn.discordapp.com/attachments/616007729718231161/906394155343818832/Screenshot_2021-11-06_at_9.36.42_AM.png\nhttps://discord.gg/dankmemer")
                except:
                    await self.client.get_channel(616007729718231161).send(f"I was unable to DM {member} that they were kicked for not completing the verification.")
                await member.kick(reason="Auto kick - Incomplete Verification")"""





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