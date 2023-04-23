import discord
from discord.ext import commands, tasks
from time import time

from main import dvvt


class Verification(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
        self.check_verification.start()

    @tasks.loop(seconds=120.0)
    async def check_verification(self):
        await self.client.wait_until_ready()
        try:
            for guild in self.client.guilds:
                print(f"Checking {guild}")
                g = await self.client.get_guild_settings(guild.id)
                if g.verification is True:
                    print(f"{guild} has Verification enabled ")
                    has_not_verified = []
                    for member in guild.members:
                        if member.bot:
                            continue
                        elif member.pending == True:
                            if time() - member.joined_at.timestamp() > 86400:
                                has_not_verified.append(member)
                        elif member.pending == False:
                            print(f"Checking {member}")
                            if len(member.roles) == 0 or (len(member.roles) > 2 and guild.get_role(911541857807384677) in member.roles):
                                if member.status != discord.Status.offline:
                                    print(f"{member} qualifies.")

                                #roleids = [837591810389442600, 671426678807068683, 671426686100963359, 671426692077584384, 649499248320184320, 758174643814793276, 837594909917708298]
                                #roles = [a := guild.get_role(roleid) for roleid in roleids if a not in member.roles]
                                #await member.add_roles(*roles, reason="Member finished Membership Screening")
                    embed = discord.Embed(title="Verify in Dank Vibes", description="Remember to click on the **Verify** Button in <#910425487103365160> to gain access to the server!", color=5763312)
                    embed.set_thumbnail(url="https://cdn.discordapp.com/icons/595457764935991326/a_fba2b3f7548d99cd344931e27930ec4d.gif?size=1024")
                    embed.set_footer(text="Dank Vibes", icon_url="https://cdn.discordapp.com/icons/595457764935991326/a_fba2b3f7548d99cd344931e27930ec4d.gif?size=1024")
                    verify = guild.get_role(911541857807384677)
                    for member in has_not_verified:
                        if verify is not None and verify not in member.roles:
                            await member.add_roles(verify)
                            try:
                                await member.send(embed=embed)
                            except:
                                await self.client.get_channel(910425487103365160).send(f"{member.mention}", delete_after=1.0)
        except Exception as e:
            print(f"verification task caught a error: {e}")

    @commands.Cog.listener()
    async def on_member_update(self, member_before, member_after):
        if time() - member_before.joined_at.timestamp() > 86400:
            return
        sc = await self.client.get_guild_settings(member_after.guild.id)
        if sc.verification is not True:
            return
        if member_before.pending != True or member_after.pending != False or member_before.bot:
            return
        if member_before.guild.id == 871734809154707467:
            guild = member_before.guild
            roleids = [905980107435442186, 905980108148461599, 905980109268324402, 905980110157541446, 905980110954455070]
            roles = [guild.get_role(roleid) for roleid in roleids]
        elif member_before.guild.id == 595457764935991326:
            guild = member_before.guild
            roleids = [837591810389442600, 671426678807068683, 671426686100963359, 671426692077584384, 649499248320184320, 837594909917708298]
            roles = [guild.get_role(roleid) for roleid in roleids]
        else:
            return
        await member_before.add_roles(*roles, reason="Member finished Membership Screening")