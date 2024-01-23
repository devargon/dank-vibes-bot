import discord
from .banappealdb import BanAppealDB, BanAppeal
from datetime import datetime, timedelta
import asyncio
import contextlib
from discord.ext import commands
from main import dvvt

class BanAppealDiscord(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client




