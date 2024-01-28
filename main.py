import asyncio
import os
import time
from typing import Optional, Union, Tuple

import amari.exceptions
from amari import api, objects
import discord
import asyncpg
import datetime
from dotenv import load_dotenv
from discord import client
from discord.ext import commands, tasks
from utils.context import DVVTcontext
from utils.format import print_exception, proper_userf
from utils.specialobjects import MISSING, ServerConfiguration, AwaitingAmariData, NoAmariData, UserInfo
from utils.errors import AmariUserNotFound, AmariDataNotFound, AmariError, AmariDeveloperError
from utils.botlogger import BotLogger


class EditContent:
    __slots__ = ('content', 'embed', 'embeds')

    def __init__(self, content, embed, embeds):
        self.content: str = content
        self.embed: discord.Embed = embed
        self.embeds: list = embeds

    def __repr__(self) -> str:
        return f"<EditContent content={self.content} embed={self.embed} embeds={self.embeds}>"

strfformat = "%d-%m-%y %H:%M:%S"


AVAILABLE_EXTENSIONS = [
    'cogs.dev',
    'cogs.errors',
    'cogs.admin',
    'cogs.help',
    'cogs.mod',
    'cogs.utility',
    'cogs.events',
    'cogs.slashtags',
    'cogs.banappeal',
]

load_dotenv('credentials.env')
token = os.getenv('TOKEN')
host = os.getenv('HOST')
database = os.getenv('DATABASE')
user = os.getenv('dbUSER')
port = int(os.getenv('dbPORT'))
password = os.getenv('dbPASSWORD')
amari_key = os.getenv('AMARI_KEY')


intents = discord.Intents(guilds=True, members=True, presences=True, messages=True, reactions=True, emojis=True, invites=True, voice_states=True, message_content=True, typing=True, moderation=True)
allowed_mentions = discord.AllowedMentions(everyone=False, roles=False)


class dvvt(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix = self.get_prefix, intents=intents, allowed_mentions=allowed_mentions, case_insensitive=True)
        self.custom_status = False
        self.AmariClient = api.AmariClient(amari_key)
        self.AmariLastUpdate = None
        self.prefixes = {}
        self.uptime = None
        self.embed_color: int = 0x57F0F0
        self.db: asyncpg.pool = None
        self.serverconfig = {}
        self.maintenance = {}
        self.maintenance_message = {}
        self.available_extensions = AVAILABLE_EXTENSIONS
        self.blacklist = {}
        self.editqueue = []
        self.deleted_edit_messages = []
        self.webhooks = {}
        self.amari_data = {}
        self.mafia_channels = {}
        self.mafia_game_details = {}
        self.clownmode = {}
        self.clownprofiles = {}
        self.clown_duration = 180
        self.logger = BotLogger(self)
        self.logstrf = strfformat
        for ext in self.available_extensions:
            self.load_extension(ext, store=False)
            print(f"{datetime.datetime.utcnow().strftime(strfformat)} | Loaded {ext}")

    async def fetch_amari_data(self, user_id: int, guild_id: int) -> Tuple[Union[None, api.User, AwaitingAmariData, NoAmariData], int, Exception]:
        guild_data = self.amari_data.get(guild_id, None)
        if guild_data is None:
            self.amari_data[guild_id] = {
                'leaderboard': AwaitingAmariData,
                'weekly_leaderboard': AwaitingAmariData,
                'last_update': round(time.time()),
                'error': None
            }
            guild_data = self.amari_data.get(guild_id)

        data_last_updated = guild_data.get('last_update', 0)
        leaderboard: Union[objects.Leaderboard, None] = guild_data.get('leaderboard', None)
        weekly_leaderboard = guild_data.get('weekly_leaderboard', None)
        error = guild_data.get('error', None)
        if type(leaderboard) == objects.Leaderboard:
            leaderboard: Union[objects.User, None] = leaderboard.get_user(user_id)
            if type(weekly_leaderboard) == objects.Leaderboard:
                weekly_leaderboard = weekly_leaderboard.get_user(user_id)
                if weekly_leaderboard is None:
                    weeklyexp = 0
                else:
                    weeklyexp = weekly_leaderboard.exp
                if leaderboard is not None:
                    leaderboard.weeklyexp = weeklyexp
        return (leaderboard, data_last_updated, error)





    @tasks.loop(seconds=0.1)
    async def edit_message(self):
        await self.wait_until_ready()
        # For some reason I am unable to edit the message if the embed is enclosed in another object, for now this function will be used for embeds only
        if len(self.editqueue) > 0:
            #print(self.editqueue)
            tup = self.editqueue.pop(0)
            m: Union[discord.PartialMessage, discord.Message] = tup[0]
            content: str = tup[1]
            embed: discord.Embed = tup[2]
            view: discord.ui.View = tup[3]
            #print(editable)
            if m.id in self.deleted_edit_messages:
                return None
            try:
                if content != 0:
                    if embed != 0:
                        if view != 0:
                            await m.edit(content=content, embed=embed, view=view)
                        else:
                            await m.edit(content=content, embed=embed)
                    else:
                        if view != 0:
                            await m.edit(content=content, view=view)
                        else:
                            await m.edit(content=content)
                else:
                    if embed != 0:
                        if view != 0:
                            await m.edit(embed=embed, view=view)
                        else:
                            await m.edit(embed=embed)
                    else:
                        if view != 0:
                            await m.edit(view=view)
            except discord.NotFound:
                self.deleted_edit_messages.append(m.id)
            except Exception as e:
                print(e)
            await asyncio.sleep(0.5)
        else:
            pass
            # nothing in queue

    async def get_webhook(self, channel: discord.TextChannel):
        if channel.id in self.webhooks:
            return self.webhooks[channel.id]
        else:
            webhooks = await channel.webhooks()
            webhook = discord.utils.get(webhooks, name=self.user.name)
            if webhook is None:
                webhook = await channel.create_webhook(name=self.user.name)
            self.webhooks[channel.id] = webhook
            return webhook


    @tasks.loop(seconds=5)
    async def update_blacklist(self):
        await self.wait_until_ready()
        blacklist_dict = dict(self.blacklist) # copy the dict so that we can iterate over it and not result in runtime error due to dictionary edits
        for user in blacklist_dict:
            if time.time() >= self.blacklist[user]:
                blacklist = await self.db.fetchrow(
                    "SELECT * FROM blacklist WHERE user_id=$1 AND time_until = $2 AND blacklist_active = $3", user, self.blacklist[user], True)
                await self.db.execute(
                    "UPDATE blacklist SET blacklist_active = $1 WHERE user_id = $2 and incident_id = $3", False, user, blacklist.get('incident_id'))
                embed = discord.Embed(title=f"Bot Unblacklist | Case {blacklist.get('incident_id')}", description=f"**Reason**: Blacklist over, automatically rescinded\n**Responsible Moderator**: {self.user.name} ({self.user.id})", color=discord.Color.green())
                user = await self.fetch_user(user)
                embed.set_author(name=f"{proper_userf(user)} ({user.id})", icon_url=user.display_avatar.url)
                if user is not None:
                    try:
                        await user.send("You are no longer blacklisted from using the bot, and can use all functions of the bot.")
                    except discord.HTTPException:
                        pass
                del self.blacklist[user.id]
                await self.get_channel(906433823594668052).send(embed=embed)
        await self.get_all_blacklisted_users()

    def add_to_edit_queue(self, message: Union[discord.PartialMessage, discord.Message] = 0, content: str = 0, embed: discord.Embed = 0, view: discord.ui.View = 0, index: Optional[int] = None):
        tup = (message, content, embed, view)
        if index is None:
            self.editqueue.append(tup)
        else:
            self.editqueue.insert(index, tup)

    def remove_queued_edit(self, message_id: int):
        parsed_fully = False
        while parsed_fully is not True:
            for i, tup in enumerate(self.editqueue):
                if tup[0].id == message_id:
                    del self.editqueue[i]
                    break
                else:
                    continue
            parsed_fully = True
        return



    @update_blacklist.before_loop
    async def before_update_blacklist(self):
        await self.wait_until_ready()

    async def get_context(self, message, *, cls=None):
        context = await super().get_context(message, cls=DVVTcontext)
        return context

    async def load_maintenance_data(self):
        results = await self.db.fetch("SELECT * FROM maintenance")
        for result in results:
            self.maintenance.setdefault(result.get('cog_name'), result.get('enabled'))
            self.maintenance_message.setdefault(result.get('cog_name'), result.get('message'))

    async def process_commands(self, message: discord.Message):
        ctx: DVVTcontext = await self.get_context(message)
        if ctx.cog:
            if ctx.author.id in self.blacklist:
                if ctx.author.id not in [650647680837484556, 515725341910892555, 321892489470410763]:
                    if time.time() >= self.blacklist[ctx.author.id]:
                        blacklist = await self.db.fetchrow("SELECT * FROM blacklist WHERE user_id=$1 AND time_until = $2 AND blacklist_active = $3", ctx.author.id, self.blacklist[ctx.author.id], True)
                        await self.db.execute("UPDATE blacklist SET blacklist_active = $1 WHERE user_id = $2 and incident_id = $3", False, message.author.id, blacklist.get('incident_id'))
                        embed = discord.Embed(title=f"Bot Unblacklist | Case {blacklist.get('incident_id')}", description=f"**Reason**: Blacklist over, automatically rescinded\n**Responsible Moderator**: {ctx.me} ({ctx.me.id})", color=discord.Color.green())
                        embed.set_author(name=f"{message.author} ({message.author.id})", icon_url=message.author.display_avatar.url)
                        await self.get_channel(906433823594668052).send(embed=embed)
                        await message.reply("You are no longer blacklisted from using the bot, and can use all functions of the bot.")
                    return
            if self.maintenance.get(ctx.cog.qualified_name) and message.author.id not in [321892489470410763, 650647680837484556]:
                maintenance_message = self.maintenance_message.get(ctx.cog.qualified_name)
                return await message.channel.send(maintenance_message)
        await self.invoke(ctx)

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    async def after_ready(self):
        await self.wait_until_ready()

    async def on_ready(self):
        for guild in self.guilds:
            guild_settings = await client.fetch_guild_settings(guild.id)
            self.serverconfig[guild.id] = guild_settings
        print(f"{datetime.datetime.utcnow().strftime(strfformat)} | Loaded all Server Configurations")
        all_tables = ['prefixes', 'dankreminders', 'stats', 'nicknames', 'channelconfigs', 'dmrequestslog',
                      'dumbfightlog', 'joinmessages', 'dmrequests', 'messagelog', 'lockdownmsgs',
                      'remindersettings', 'inventories', 'iteminfo', 'tempweekly', 'rules', 'serverconfig',
                      'owocurrent', 'owopast', 'temp', 'stickymessages', 'maintenance', 'teleport',
                      'suggestion_response', 'suggestions', 'lockdownprofiles', 'grinderdata', 'messagemilestones',
                      'viprolemessages', 'karutaeventconfig', 'autoreactions', 'owocount', 'milestones', 'votereminder',
                      'voters', 'cooldowns', 'selfrolemessages', 'devmode', 'blacklisted_words',
                      'blacklist', 'freezenick', 'autorole', 'giveaways', 'giveawayentrants', 'dankdrops', 'autorole',
                      'donation_categories', 'christmaseventconfig', 'commandaccess', 'ignoredchristmascat',
                      'ignoredchristmaschan', 'perkremoval', 'commandlog', 'timedunlock', 'nickname_changes',
                      'name_changes', 'timers', 'infections', 'polls', 'pollvotes', 'highlight', 'highlight_ignores',
                      'reminders', 'userconfig', 'modlog', 'watchlist', 'usercleanup', 'giveawayconfig', 'contests',
                      'contest_submissions', 'contest_votes', 'customroles']
        print(f"{datetime.datetime.utcnow().strftime(strfformat)} | Checking for missing databases")
        tables = await self.db.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
        tables = [i.get('table_name') for i in tables]
        if tables is None:
            pass
        else:
            missing_tables = []
            for table in all_tables:
                if table not in tables:
                    missing_tables.append(table)
            if len(missing_tables) == 0:
                pass
            else:
                print(missing_tables)
                print(f"Some databases do not exist, creating them now...")
                await self.db.execute("""CREATE TABLE IF NOT EXISTS autoreactions(guild_id bigint, trigger text, response text);
CREATE TABLE IF NOT EXISTS autorole(member_id bigint, guild_id bigint, role_id bigint, time bigint);
CREATE TABLE IF NOT EXISTS blacklist(incident_id serial, user_id bigint, moderator_id bigint, blacklist_active boolean, time_until bigint, reason text);
CREATE TABLE IF NOT EXISTS blacklisted_words(string text);
CREATE TABLE IF NOT EXISTS channelconfigs(guild_id bigint NOT null PRIMARY KEY, nickname_channel_id bigint, dmchannel_id bigint);
CREATE TABLE IF NOT EXISTS christmaseventconfig(guild_id bigint, percentage real);
CREATE TABLE IF NOT EXISTS commandaccess(member_id bigint, command text, until bigint);
CREATE TABLE IF NOT EXISTS cooldowns(command_name text, member_id bigint, time bigint);
CREATE TABLE IF NOT EXISTS dankdrops(guild_id bigint, name text, price text, time bigint);
CREATE TABLE IF NOT EXISTS dankreminders(member_id bigint, remindertype bigint, channel_id bigint, guild_id bigint, time bigint);
CREATE TABLE IF NOT EXISTS devmode(user_id bigint, devmode boolean);
CREATE TABLE IF NOT EXISTS donation_categories(guild_id bigint, category_name text);
CREATE TABLE IF NOT EXISTS dmrequests(id serial, member_id bigint, target_id bigint, dmcontent text, messageid bigint);
CREATE TABLE IF NOT EXISTS dmrequestslog(id bigint, member_id bigint, target_id bigint, approver_id bigint, dmcontent text, status integer);
CREATE TABLE IF NOT EXISTS dumbfightlog(invoker_id bigint, target_id bigint, did_win integer);
CREATE TABLE IF NOT EXISTS freezenick(id serial, user_id bigint, guild_id bigint, nickname text, old_nickname text, time bigint, reason text, responsible_moderator bigint);
CREATE TABLE IF NOT EXISTS grinderdata(user_id bigint PRIMARY KEY, today bigint, past_week bigint, last_week bigint, past_month bigint, all_time bigint, last_dono_time bigint, last_dono_msg text, advance_amt bigint); 
CREATE TABLE IF NOT EXISTS giveaways(guild_id bigint, channel_id bigint, message_id bigint, time bigint, name text, host_id bigint, winners integer);
CREATE TABLE IF NOT EXISTS giveawayentrants(message_id bigint, user_id bigint);
CREATE TABLE IF NOT EXISTS ignoredchristmascat(guild_id bigint, category_id bigint PRIMARY KEY);
CREATE TABLE IF NOT EXISTS ignoredchristmaschan(guild_id bigint, channel_id bigint PRIMARY KEY);
CREATE TABLE IF NOT EXISTS inventories(user_id bigint PRIMARY KEY, skull bigint, argonphallicobject bigint, llamaspit bigint, slicefrenzylesliecake bigint, wickedrusteze bigint);
CREATE TABLE IF NOT EXISTS iteminfo(name text PRIMARY KEY, fullname text, description text, emoji text, image text, hidden boolean);
CREATE TABLE IF NOT EXISTS joinmessages(guild_id bigint PRIMARY KEY, channel_id bigint, plain_text text, embed_details text, delete_after integer);
CREATE TABLE IF NOT EXISTS karutaeventconfig(channel_id text, percentage_chance real);
CREATE TABLE IF NOT EXISTS lockdownmsgs(guild_id bigint, profile_name text, startmsg text, endmsg text);
CREATE TABLE IF NOT EXISTS lockdownprofiles(guild_id bigint, profile_name text, channel_id bigint);
CREATE TABLE IF NOT EXISTS maintenance(cog_name text PRIMARY KEY, message text, enabled boolean);
CREATE TABLE IF NOT EXISTS messagelog(user_id bigint PRIMARY KEY, messagecount bigint);
CREATE TABLE IF NOT EXISTS messagemilestones(messagecount integer, roleid bigint);
CREATE TABLE IF NOT EXISTS milestones(votecount integer, roleid bigint);
CREATE TABLE IF NOT EXISTS nicknames(id serial, member_id bigint PRIMARY KEY, nickname text, messageid bigint);
CREATE TABLE IF NOT EXISTS owocount(member_id bigint PRIMARY KEY, daily_count integer, weekly_count integer, total_count integer, yesterday integer, last_week integer);
CREATE TABLE IF NOT EXISTS owocurrent(member_id bigint PRIMARY KEY, daily_count integer, weekly_count integer, total_count integer);
CREATE TABLE IF NOT EXISTS owopast(member_id bigint PRIMARY KEY, yesterday integer, last_week integer);
CREATE TABLE IF NOT EXISTS perkremoval(member_id bigint, perk text, until bigint);
CREATE TABLE IF NOT EXISTS prefixes(guild_id bigint PRIMARY KEY, prefix text);
CREATE TABLE IF NOT EXISTS remindersettings(member_id bigint PRIMARY KEY, method integer, daily bigint, lottery bigint, work bigint, lifesaver bigint, apple integer, redeem integer, weekly integer, monthly integer, hunt integer, fish integer, dig integer, highlow integer, snakeeyes integer, search integer, crime integer, beg integer, dailybox integer, horseshoe integer, pizza integer, drop integer);
CREATE TABLE IF NOT EXISTS rules(guild_id bigint, command text, role_id bigint, whitelist boolean);
CREATE TABLE IF NOT EXISTS selfrolemessages(guild_id bigint, age bigint, gender bigint, location bigint, minigames bigint, event_pings bigint, dank_pings bigint, server_pings bigint, bot_roles bigint, random_color bigint, colors bigint, specialcolors bigint, boostping bigint, vipheist bigint);
CREATE TABLE IF NOT EXISTS serverconfig(guild_id bigint PRIMARY KEY NOT NULL, owodailylb bool NOT NULL DEFAULT FALSE, verification bool NOT NULL DEFAULT TRUE, censor bool NOT NULL DEFAULT FALSE, owoweeklylb bool NOT NULL DEFAULT TRUE, votelb bool NOT NULL DEFAULT TRUE, timeoutlog bool NOT NULL DEFAULT FALSE, statusrole bool NOT NULL DEFAULT FALSE, statusroleid bigint NOT NULL DEFAULT 0, statustext text NOT NULL DEFAULT 'lorem ipsum');
CREATE TABLE IF NOT EXISTS stats(member_id bigint, remindertype integer, time bigint);
CREATE TABLE IF NOT EXISTS stickmessages(guild_id bigint PRIMARY KEY, channel_id bigint, message_id bigint, type integer, message text);
CREATE TABLE IF NOT EXISTS suggestion_response(suggestion_id integer, user_id bigint, response_id bigint, message_id bigint, message text);
CREATE TABLE IF NOT EXISTS suggestions(suggestion_id serial, user_id bigint, finish boolean, response_id bigint, suggestion text);
CREATE TABLE IF NOT EXISTS teleport(member_id bigint, checkpoint text, channel_id bigint);
CREATE TABLE IF NOT EXISTS temp(member_id bigint PRIMARY KEY, daily_count integer, weekly_count integer, total_count integer, yesterday integer, last_week integer);
CREATE TABLE IF NOT EXISTS tempweekly(member_id bigint PRIMARY KEY, yesterday integer, last_week integer);
CREATE TABLE IF NOT EXISTS timedrole(member_id bigint, guild_id bigint, role_id bigint, time bigint);
CREATE TABLE IF NOT EXISTS viprolemessages(guild_id bigint, colors bigint, vipcolors bigint, boostgaw bigint, vipheistping bigint);
CREATE TABLE IF NOT EXISTS votecount(member_id bigint PRIMARY KEY, count integer);
CREATE TABLE IF NOT EXISTS commandlog(guild_id bigint, channel_id bigint, user_id bigint, command text, message text, time bigint);
CREATE TABLE IF NOT EXISTS timedunlock(guild_id bigint, channel_id bigint, time bigint, responsible_moderator bigint);
CREATE TABLE IF NOT EXISTS nickname_changes(guild_id bigint, member_id bigint, nickname text, time bigint);
CREATE TABLE IF NOT EXISTS name_changes(user_id bigint, name text, time bigint);
CREATE TABLE IF NOT EXISTS timers(guild_id bigint, channel_id bigint, message_id bigint, user_id bigint, time bigint, title text);
CREATE TABLE IF NOT EXISTS infections(infectioncase serial, member_id bigint PRIMARY KEY, guild_id bigint, channel_id bigint, message_id bigint, timeinfected bigint);
CREATE TABLE IF NOT EXISTS polls(poll_id serial, guild_id bigint, channel_id bigint, invoked_message_id bigint, message_id bigint, creator_id bigint, poll_name text, choices text, created bigint);
CREATE TABLE IF NOT EXISTS pollvotes(poll_id integer, user_id bigint, choice text);
CREATE TABLE IF NOT EXISTS highlight (guild_id bigint, user_id bigint, highlights text);
CREATE TABLE IF NOT EXISTS highlight_ignores (guild_id bigint, user_id bigint, ignore_type text, ignore_id bigint);
CREATE TABLE IF NOT EXISTS reminders(id serial, user_id bigint, guild_id bigint, channel_id bigint, message_id bigint, name text, time bigint, created_time bigint);
CREATE TABLE IF NOT EXISTS userconfig(user_id bigint PRIMARY KEY, votereminder bigint, dumbfight_result bool, dumbfight_rig_duration bigint, virus_immune bigint, received_daily_potion bool);
CREATE TABLE IF NOT EXISTS modlog(case_id serial, guild_id bigint not null, moderator_id bigint not null, offender_id bigint not null, action text not null, reason text, start_time bigint, duration bigint, end_time bigint);
CREATE TABLE IF NOT EXISTS changelog(version_number serial, version_str text, changelog text);
CREATE TABLE IF NOT EXISTS watchlist(guild_id bigint, user_id bigint, target_id bigint, remarks text);
CREATE TABLE IF NOT EXISTS usercleanup(guild_id bigint, target_id bigint, channel_id bigint, message text);
CREATE TABLE IF NOT EXISTS giveawayconfig(guild_id bigint not null, channel_id bigint not null constraint giveawayconfig_pkey primary key, bypass_roles text, blacklisted_roles text, multi jsonb);
CREATE TABLE IF NOT EXISTS dankitems(name bigint, IDcode text PRIMARY KEY, image_url text, type text, trade_value int, last_updated bigint default 0, overwrite bool default false);
CREATE TABLE IF NOT EXISTS contests(contest_id serial, guild_id bigint not null, contest_starter_id bigint not null, contest_channel_id bigint not null, name text, created bigint, active bool default true, voting bool default false);
CREATE TABLE IF NOT EXISTS contest_submissions(contest_id int not null, entry_id int, submitter_id bigint not null, media_link text not null, second_media_link text, approve_id bigint, msg_id bigint, approved bool default false);
CREATE TABLE IF NOT EXISTS contest_votes(contest_id int not null, entry_id int, user_id bigint not null);
CREATE TABLE IF NOT EXISTS customroles(guild_id bigint NOT NULL, user_id bigint NOT NULL, role_id bigint NOT NULL);
CREATE TABLE IF NOT EXISTS payoutchannels(channel_id BIGINT PRIMARY KEY, ticket_user_id BIGINT, staff BIGINT);
CREATE SCHEMA IF NOT EXISTS donations""")
        print(f"{datetime.datetime.utcnow().strftime(strfformat)} | {self.user} ({self.user.id}) is ready")

    @property
    def error_channel(self):
        return self.get_guild(871734809154707467).get_channel(871737028105109574)

    async def on_guild_join(self, guild):
        await self.db.execute('INSERT INTO prefixes VALUES ($1, $2) ON CONFLICT DO UPDATE SET prefix=$2', guild.id, "dv.")

    async def get_prefix(self, message):
        if message.guild is None:
            return commands.when_mentioned_or('.')(self, message)
        guild_id = message.guild.id
        if not (prefix := self.prefixes.get(guild_id)):
            query = "SELECT prefix FROM prefixes WHERE guild_id=$1"
            data = await self.db.fetchrow(query, guild_id)
            if data is None:
                await self.db.execute("INSERT INTO prefixes VALUES ($1, $2)", guild_id, 'dv.')
                data = {}
            prefix = self.prefixes.setdefault(guild_id, data.get("prefix") or '.')
        if message.content.lower().startswith(prefix):
            prefix = message.content[:len(prefix)]
        return commands.when_mentioned_or(prefix)(self, message)

    async def set_prefix(self, guild, prefix):
        await self.db.execute('UPDATE prefixes SET prefix=$1 WHERE guild_id=$2', prefix, guild.id)
        self.prefixes[guild.id] = prefix

    async def check_blacklisted_content(self, string):
        blacklisted_words = await self.db.fetch("SELECT * FROM blacklisted_words")
        string = string.lower()
        for word in blacklisted_words:
            if word.get('string') in string.lower():
                return True
        return False

    async def get_guild_settings(self, guild_id):
        serverconf = self.serverconfig.get(guild_id, None)
        if serverconf is None:
            serverconf = await self.fetch_guild_settings(guild_id)
            self.serverconfig[guild_id] = serverconf
        return serverconf


    async def fetch_guild_settings(self, guild_id):
        serverconfig = await self.db.fetchrow("SELECT * FROM serverconfig WHERE guild_id=$1", guild_id)
        if serverconfig is None:
            await self.db.execute("INSERT INTO serverconfig(guild_id) VALUES ($1)", guild_id)
            serverconfig = await self.db.fetchrow("SELECT * FROM serverconfig WHERE guild_id=$1", guild_id)
        self.serverconfig[guild_id] = ServerConfiguration(serverconfig)
        return ServerConfiguration(serverconfig)

    async def fetch_user_info(self, user_id):
        userinfo = await self.db.fetchrow("SELECT * FROM userinfo WHERE user_id=$1", user_id)
        if userinfo is None:
            await self.db.execute("INSERT INTO userinfo(user_id) VALUES ($1)", user_id)
            userinfo = await self.db.fetchrow("SELECT * FROM userinfo WHERE user_id=$1", user_id)
        return UserInfo(userinfo)

    async def update_user_info(self, userinfo: UserInfo):
        q = "UPDATE userinfo SET notify_about_logging = $1, bypass_ban = $2, heists = $3, heistamt = $4, timezone = $5 WHERE user_id = $6"
        values = (userinfo.notify_about_logging, userinfo.bypass_ban, userinfo.heists, userinfo.heistamt, userinfo.timezone, userinfo.user_id)
        await self.db.execute(q, *values)
        return

    async def get_all_blacklisted_users(self):
        blacklist_dict = {}
        blacklist = await self.db.fetch("SELECT * FROM blacklist WHERE blacklist_active = $1", True)
        for entry in blacklist:
            user_id = entry.get('user_id')
            time_until = entry.get('time_until')
            if time_until is None or user_id is None:
                pass
            else:
                blacklist_dict[user_id] = time_until
        self.blacklist = blacklist_dict

    async def check_blacklisted_user(self, member):
        blacklisted_users = await self.db.fetchrow("SELECT * FROM blacklist WHERE user_id = $1 and blacklist_active = $2", member.id, True)
        if blacklisted_users:
            return True
        return False

    def get_guild_prefix(self, guild):
        if guild is None:
            return 'dv.'
        return self.prefixes.get(guild.id)

    async def shutdown(self):
        """Cancels tasks and shuts down the bot."""
        await self.topgg_webhook.close()
        await self.close()

    def starter(self):
        """starts the bot properly."""
        start = time.time()
        print(f"{datetime.datetime.utcnow().strftime(strfformat)} | Starting Bot")
        try:
            pool_pg = self.loop.run_until_complete(asyncpg.create_pool(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            ))
        except Exception as e:
            print_exception(f"{datetime.datetime.utcnow().strftime(strfformat)} | Could not connect to databases:", e)
        else:
            self.uptime = discord.utils.utcnow()
            self.db = pool_pg
            print(f"{datetime.datetime.utcnow().strftime(strfformat)} | Connected to the database")
            self.loop.create_task(self.after_ready())
            self.loop.create_task(self.load_maintenance_data())
            self.loop.create_task(self.get_all_blacklisted_users())
            self.edit_message.start()
            self.update_blacklist.start()
            self.run(token)

if __name__ == '__main__':
    client = dvvt()
    client.starter()