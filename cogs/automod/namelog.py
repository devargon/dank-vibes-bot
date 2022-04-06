import discord
from discord.ext import commands
from time import time

class NameLogging(commands.Cog):
    def __init__(self, client):
        self.client = client

    # nickname changes are recorded in verification

    @commands.Cog.listener()
    async def on_user_update(self, user_before, user_after):
        if user_before.name != user_after.name:
            new_name = user_after.name
            await self.client.db.execute("INSERT INTO name_changes VALUES($1, $2, $3)", user_before.id, new_name, round(time()))