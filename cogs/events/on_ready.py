import os

import discord
from discord.ext import commands
from .status_utils import check_status, get_custom_activity
from .status_task import check_status
from main import dvvt

class Ready(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
