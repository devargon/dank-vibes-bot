from collections import Counter

import discord
from discord.ext import commands

import re
import os
import sys
import time
import typing
import psutil
import asyncio
import aiohttp
from datetime import datetime
import humanize
import functools
from abc import ABC
import httpcore._exceptions
from googletrans import Translator
import googletrans, googletrans.models

from utils import checks
from utils.context import DVVTcontext
from utils.paginator import SingleMenuPaginator
from utils.specialobjects import ContestSubmission, Contest
from utils.time import humanize_timedelta
from utils.errors import ArgumentBaseError
from utils.converters import BetterTimeConverter
from utils.format import ordinal

from .l2lvc import L2LVC
from .whois import Whois
from .teleport import Teleport
from .nicknames import nicknames
from .suggestion import Suggestion
from .polls import polls
from .autoreactor import Autoreaction
from .highlights import Highlight
from .reminders import reminders
from .utility_slash import UtilitySlash
from .customrole import CustomRoleManagement

class GetHeistPing(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Get the Heist Ping role", style=discord.ButtonStyle.green)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not discord.utils.get(interaction.user.roles, name="Heist Ping"):
            await interaction.user.add_roles(discord.utils.get(interaction.guild.roles, name="Heist Ping"))
            await interaction.response.send_message("<:DVB_True:887589686808309791> The <@&758174643814793276> role has been added to you!", ephemeral=True)
        else:
            await interaction.response.send_message("<:DVB_True:887589686808309791> You already have the <@&758174643814793276> role.", ephemeral=True)

class TimerRemindMe(discord.ui.View):
    def __init__(self, timestamp, what_to_remind):
        self.timestamp = timestamp
        self.what_to_remind = what_to_remind
        self.reminded = []
        super().__init__(timeout=None)

    @discord.ui.button(label="Remind Me!", emoji="🔔", style=discord.ButtonStyle.blurple)
    async def remind_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.channel.id in [876827800236064808, 690125458272288814, 871737314831908974]:
            heistpingview = GetHeistPing()
        else:
            heistpingview = None
        if time.time() > self.timestamp:

            await interaction.response.send_message("This timer is over.", view=heistpingview, ephemeral=True)
            button.disabled = True
            return await interaction.message.edit(view=self)
        if interaction.user.id in self.reminded:
            return await interaction.response.send_message("You've already chosen to be reminded!", view=heistpingview, ephemeral=True)
        else:
            await interaction.client.get_cog('utility').add_reminder(interaction.user.id, interaction.guild.id, 698462922682138654, interaction.message.id, self.what_to_remind, self.timestamp)
            if interaction.channel.id in [876827800236064808, 690125458272288814, 871737314831908974]:
                if interaction.guild.id == 595457764935991326:
                    heistping = interaction.guild.get_role(758174643814793276)
                    if heistping in interaction.guild.roles:
                        await interaction.user.add_roles(heistping)
                await interaction.response.send_message(f"Alright! I'll remind you about **{self.what_to_remind}** in **{humanize_timedelta(seconds=round(self.timestamp - time.time()))}**.\nI've also given you the **Heist Ping** role for you to be reminded of future heists!", ephemeral=True)
            else:
                await interaction.response.send_message(f"Alright! I'll remind you about **{self.what_to_remind}** in **{humanize_timedelta(seconds=round(self.timestamp - time.time()))}**.", ephemeral=True)
            self.reminded.append(interaction.user.id)
            return


LANGUAGE_CODES = [l for l in googletrans.LANGUAGES.keys()]

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    pass

class Utility(CustomRoleManagement, UtilitySlash, reminders, Highlight, Autoreaction, polls, Whois, L2LVC, nicknames, Suggestion, Teleport, commands.Cog, name='utility', metaclass=CompositeMetaClass):
    """
    Utility commands
    """
    def __init__(self, client):
        self.client = client
        self.nickconfig = {}
        self.translator = Translator()
        self.views_added = False
        self.last_seen = {}
        self.regex_pattern = re.compile('([^\s\w]|_)+')
        self.website_regex = re.compile("https?:\/\/[^\s]*")
        self.blacklist = []


    async def get_text_to_translate(self, ctx, userinput):
        try:
            msg = await commands.MessageConverter().convert(ctx=ctx, argument=userinput)
        except Exception as e:
            if isinstance(e, commands.ChannelNotReadable):
                raise ArgumentBaseError(message="I do not have permission to view the channel where the message is in.")
            else:
                if ctx.message.reference and isinstance(ctx.message.reference.resolved, discord.Message):
                    return ctx.message.reference.resolved.content
                else:
                    return userinput
        else:
            return msg.content


    @commands.cooldown(10, 1, commands.BucketType.user)
    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name="translate", aliases=['trans', 'tl'], invoke_without_command=True)
    async def translate_command(self, ctx, dest_language: typing.Optional[typing.Literal['af', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn', 'bs', 'bg', 'ca', 'ceb', 'ny', 'zh-cn', 'zh-tw', 'co', 'hr', 'cs', 'da', 'nl', 'en', 'eo', 'et', 'tl', 'fi', 'fr', 'fy', 'gl', 'ka', 'de', 'el', 'gu', 'ht', 'ha', 'haw', 'iw', 'he', 'hi', 'hmn', 'hu', 'is', 'ig', 'id', 'ga', 'it', 'ja', 'jw', 'kn', 'kk', 'km', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'lt', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'mi', 'mr', 'mn', 'my', 'ne', 'no', 'or', 'ps', 'fa', 'pl', 'pt', 'pa', 'ro', 'ru', 'sm', 'gd', 'sr', 'st', 'sn', 'sd', 'si', 'sk', 'sl', 'so', 'es', 'su', 'sw', 'sv', 'tg', 'ta', 'te', 'th', 'tr', 'uk', 'ur', 'ug', 'uz', 'vi', 'cy', 'xh', 'yi', 'yo', 'zu']] = 'en', *, text: str = None):
        """
        Translate text up to 1000 characters into a language of your choice, or English.
        By default, the text's language is auto-detected then translated into English.
        You can specify a language before the text to translate it into that language.

        Examples:
        `dv.translate 永远不会放弃你` will detect the text as Chinese and translate it into English.
        `dv.translate hi 永远不会放弃你` will detect the text as Chinese, then translate it into Hindi, returning the result.

        A list of languages available is shown in `dv.translate languages`.
        """
        async with ctx.typing():
            text = await self.get_text_to_translate(ctx, text)
            if text is not None:
                if dest_language:
                    if dest_language.lower() not in LANGUAGE_CODES:
                        dest_language = "en"
                    else:
                        dest_language = dest_language.lower()
                else:
                    dest_language = "en"
            else:
                return await ctx.send("Please specify text to translate.")
            if len(text) > 1000:
                    return await ctx.send("Please specify text to translate.")
            if len(text) > 1000:
                return await ctx.send("The text to translate can only be 1000 characters long.")
            embed = discord.Embed(title="Translate result", color=self.client.embed_color, timestamp=discord.utils.utcnow())
            embed.add_field(name=f"Original Text - Detecting Language...", value=f"```\n{text}\n```", inline=False)
            embed.add_field(name=f"Translated Text - Loading...", value=f"```\nTranslating\n```", inline=False)
            transmsg = await ctx.send(embed=embed)
            task = functools.partial(self.translator.translate, text=text, dest=dest_language)
            try:
                translated: googletrans.models.Translated = await self.client.loop.run_in_executor(None, task)
            except Exception as e:
                if isinstance(e, httpcore._exceptions.ConnectError):
                    embed.color = discord.Color.red()
                    embed.set_field_at(index=-2, name=f"Original Text", value=f"```\n{text}\n```", inline=False)
                    embed.set_field_at(index=-1, name=f"Translated Text", value=f"```\nThe API is unavailable at the moment.\n```", inline=False)
                    await transmsg.edit(embed=embed)
                    return
                else:
                    raise e
        embed.set_field_at(index=-2, name=f"Original Text - {googletrans.LANGUAGES.get(translated.src.lower(), 'Unknown Language').title()}", value=f"```\n{text}\n```", inline=False)
        embed.set_field_at(index=-1, name=f"Translated Text - {googletrans.LANGUAGES.get(translated.dest.lower(), 'Unknown Language').title()}", value=f"```\n{translated.text}\n```", inline=False)
        embed.set_footer(icon_url="https://upload.wikimedia.org/wikipedia/commons/d/db/Google_Translate_Icon.png", text="Powered by Google Translate")
        await transmsg.edit(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @translate_command.command(name="languages", aliases=["langs", "lang"])
    async def translate_languages(self, ctx):
        """
        List all languages available for translation.
        """
        embed = discord.Embed(title="Languages", description="To specify a language when using the `translate` command, type the two letter codes of the language, with the exception of Chinese (Simplified) and Chinese (Traditional), which you must use the full code (`zh-cn`/`zh-tw`).\nAn example is: If I wanted to get the Hindi version of 永远不会放弃你, I will run `dv.translate hi 永远不会放弃你`, as `hi` stands for the Hindi language shown below.", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_image(url="https://cdn.nogra.xyz/core/dvb_trans_languages.png")
        await ctx.send(embed=embed)


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
            embed.description = "<:DVB_greentick:955345438419087360> **Server's current prefix is :** `{}`".format(current_prefix)
            return await ctx.send(embed=embed)
        if "@everyone" in prefix or "@here" in prefix:
            return await ctx.send("You can't do that.")
        try:
            await self.client.set_prefix(ctx.guild, prefix)
            embed = discord.Embed(color=self.client.embed_color)
            embed.description = "<:DVB_greentick:955345438419087360> **Server's prefix changed to `{}`**".format(prefix)
            await ctx.send(embed=embed)
        except Exception:
            return await ctx.send_error()

    @commands.command(name='info')
    async def info(self, ctx):
        """
        Shows some information about this bot.
        """
        value_1 = []
        value_1.append(f'<:DVB_commands:913426937869926440> {len(self.client.commands)}')
        value_1.append(f'<:DVB_users:913426937362391111> {len(self.client.users)}')
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
        value_1.append(f"<:DVB_text_channel:955345569319104573> {text}")
        value_1.append(f'<:DVB_voice_channel:955345567263911947> {voice}')
        if stage != 0:
            value_1.append(f'<:DVB_stage_channel:955345570900344863> {stage}')
        py_version = "{}.{}.{}".format(*sys.version_info[:3])
        dpy_version = discord.__version__
        embed = discord.Embed(description=f"{ctx.guild.me.name} is a multipurpose bot designed to help members and enhance the Dank Vibes experience with a helpful set of fun and utility commands. \n\n{ctx.guild.me.name} is created by {str(self.client.get_user(321892489470410763))} with the Pycord library, and developed by {str(self.client.get_user(321892489470410763))} and {str(self.client.get_user(650647680837484556))}.", color=self.client.embed_color)
        embed.add_field(name='Stats', value="\n".join(value_1), inline=True)
        embed.add_field(name='Versions', value=f"<:DVB_python:955345550193078272> `{py_version}`\n<:DVB_PyCord:937351289514385428> `{dpy_version}`", inline=True)
        embed.add_field(name='Developers', value=f"{str(self.client.get_user(650647680837484556))}", inline=True)
        embed.add_field(name="Special Thanks To", value=f"{str(await self.client.fetch_user(727498137232736306))}\n{self.client.get_user(321892489470410763)}\n{self.client.get_user(560251854399733760)}\n{self.client.get_user(886598864965103727)} <3", inline=True)
        embed.add_field(name="Important Links", value="[Documentation](https://docs.dvbot.nogra.xyz)\n[Status Page](http://status.dvbot.nogra.xyz/)\n[Terms of Service](https://docs.dvbot.nogra.xyz/legal/terms/)\n[Privacy Policy](https://docs.dvbot.nogra.xyz/legal/privacy/)", inline=False)
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
        embed.set_author(name=f"About {ctx.guild.me.name}", icon_url=ctx.guild.me.display_avatar.url)
        embed.set_thumbnail(url=ctx.guild.me.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="checkpvc", aliases = ["privchannel", "pvc"])
    async def checkoverwrites(self, ctx, channel:discord.TextChannel = None):
        """
        Checks the permission overwrites for that channel. Can be used to check who is in a private channel.
        """
        if channel is None:
            channel = ctx.channel
        modrole = ctx.guild.get_role(608495204399448066)
        if modrole not in ctx.author.roles:
            channel = ctx.channel
        channel_details = await self.client.db.fetchrow("SELECT * FROM channels WHERE channel_id = $1", channel.id)
        owner = self.client.get_user(channel_details.get('owner_id'))
        owner_str = f"**{owner}** {owner.mention}"
        if owner not in channel.overwrites and not (owner.permissions_for(channel).send_messages and owner.permissions_for(channel).view_channel):
            owner_str += "\n⚠️ Not in channel"
        members = [overwriteobject for overwriteobject in channel.overwrites if isinstance(overwriteobject, discord.Member) and not overwriteobject.bot] # gets all members who have some sort of overwrite in that channel
        membersin = []
        for member in members:
            if member.id != owner.id:
                permissions = channel.permissions_for(member)
                if permissions.view_channel == True:
                    membersin.append(f"**{member}** {member.mention}")
        membermsg = "".join(f"`{count}.` {i}\n" for count, i in enumerate(membersin, start=1))
        embed = discord.Embed(title=f"Private Channel Details of #{channel.name}", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.add_field(name="Owner 🧑‍⚖️", value=owner or "Unknown", inline=True)
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
        user = await self.client.db.fetchrow("SELECT * FROM messagelog WHERE user_id = $1", member.id)
        if user is None:
            return await ctx.send("Hmm... it appears that you have not sent a message in <#608498967474601995>. Contact a mod if you think this is wrong.")
        all = await self.client.db.fetch("SELECT user_id FROM messagelog ORDER BY messagecount DESC")
        user2 = await self.client.db.fetchrow("SELECT user_id FROM messagelog WHERE user_id = $1", member.id)
        position = ordinal(all.index(user2)+1)
        embed = discord.Embed(title="Your number of messages sent in #general-chat", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=member, icon_url=member.display_avatar.url)
        embed.add_field(name="Message count", value=user.get('messagecount'), inline=True)
        embed.add_field(name="Position", value=f"{position} {'🏆' if all.index(user2) < 10 else ''}", inline=True)
        try:
            await ctx.reply(embed=embed)
        except:
            await ctx.send(embed=embed)

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
        db_cds = await self.client.db.fetch("SELECT * FROM cooldowns WHERE member_id = $1", ctx.author.id)
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

    @commands.command(name="invite", hidden=True)
    async def _invite(self, ctx):
        if ctx.author.id != 650647680837484556:
            invite_link = discord.utils.oauth_url(self.client.user.id, scopes=['bot'])
            await ctx.send(f"<{invite_link}>")
        else:
            embed = discord.Embed(title=f"Invite {self.client.user.name}!", description="[Click here to invite me to your server!](https://www.youtube.com/watch?v=9cjS9z0ZKUo)", color=self.client.embed_color)
            await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='timer')
    async def timer(self, ctx, channel: typing.Optional[discord.TextChannel] = None, duration: BetterTimeConverter = None, *, title:str = None):
        """
        Start a timer to be shown in a message! You can include a title for the timer, and a channel for the timer to be sent to.
        """
        if channel is None:
            channel = ctx.channel
        if title is not None and len(title) > 50:
            return await ctx.send("The timer's title cannot be longer than 50 characters.")
        if duration is None:
            return await ctx.send("You must specify a time.")
        await ctx.message.delete()
        titleembed = f"Timer" if title is None else f"{title} Timer"
        endtime = round(time.time()) + duration
        embed = discord.Embed(title=humanize_timedelta(seconds=duration), color=self.client.embed_color, timestamp=datetime.fromtimestamp(endtime))
        embed.set_author(name=f"{ctx.author.name}'s {titleembed}", icon_url=ctx.guild.icon.url)
        embed.set_footer(text="Ends at")
        msg = await channel.send(embed=embed, view=TimerRemindMe(endtime, f"{title} in {channel.mention}"))
        await self.client.db.execute("INSERT INTO timers(guild_id, channel_id, message_id, user_id, time, title) VALUES ($1, $2, $3, $4, $5, $6)", ctx.guild.id, channel.id, msg.id, ctx.author.id, endtime, title)

    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name='avatar', aliases=['av', 'pfp', 'banner', 'bn', 'sav'])
    async def avatar(self, ctx, user: typing.Optional[discord.Member] = None):
        """
        Shows you or a user's avatar, banner or server banner.
        """
        if user is None:
            user = ctx.author
        # Getting avatar URL
        avatar = user.avatar
        if avatar is None:
            avatar = self.client.get_user(user.id).display_avatar
        avatar_url = avatar.with_size(1024).url
        # Getting Server Avatar URL
        d_avatar = user.display_avatar
        if d_avatar == avatar:
            d_avatar_url = None
        else:
            d_avatar_url = d_avatar.with_size(1024).url
        # Getting banner URL
        api_fetched_user = await self.client.fetch_user(user.id)
        banner = api_fetched_user.banner
        if banner is None:
            banner_url = None
        else:
            banner_url = banner.with_size(1024).url
        if ctx.invoked_with in ['av', 'pfp', 'avatar']:
            init_picked = 'av'
        elif ctx.invoked_with in ['banner', 'bn']:
            if banner_url is None:
                init_picked = 'av'
            else:
                init_picked = 'bn'
        elif ctx.invoked_with in ['sav']:
            if d_avatar_url is None:
                init_picked = 'av'
            else:
                init_picked = 'sav'
        else:
            return
        def generate_embed(user, name, url):
            embed = discord.Embed(title=f"{user}'s {name}", color=self.client.embed_color)
            embed.set_image(url=url)
            return embed
        class AvatarView(discord.ui.View):
            def __init__(self, ctx, user, avatar_url, d_avatar_url, banner_url, init_picked):
                self.ctx: DVVTcontext = ctx
                self.user = user
                self.avatar_url = avatar_url
                self.d_avatar_url = d_avatar_url
                self.banner_url = banner_url
                self.init_picked = init_picked
                self.response = None
                super().__init__(timeout=None)

                async def update_message(label, button, interaction):
                    if label == 'Avatar':
                        new_embed = generate_embed(self.user, label, self.avatar_url)
                    elif label == 'Server Avatar':
                        new_embed = generate_embed(self.user, label, self.d_avatar_url)
                    elif label == 'Banner':
                        new_embed = generate_embed(self.user, label, self.banner_url)
                    else:
                        return
                    for b in self.children:
                        if b.style == discord.ButtonStyle.green:
                            b.style = discord.ButtonStyle.grey
                        if b == button:
                            b.style = discord.ButtonStyle.green
                    await interaction.response.edit_message(embed=new_embed, view=self)



                class SelectButton(discord.ui.Button):
                    async def callback(self, interaction: discord.Interaction):
                        if self.style == discord.ButtonStyle.green:
                            return
                        else:
                            await update_message(self.label, self, interaction)

                self.add_item(SelectButton(label='Avatar', style=discord.ButtonStyle.green if init_picked == 'av' else discord.ButtonStyle.grey))
                self.add_item(SelectButton(label='Server Avatar', style=discord.ButtonStyle.green if init_picked == 'sav' else discord.ButtonStyle.grey, disabled=True if d_avatar_url is None else False))
                self.add_item(SelectButton(label='Banner', style=discord.ButtonStyle.green if init_picked == 'bn' else discord.ButtonStyle.grey, disabled=True if banner_url is None else False))

            async def on_timeout(self):
                for b in self.children:
                    b.disabled = True
                await self.response.edit(view=self)

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("stop touching this you twat", ephemeral=True)
                    return False
                else:
                    return True

        if init_picked == 'av':
            embed = generate_embed(user, 'Avatar', avatar_url)
        elif init_picked == 'bn':
            embed = generate_embed(user, 'Banner', banner_url)
        elif init_picked == 'sav':
            embed = generate_embed(user, 'Server Avatar', d_avatar_url)
        else:
            return
        avatarview = AvatarView(ctx, user, avatar_url, d_avatar_url, banner_url, init_picked)
        avatarview.response = await ctx.send(embed=embed, view=avatarview)
        await avatarview.wait()

    @commands.command(name="changelog")
    async def changelog(self, ctx):
        """
        Shows the changelog.
        """
        changelogs = await self.client.db.fetch("SELECT version_str, changelog FROM changelog ORDER BY version_number DESC")
        pages = []
        for changelog in changelogs:
            embed = discord.Embed(color=self.client.embed_color, title=f"{changelog.get('version_str')}").set_author(name=f"{self.client.user.name} Changelog", icon_url=self.client.user.avatar.url)
            is_continued = False
            changelog_text = changelog.get('changelog')
            if len(changelog_text) > 3000:
                changelog_split = changelog_text.split('\n')
                existing_text = ''
                while len(changelog_split) > 0:
                    if len(existing_text + changelog_split[0] + '\n') > 3000:
                        embed.title += "(Continued)" if is_continued else ""
                        embed.description = existing_text + "\n*Continued...* ➡️"
                        pages.append(embed)
                        embed = discord.Embed(color=self.client.embed_color, title=f"{changelog.get('version_str')}").set_author(name=f"{self.client.user.name} Changelog", icon_url=self.client.user.avatar.url)
                        existing_text = changelog_split[0]
                        is_continued = True
                        del changelog_split[0]
                    else:
                        existing_text += changelog_split[0] + '\n'
                        del changelog_split[0]
                embed.title += "(Continued)" if is_continued else ""
                embed.description = existing_text
                pages.append(embed)
            else:
                embed.description = changelog_text
                pages.append(embed)
        paginator = SingleMenuPaginator(pages=pages)
        await paginator.send(ctx)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="contestleaderboard", aliases=['clb', 'contestlb'])
    async def contest_leaderboard(self, ctx: DVVTcontext, contest_id: int):
        """
        See all the leaderboard and check out all the entries of a previous contest.
        Cannot be used for ongoing contests.
        """
        if (contest := await self.client.db.fetchrow("SELECT * FROM contests WHERE contest_id = $1 AND guild_id = $2", contest_id, ctx.guild.id)) is None:
            return await ctx.send(f"A contest with the ID `{contest_id}` doesn't exist in your server.")
        contest = Contest(contest)
        if contest.active is True or contest.voting is True:
            return await ctx.send(f"**Contest #{contest_id} is still active!**\nWait until the contest is over before checking its leaderboard.")
        submissions = await self.client.db.fetch("SELECT * FROM contest_submissions WHERE contest_id = $1", contest_id)
        votes = await self.client.db.fetch("SELECT * FROM contest_votes WHERE contest_id = $1", contest_id)
        votes = Counter(vote.get('entry_id') for vote in votes)
        votes = dict(votes)
        for submission in submissions:
            if submission.get('entry_id') not in votes:
                votes[submission.get('entry_id')] = 0
        emojis = {
            0: "🏆",
            1: "🥈",
            2: "🥉",
        }

        def get_submission(entryid) -> typing.Union[None, ContestSubmission]:
            for submission_record in submissions:
                if submission_record.get('entry_id') == entryid:
                    return ContestSubmission(submission_record)
            return None

        index = 0
        pag_pages = []

        for entry_id, number_of_votes in dict(votes).items():

            submission = get_submission(entry_id)
            if submission is not None:
                user = self.client.get_user(submission.submitter_id)
                if user is None:
                    user_proper = str(submission.submitter_id)
                    user_id = str(submission.submitter_id)
                    user_avatar = discord.Embed.Empty
                else:
                    user_proper = f"{user.name}#{user.discriminator}"
                    user_id = f"{user.id}"
                    user_avatar = user.display_avatar.with_size(128).url
                emoji = emojis.get(index, "🏅") if index < 5 else ""
                place = f"{ordinal(index + 1)} Place"
                if index < 5:
                    place_str = f"{emoji} {place} {emoji}"
                else:
                    place_str = ""
                leaderboardembed = discord.Embed(title=place_str, color=self.client.embed_color)
                leaderboardembed.add_field(name="Votes", value=str(number_of_votes), inline=True)
                leaderboardembed.add_field(name="Link", value=f"[Link to submission](https://discord.com/channels/{ctx.guild.id}/{contest.contest_channel_id}/{submission.msg_id})", inline=True)
                leaderboardembed.set_author(name=user_proper, icon_url=user_avatar)
                leaderboardembed.set_image(url=submission.media_link)
                leaderboardembed.set_footer(text=f"Submitter ID: {user_id}")
                pag_pages.append(leaderboardembed)
                index += 1
            else:
                pass
        paginator = SingleMenuPaginator(pag_pages, author_check=True)
        await paginator.send(ctx)