import html
import os

import bleach
import discord

from .banappealdb import BanAppealDB, BanAppeal
from datetime import datetime, timedelta
import asyncio
import contextlib
from discord.ext import commands
from main import dvvt
import server
from aiohttp import web

from utils.format import print_exception

server_id = 1200400184748802168 if "preproduction" in os.getenv("APPEALS_SERVER_HOST") else 1288032530569625660 if "banappeal." in os.getenv("APPEALS_SERVER_HOST") else 871734809154707467
banappeal_chn_id = 1200705116857176135 if "preproduction" in os.getenv("APPEALS_SERVER_HOST") else 1345459131204505691 if "banappeal." in os.getenv("APPEALS_SERVER_HOST") else 1194673636196491396
modlog_chn_id = 1200707746622869535 if "preproduction" in os.getenv("APPEALS_SERVER_HOST") else 1317868064469028874 if "banappeal." in os.getenv("APPEALS_SERVER_HOST") else 999661054067998720

def status_400(data: dict):
    return web.json_response(data=data, status=400)

def status_500(data: dict):
    return web.json_response(data=data, status=500)


ban_cache = {}


class BanAppealServer(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
        self.server = server.HTTPServer(
            bot=self.client,
            host="0.0.0.0",
            port=5003,
        )
        self.client.loop.create_task(self._start_server())

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        print("Caught a ban!")
        current_time = datetime.now()

        if guild.id not in ban_cache:
            ban_cache[guild.id] = {}
        ban_obj = await guild.fetch_ban(user)

        ban_cache[guild.id][user.id] = ({"is_banned": True, "ban_reason": ban_obj.reason}, current_time)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        print("Caught an unban!")
        current_time = datetime.now()

        if guild.id not in ban_cache:
            ban_cache[guild.id] = {}
        ban_cache[guild.id][user.id] = ({"is_banned": False}, current_time)


    async def _start_server(self):
        await self.client.wait_until_ready()
        print("Starting custom Web Server for port 5003")
        await self.server.start()

    @server.add_route(path="/api/user", method="GET", cog="BanAppeal")
    async def get_user_details(self: dvvt, request: web.Request):
        if request.headers.get("authorization") != os.getenv("APPEALS_SHARED_SECRET"):
            return web.json_response(data={"error": "Unauthorized request"}, status=401)

        banappealdb = BanAppealDB(self.db)
        user_id = request.query.get("id")
        if user_id is None:
            return status_400({"error": "id query is required"})

        try:
            user_id = int(user_id)
        except ValueError:
            return status_400({"error": "id is not a number"})

        obj = discord.Object(user_id)
        guild = self.get_guild(server_id)
        if guild is None:
            web.json_response(data={"error": "INTERNAL SERVER ERROR"}, status=500)
            raise ValueError("Guild could not be fetched for /api/user")

        cache_validity = timedelta(minutes=7)
        current_time = datetime.now()
        cached_ban = ban_cache.get(guild.id, {}).get(user_id)

        # Check if cached data is valid
        if cached_ban and (current_time - cached_ban[1]) < cache_validity:
            data = {"ban": cached_ban[0]}
        else:
            # Fetch new ban data
            try:
                ban = await guild.fetch_ban(obj)
                ban_details = {"is_banned": True, "ban_reason": ban.reason}
                data = {"ban": ban_details}
                # Update cache
                if guild.id not in ban_cache:
                    ban_cache[guild.id] = {}
                ban_cache[guild.id][user_id] = (ban_details, current_time)
            except discord.NotFound:
                # User not banned, update cache accordingly
                if guild.id not in ban_cache:
                    ban_cache[guild.id] = {}
                ban_cache[guild.id][user_id] = ({"is_banned": False}, current_time)
                data = {"ban": {"is_banned": False}}
        if data.get("ban").get("is_banned") is not True and user_id == 312876934755385344:
            ban_appeals = await banappealdb.get_all_ban_appeals(100)
        else:
            ban_appeals = await banappealdb.get_user_all_ban_appeals(user_id)
        data['past_appeals'] = [banappeal.to_presentable_format() for banappeal in ban_appeals]

        print(data)
        return web.json_response(data=data, status=200)

    @server.add_route(path="/api/appeals/{user_id:\d+}/{appeal_id:\d+}", method="GET", cog="BanAppeal")
    async def get_an_appeal(self: dvvt, request: web.Request):
        if request.headers.get("authorization") != os.getenv("APPEALS_SHARED_SECRET"):
            return web.json_response(data={"error": "Unauthorized request"}, status=401)

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
        if banappeal.user_id != user_id and user_id != 312876934755385344:
            return web.json_response(status=404, data={"Error": f"Ban appeal with ID {appeal_id} not found"})
        return web.json_response(data=banappeal.to_presentable_format(), status=200)

    @server.add_route(path="/api/appeal/{appeal_id:\d+}", method="PUT", cog="BanAppeal")
    async def update_appeal(self: dvvt, request: web.Request):
        if request.headers.get("authorization") != os.getenv("APPEALS_SHARED_SECRET"):
            return web.json_response(data={"error": "Unauthorized request"}, status=401)

        appeal_id = request.match_info['appeal_id']
        if appeal_id is None:
            return status_400({"error": "Invalid parameters provided"})
        if (appeal_id := int(appeal_id)) is None:
            return status_400({"error": "Invalid parameters provided"})
        if request.content_type == 'application/json':
            data = await request.json()
        elif request.content_type == 'application/x-www-form-urlencoded' or request.content_type == 'multipart/form-data':
            data = await request.post()
        else:
            return status_400(data={"error": "Unsupported content type"})
        user_id = data.get('user_id')  # Add this after frontend submits, before backend submits
        if user_id is None:
            return status_400(data={"error": "id query is required"})
        banappealdb = BanAppealDB(self.db)
        try:
            user_id = int(user_id)
        except ValueError:
            return status_400(data={"error": "id is not a number"})
        ban_appeal = await banappealdb.get_ban_appeal_by_appeal_id(appeal_id)
        if ban_appeal is None or ban_appeal.user_id != user_id:
            return web.json_response(data={"error": "Ban appeal not found"}, status=404)
        if ban_appeal.appeal_status != 0:
            return web.json_response(data={"error": "Ban appeal is already reviewed"}, status=404)
        appeal_answer1 = data.get('appeal_answer1')
        appeal_answer2 = data.get('appeal_answer2')
        appeal_answer3 = data.get('appeal_answer3')
        if isinstance(appeal_answer1, str) and appeal_answer1.strip():
            ban_appeal.appeal_answer1 = html.escape(appeal_answer1).strip()[:1024]
        if isinstance(appeal_answer2, str) and appeal_answer2.strip():
            ban_appeal.appeal_answer2 = html.escape(appeal_answer2).strip()[:1024]
        if isinstance(appeal_answer3, str) and appeal_answer3.strip():
            ban_appeal.appeal_answer3 = html.escape(appeal_answer3).strip()[:1024]
        try:
            input_email = data['email']
        except KeyError:
            pass
        else:
            if type(input_email) == str:
                ban_appeal.email = input_email.strip()
            else:
                ban_appeal.email = None
        print("Among us")
        try:
            await banappealdb.update_ban_appeal(ban_appeal)
        except Exception as e:
            print_exception("Exception while updating appeal", e)
            return status_500(data={"error": "An error occured while trying to update your appeal."})
        else:
            return web.json_response(data={"appeal_id": ban_appeal.appeal_id}, status=200)

    @server.add_route(path="/api/appeal", method="POST", cog="BanAppeal")
    async def post_appeal(self: dvvt, request: web.Request):
        if request.headers.get("authorization") != os.getenv("APPEALS_SHARED_SECRET"):
            return web.json_response(data={"error": "Unauthorized request"}, status=401)

        if request.content_type == 'application/json':
            data = await request.json()
        elif request.content_type == 'application/x-www-form-urlencoded' or request.content_type == 'multipart/form-data':
            data = await request.post()
        else:
            return status_400(data={"error": "Unsupported content type"})
        user_id = data.get('user_id')  # Add this after frontend submits, before backend submits
        if user_id is None:
            return status_400(data={"error": "id query is required"})
        banappealdb = BanAppealDB(self.db)
        try:
            user_id = int(user_id)
        except ValueError:
            return status_400(data={"error": "id is not a number"})
        user_ban_appeals = await banappealdb.get_user_all_ban_appeals(user_id)
        if len(user_ban_appeals) > 0:
            most_recent_appeal = user_ban_appeals[0]
            if most_recent_appeal.appeal_status == 0:
                return status_400(data={
                    "error": "Your current appeal is still Pending. Patiently wait for moderators to review it.",
                    "appeal_id": most_recent_appeal.appeal_id})
            if discord.utils.utcnow() - most_recent_appeal.appeal_timestamp <= timedelta(days=30):
                return status_400(data={
                    "error": "You've recently submitted an appeal. You can make a new appeal 30 days after your previous one.",
                    "next_appeal_dt": (most_recent_appeal.appeal_timestamp + timedelta(days=30)).isoformat()})
        appealer = await self.get_or_fetch_user(user_id)
        guild = self.get_guild(server_id)
        if guild is None:
            status_500(data={"error": "INTERNAL SERVER ERROR"})
            raise ValueError("Guild could not be fetched for /api/appeal")
        try:
            ban = await guild.fetch_ban(appealer or discord.Object(user_id))
        except discord.NotFound:
            return status_400(data={"error": "You are currently not banned."})
        except (discord.Forbidden, discord.HTTPException) as e:
            print_exception("Error while fetching ban", e)
            return status_500(data={"error": "I am unable to check if you're banned at the moment."})
        ban_reason = ban.reason or "Not specified"
        if ban_reason == "Account too young" or ban_reason == "Dungeon auto-ban":
            version = 2
        else:
            version = 1

        if version == 1:
            appeal_answer1 = data.get('appeal_answer1')
            appeal_answer2 = data.get('appeal_answer2')
            appeal_answer3 = data.get('appeal_answer3')
            if appeal_answer1 is None or appeal_answer2 is None or appeal_answer3 is None:
                return status_400(data={"error": "You did not fill up all of the required fields."})
            appeal_answer1 = bleach.clean(appeal_answer1, strip=True)[:1024]
            appeal_answer2 = bleach.clean(appeal_answer2, strip=True)[:1024]
            appeal_answer3 = bleach.clean(appeal_answer3, strip=True)[:1024]



            new_appeal_id = await banappealdb.add_new_ban_appeal(user_id, ban_reason, appeal_answer1, appeal_answer2,
                                                                 appeal_answer3, version, discord.utils.utcnow() + timedelta(days=7))

        elif version == 2:
            appeal_answer3 = data.get('appeal_answer3')
            appeal_answer3 = bleach.clean(appeal_answer3, strip=True)[:1024]
            if appeal_answer3 is None:
                return status_400(data={"error": "You did not fill up all of the required fields."})
            if (account_create_duration := discord.utils.utcnow() - appealer.created_at) <= timedelta(days=10):  # Account is less than 10 days old
                time_until_dungeon_off = timedelta(days=10) - account_create_duration
                review_by = discord.utils.utcnow() + time_until_dungeon_off + (timedelta(days=5) if time_until_dungeon_off > timedelta(days=2) else timedelta(days=7))
            else:
                review_by = discord.utils.utcnow() + timedelta(days=7)

            new_appeal_id = await banappealdb.add_new_ban_appeal(user_id, ban_reason, "PLACEHOLDER", "PLACEHOLDER",
                                                                 appeal_answer3, version, review_by)
        else:
            new_appeal_id = None
        if new_appeal_id:
            new_appeal = await banappealdb.get_ban_appeal_by_appeal_id(new_appeal_id)
            cog = self.get_cog('banappeal')
            cog.discordBanAppealPostQueue.append(new_appeal)
            return web.json_response(data={"appeal_id": new_appeal_id},
                                     status=200)  # on frontend, I want a query thing showing if it's newly posted if EJS can't provide that functionality
        else:
            return status_500(data={"error": "An error occured while trying to post your new appeal."})

    @server.add_route(path="/", method="GET", cog="BanAppeal")
    async def home(self: dvvt, request):
        if request.headers.get("authorization") != os.getenv("APPEALS_SHARED_SECRET"):
            return web.json_response(data={"error": "Unauthorized request"}, status=401)

        print(dir(self))
        print(type(self.user.name))
        return web.json_response(status=404)

    @server.add_route(path="/check-queue", method="GET", cog="BanAppeal")
    async def check_queue(self: dvvt, request):
        if request.headers.get("authorization") != os.getenv("APPEALS_SHARED_SECRET"):
            return web.json_response(data={"error": "Unauthorized request"}, status=401)

        cog = self.get_cog('banappeal')
        data = {
            "post_queue": [i.to_full_format() for i in cog.discordBanAppealPostQueue],
            "update_queue": [i.to_full_format() for i in cog.discordBanAppealUpdateQueue]
        }
        return web.json_response(data=data, status=200)
