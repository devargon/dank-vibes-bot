import discord
from discord.ext import commands
from .freezenick import Freezenick
from .verification import Verification
from .timedrole import timedrole
from .timedunlock import TimedUnlock
from .namelog import NameLogging
from abc import ABC
import os
from utils import checks

verify_role = 911541857807384677

class verifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="✅", label="Verify", style=discord.ButtonStyle.blurple, custom_id='dv:verify')
    async def verifybutton(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send("<a:DVB_Loading:909997219644604447> Verifying you...", ephemeral=True)
        verifyrole = interaction.guild.get_role(verify_role)
        if verifyrole:
            await interaction.user.remove_roles(verifyrole)
        roleids = [905980110954455070, 905980110157541446, 905980109268324402, 905980108148461599, 905980107435442186] \
            if os.getenv('state') == '1' else \
            [837591810389442600, 671426678807068683, 671426686100963359, 671426692077584384, 649499248320184320]
        roles = [interaction.guild.get_role(roleid) for roleid in roleids]
        for role in roles:
            if role not in interaction.user.roles:
                await interaction.user.add_roles(role, reason="User completed manual verification")
        await interaction.followup.send("You've been verified! You should now be able to talk.", ephemeral=True)

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """
    pass

class AutoMod(NameLogging, timedrole, TimedUnlock, Verification, Freezenick, commands.Cog):
    """
    This file is just a placeholder for the various automod functions/modules.
    """
    def __init__(self, client):
        self.client = client
        self.freezenick.start()
        self.check_verification.start()
        self.timedrole.start()
        self.unlock.start()
        self.verifyview = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.verifyview == True:
            self.client.add_view(verifyView())
            self.verifyview = True

    def cog_unload(self) -> None:
        self.freezenick.stop()
        self.check_verification.stop()
        self.timedrole.stop()
        self.unlock.start()

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="verify")
    async def verify(self, ctx):
        """
        Sends the message that allows people to be verified with a button.
        """
        embed = discord.Embed(title="__**VERIFY**__", url="https://discord.gg/invite/dankmemer",
                              description="Click the **Verify** button below this embed to gain access to the server. By clicking you agree to all the rules mentioned above!\n** **",
                              color=5763312)
        embed.set_footer(text="Dank Vibes",
                         icon_url="https://cdn.discordapp.com/icons/595457764935991326/a_58b91a8c9e75742d7b423411b0205b2b.gif")
        embed.set_image(url="https://cdn.discordapp.com/attachments/616007729718231161/910817422557196328/rawr_nya.gif")
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/icons/595457764935991326/a_fba2b3f7548d99cd344931e27930ec4d.gif?size=1024")
        await ctx.send(embed=embed, view=verifyView())