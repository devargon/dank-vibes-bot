import discord
from typing import Union
from discord.ext import commands, menus
from utils.menus import CustomMenu
from utils import checks


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
            return await ctx.send("Checkpoint name is a required argument.")
        if not (channel_id := await self.client.pool_pg.fetchval("SELECT channel_id FROM teleport WHERE member_id=$1 AND checkpoint=$2", ctx.author.id, checkpoint.lower())):
            return await ctx.send("I don't have any channel saved for that checkpoint.")
        channel = self.client.get_channel(channel_id)
        if not channel:
            return await ctx.send("I couldn't find a channel with that id.")
        await ctx.send(channel.mention, delete_after=5)

    @teleport.command(name='add', usage="<checkpoint_name> <channel>")
    async def teleport_add(self, ctx, checkpoint: str = None, channel: Union[discord.TextChannel, discord.VoiceChannel] = None):
        """
        Adds a checkpoint.
        """
        if checkpoint is None:
            return await ctx.send("Checkpoint name is a required argument.")
        if channel is None:
            return await ctx.send("Channel is a required argument.")
        if await self.client.pool_pg.fetchval("SELECT * FROM teleport WHERE member_id=$1 AND checkpoint=$2", ctx.author.id, checkpoint.lower()):
            return await ctx.send("You already have a checkpoint with that name.")
        await self.client.pool_pg.execute("INSERT INTO teleport VALUES ($1, $2, $3)", ctx.author.id, checkpoint.lower(), channel.id)
        await ctx.send("Checkpoint added.")
    
    @teleport.command(name='remove', usage="<checkpoint_name>")
    async def teleport_remove(self, ctx, checkpoint: str = None):
        """
        Removes a checkpoint.
        """
        if checkpoint is None:
            return await ctx.send("Checkpoint name is a required argument.")
        if not await self.client.pool_pg.fetchval("SELECT * FROM teleport WHERE member_id=$1 AND checkpoint=$2", ctx.author.id, checkpoint.lower()):
            return await ctx.send("You don't have any checkpoint saved with that name.")
        await self.client.pool_pg.execute("DELETE FROM teleport WHERE member_id=$1, AND checkpoint=$2", ctx.author.id, checkpoint.lower())
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
            channel = self.client.get_channel(channel_id)
            channel = channel.mention if channel else f"<#{channel_id}>"
            checkpoints.append((checkpoint, channel))
        checkpoints = [(result.get('checkpoint'), self.client.get_channel(result.get('channel_id')).mention) for result in results]
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