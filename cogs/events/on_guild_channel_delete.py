import asyncio

import discord
from discord.ext import commands
from main import dvvt

class GuildChannelDelete(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client