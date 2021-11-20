import aiohttp
import datetime
import sys
import time
import discord
import humanize
from abc import ABC
from .l2lvc import L2LVC
from .nicknames import nicknames
from discord.ext import commands
from .teleport import Teleport
from .suggestion import Suggestion
from .whois import Whois
from utils.time import humanize_timedelta
import psutil
import os
import asyncio
from utils.format import ordinal, comma_number, plural
from utils import checks
import os

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
        embed.add_field(name="Special Thanks To", value=f"{str(await self.client.fetch_user(727498137232736306))}\n{str(await self.client.fetch_user(560251854399733760))} <:DVB_RoarHeart:904877487778070528>\n{str(await self.client.fetch_user(642318626044772362))}", inline=True)
        if ctx.author.id in [650647680837484556, 515725341910892555, 321892489470410763]:
            loop = asyncio.get_event_loop()
            def get_advanced_details():
                nano_process = psutil.Process(os.getpid())
                memory = round(nano_process.memory_info()[0] / float(2 ** 20), 1)  # Converts to MB
                cpu = psutil.cpu_percent(interval=0.5)
                delta = discord.utils.utcnow() - self.client.uptime
                uptime_str = humanize.precisedelta(delta, format="%0.0f")
                return memory, cpu, uptime_str
            details = await loop.run_in_executor(None, get_advanced_details)
            embed.add_field(name="RAM Usage", value=f"{details[0]}MB", inline=True)
            embed.add_field(name="CPU Usage", value=f"{details[1]}%", inline=True)
            embed.add_field(name="Uptime", value=f"{details[2]}", inline=True)
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

    @checks.dev()
    @commands.command(name="github")
    async def irdkwhatthisis(self, ctx):
        """
        Shows the link to the github repo.
        """
        embed = discord.Embed(title="<a:DVB_Loading:909997219644604447> Contacting the GitHub server...", color=self.client.embed_color)
        msg = await ctx.send(embed=embed)
        now = time.perf_counter()
        token = f"token {os.getenv('GITHUBPAT')}"
        headers = {'Authorization': token}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get("https://api.github.com/repos/argo0n/dank-vibes-bot") as r:
                if r.status == 200:
                    data = await r.json()
                    if "full_name" in data:
                        embed.title = f"GitHub Repository: {data['full_name']}"
                        if "html_url" in data:
                            embed.url=data['html_url']
                    else:
                        embed.title = "Retrieving data failed."
                        embed.description = "Data did not have a key for `full_name`."
                        embed.color = discord.Color.red()
                        return await msg.edit(embed=embed)
                    if "description" in data:
                        embed.description = data['description']
                    if "owner" in data:
                        if "login" in data['owner']:
                            embed.add_field(name="🧑‍⚖️ Owner", value=f"[{data['owner']['login']}]({data['owner']['html_url']})", inline=True)
                    if "size" in data:
                        embed.add_field(name="💾 Size", value=f"{comma_number(data['size'])} KB", inline=True)
                    if "visibility" in data:
                        embed.add_field(name="🔒 Visibility", value=data['visibility'], inline=True)
                    if "default_branch" in data:
                        default_branch = data['default_branch']
                    else:
                        default_branch = None
                else:
                    embed.title = "Retrieving data failed."
                    embed.description = f"GitHub did not return a 200 status code.\nStatus code: {r.status}"
                    embed.color=discord.Color.red()
                    return await msg.edit(embed=embed)
            async with session.get("https://api.github.com/repos/argo0n/dank-vibes-bot/contributors") as r:
                if r.status == 200:
                    data = await r.json()
                    if len(data) > 0:
                        embed.add_field(name="🧑‍💻 Contributors", value="\n".join([f"[{contributor['login']}]({contributor['html_url']})" for contributor in data]), inline=True)
                else:
                    embed.add_field(name="🧑‍💻 Contributors", value=f"GitHub did not return a 200 status code.\nStatus code: {r.status}", inline=True)
            async with session.get("https://api.github.com/repos/argo0n/dank-vibes-bot/branches") as r:
                if r.status == 200:
                    data = await r.json()
                    if len(data) > 0:
                        branches = [branch['name'] for branch in data]
                        formatted_branches = []
                        for branch in branches:
                            if branch == default_branch:
                                formatted_branches.append(f"**{branch}**")
                            else:
                                formatted_branches.append(branch)
                        embed.add_field(name="📂 Branches", value="\n".join(formatted_branches), inline=True)
                else:
                    embed.add_field(name="📂 Branches", value=f"GitHub did not return a 200 status code.\nStatus code: {r.status}", inline=True)
                embed.add_field(name="🛠️ Last commit", value="<a:DVB_Loading:909997219644604447> Contacting the GitHub server...", inline=False)
            await msg.edit(content="Initial data retrieved in `{}`ms".format(round((time.perf_counter() - now) * 1000)), embed=embed)
            async with session.get("https://api.github.com/repos/argo0n/dank-vibes-bot/commits?page=1&per_page=1") as r:
                content = await r.json()
                embed.remove_field(-1)
                if r.status == 200:
                    if len(content) > 0:
                        async with session.get(content[0]['url']) as r:
                            if r.status == 200:
                                content = await r.json()
                                sha = content['sha']
                                um = [f"[`{sha[:7]}`]({content['html_url']}) [{content['commit']['message']}]({content['html_url']})"]
                                idk = "<:ReplyCont:871807889587707976> **Commited by:** " + content['commit']['author']['name']
                                um.append(idk)
                                date = datetime.datetime.strptime(content['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ")
                                date = date.strftime("%d %b %Y, %I:%M:%S %p")
                                idk = "<:ReplyCont:871807889587707976> **At: ** " + date
                                um.append(idk)
                                if 'stats' in content:
                                    stats = content['stats']
                                    idk = f"<:Reply:871808167011549244> {plural(int(stats['additions'])):addition}, {plural(int(stats['deletions'])):deletion}"
                                    um.append(idk)
                                embed.add_field(name="🛠️ Last commit", value="\n".join(um), inline=False)
                                fileschanged = []
                                if 'files' in content and len(content['files']) > 0:
                                    files = content['files']
                                    for file in files:
                                        idk = f"[{file['filename']}]({file['blob_url']}) <:DVB_plus:910010210310041630> {file['additions']}, <:DVB_minus:910010210310057994> {file['deletions']}"
                                        fileschanged.append(idk)
                                else:
                                    fileschanged.append("No files changed.")
                            else:
                                um = ["GitHub did not return a 200 status code.\nStatus code: {r.status}"]
                    else:
                        um = ["GitHub did not return any commits."]
                    totalfileschanged = "\n".join(fileschanged)
                    if len(totalfileschanged) > 1024:
                        tempstring = ''
                        for file in fileschanged:
                            if len(tempstring) + len(file) < 1024:
                                tempstring += file + "\n"
                            else:
                                embed.add_field(name="📂 Files changed", value=tempstring, inline=False)
                                tempstring = file + "\n"
                        embed.add_field(name="📂 Files changed", value=tempstring, inline=False)
                    else:
                        embed.add_field(name="📂 Files changed", value="\n".join(fileschanged), inline=False)
                else:
                    embed.add_field(name="🛠️ Last commit", value=f"GitHub did not return a 200 status code.\nStatus code: {r.status}", inline=False)
                await msg.edit(content="All retrieved in `{}`ms".format(round((time.perf_counter() - now) * 1000)), embed=embed)
