import os
import time
import discord
import asyncpg
import datetime
from dotenv import load_dotenv
from discord import client
from discord.ext import commands
from utils.context import DVVTcontext
from utils.format import print_exception

AVAILABLE_EXTENSIONS = ['cogs.dev',
'cogs.errors',
'cogs.admin',
'cogs.autoreaction',
'cogs.banbattle',
'cogs.dankmemer',
'cogs.fun',
'cogs.help',
'cogs.mod',
'cogs.owo',
'cogs.utility',
'cogs.votetracker',
'cogs.messagetracking',
'cogs.grinder',
'cogs.automod'
]

load_dotenv('credentials.env')
token = os.getenv('TOKEN')
host = os.getenv('HOST') if os.name == "nt" else '127.0.0.1'
database = os.getenv('DATABASE')
user = os.getenv('USER') if os.name == 'nt' else 'dankvibes'
password = os.getenv('PASSWORD') if os.name == 'nt' else 'Qwerty12345'


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

        for ext in self.available_extensions:
            self.load_extension(ext)

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
            if ctx.author.id not in [650647680837484556, 515725341910892555, 321892489470410763]:
                blacklist = await self.pool_pg.fetchrow("SELECT * FROM blacklist WHERE user_id = $1 and blacklist_active = $2", message.author.id, True)
                if blacklist and time.time() >= blacklist.get('time_until'):
                    await self.pool_pg.execute("UPDATE blacklist SET blacklist_active = $1 WHERE user_id = $2 and incident_id = $3", False, message.author.id, blacklist.get('incident_id'))
                    embed = discord.Embed(title=f"Bot Unblacklist | Case {blacklist.get('incident_id')}", description=f"**Reason**: Blacklist over, automatically rescinded\n**Responsible Moderator**: {ctx.me} ({ctx.me.id})", color=discord.Color.green())
                    embed.set_author(name=f"{message.author} ({message.author.id})", icon_url=message.author.display_avatar.url)
                    await self.get_channel(906433823594668052).send(embed=embed)
                    await message.reply("You are no longer blacklisted from using the bot, and can use all functions of the bot.")
                    return await self.invoke(ctx)
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
            self.run(token)

if __name__ == '__main__':
    client = dvvt()
    client.starter()