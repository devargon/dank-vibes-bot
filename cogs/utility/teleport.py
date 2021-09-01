import re
import discord
from utils import checks
from discord.ext import commands, menus
from utils.menus import CustomMenu

class get_checkpoint_pages(menus.ListPageSource):
    def __init__(self, data, author):
        self.data = data
        self.author = author
        super().__init__(data, per_page=20)
    
    async def format_page(self, menu, entries):
        embed = discord.Embed(color=0x57F0F0)
        embed.set_author(name=f"{self.author.name}'s checkpoints", icon_url=self.author.avatar_url)
        embed.description = "\n".join(f"• {entry[0]}: {entry[1]}" for entry in entries)
        return embed

class Teleport(commands.Cog):
    def __init___(self, client):
        self.client = client

    @checks.has_permissions_or_role(administrator=True)
    @commands.group(name='teleport', aliases=['tp'], invoke_without_command=True, usage='<checkpoint_name>')
    async def teleport(self, ctx, checkpoint: str = None):
        """
        Teleport between your saved checkpoints.
        """
        if checkpoint is None:
            return await ctx.send("You need to include a checkpoint name.")
        if not (channel_id := await self.client.pool_pg.fetchval("SELECT channel_id FROM teleport WHERE member_id=$1 AND checkpoint=$2", ctx.author.id, checkpoint.lower())):
            return await ctx.send("I don't have any channel saved for that checkpoint.")
        channel = f"<#{channel_id}>"
        await ctx.send(channel, delete_after=5)

    @teleport.command(name='add', usage="<checkpoint_name> <channel>")
    async def teleport_add(self, ctx, checkpoint: str = None, channel: str = None):
        """
        Adds a checkpoint.
        """
        if checkpoint is None:
            return await ctx.send("You need to include a checkpoint name.")
        if channel is None:
            return await ctx.send("Mention a valid channel for your checkpoint.")
        if await self.client.pool_pg.fetchval("SELECT * FROM teleport WHERE member_id=$1 AND checkpoint=$2", ctx.author.id, checkpoint.lower()):
            return await ctx.send("You already have a checkpoint with that name.")
        channel_re = re.compile(r"<#(?P<id>\d+)>")
        if len(channel) == 18 and channel.isdigit():
            channel_id = channel
        elif (ids := channel_re.findall(channel)):
            channel_id = ids[0]
        else:
            return await ctx.send("You didn't mention a valid channel, try again!")
        await self.client.pool_pg.execute("INSERT INTO teleport VALUES ($1, $2, $3)", ctx.author.id, checkpoint.lower(), int(channel_id))
        await ctx.send("Checkpoint added.")
    
    @teleport.command(name='remove', usage="<checkpoint_name>")
    async def teleport_remove(self, ctx, checkpoint: str = None):
        """
        Removes a checkpoint.
        """
        if checkpoint is None:
            return await ctx.send("You need to include a checkpoint name.")
        if not await self.client.pool_pg.fetchval("SELECT * FROM teleport WHERE member_id=$1 AND checkpoint=$2", ctx.author.id, checkpoint.lower()):
            return await ctx.send("You don't have any checkpoint saved with that name.")
        await self.client.pool_pg.execute("DELETE FROM teleport WHERE member_id=$1 AND checkpoint=$2", ctx.author.id, checkpoint.lower())
        await ctx.send("Checkpoint removed.")
    
    @teleport.command(name='list')
    async def teleport_list(self, ctx):
        """
        Shows all checkpoints and channels.
        """
        results = await self.client.pool_pg.fetch("SELECT checkpoint, channel_id FROM teleport WHERE member_id=$1", ctx.author.id)
        if len(results) == 0:
            return await ctx.send("You don't have any checkpoint saved.")
        checkpoints = []
        for result in results:
            checkpoint = result.get('checkpoint')
            channel_id = result.get('channel_id')
            checkpoints.append((checkpoint, f"<#{channel_id}>"))
        pages = CustomMenu(source=get_checkpoint_pages(checkpoints, ctx.author), clear_reactions_after=True, timeout=60)
        await pages.start(ctx)
        return await ctx.checkmark()

    @teleport.command(name='clear', aliases=['reset'])
    async def teleport_clear(self, ctx):
        """
        Removes all checkpoints.
        """
        await self.client.pool_pg.execute("DELETE FROM teleport WHERE member_id=$1", ctx.author.id)
        await ctx.checkmark()
        return await ctx.send("All checkpoints have been removed.")