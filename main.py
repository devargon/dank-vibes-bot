import datetime
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils.botlogger import BotLogger
from utils.context import DVVTcontext

strfformat = "%d-%m-%y %H:%M:%S"


AVAILABLE_EXTENSIONS = [
    'cogs.dev',
    'cogs.errors',
    'cogs.help',
]

load_dotenv('credentials.env')
token = os.getenv('TOKEN')


intents = discord.Intents(guilds=True, members=True, presences=True, messages=True, reactions=True, emojis=True, invites=True, voice_states=True, message_content=True, typing=True, moderation=True)
allowed_mentions = discord.AllowedMentions(everyone=False, roles=False)


class dvvt(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="b.", intents=intents, allowed_mentions=allowed_mentions, case_insensitive=True)
        self.custom_status = False
        self.prefixes = {}
        self.uptime = None
        self.embed_color: int = 0x57F0F0
        self.db = None
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


    async def get_context(self, message, *, cls=None):
        context = await super().get_context(message, cls=DVVTcontext)
        return context

    async def process_commands(self, message: discord.Message):
        ctx: DVVTcontext = await self.get_context(message)
        await self.invoke(ctx)

    async def on_ready(self):
        await self.change_presence(status=discord.Status.invisible)
        print(f"I am {self.user}, looking at files {os.getenv('FILE')}")

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    @property
    def error_channel(self):
        return self.get_guild(871734809154707467).get_channel(871737028105109574)

    async def shutdown(self):
        """Cancels tasks and shuts down the bot."""
        await self.close()

    def starter(self):
        """starts the bot properly."""
        print(f"{datetime.datetime.utcnow().strftime(strfformat)} | Starting Bot")
        self.uptime = discord.utils.utcnow()
        self.run(token)

if __name__ == '__main__':
    client = dvvt()
    client.starter()