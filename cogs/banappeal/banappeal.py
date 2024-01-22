import html
import random
from datetime import timedelta, datetime

import discord
import asyncio
import contextlib

import typing

import server
from aiohttp import web

from cogs.banappeal.banappealdb import BanAppealDB
from main import dvvt
from utils.time import humanize_timedelta
from utils.format import proper_userf, print_exception
from utils import checks
from utils.buttons import *
from discord.ext import commands
from time import perf_counter
from .banappeal_discord import BanAppealDiscord
from .banappeal_server import BanAppealServer

server_id = 871734809154707467
banappeal_chn_id = 1194673636196491396

class BanAppeal(BanAppealServer, BanAppealDiscord, commands.Cog, name='banappeal'):
    """
    Banappeal commands
    """
    def __init__(self, client):
        self.client = client
        self.server = server.HTTPServer(
            bot=self.client,
            host="0.0.0.0",
            port=5003,
        )
        self.client.loop.create_task(self._start_server())

    async def _start_server(self):
        await self.client.wait_until_ready()
        print("Starting custom Web Server for port 5003")
        await self.server.start()



    @checks.is_dvbm()
    @commands.command(name='bbon')
    async def bbon(self, ctx, member: discord.Member = None):
        await ctx.send("An unexpected error occurred.", delete_after=5)
