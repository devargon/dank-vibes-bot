import time
import discord
import datetime
import asyncio
from discord.ext import commands
from utils import checks
from utils.format import text_to_file
from.lockdown import lockdown
from utils.buttons import *
from .browser_screenshot import BrowserScreenshot
from selenium import webdriver

class Mod(BrowserScreenshot, lockdown, commands.Cog, name='mod'):
    """
    Mod commands
    """
    def __init__(self, client):
        self.op = webdriver.ChromeOptions() # selenium options for chrome
        self.op.add_argument('--no-sandbox')
        self.op.add_argument('--disable-gpu')
        self.op.add_argument('--headless')
        self.op.add_argument("--window-size=1920,1080")
        self.op.add_argument('--allow-running-insecure-content')
        self.op.add_argument('--ignore-certificate-errors')
        self.op.add_argument('--user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36"')
        self.client = client

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="self", aliases=["selfroles"])
    async def selfroles(self, ctx, channel:discord.TextChannel = None):
        """
        Sends a message showing the 5 self roles which can be gotten via buttons.
        """
        roleids = [859493857061503008, 758174135276142593, 758174643814793276, 680131933778346011, 713477937130766396]#[895815546292035625, 895815588289581096, 895815773208051763, 895815799812521994, 895815832465190933]
        role1 = ctx.guild.get_role(roleids[0])
        role2 = ctx.guild.get_role(roleids[1])
        role3 = ctx.guild.get_role(roleids[2])
        role4 = ctx.guild.get_role(roleids[3])
        role5 = ctx.guild.get_role(roleids[4])
        if role1 == None or role2 == None or role3 == None or role4 == None or role5 == None:
            return await ctx.send("1 or more roles in this command is/are declared as invalid, hence the command cannot proceed.")
        roles = [role1, role2, role3, role4, role5]
        if channel is None:
            channel = ctx.channel
        class selfroles(discord.ui.View):
            def __init__(self, ctx: DVVTcontext, client, timeout):
                self.context = ctx
                self.response = None
                self.result = None
                self.client = client
                super().__init__(timeout=timeout)
                emojis = ["<a:dv_wStarOwO:837787067303198750>", "<a:dv_wHeartsOwO:837787079320666138>", "<a:dv_wSparklesOwO:837782054782632006>", "<a:dv_wpinkHeartOwO:837781949337960467>", "<:dv_wFlowerOwO:837700860511256627>"]
                rolenames = []
                for role in roles:
                    rolenames.append(role.name)

                class somebutton(discord.ui.Button):
                    async def callback(self, interaction: discord.Interaction):
                        print(str(self.emoji))
                        print(emojis.index(str(self.emoji)))
                        target_role = roles[emojis.index(str(self.emoji))]
                        if target_role in interaction.user.roles:
                            await interaction.user.remove_roles(target_role, reason="Selfrole")
                            await interaction.response.send_message(f"The role **{target_role.name}** has been removed from you.", ephemeral=True)
                        else:
                            await interaction.user.add_roles(target_role, reason="Selfrole")
                            await interaction.response.send_message(f"The role **{target_role.name}** has been added to you.", ephemeral=True)
                        #await update_roles(self.emoji)
                for emoji in emojis:
                    self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=rolenames[emojis.index(emoji)], style=discord.ButtonStyle.grey))
        await channel.send("Press the button to claim your role.", view=selfroles(ctx, self.client, None))


    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="getraw", aliases = ['raw', 'rawmessage'])
    async def getrawmessage(self, ctx, message_id=None, channel:discord.TextChannel=None):
        """
        Gets the raw content of a message.
        """
        if not message_id:
            return await ctx.send("`dv.getraw <message_id> <channel>`\nMessage ID is a required argument.")
        if not channel:
            channel = ctx.channel
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send(f"I did not find a message with the ID {message_id} in {channel}. {'DId you forget to include `channel`?' if channel == ctx.channel else ''}")
        else:
            content = message.content
            if "‍" in content or "​" in content:
                return await ctx.send("Nice try, but you won't be able to get the raw text for hiding pings.")
            if len(content) > 4096:
                await ctx.send(f"Raw content of message with ID {message_id} in {channel}", file=text_to_file(content, "file.txt", "utf8"))
            else:
                await ctx.send(embed=discord.Embed(title=f"Raw content of message with ID {message_id} in {channel}", description=f"```\n{content}\n```", color = self.client.embed_color))

    @commands.command(name="memberpvc", brief = "Checks the private channels that a member has access to", description = "Checks the private channels that a member has access to", aliases = ["pvcmember"])
    @commands.has_guild_permissions(manage_roles=True)
    async def memberpvc(self, ctx, member:discord.Member = None):
        """
        Checks the private channels that a member has access to
        """
        if member is None:
            await ctx.send("Wanted to check another member, and not yourself? You need to include a member.\nUsage of command: `memberpvc [channel]`")
            member = ctx.author
        # categoryids = [869943348608270446] this is for my server
        categoryids = [802467427208265728, 763457841133912074, 789195494664306688, 783299769580781588, 805052824185733120, 834696686923284510, 847897065081274409] # this is for dv (all the category IDs for the VIP channels)
        categories = []
        for categoryid in categoryids:
            category = discord.utils.find(lambda m: m.id == categoryid, ctx.guild.categories)
            if category is None:
                await ctx.send(f"I could not find a category for the ID {category}")
            else:
                categories.append(category) # gets all the categories for channels
        accessiblechannels = []
        for category in categories:
            for channel in category.channels:
                if channel.id in [820011058629836821, 763458133116059680]:
                    pass
                else:
                    permissions = channel.permissions_for(member)
                    if permissions.view_channel == True:
                        accessiblechannels.append(channel.mention) # gets all the channels that the user can see in private channels
        streeng = "" #ignore the spelling
        for channel in accessiblechannels:
            if len(streeng) < 3900:
                streeng += f"{channel}\n"
            else:
                embed = discord.Embed(title = f"Channels that {member.name}#{member.discriminator} can access", description=streeng, color = 0x57f0f0)
                await ctx.send(embed=embed)
                streeng = f"{channel}\n"
        embed = discord.Embed(title=f"Channels that {member.name}#{member.discriminator} can access",
                            description=streeng, color=0x57f0f0)
        await ctx.send(embed=embed)
