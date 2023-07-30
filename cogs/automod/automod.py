import contextlib
import time
from datetime import timedelta

import discord
from discord.ext import commands, tasks

from utils.context import DVVTcontext
from utils.format import human_join
from .amari_task import AmariTask
from .freezenick import Freezenick
from .timedrole import timedrole
from .timedunlock import TimedUnlock
from .namelog import NameLogging
from .timer import timer
from .status import AutoStatus
from .editpoll import polledition
from .reminders import reminders_
from .commandcleanup import CommandCleanup
from .watchlist import WatchList
from abc import ABC
import os

level_50_role = 944519459580821524 if os.getenv('state') == '0' else 943883516565942352


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """
    pass


class AutoMod(AmariTask, reminders_, polledition, AutoStatus, timer, NameLogging, timedrole, TimedUnlock, Freezenick, CommandCleanup, WatchList, commands.Cog):
    """
    This file is just a placeholder for the various automod functions/modules.
    """
    def __init__(self, client):
        self.client = client
        self.freezenick.start()
        self.amari_task.start()
        self.timedrole.start()
        self.unlock.start()
        self.timer_loop.start()
        self.change_status.start()
        self.edit_polls.start()
        self.reminder_check.start()
        self.daily_potion_reset.start()
        self.status = None
        self.received_daily_potion = []
        self.limit = {} # for commandcleanup

    async def add_item_count(self, item, user, amount):
        does_inventory_exist = await self.client.db.fetchrow("SELECT * FROM inventories WHERE user_id = $1",
                                                                  user.id)
        useritem_query = "SELECT {} FROM inventories WHERE user_id = $1".format(item)
        useritem = await self.client.db.fetchval(useritem_query, user.id)
        if does_inventory_exist:
            if useritem is None:
                useritem_query = "UPDATE inventories SET {} = $2 WHERE user_id = $1 RETURNING {}".format(item, item)
            else:
                useritem_query = "UPDATE inventories SET {} = {} + $2 WHERE user_id = $1 RETURNING {}".format(item, item, item)
        else:
            useritem_query = "INSERT INTO inventories (user_id, {}) VALUES ($1, $2) RETURNING {}".format(item, item)
        return await self.client.db.fetchval(useritem_query, user.id, amount, column=item)

    @commands.Cog.listener()
    async def on_command(self, ctx: DVVTcontext):
        if ctx.guild is None:
            return
        if ctx.author.id not in self.received_daily_potion:
            entry = await self.client.db.fetchrow("SELECT * FROM userconfig WHERE user_id = $1", ctx.author.id)
            if entry is None:
                if discord.utils.get(ctx.author.roles, id=level_50_role):
                    await self.client.db.execute("INSERT INTO userconfig (user_id, received_daily_potion) VALUES ($1, $2)", ctx.author.id, True)
                    self.received_daily_potion = self.received_daily_potion + [ctx.author.id]
                    await self.add_item_count('dumbfightpotion', ctx.author, 1)
                    try:
                        await ctx.reply("You have received `1` Dumbfight Potion as you're currently **Level 50** and above!")
                    except discord.HTTPException:
                        await ctx.send("You have received `1` Dumbfight Potion as you're currently **Level 50** and above!")
            elif entry.get('received_daily_potion') is not True:
                if discord.utils.get(ctx.author.roles, id=level_50_role):
                    await self.client.db.execute("UPDATE userconfig SET received_daily_potion = $1 WHERE user_id = $2", True, ctx.author.id)
                    await self.add_item_count('dumbfightpotion', ctx.author, 1)
                    self.received_daily_potion.append(ctx.author.id)
                    try:
                        await ctx.reply("You have received `1` Dumbfight Potion as you're currently **Level 50** and above!")
                    except discord.HTTPException:
                        await ctx.send("You have received `1` Dumbfight Potion as you're currently **Level 50** and above!")
            elif entry.get('received_daily_potion') is True:
                self.received_daily_potion = self.received_daily_potion + [ctx.author.id]
            else:
                pass
        item_active_durations = await self.client.db.fetchrow("SELECT dumbfight_rig_duration, snipe_res_duration FROM userconfig WHERE user_id = $1", ctx.author.id)
        effects_worn_off = []
        if item_active_durations is not None:
            if item_active_durations.get('dumbfight_rig_duration') is not None and item_active_durations.get('dumbfight_rig_duration') < time.time():
                effects_worn_off.append('**Dumbfight Potion**')
                await self.client.db.execute("UPDATE userconfig SET dumbfight_rig_duration = NULL, dumbfight_result = NULL WHERE user_id = $1", ctx.author.id)
            if item_active_durations.get('snipe_res_duration') is not None and item_active_durations.get('snipe_res_duration') < time.time():
                effects_worn_off.append('**Snipe Pill**')
                await self.client.db.execute("UPDATE userconfig SET snipe_res_duration = NULL, snipe_res_result = NULL WHERE user_id = $1", ctx.author.id)
            if len(effects_worn_off) > 0:
                m = f"> **{ctx.author.name}**, the effects of the {human_join(effects_worn_off, final='and')} has worn off."
                try:
                    await ctx.reply(m)
                except Exception as e:
                    await ctx.send(m)

    @tasks.loop(hours=24)
    async def daily_potion_reset(self):
        self.received_daily_potion = []
        await self.client.db.execute("UPDATE userconfig SET received_daily_potion = $1", False)

    @daily_potion_reset.before_loop
    async def wait_until_8am(self):
        await self.client.wait_until_ready()
        now = discord.utils.utcnow()
        next_run = now.replace(hour=0, minute=0, second=0)
        if next_run < now:
            next_run += timedelta(days=1)
        await discord.utils.sleep_until(next_run)


    @commands.Cog.listener()
    async def on_ready(self):
        pass

    def cog_unload(self):
        self.freezenick.stop()
        self.timedrole.stop()
        self.unlock.start()
        self.timer_loop.stop()
        self.change_status.stop()
        self.edit_polls.cancel()