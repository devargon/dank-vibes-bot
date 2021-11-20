import discord
from utils import checks
from discord.ext import commands, menus
from utils.buttons import *

class censor_list_pagination(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=20)

    async def format_page(self, menu, page):
        embed = discord.Embed(color=menu.ctx.bot.embed_color, title=self.title, timestamp=discord.utils.utcnow())
        embed.description = "\n".join(page)
        embed.set_footer(text="Content in this censor list is used for moderating echo-like commands in this bot, and will not auto delete messages with such blacklisted content.")
        return embed

class censor(commands.Cog):
    def __init__(self, client):
        self.client = client

    @checks.has_permissions_or_role(administrator=True)
    @commands.group(name='censor', invoke_without_command=True)
    async def censor(self, ctx, *, content: str = None):
        """
        Censor a word or phrase.
        To view the list of censored words, use `censor list`.
        To remove a censored word, use `censor remove`.
        """
        if content is None:
            return await ctx.send("You need to specify what you want to censor.")
        content = content.lower()
        if len(content) > 1000:
            return await ctx.send("You can only censor strings up to 1000 characters long.")
        existing = await self.client.pool_pg.fetchval("SELECT string FROM blacklisted_words WHERE string = $1", content)
        if existing:
            await ctx.send(f"`{content}` is already blacklisted.")
        else:
            await self.client.pool_pg.execute("INSERT INTO blacklisted_words(string) VALUES ($1)", content)
            await ctx.send(f"<:DVB_True:887589686808309791> `{content}` has been blacklisted.")

    @checks.has_permissions_or_role(administrator=True)
    @censor.command(name='list')
    async def censor_list(self, ctx):
        """
        List all blacklisted words.
        """
        entries = await self.client.pool_pg.fetch("SELECT string FROM blacklisted_words")
        if not entries:
            return await ctx.send("There are no blacklisted words.")
        blacklisted = [entry.get('string') for entry in entries]
        title = "Blacklisted Words"
        menu = menus.MenuPages(source=censor_list_pagination(blacklisted, title), clear_reactions_after=True)
        await menu.start(ctx)

    @checks.has_permissions_or_role(administrator=True)
    @censor.command(name='add', aliases=['+'])
    async def censor_add(self, ctx, *, content: str = None):
        """
        Censor a word or phrase.
        """
        if content is None:
            return await ctx.send("You need to specify what you want to censor.")
        content = content.lower()
        if len(content) > 1000:
            return await ctx.send("You can only censor strings up to 1000 characters long.")
        existing = await self.client.pool_pg.fetchval("SELECT string FROM blacklisted_words WHERE string = $1", content)
        if existing:
            await ctx.send(f"`{content}` is already blacklisted.")
        else:
            await self.client.pool_pg.execute("INSERT INTO blacklisted_words(string) VALUES ($1)", content)
            await ctx.send(f"<:DVB_True:887589686808309791> `{content}` has been blacklisted.")

    @checks.has_permissions_or_role(administrator=True)
    @censor.command(name='remove', aliases=['delete', '-'])
    async def censor_remove(self, ctx, *, content: str = None):
        """
        Removes a word or phrase from being censored by Dank Vibes Bot.
        """
        if content is None:
            return await ctx.send("You need to specify what you want to censor.")
        if len(content) > 1000:
            return await ctx.send("You can only censor strings up to 1000 characters long.")
        existing = await self.client.pool_pg.fetchval("SELECT string FROM blacklisted_words WHERE string = $1", content)
        if existing:
            await self.client.pool_pg.execute("DELETE FROM blacklisted_words WHERE string = $1", content)
            await ctx.send(f"<:DVB_True:887589686808309791> `{content}` has been removed from the blacklist.")
        else:
            await ctx.send(f"`{content}` is already not blacklisted!")