import os
import discord
import datetime
import sqlite3
from dotenv import load_dotenv
from discord import client
from discord.ext import commands
from utils.context import DVVTcontext

AVAILABLE_EXTENSIONS = ['cogs.dev',
'cogs.errors',
'cogs.help',
'cogs.votetracker',
'cogs.utility']

load_dotenv('credentials.env')
token = os.getenv('TOKEN')
con = sqlite3.connect('database.db')
cur = con.cursor()

intents = discord.Intents(guilds = True, members = True, presences = True, messages = True, reactions = True, emojis = True, invites = True, voice_states = True)
allowed_mentions = discord.AllowedMentions(everyone=False, roles=False)

class dvvt(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix = self.get_prefix, intents=intents, allowed_mentions=allowed_mentions, case_insensitive=True)
        self.prefixes = {}
        self.uptime = None
        self.embed_color = 0x57F0F0
        self.available_extensions = AVAILABLE_EXTENSIONS

        for ext in self.available_extensions:
            self.load_extension(ext)

    async def get_context(self, message, *, cls=None):
        context = await super().get_context(message, cls=DVVTcontext)
        return context

    async def on_ready(self):
        cur.execute('''CREATE TABLE IF NOT EXISTS prefixes
                (guild_id text PRIMARY KEY, prefix text)''')
        con.commit()
        print("Bot is ready")
    
    async def on_guild_join(self, guild):
        query = '''INSERT OR REPLACE INTO prefixes VALUES (?, ?)'''
        cur.execute(query, (guild.id, "dv.",))
        con.commit()

    async def get_prefix(self, message):
        if message.guild is None:
            return commands.when_mentioned_or('.')(self, message)
        guild_id = message.guild.id
        if not (prefix := self.prefixes.get(guild_id)):
            print(self.prefixes.get(guild_id))
            query = "SELECT prefix FROM prefixes WHERE guild_id=$1"
            cur.execute(query, (guild_id,))
            data = cur.fetchone()
            if not data:
                cur.execute('''INSERT INTO prefixes VALUES (?, ?)''', (guild_id, "dv.",))
                con.commit()
                data = {}
            prefix = self.prefixes.setdefault(guild_id, data[0] or "dv.")
        return commands.when_mentioned_or(prefix)(self, message)

    async def set_prefix(self, guild, prefix):
        query = "UPDATE prefixes SET prefix=? WHERE guild_id=?"
        cur.execute(query, (prefix, guild.id,))
        con.commit()
        self.prefixes[guild.id] = prefix

    def get_guild_prefix(self, guild):
        if guild is None:
            return '.'
        return self.prefixes.get(guild.id)

    async def shutdown(self):
        """Cancels tasks and shuts down the bot."""
        con.close()
        await self.close()

    def starter(self):
        """starts the bot properly."""
        self.uptime = datetime.datetime.utcnow()
        self.run(token)

if __name__ == '__main__':
    client = dvvt()
    client.starter()