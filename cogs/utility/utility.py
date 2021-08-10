import sys
import time
import discord
import asyncio
import humanize
import datetime
from abc import ABC
from .whois import Whois
from .l2lvc import L2LVC
from .nicknames import nicknames
from discord.ext import commands

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    pass

class Utility(Whois, L2LVC, nicknames, commands.Cog, name='utility', metaclass=CompositeMetaClass):
    """
    Utility commands
    """
    def __init__(self, client):
        self.client = client

    @commands.guild_only()
    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """
        Shows the bot uptime from when it was started.
        """
        since = self.client.uptime.strftime("%b %d, %H:%M:%S")
        delta = datetime.datetime.utcnow() - self.client.uptime
        uptime_str = humanize.precisedelta(delta, format="%0.0f")
        embed = discord.Embed(color=self.client.embed_color, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Uptime", value=uptime_str, inline=False)
        embed.add_field(name='Since', value=since, inline=False)
        embed.set_author(name=ctx.me.name)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name='ping')
    async def ping(self, ctx):
        """
        Get bot's latency.
        """
        start = time.perf_counter()
        message = await ctx.send("Ping?")
        end = time.perf_counter()
        totalping = round((end - start) * 1000)
        embed = discord.Embed(title='Pong!', color=self.client.embed_color)
        embed.description = f"**API:** `{round(self.client.latency * 1000)}` ms\n**RoundTrip:** `{totalping}` ms"
        try:
            await message.edit(content=None, embed=embed)
        except discord.NotFound:
            await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name='prefix', usage='[prefix]')
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix(self, ctx, *, prefix: str = None):
        """
        Changes the server's prefix.
        """
        if prefix is None:
            embed = discord.Embed(color=self.client.embed_color)
            current_prefix = self.client.get_guild_prefix(ctx.guild)
            embed.description = "<:greentick:806531672140283944> **Server's current prefix is :** `{}`".format(current_prefix)
            return await ctx.send(embed=embed)
        if "@everyone" in prefix or "@here" in prefix:
            return await ctx.send("You can't do that.")
        try:
            await self.client.set_prefix(ctx.guild, prefix)
            embed = discord.Embed(color=self.client.embed_color)
            embed.description = "<:greentick:806531672140283944> **Server's prefix changed to `{}`**".format(prefix)
            await ctx.send(embed=embed)
        except Exception:
            return await ctx.send_error()

    @commands.command(name='info')
    async def info(self, ctx):
        value_1 = []
        value_1.append(f'⚙ Commands: {len(self.client.commands)}')
        value_1.append(f'<:user_mention:868806554961453116> Users: `{len(self.client.users)}`')
        text = 0
        voice = 0
        stage = 0
        for guild in self.client.guilds:
            if guild.unavailable:
                continue
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text += 1
                elif isinstance(channel, discord.VoiceChannel):
                    voice += 1
                elif isinstance(channel, discord.StageChannel):
                    stage += 1
        value_1.append(f"<:text_channel:868806636230283314>  Text Channels: `{text}`")
        value_1.append(f'<:voice_channel:868806601123958834> Voice Channels: `{voice}`')
        if stage != 0:
            value_1.append(f'<:stage_channel:868806674452987924> Stage Channels: `{stage}`')
        py_version = "{}.{}.{}".format(*sys.version_info[:3])
        dpy_version = discord.__version__
        embed = discord.Embed(color=self.client.embed_color)
        embed.add_field(name='Stats', value="\n".join(value_1), inline=True)
        embed.add_field(name='Versions', value=f"<:python:868806455317393428> Python: `{py_version}`\n<:discordpy:868806486241992724> Discord.py: `{dpy_version}`", inline=True)
        embed.add_field(name='Developers', value=f"{str(self.client.get_user(650647680837484556))}\n{str(self.client.get_user(321892489470410763))}", inline=True)
        embed.add_field(name="Credits", value=f"{str(await self.client.fetch_user(727498137232736306))}", inline=True)
        embed.set_author(name=str(ctx.guild.me), icon_url=ctx.guild.me.avatar_url)
        embed.set_thumbnail(url=ctx.guild.me.avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="checkoverwrites", brief = "Checks the permission overwrites for that channel. Can be used to check who is in a private channel.", description = "Checks the permission overwrites for that channel. Can be used to check who is in a private channel.", aliases = ["privchannel", "pvc", "checkpvc"])
    async def checkoverwrites(self, ctx, channel:discord.TextChannel=None):
        """
        Checks the permission overwrites for that channel. Can be used to check who is in a private channel.
        """
        modrole = ctx.guild.get_role(608495204399448066)
        ownerrole = ctx.guild.get_role(608500355973644299)
        if modrole is None or ownerrole is None:
            await ctx.send("I had a problem checking for the required roles. For safety reasons, this command cannot be run until this problem is fixed.\n(Roles are defined as None)")
            return
        if modrole in ctx.author.roles or ownerrole in ctx.author.roles:
            if channel is None:
                await ctx.send("Wanted to check another channel, and not this one? You need to mention a channel.\nUsage of command: `checkoverwrites [channel]`")
                channel = ctx.channel # references the current channel
            messages = await channel.history(limit=1, oldest_first=True).flatten()
            message = messages[0]
            members = [overwriteobject for overwriteobject in channel.overwrites if isinstance(overwriteobject, discord.Member) and not overwriteobject.bot] # gets all members who have some sort of overwrite in that channel
            membersin = []
            for member in members:
                permissions = channel.permissions_for(member)
                if permissions.view_channel == True:
                    membersin.append(f"**{member.display_name}#{member.discriminator}** {member.mention} 🧑‍⚖️" if member.mentioned_in(message) else f"**{member.display_name}#{member.discriminator}** {member.mention}") # add them to a final list that shows who is in the channel
            members = "\n".join(membersin)
            members += f"\n\nMember Count: `{len(membersin)-1 if '🧑‍⚖️' in members else len(membersin)}`\n*This automatically excludes owners of the channel.*"
            embed = discord.Embed(
                title=f"Members in #{channel.name}",
                description=members[0:4096] or "It appears there's no one in this channel.", # limit the characters in case
                color=0x57F0F0,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_footer(icon_url=ctx.guild.icon_url, text="uwu") # you can remove this if you want idk
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"You do not have the required role (`{modrole}` or `{ownerrole}`) to use this command.") #self explanatory
            return

    @commands.command(name="hideping", brief="hides ping", description= "hides ping", aliases = ["hp", "secretping", "sp"], hidden=True)
    @commands.cooldown(1,5, commands.BucketType.user)
    async def hideping(self, ctx, member: discord.Member=None, *, message=None):
        """
        hides ping
        """
        perm_role = ctx.guild.get_role(865534172403597312)
        if perm_role is not None and perm_role not in ctx.author.roles:
            raise commands.CheckFailure()
        if member is None:
            await ctx.send("You missed out `member` for this command.\n**Usage**: `hideping [member] [message]`")
            return
        message = "" if message is None else message
        try:
            await ctx.message.delete() # hides the ping so it has to delete the message that was sent to ping user
        except discord.Forbidden:
            embed = discord.Embed(title="Command failed", description = "I could not complete this command as I am missing the permissions to delete your message.", color = 0xB00B13)
            embed.set_footer(text="Created by Argon#0002 uwu wicked now give me your role", icon_url=ctx.guild.icon_url)
            await ctx.send("I could not complete this command as I am missing the permissions to delete your message.")
            return
        content = f"‍{message}||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍ <@{member.id}>" # ik this looks sketchy, but you can paste it in discord and send it to see how this looks like :MochaLaugh:
        await ctx.send(content)

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

    @commands.command(name="lockgen", brief = "Locks specified channel for 5 seconds", description = "Locks specified channel for 5 seconds", aliases = ["lg"])
    @commands.cooldown(1, 10800, commands.BucketType.user)
    async def lockgen(self, ctx):
        """
        Locks specified channel for 5 seconds
        """
        roleid = 865534338471690280 # DV's Voted 150x: 865534338471690280
        genchatid = 608498967474601995 # DV's genchat: 608498967474601995
        genchat = self.client.get_channel(genchatid)
        role = ctx.guild.get_role(roleid)
        if role not in ctx.author.roles:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"You do not have the required role (`{role}`) to use this command.")
        if genchat is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"Could not find a channel with the ID {genchatid}.")
        if ctx.channel != genchat:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"This command can only be used in {genchat.mention}!")
        if role is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"Could not find a role with the ID {roleid}.")
        originaloverwrite = genchat.overwrites_for(ctx.guild.default_role) # this is the overwrite that will be restored to gen chat when the lockdown is over
        newoverwrite = genchat.overwrites_for(ctx.guild.default_role) # this is the overwrite that i will edit to lockdown the channel
        authornewoverwrite = genchat.overwrites_for(ctx.author) # this is the overwrite that I will edit to allow the invoker to continue talking
        authornewoverwrite.send_messages=True # this edits the author's overwrite
        newoverwrite.send_messages = False # this edits the @everyone overwrite
        authororiginaloverwrite = None if ctx.author not in genchat.overwrites else genchat.overwrites_for(ctx.author) # this is the BEFORE overwrite for an individual member, if the author already had an overwrite (such as no react) it will use that to restore, otherwise None since it won't have any overwrites in the first place
        try:
            await genchat.set_permissions(ctx.author, overwrite=authornewoverwrite, reason=f"Lockdown invoker gets to talk c:") # allows author to talk
            await genchat.set_permissions(ctx.guild.default_role, overwrite = newoverwrite, reason = f"5 second lockdown initiated by {ctx.author.name}#{ctx.author.discriminator} with the {role.name} perk") # does not allow anyone else to talk
        except discord.Forbidden:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"I do not have the required permission to lock down **{genchat.name}**.")
        message = await ctx.send(f"✅ Locked down **{genchat.name}** for 5 seconds.")
        await asyncio.sleep(5)
        try:
            await genchat.set_permissions(ctx.guild.default_role, overwrite = originaloverwrite, reason = "Lockdown over uwu") # restores
            await genchat.set_permissions(ctx.author, overwrite = authororiginaloverwrite, reason = "Overwrite no longer required") # restores
        except discord.Forbidden:
            return await ctx.send(f"I do not have the required permission to remove the lockdown for **{genchat.name}**.")
        else:
            try:
                await message.add_reaction("🔓")
            except discord.Forbidden:
                pass

    @commands.command(name="gcheck", brief = "Reminds DV Grinders that the requirement has been checked.", description = "Reminds DV Grinders that the requirement has been checked.")
    async def gcheck(self, ctx):
        """
        Reminds DV Grinders that the requirement has been checked.
        """
        grinderrole = ctx.guild.get_role(859494328422367273)
        tgrinderrole = ctx.guild.get_role(827270880182009956)
        if grinderrole is None or tgrinderrole is None:
            return await ctx.send("One or more roles declared in this command are invalid, hence the command cannot proceed.")
        if ctx.author.id not in [719890992723001354, 542447261658120221]: #bav and mystic
            if not ctx.author.guild_permissions.manage_roles == True: # modms+
                return await ctx.send("You need to be a `mystic` or `bav` or have the required permissions to use this command.")
        else:
            pass
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
        embed = discord.Embed(title="DM Grinders?", description = f"I will be DMing these members with the {grinderrole.mention} and {tgrinderrole.mention} role to update them about the grinder check:\n\n{message}\n\nAre you sure?", color=0x57F0F0)
        message = await ctx.send(embed=embed)
        reactions = ["<:checkmark:841187106654519296>", "<:crossmark:841186660662247444>"]
        for reaction in reactions:
            await message.add_reaction(reaction)
        def check(payload):
            return payload.user_id == ctx.message.author.id and payload.channel_id == ctx.channel.id and payload.message_id == message.id and str(payload.emoji) in reactions
        try:
            response = await self.client.wait_for('raw_reaction_add', timeout=15, check=check)
            if not str(response.emoji) == '<:checkmark:841187106654519296>':
                return await message.edit(content="Command stopped.")
        except asyncio.TimeoutError:
            ctx.command.reset_cooldown(ctx)
            return await message.edit(content="You didn't react on time.")
        else:
            await message.clear_reactions()
            msg = await ctx.send("<a:typing:839487089304141875> DMing grinders... ")
            embed = discord.Embed(title="DV Grinders Team", description=f"<a:dv_pointArrowOwO:837656328482062336> The daily grinder requirement has been checked.\n<a:dv_pointArrowOwO:837656328482062336> <#862574856846704661> is now unlocked and you may send the cash to `Dank Vibes Holder#2553`\n<a:dv_pointArrowOwO:837656328482062336> The next requirement check will take place in about <t:{round(time.time())+86400}:R> ( i.e between 1:30 and 3:30 GMT)", color=0x57F0F0)
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/595457764935991326/a_58b91a8c9e75742d7b423411b0205b2b.gif")
            embed.set_footer(text="DM/Ping TheMysticLegacy#0001 or Bav#0507 if you have any queries.",icon_url=ctx.guild.icon_url)
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
