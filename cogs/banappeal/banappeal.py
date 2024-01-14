import html
import random
from datetime import timedelta

import discord
import asyncio
import contextlib

import typing

import server
from aiohttp import web

from cogs.banappeal.banappealdb import BanAppealDB
from main import dvvt
from utils.time import humanize_timedelta
from utils.format import proper_userf
from utils import checks
from utils.buttons import *
from discord.ext import commands
from time import perf_counter

server_id = 871734809154707467
banappeal_chn_id = 1194673636196491396

def status_400(data: dict):
    return web.json_response(data=data, status=400)

def status_500(data: dict):
    return web.json_response(data=data, status=500)


class BanAppeal(commands.Cog, name='banappeal'):
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


    @server.add_route(path="/api/user", method="GET", cog="BanAppeal")
    async def get_user_details(self: dvvt, request: web.Request):
        user_id = request.query.get("id")
        if user_id is None:
            return status_400({"error": "id query is required"})
        banappealdb = BanAppealDB(self.db)
        try:
            user_id = int(user_id)
        except ValueError:
            return status_400({"error": "id is not a number"})
        obj = discord.Object(user_id)
        guild = self.get_guild(server_id)
        if guild is None:
            web.json_response(data={"error": "INTERNAL SERVER ERROR"}, status=500)
            raise ValueError("Guild could not be fetched for /api/user")
        data = {'past_appeals': [], "ban": {"is_banned": False, "ban_reason": None}}
        try:
            ban = await guild.fetch_ban(obj)
            data["ban"]["is_banned"] = True
            data["ban"]["ban_reason"] = ban.reason
        except discord.NotFound:
            # do something here??
            print(":")
        else:
            ban_appeals = await banappealdb.get_user_all_ban_appeals(user_id)
            for banappeal in ban_appeals:
                data['past_appeals'].append(banappeal.to_public_dict())
        return web.json_response(data=data, status=200)

    @server.add_route(path="/api/appeals/{user_id:\d+}/{appeal_id:\d+}", method="GET", cog="BanAppeal")
    async def get_an_appeal(self: dvvt, request: web.Request):
        user_id = request.match_info['user_id']
        appeal_id = request.match_info['appeal_id']
        if user_id is None or appeal_id is None:
            return status_400({"error": "Invalid parameters provided"})
        if (user_id := int(user_id)) is None or (appeal_id := int(appeal_id)) is None:
            return status_400({"error": "Invalid parameters provided"})
        banappealdb = BanAppealDB(self.db)
        banappeal = await banappealdb.get_ban_appeal_by_appeal_id(appeal_id)
        if banappeal is None:
            return web.json_response(status=404, data={"Error": f"Ban appeal with ID {appeal_id} not found"})
        if banappeal.user_id != user_id:
            return web.json_response(status=404, data={"Error": f"Ban appeal with ID {appeal_id} not found"})
        return web.json_response(data=banappeal.to_presentable_format(), status=200)


    @server.add_route(path="/api/appeal", method="POST", cog="BanAppeal")
    async def post_appeal(self: dvvt, request: web.Request):
        if request.content_type == 'application/json':
            data = await request.json()
        elif request.content_type == 'application/x-www-form-urlencoded' or request.content_type == 'multipart/form-data':
            data = await request.post()
        else:
            # Unsupported content type
            response_text = "Unsupported content type"

            return status_400(data={"error": "Unsupported content type"})
        user_id = data.get('user_id') # Add this after frontend submits, before backend submits
        if user_id is None:
            return status_400(data={"error": "id query is required"})
        banappealdb = BanAppealDB(self.db)
        try:
            user_id = int(user_id)
        except ValueError:
            return status_400(data={"error": "id is not a number"})
        obj = discord.Object(user_id)
        guild = self.get_guild(server_id)
        if guild is None:
            status_500(data={"error": "INTERNAL SERVER ERROR"})
            raise ValueError("Guild could not be fetched for /api/appeal")
        try:
            ban = await guild.fetch_ban(obj)
        except discord.NotFound:
            return status_400(data={"error": "User is not currently banned"})
        ban_reason = ban.reason
        appeal_answer1 = data.get('appeal_answer1')
        appeal_answer2 = data.get('appeal_answer2')
        appeal_answer3 = data.get('appeal_answer3')
        if appeal_answer1 is None or appeal_answer2 is None or appeal_answer1 is None:
            return status_400(data={"error": "One or mmore appeal answers are invalid "})
        appeal_answer1 = html.escape(appeal_answer1)[:1024]
        appeal_answer2 = html.escape(appeal_answer2)[:1024]
        appeal_answer3 = html.escape(appeal_answer3)[:1024]
        latest_appeal = await banappealdb.get_user_latest_ban_appeal(user_id)
        print(latest_appeal)
        if latest_appeal:
            if latest_appeal.appeal_status == 0:
                return web.json_response(data={"error": "A ban appeal made by you is currently under review.", "appeal_id": latest_appeal.appeal_id})
            if (next_appeal_dt := (latest_appeal.appeal_timestamp +  timedelta(days=30))) > discord.utils.utcnow():
                return web.json_response(data={"error": "You have just made a ban appeal recently.", "next_appeal_dt": next_appeal_dt.isoformat()})
        await banappealdb.add_new_ban_appeal(user_id, ban_reason, appeal_answer1, appeal_answer2, appeal_answer3)
        return web.Response(status=200) # on frontend, I want a query thing showing if it's newly posted if EJS can't provide that functionality


    @server.add_route(path="/", method="GET", cog="BanAppeal")
    async def home(self: dvvt, request):
        print(dir(self))
        print(type(self.user.name))
        return web.json_response(data={"foo": f"{self.user.name}"}, status=200)

    @checks.is_dvbm()
    @commands.command(name='bbon')
    async def bbon(self, ctx, member: discord.Member = None):
        await ctx.send("An unexpected error occurred.", delete_after=5)

