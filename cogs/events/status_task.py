import os

import discord
from discord.ext import commands, tasks
from .status_utils import check_status, get_custom_activity

from main import dvvt

guild_id = 871734809154707467 if os.getenv('state') == '1' else 595457764935991326

class StatusTasks(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client