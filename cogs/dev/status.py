import discord
from utils import checks
from discord.ext import commands

status_emojis = {
    discord.Status.dnd: "<:status_dnd:840918521918783508>",
    discord.Status.idle: "<:status_idle:840918469327192096>",
    discord.Status.online: "<:status_online:840918419246415873>",
    discord.Status.offline: "<:status_offline:840918448560930867>",
    discord.Status.invisible: "<:status_offline:840918448560930867>",
    discord.Status.do_not_disturb: "<:status_dnd:840918521918783508>",
}

class Status(commands.Cog):
    """
    This module allows you to set bot's status and other different things.
    """
    def __init__(self, client):
        self.client = client

    @checks.admoon()
    @commands.group(name='status', hidden=True, invoke_without_command=True, usage='<status>')
    async def status(self, ctx, *, status: str = None):
        """
        Sets bot's status.

        Available statuses:
            online
            idle
            dnd
            invisible
        """
        if status is None:
            await ctx.send("Available statuses: `online`, `idle`, `dnd` and `invisible`.", delete_after=3)
            await ctx.message.delete(delay=3)
        statuses = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible,
            "offline": discord.Status.invisible,
        }
        activity = ctx.me.activity
        try:
            status = statuses[status.lower()]
        except KeyError:
            await ctx.send("That's not a valid status", delete_after=3)
            await ctx.message.delete(delay=3)
        else:
            await self.client.change_presence(status=status, activity=activity)
            emoji = status_emojis[ctx.me.status]
            await ctx.checkmark()
            await ctx.send("Status changed to {}.".format(emoji), delete_after=5)
        await ctx.message.delete(delay=5)

    @checks.admoon()
    @status.command(name='game', aliases=['play'], hidden=True, usage='<game>')
    async def status_game(self, ctx, *, game: str = None):
        """
        Set's bot's playing status.

        Leaving <game> empty will clear the bot's status.
        """
        if game:
            if len(game) > 128:
                await ctx.send("The maximum length of game description is 128 characters.", delete_after=3)
                return await ctx.message.delete(delay=3)
            game = discord.Game(name=game)
        else:
            game = None
        status = ctx.me.status
        await self.client.change_presence(status=status, activity=game)
        if game:
            emoji = status_emojis[ctx.me.status]
            await ctx.checkmark()
            await ctx.send("Status set to {emoji} | `Playing {game.name}`.".format(emoji=emoji, game=game), delete_after=5)
        else:
            await ctx.checkmark()
            await ctx.send("Status cleared.", delete_after=5)
        await ctx.message.delete(delay=5)

    @checks.admoon()
    @status.command(name='Listening', aliases=['listen'], hidden=True, usage='<listen>')
    async def status_listening(self, ctx, *, listening: str = None):
        """
        Sets bot's listening status.

        Leaving <listen> empty will clear the bot's status.
        """
        if listening:
            if len(listening) > 128:
                await ctx.send("The maximum length of listening description is 128 characters.", delete_after=3)
                return await ctx.message.delete(delay=3)
            activity = discord.Activity(name=listening, type=discord.ActivityType.listening)
        else:
            activity = None
        status = ctx.me.status
        await self.client.change_presence(status=status, activity=activity)
        if activity:
            emoji = status_emojis[ctx.me.status]
            await ctx.checkmark()
            await ctx.send("Status set to {emoji} | `Listening to {listening}`.".format(emoji=emoji, listening=listening), delete_after=5)
        else:
            await ctx.checkmark()
            await ctx.send("Status cleared.", delete_after=5)
        await ctx.message.delete(delay=5)

    @checks.admoon()
    @status.command(name='watching', aliases=['watch'], hidden=True, usage='<watch>')
    async def status_watching(self, ctx, *, watching: str = None):
        """
        Sets bot's watching status.

        Leaving <watch> empty will clear the bot's status.
        """
        if watching:
            if len(watching) > 128:
                await ctx.send("The maximum length of watching description is 128 characters.", delete_after=3)
                return await ctx.message.delete(delay=3)
            activity = discord.Activity(name=watching, type=discord.ActivityType.watching)
        else:
            activity = None
        status = ctx.me.status
        await self.client.change_presence(status=status, activity=activity)
        if activity:
            emoji = status_emojis[ctx.me.status]
            await ctx.checkmark()
            await ctx.send("Status set to {emoji} | `Watching {watching}`.".format(emoji=emoji, watching=watching), delete_after=5)
        else:
            await ctx.checkmark()
            await ctx.send("Status cleared.", delete_after=5)
        await ctx.message.delete(delay=5)

    @checks.admoon()
    @status.command(name='competing', aliases=['compete'], hidden=True, usage='<compete>')
    async def status_competing(self, ctx, *, competing: str = None):
        """
        Sets bot's competing status.

        Leaving <compete> empty will clear the bot's status.
        """
        if competing:
            if len(competing) > 128:
                await ctx.send("The maximum length of competing description is 128 characters.", delete_after=3)
                return await ctx.message.delete(delay=3)
            activity = discord.Activity(name=competing, type=discord.ActivityType.competing)
        else:
            activity = None
        status = ctx.me.status
        await self.client.change_presence(status=status, activity=activity)
        if competing:
            emoji = status_emojis[ctx.me.status]
            await ctx.checkmark()
            await ctx.send("Status set to {emoji} | `Competing {competing}`.".format(emoji=emoji, competing=competing), delete_after=5)
        else:
            await ctx.checkmark()
            await ctx.send("Status cleared.", delete_after=5)
        await ctx.message.delete(delay=5)

    @checks.admoon()
    @status.command(name='streaming', aliases=['stream'], hidden=True, usage='<stream>')
    async def status_streaming(self, ctx, *, streaming: str = None):
        """
        Sets bot's streaming status.

        Leaving <stream> empty will clear the bot's status.
        """
        if streaming:
            if len(streaming) > 128:
                await ctx.send("The maximum length of the stream title is 128 characters.", delete_after=3)
                return await ctx.message.delete(delay=3)
            url = "https://www.twitch.tv/twitch"
            activity = discord.Streaming(url=url, name=streaming)
        else:
            activity = None
        status = ctx.me.status
        await self.client.change_presence(status=status, activity=activity)
        if streaming:
            await ctx.checkmark()
            await ctx.send("Status set to <:status_streaming:840918373557600257> | `Streaming {streaming}`".format(streaming=streaming), delete_after=5)
        else:
            await ctx.checkmark()
            await ctx.send("Status cleared.", delete_after=5)
        await ctx.message.delete(delay=5)

    @checks.admoon()
    @status.command(name='clear', hidden=True)
    async def status_clear(self, ctx):
        """
        Clears bot's status.
        """
        status = ctx.me.status
        activity = None
        await self.client.change_presence(status=status, activity=activity)
        await ctx.checkmark()
        await ctx.send('Status cleared.', delete_after=5)
        await ctx.message.delete(delay=5)