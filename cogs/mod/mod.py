import time
import discord
import datetime
import asyncio
from discord.ext import commands
from utils import checks
from utils.format import text_to_file
from.lockdown import lockdown
from utils.buttons import *

class Mod(lockdown, commands.Cog, name='mod'):
    """
    Mod commands
    """
    def __init__(self, client):
        self.client = client
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

    @checks.is_bav_or_mystic()
    @commands.command(name="gcheck", brief = "Reminds DV Grinders that the requirement has been checked.", description = "Reminds DV Grinders that the requirement has been checked.")
    async def gcheck(self, ctx):
        """
        Reminds DV Grinders that the requirement has been checked.
        """
        grinderrole = ctx.guild.get_role(859494328422367273)
        tgrinderrole = ctx.guild.get_role(827270880182009956)
        if grinderrole is None or tgrinderrole is None:
            return await ctx.send("One or more roles declared in this command are invalid, hence the command cannot proceed.")
        grinders = [member for member in ctx.guild.members if grinderrole in member.roles or tgrinderrole in member.roles] # gets all grinders
        if len(grinders) == 0:
            return await ctx.send("There are no grinders to be DMed.")
        hiddengrinders = len(grinders) - 20 #number of grinders that will be hidden in "and ... more"
        message = ""
        while len(message) < 3700 and len(grinders) > hiddengrinders and len(grinders) > 0:
            member = grinders.pop(0)
            message += f"{member}\n" # add grinders name to embed
        if len(grinders) != 0:
            message += f"And **{len(grinders)}** more."
        confirmview = confirm(ctx, self.client, 15.0)
        embed = discord.Embed(title="DM Grinders?", description = f"I will be DMing these members with the {grinderrole.mention} and {tgrinderrole.mention} role to update them about the grinder check:\n\n{message}\n\nAre you sure?", color=0x57F0F0)
        message = await ctx.send(embed=embed, view=confirmview)
        confirmview.response = message
        await confirmview.wait()
        if confirmview.returning_value is None:
            embed.description = "Action cancelled."
            embed.color = discord.Color.red()
            return await message.edit(content="You didn't click on a button on time. Do you know how to click buttons?", embed=embed)
        if confirmview.returning_value == False:
            embed.description = "Action cancelled."
            embed.color = discord.Color.red()
            return await message.edit(content="Command stopped.", embed=embed)
        if confirmview.returning_value == True:
            msg = await ctx.send("<a:typing:839487089304141875> DMing grinders... ")
            embed = discord.Embed(title="DV Grinders Team", description=f"<a:dv_pointArrowOwO:837656328482062336> The daily grinder requirement has been checked.\n<a:dv_pointArrowOwO:837656328482062336> <#862574856846704661> is now unlocked and you may send the cash to `Dank Vibes Holder#2553`\n<a:dv_pointArrowOwO:837656328482062336> The next requirement check will take place in about <t:{round(time.time())+86400}:R> ( i.e between 1:30 and 3:30 GMT)", color=0x57F0F0)
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/595457764935991326/a_58b91a8c9e75742d7b423411b0205b2b.gif")
            embed.set_footer(text="DM/Ping TheMysticLegacy#0001 or Bav#0507 if you have any queries.",icon_url=ctx.guild.icon.url)
            success = 0
            grinders = [member for member in ctx.guild.members if grinderrole in member.roles or tgrinderrole in member.roles] # gets the grinder list again since the earlier one was popped
            faileddms = []
            for grinder in grinders:
                try:
                    await grinder.send(f"Hello {grinder.name}! I have a message for you:" if grinder.id != 709350868733919314 else f"Hello {grinder.name}! I have a message for you:\n||btw haii wiz uwu <a:dv_nekoWaveOwO:837756827255963718>- argon||", embed=embed) # hehe
                    success += 1
                except discord.Forbidden:
                    faileddms.append(grinder.mention) # gets list of people who will be pinged later
            if len(faileddms) > 0:
                channel = self.client.get_channel(862574856846704661)
                await channel.send(f"{' '.join(faileddms)}\n<a:dv_pointArrowOwO:837656328482062336> The daily grinder requirement has been checked.\n<a:dv_pointArrowOwO:837656328482062336> <#862574856846704661> is now unlocked and you may send the cash to `Dank Vibes Holder#2553`\n<a:dv_pointArrowOwO:837656328482062336> The next requirement check will take place in about <t:{round(time.time())+86400}:R> ( i.e between 1:30 and 3:30 GMT).")
            await msg.edit(content=f"DMed {success} members successfully, the rest were pinged in <#862574856846704661>.")