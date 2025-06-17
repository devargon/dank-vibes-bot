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

def get_display_time_now():
    return datetime.datetime.utcnow().strftime(strfformat)


AVAILABLE_EXTENSIONS = [
    'cogs.dev',
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
    'cogs.automod',
    'cogs.giveaways',
    'cogs.dankmemer',
    'cogs.events',
    'cogs.imgen',
    'cogs.disboard',
    'cogs.slashtags',
    'cogs.banappeal',
    'cogs.ai_moderation',
    'cogs.amari_import',
    'cogs.actions'
]

load_dotenv('credentials.env')
token = os.getenv('TOKEN')
host = os.getenv('HOST')
database = os.getenv('DATABASE')
user = os.getenv('dbUSER')
port = int(os.getenv('dbPORT'))
password = os.getenv('dbPASSWORD')
amari_key = os.getenv('AMARI_KEY')

TABLE_SCHEMAS_PATH = "./table_schemas"

intents = discord.Intents(guilds=True, members=True, presences=True, messages=True, reactions=True, emojis=True, invites=True, voice_states=True, message_content=True, typing=True, moderation=True)
allowed_mentions = discord.AllowedMentions(everyone=False, roles=False)


class dvvt(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix = self.get_prefix, intents=intents, allowed_mentions=allowed_mentions, case_insensitive=True)
        self.custom_status = False
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
            print(f"{get_display_time_now()} | Loaded {ext}")
        self.add_check(self.check_application_command_validity)

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

    async def initialize_database(self):
        print(f"{get_display_time_now()} | Checking tables")
        schema_files = sorted([
            f for f in os.listdir(TABLE_SCHEMAS_PATH)
            if f.endswith(".sql") and "_" in f
        ])

        table_to_file = {}
        for file in schema_files:
            parts = file.split("_")
            if len(parts) < 2:
                print(f"{get_display_time_now()} | ⚠️ Skipping invalid file name: {file}")
                continue
            table_name = "_".join(parts[1:]).replace(".sql", "")
            table_to_file[table_name] = file

        result = await self.db.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"
        )
        db_tables = set(row["table_name"] for row in result)
        schema_tables = set(table_to_file.keys())

        valid_tables = db_tables & schema_tables
        missing_tables = schema_tables - db_tables
        extra_tables = db_tables - schema_tables

        for table in sorted(missing_tables):
            file = table_to_file[table]
            with open(os.path.join(TABLE_SCHEMAS_PATH, file), 'r') as f:
                sql = f.read()
                await self.db.execute(sql)
            print(f"{get_display_time_now()} | ✅ Created missing table `{table}` from `{file}`")

        print(f"\n{get_display_time_now()} | ✅ Valid tables ({len(valid_tables)}): {', '.join(sorted(valid_tables))}")
        print(f"{get_display_time_now()} | ❌ Missing tables created ({len(missing_tables)}): {', '.join(sorted(missing_tables))}")
        print(
            f"{get_display_time_now()} | ⚠️ Extra tables in DB not in schema folder ({len(extra_tables)}): {', '.join(sorted(extra_tables))}\n")


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
                if ctx.author.id not in [312876934755385344, 515725341910892555, 321892489470410763]:
                    if time.time() >= self.blacklist[ctx.author.id]:
                        blacklist = await self.db.fetchrow("SELECT * FROM blacklist WHERE user_id=$1 AND time_until = $2 AND blacklist_active = $3", ctx.author.id, self.blacklist[ctx.author.id], True)
                        await self.db.execute("UPDATE blacklist SET blacklist_active = $1 WHERE user_id = $2 and incident_id = $3", False, message.author.id, blacklist.get('incident_id'))
                        embed = discord.Embed(title=f"Bot Unblacklist | Case {blacklist.get('incident_id')}", description=f"**Reason**: Blacklist over, automatically rescinded\n**Responsible Moderator**: {ctx.me} ({ctx.me.id})", color=discord.Color.green())
                        embed.set_author(name=f"{message.author} ({message.author.id})", icon_url=message.author.display_avatar.url)
                        await self.get_channel(906433823594668052).send(embed=embed)
                        await message.reply("You are no longer blacklisted from using the bot, and can use all functions of the bot.")
                    return
            if self.maintenance.get(ctx.cog.qualified_name) and message.author.id not in [321892489470410763, 312876934755385344]:
                maintenance_message = self.maintenance_message.get(ctx.cog.qualified_name)
                return await message.channel.send(maintenance_message)
        await self.invoke(ctx)

    async def check_application_command_validity(self, ctx):
        if isinstance(ctx, discord.ApplicationCommand) or isinstance(ctx, discord.ApplicationContext):
            if ctx.cog:
                if ctx.author.id in self.blacklist:
                    if ctx.author.id not in [312876934755385344, 515725341910892555, 321892489470410763]:
                        if time.time() >= self.blacklist[ctx.author.id]:
                            blacklist = await self.db.fetchrow(
                                "SELECT * FROM blacklist WHERE user_id=$1 AND time_until = $2 AND blacklist_active = $3",
                                ctx.author.id, self.blacklist[ctx.author.id], True)
                            await self.db.execute(
                                "UPDATE blacklist SET blacklist_active = $1 WHERE user_id = $2 and incident_id = $3",
                                False, ctx.author.id, blacklist.get('incident_id'))
                            embed = discord.Embed(title=f"Bot Unblacklist | Case {blacklist.get('incident_id')}",
                                                  description=f"**Reason**: Blacklist over, automatically rescinded\n**Responsible Moderator**: {ctx.me} ({ctx.me.id})",
                                                  color=discord.Color.green())
                            embed.set_author(name=f"{ctx.author} ({ctx.author.id})",
                                             icon_url=ctx.author.display_avatar.url)
                            await self.get_channel(906433823594668052).send(embed=embed)
                        return False
                if self.maintenance.get(ctx.cog.qualified_name) and ctx.author.id not in [321892489470410763,
                                                                                              312876934755385344]:
                    maintenance_message = self.maintenance_message.get(ctx.cog.qualified_name)
                    await ctx.respond(maintenance_message)
                    return False
        return True

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    async def after_ready(self):
        await self.wait_until_ready()

    async def on_ready(self):
        await self.initialize_database()
        for guild in self.guilds:
            guild_settings = await client.fetch_guild_settings(guild.id)
            self.serverconfig[guild.id] = guild_settings
        print(f"{get_display_time_now()} | Loaded all Server Configurations")
        await self.db.execute("CREATE SCHEMA IF NOT EXISTS donations;")
        print(f"{get_display_time_now()} | {self.user} ({self.user.id}) is ready")

    @property
    def error_channel(self):
        return self.get_guild(871734809154707467).get_channel(871737028105109574)

    async def on_guild_join(self, guild):
        await self.db.execute('INSERT INTO prefixes VALUES ($1, $2) ON CONFLICT DO UPDATE SET prefix=$2', guild.id, "dv.")

    async def create_amari_client(self):
        return api.AmariClient(amari_key)

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
        print(f"{get_display_time_now()} | Starting Bot")
        try:
            pool_pg = self.loop.run_until_complete(asyncpg.create_pool(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            ))
        except Exception as e:
            print_exception(f"{get_display_time_now()} | Could not connect to databases:", e)
        else:
            self.uptime = discord.utils.utcnow()
            self.db = pool_pg
            self.AmariClient = self.loop.run_until_complete(self.create_amari_client())
            print(f"{get_display_time_now()} | Connected to the database")
            self.loop.create_task(self.after_ready())
            self.loop.create_task(self.load_maintenance_data())
            self.loop.create_task(self.get_all_blacklisted_users())
            self.edit_message.start()
            self.update_blacklist.start()
            self.run(token)

if __name__ == '__main__':
    client = dvvt()
    client.starter()