import os

import discord
from discord.ext import commands
from main import dvvt

class Ready(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
