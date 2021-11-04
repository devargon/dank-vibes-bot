import sys
import time
import discord
import humanize
import datetime
from abc import ABC
from .whois import Whois
from .l2lvc import L2LVC
from .nicknames import nicknames
from discord.ext import commands
from .teleport import Teleport
from .suggestion import Suggestion
from utils.format import ordinal
from utils.time import humanize_timedelta

footertext = {
    752403154259148810: 'stinky !! 😤',
    395020663116529674: 'diarhea human',
    594959254369337345: 'Kannazumi',
    602066975866355752: 'i\'m standing on thick ice',
    542905463541465088: 'DiAri',
    27409176946409543: 'funky',
    650647680837484556: 'wow, the cleanest human has summoned me',
    406748083377012746: 'jitu :)',
    436720581501517824: 'clayde nice pfp',
    493063931191885825: 'the nicest human on earth :3',
    515725341910892555: 'no you are not getting su perms ven',
    642318626044772362: 'sussy amogus impostor',
    752242566493372539: 'ley please tell blu to be less stinky ty',
    264019387009204224: 'DiAri',
    424685275793457173: 'foxy',
    740783485270229084: 'AKEH',
    506320624377921546: 'Hi Jenn :)',
    366069251137863681: 'bobbi :(',
    560251854399733760: 'frenzy uwu :3',
    392127809939570688: 'hi kathy :)',
    697969807789654076: 'desteva uwu',
    517115653623119913: 'dany :)',
    689561648863772813: 'Kannazumi',
    722202979532275752: 'the delete button is so close to the enter button',
    695161675782815825: 'ann hiihihihihii',
    592092580846632994: 'hey tanzil',
    727409176946409543: 'jazyyyyyy',
    663867896195186698: 'hello leslie :)',
    267608116370079745: 'hey kate :))',
    886598864965103727: 'azumi i hope you lose all your dumbfights',
    722109586487640074: 'hello demon :))',
    719890992723001354: 'mystic :(',
    542447261658120221: 'bav you pro',
    501319699167051777: 'hello ghosty :)',
    391242096201302039: 'hello pacific',
}
from utils.format import ordinal
from utils import checks

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    pass

class Utility(Whois, L2LVC, nicknames, Suggestion, Teleport, commands.Cog, name='utility', metaclass=CompositeMetaClass):
    """
    Utility commands
    """
    def __init__(self, client):
        self.client = client
        self.nickconfig = {}
        self.persistent_views_added = False

    @commands.guild_only()
    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """
        Shows the bot uptime from when it was started.
        """
        since = self.client.uptime.strftime("%b %d, %H:%M:%S")
        delta = discord.utils.utcnow() - self.client.uptime
        uptime_str = humanize.precisedelta(delta, format="%0.0f")
        embed = discord.Embed(color=self.client.embed_color, timestamp=discord.utils.utcnow())
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
        """
        Shows some information about this bot.
        """
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
        embed.set_author(name=str(ctx.guild.me), icon_url=ctx.guild.me.display_avatar.url)
        embed.set_thumbnail(url=ctx.guild.me.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="checkpvc", aliases = ["privchannel", "pvc"])
    async def checkoverwrites(self, ctx, channel:discord.TextChannel=None):
        """
        Checks the permission overwrites for that channel. Can be used to check who is in a private channel.
        """
        if channel is None:
            channel = ctx.channel
        modrole = ctx.guild.get_role(608495204399448066)
        messages = await channel.history(limit=1, oldest_first=True).flatten()
        message = None if len(messages) == 0 else messages[0]
        if modrole not in ctx.author.roles:
            channel = ctx.channel
            if ctx.channel.category_id not in [802467427208265728, 763457841133912074, 789195494664306688, 783299769580781588, 805052824185733120, 834696686923284510, 847897065081274409]:
                return await ctx.send("You can only use this command in your own private channel.")
            if not ctx.author.mentioned_in(message):
                return await ctx.send("You can't check the members in this channel as you do not own this channel. If you think there is an error, please contact a Moderator in <#870880772985344010>.")
        owner = None
        owner_member = None
        if len(message.mentions) > 0:
            owner_member = message.mentions[0]
            owner = f"**{owner_member}** {owner_member.mention}"
            if owner_member not in channel.overwrites:
                owner += "\n⚠️ Not in channel"
        else:
            owner_member = None
        members = [overwriteobject for overwriteobject in channel.overwrites if isinstance(overwriteobject, discord.Member) and not overwriteobject.bot] # gets all members who have some sort of overwrite in that channel
        membersin = []
        for member in members:
            if member != owner_member:
                permissions = channel.permissions_for(member)
                if permissions.view_channel == True:
                    membersin.append(f"**{member}** {member.mention}")
        membermsg = "".join(f"`{count}.` {i}\n" for count, i in enumerate(membersin, start=1))
        embed = discord.Embed(title=f"Private Channel Details of #{channel.name}", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.add_field(name="Owner 🧑‍⚖️", value = owner or "Unknown", inline=True)
        embed.add_field(name="Members", value=membermsg if len(membermsg) > 0 else "No one is in this channel.", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Member Count", value=f"`{len(membersin)}`", inline=True)
        embed.add_field(name="Created at", value=channel.created_at.strftime("%a, %b %d, %Y") if channel.created_at is not None else 'Unknown')
        category = discord.utils.get(ctx.guild.categories, id=channel.category_id)
        embed.add_field(name="Under Category", value=category.name or "Unknown")
        if ctx.author.id in footertext:
            embed.set_footer(icon_url=ctx.guild.icon.url, text=footertext[ctx.author.id]) # you can remove this if you want idk
        await ctx.send(embed=embed)

    @checks.not_in_gen()
    @commands.command(name="mymessages", aliases=["messagecount", "mym"])
    async def messagecount(self, ctx, member:discord.Member = None):
        """
        Shows the number of messages a member has sent in <#608498967474601995>.
        """
        if member is None:
            member = ctx.author
        user = await self.client.pool_pg.fetchrow("SELECT * FROM messagelog WHERE user_id = $1", member.id)
        if user is None:
            return await ctx.send("Hmm... it appears that you have not sent a message in <#608498967474601995>. Contact a mod if you think this is wrong.")
        all = await self.client.pool_pg.fetch("SELECT user_id FROM messagelog ORDER BY messagecount DESC")
        user2 = await self.client.pool_pg.fetchrow("SELECT user_id FROM messagelog WHERE user_id = $1", member.id)
        position = ordinal(all.index(user2)+1)
        embed = discord.Embed(title="Your number of messages sent in #general-chat", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=member, icon_url=member.display_avatar.url)
        embed.add_field(name="Message count", value=user.get('messagecount'), inline=True)
        embed.add_field(name="Position", value=f"{position} {'🏆' if all.index(user2) < 10 else ''}", inline=True)
        await ctx.reply(embed=embed)

    @commands.command(name="cooldowns", aliases = ['mycooldowns', 'cds', 'mycds', 'cd'])
    async def cooldowns(self, ctx):
        """
        Shows your active cooldowns in Dank Vibes Bot.
        """
        cooldownlst = []
        for Command in self.client.commands:
            Command._buckets._verify_cache_integrity() # removes old cooldowns
            if len(Command._buckets._cache) and ctx.author.id in Command._buckets._cache:
                command_cache = Command._buckets._cache[ctx.author.id]
                duration = command_cache.get_retry_after()
                if duration > 0:
                    cooldownlst.append(f"**{Command.name}**: {humanize_timedelta(seconds=duration)}")
        db_cds = await self.client.pool_pg.fetch("SELECT * FROM cooldowns WHERE member_id = $1", ctx.author.id)
        if len(db_cds) > 0:
            for cd in db_cds:
                command_name = cd.get('command_name')
                duration_of_cd = cd.get('time') - round(time.time())
                if duration_of_cd > 0:
                    cooldownlst.append(f"**{command_name}**: {humanize_timedelta(seconds=duration_of_cd)}")
        embed = discord.Embed(color=self.client.embed_color, description='\n'.join(cooldownlst) if cooldownlst else "You have no existing cooldowns!", timestamp=discord.utils.utcnow())
        embed.set_author(name=f"{ctx.author.name}'s Cooldowns", icon_url=str(ctx.author.display_avatar.url))
        embed.set_footer(text=ctx.guild.name,  icon_url=str(ctx.guild.icon.url))
        await ctx.send(embed=embed)