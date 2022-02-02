import os
import time
import discord
import asyncpg
import datetime
from dotenv import load_dotenv
from discord import client
from discord.ext import commands, tasks
from utils.context import DVVTcontext
from utils.format import print_exception

AVAILABLE_EXTENSIONS = ['cogs.dev',
'cogs.errors',
'cogs.admin',
'cogs.autoreaction',
'cogs.banbattle',
'cogs.fun',
'cogs.help',
'cogs.mod',
'cogs.owo',
'cogs.utility',
'cogs.votetracker',
'cogs.messagetracking',
'cogs.grinder',
'cogs.automod',
'cogs.giveaways',
'cogs.donations',
'cogs.dankmemer',
'cogs.infection',
'cogs.imgen'
]

load_dotenv('credentials.env')
token = os.getenv('TOKEN')
host = os.getenv('HOST')
database = os.getenv('DATABASE')
user = os.getenv('dbUSER')
password = os.getenv('dbPASSWORD')


intents = discord.Intents(guilds = True, members = True, presences = True, messages = True, reactions = True, emojis = True, invites = True, voice_states = True)
allowed_mentions = discord.AllowedMentions(everyone=False, roles=False)

class dvvt(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix = self.get_prefix, intents=intents, allowed_mentions=allowed_mentions, case_insensitive=True)
        self.prefixes = {}
        self.uptime = None
        self.embed_color = 0x57F0F0
        self.pool_pg = None
        self.maintenance = {}
        self.maintenance_message = {}
        self.available_extensions = AVAILABLE_EXTENSIONS
        self.blacklist = {}

        for ext in self.available_extensions:
            self.load_extension(ext)

    @tasks.loop(seconds=5)
    async def update_blacklist(self):
        await self.wait_until_ready()
        blacklist_dict = dict(self.blacklist) # copy the dict so that we can iterate over it and not result in runtime error due to dictionary edits
        for user in blacklist_dict:
            if time.time() >= self.blacklist[user]:
                blacklist = await self.pool_pg.fetchrow(
                    "SELECT * FROM blacklist WHERE user_id=$1 AND time_until = $2 AND blacklist_active = $3", user, self.blacklist[user], True)
                await self.pool_pg.execute(
                    "UPDATE blacklist SET blacklist_active = $1 WHERE user_id = $2 and incident_id = $3", False, user, blacklist.get('incident_id'))
                embed = discord.Embed(title=f"Bot Unblacklist | Case {blacklist.get('incident_id')}", description=f"**Reason**: Blacklist over, automatically rescinded\n**Responsible Moderator**: {self.user.name} ({self.user.id})", color=discord.Color.green())
                user = await self.fetch_user(user)
                embed.set_author(name=f"{user} ({user.id})", icon_url=user.display_avatar.url)
                if user is not None:
                    try:
                        await user.send("You are no longer blacklisted from using the bot, and can use all functions of the bot.")
                    except discord.HTTPException:
                        pass
                del self.blacklist[user.id]
        await self.get_all_blacklisted_users()

    @update_blacklist.before_loop
    async def before_update_blacklist(self):
        await self.wait_until_ready()

    async def get_context(self, message, *, cls=None):
        context = await super().get_context(message, cls=DVVTcontext)
        return context

    async def load_maintenance_data(self):
        results = await self.pool_pg.fetch("SELECT * FROM maintenance")
        for result in results:
            self.maintenance.setdefault(result.get('cog_name'), result.get('enabled'))
            self.maintenance_message.setdefault(result.get('cog_name'), result.get('message'))

    async def process_commands(self, message: discord.Message):
        ctx = await self.get_context(message)
        if ctx.cog:
            if ctx.author.id in self.blacklist:
                if ctx.author.id not in [650647680837484556, 515725341910892555, 321892489470410763]:
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
        all_tables = ['prefixes', 'dankreminders', 'stats', 'nicknames', 'channelconfigs', 'dmrequestslog',
                      'dumbfightlog', 'joinmessages', 'dmrequests', 'messagelog', 'lockdownmsgs',
                      'remindersettings', 'inventories', 'iteminfo', 'tempweekly', 'rules', 'serverconfig',
                      'owocurrent', 'owopast', 'temp', 'stickymessages', 'maintenance', 'teleport',
                      'suggestion_response', 'suggestions', 'lockdownprofiles', 'grinderdata', 'messagemilestones',
                      'viprolemessages', 'karutaeventconfig', 'autoreactions', 'owocount', 'milestones', 'rmpreference',
                      'roleremove', 'votecount', 'cooldowns', 'selfrolemessages', 'devmode', 'blacklisted_words',
                      'blacklist', 'freezenick', 'autorole', 'giveaways', 'giveawayentrants', 'dankdrops', 'autorole',
                      'donation_categories', 'christmaseventconfig', 'commandaccess', 'ignoredchristmascat',
                      'ignoredchristmaschan', 'perkremoval', 'commandlog', 'timedunlock', 'nickname_changes',
                      'name_changes', 'timers', 'infections', 'polls', 'pollvotes', 'highlight', 'highlight_ignores']
        tables = await self.pool_pg.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
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
                print("Some databases do not exist, creating them now...")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS autoreactions(guild_id bigint, trigger text, response text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS autorole(member_id bigint, guild_id bigint, role_id bigint, time bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS blacklist(incident_id serial, user_id bigint, moderator_id bigint, blacklist_active boolean, time_until bigint, reason text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS blacklisted_words(string text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS channelconfigs(guild_id bigint NOT null PRIMARY KEY, nickname_channel_id bigint, dmchannel_id bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS christmaseventconfig(guild_id bigint, percentage real)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS commandaccess(member_id bigint, command text, until bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS cooldowns(command_name text, member_id bigint, time bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS dankdrops(guild_id bigint, name text, price text, time bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS dankreminders(member_id bigint, remindertype bigint, channel_id bigint, guild_id bigint, time bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS devmode(user_id bigint, devmode boolean)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS donation_categories(guild_id bigint, category_name text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS dmrequests(id serial, member_id bigint, target_id bigint, dmcontent text, messageid bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS dmrequestslog(id bigint, member_id bigint, target_id bigint, approver_id bigint, dmcontent text, status integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS dumbfightlog(invoker_id bigint, target_id bigint, did_win integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS freezenick(id serial, user_id bigint, guild_id bigint, nickname text, old_nickname text, time bigint, reason text, responsible_moderator bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS grinderdata(user_id bigint PRIMARY KEY, today bigint, past_week bigint, last_week bigint, past_month bigint, all_time bigint, last_dono_time bigint, last_dono_msg text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS giveaways(guild_id bigint, channel_id bigint, message_id bigint, time bigint, name text, host_id bigint, winners integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS giveawayentrants(message_id bigint, user_id bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS ignoredchristmascat(guild_id bigint, category_id bigint PRIMARY KEY)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS ignoredchristmaschan(guild_id bigint, channel_id bigint PRIMARY KEY)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS inventories(user_id bigint PRIMARY KEY, skull bigint, argonphallicobject bigint, llamaspit bigint, slicefrenzylesliecake bigint, wickedrusteze bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS iteminfo(name text PRIMARY KEY, fullname text, description text, emoji text, image text, hidden boolean)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS joinmessages(guild_id bigint PRIMARY KEY, channel_id bigint, plain_text text, embed_details text, delete_after integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS karutaeventconfig(channel_id text, percentage_chance real)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS lockdownmsgs(guild_id bigint, profile_name text, startmsg text, endmsg text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS lockdownprofiles(guild_id bigint, profile_name text, channel_id bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS maintenance(cog_name text PRIMARY KEY, message text, enabled boolean)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS messagelog(user_id bigint PRIMARY KEY, messagecount bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS messagemilestones(messagecount integer, roleid bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS milestones(votecount integer, roleid bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS nicknames(id serial, member_id bigint PRIMARY KEY, nickname text, messageid bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS owocount(member_id bigint PRIMARY KEY, daily_count integer, weekly_count integer, total_count integer, yesterday integer, last_week integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS owocurrent(member_id bigint PRIMARY KEY, daily_count integer, weekly_count integer, total_count integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS owopast(member_id bigint PRIMARY KEY, yesterday integer, last_week integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS perkremoval(member_id bigint, perk text, until bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS prefixes(guild_id bigint PRIMARY KEY, prefix text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS remindersettings(member_id bigint PRIMARY KEY, method integer, daily bigint, lottery bigint, work bigint, lifesaver bigint, apple integer, redeem integer, weekly integer, monthly integer, hunt integer, fish integer, dig integer, highlow integer, snakeeyes integer, search integer, crime integer, beg integer, dailybox integer, horseshoe integer, pizza integer, drop integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS rmpreference(member_id bigint PRIMARY KEY, rmtype integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS roleremove(member_id bigint PRIMARY KEY)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS rules(guild_id bigint, command text, role_id bigint, whitelist boolean)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS selfrolemessages(guild_id bigint, age bigint, gender bigint, location bigint, minigames bigint, event_pings bigint, dank_pings bigint, server_pings bigint, bot_roles bigint, random_color bigint, colors bigint, specialcolors bigint, boostping bigint, vipheist bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS serverconfig(guild_id bigint, settings text, enabled boolean)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS stats(member_id bigint, remindertype integer, time bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS stickmessages(guild_id bigint PRIMARY KEY, channel_id bigint, message_id bigint, type integer, message text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS suggestion_response(suggestion_id integer, user_id bigint, response_id bigint, message_id bigint, message text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS suggestions(suggestion_id serial, user_id bigint, finish boolean, response_id bigint, suggestion text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS teleport(member_id bigint, checkpoint text, channel_id bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS temp(member_id bigint PRIMARY KEY, daily_count integer, weekly_count integer, total_count integer, yesterday integer, last_week integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS tempweekly(member_id bigint PRIMARY KEY, yesterday integer, last_week integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS timedrole(member_id bigint, guild_id bigint, role_id bigint, time bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS viprolemessages(guild_id bigint, colors bigint, vipcolors bigint, boostgaw bigint, vipheistping bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS votecount(member_id bigint PRIMARY KEY, count integer)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS commandlog(guild_id bigint, channel_id bigint, user_id bigint, command text, message text, time bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS timedunlock(guild_id bigint, channel_id bigint, time bigint, responsible_moderator bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS nickname_changes(guild_id bigint, member_id bigint, nickname text, time bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS name_changes(user_id bigint, name text, time bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS timers(guild_id bigint, channel_id bigint, message_id bigint, user_id bigint, time bigint, title text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS infections(infectioncase serial, member_id bigint PRIMARY KEY, guild_id bigint, channel_id bigint, message_id bigint, timeinfected bigint)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS polls(poll_id serial, guild_id bigint, channel_id bigint, invoked_message_id bigint, message_id bigint, creator_id bigint, poll_name text, choices text, created bigint)"),
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS pollvotes(poll_id integer, user_id bigint, choice text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS highlight (guild_id bigint, user_id bigint, highlights text)")
                await self.pool_pg.execute("CREATE TABLE IF NOT EXISTS highlight_ignores (guild_id bigint, user_id bigint, ignore_type text, ignore_id bigint)")
                await self.pool_pg.execute("CREATE SCHEMA IF NOT EXISTS donations")
        print("Bot is ready")

    @property
    def error_channel(self):
        return self.get_guild(871734809154707467).get_channel(871737028105109574)

    async def on_guild_join(self, guild):
        await self.pool_pg.execute('INSERT INTO prefixes VALUES ($1, $2) ON CONFLICT DO UPDATE SET prefix=$2', guild.id, "dv.")

    async def get_prefix(self, message):
        if message.guild is None:
            return commands.when_mentioned_or('.')(self, message)
        guild_id = message.guild.id
        if not (prefix := self.prefixes.get(guild_id)):
            query = "SELECT prefix FROM prefixes WHERE guild_id=$1"
            data = await self.pool_pg.fetchrow(query, guild_id)
            if data is None:
                await self.pool_pg.execute("INSERT INTO prefixes VALUES ($1, $2)", guild_id, 'dv.')
                data = {}
            prefix = self.prefixes.setdefault(guild_id, data.get("prefix") or '.')
        if message.content.lower().startswith(prefix):
            prefix = message.content[:len(prefix)]
        return commands.when_mentioned_or(prefix)(self, message)

    async def set_prefix(self, guild, prefix):
        await self.pool_pg.execute('UPDATE prefixes SET prefix=$1 WHERE guild_id=$2', prefix, guild.id)
        self.prefixes[guild.id] = prefix

    async def check_blacklisted_content(self, string):
        blacklisted_words = await self.pool_pg.fetch("SELECT * FROM blacklisted_words")
        string = string.lower()
        for word in blacklisted_words:
            if word.get('string') in string.lower():
                return True
        return False

    async def get_all_blacklisted_users(self):
        blacklist_dict = {}
        blacklist = await self.pool_pg.fetch("SELECT * FROM blacklist WHERE blacklist_active = $1", True)
        for entry in blacklist:
            user_id = entry.get('user_id')
            time_until = entry.get('time_until')
            if time_until is None or user_id is None:
                pass
            else:
                blacklist_dict[user_id] = time_until
        self.blacklist = blacklist_dict

    async def check_blacklisted_user(self, member):
        blacklisted_users = await self.pool_pg.fetchrow("SELECT * FROM blacklist WHERE user_id = $1 and blacklist_active = $2", member.id, True)
        if blacklisted_users:
            return True
        return False

    def get_guild_prefix(self, guild):
        if guild is None:
            return 'dv.'
        return self.prefixes.get(guild.id)

    async def shutdown(self):
        """Cancels tasks and shuts down the bot."""
        await self.close()

    def starter(self):
        """starts the bot properly."""
        try:
            start = time.time()
            pool_pg = self.loop.run_until_complete(asyncpg.create_pool(
                host=host,
                database=database,
                user=user,
                password=password
            ))
        except Exception as e:
            print_exception("Could not connect to databases:", e)
        else:
            self.uptime = discord.utils.utcnow()
            self.pool_pg = pool_pg
            print(f"Connected to the database ({round(time.time() - start, 2)})s")
            self.loop.create_task(self.after_ready())
            self.loop.create_task(self.load_maintenance_data())
            self.loop.create_task(self.get_all_blacklisted_users())
            self.update_blacklist.start()
            self.run(token)

if __name__ == '__main__':
    client = dvvt()
    client.starter()