import contextlib
import time
from datetime import timedelta

import discord
from discord.ext import commands, tasks

from utils.context import DVVTcontext
from .freezenick import Freezenick
from .verification import Verification
from .timedrole import timedrole
from .timedunlock import TimedUnlock
from .namelog import NameLogging
from .timer import timer
from .status import AutoStatus
from .editpoll import polledition
from .reminders import reminders_
from abc import ABC
import os
from utils import checks

verify_role = 911541857807384677
level_50_role = 678318507016060948 if os.getenv('state') == '0' else 943883516565942352

class verifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="✅", label="Verify", style=discord.ButtonStyle.blurple, custom_id='dv:verify')
    async def verifybutton(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send("<a:DVB_Loading:909997219644604447> Verifying you...", ephemeral=True)
        verifyrole = interaction.guild.get_role(verify_role)
        if verifyrole:
            await interaction.user.remove_roles(verifyrole)
        roleids = [905980110954455070, 905980110157541446, 905980109268324402, 905980108148461599, 905980107435442186] \
            if os.getenv('state') == '1' else \
            [837591810389442600, 671426678807068683, 671426686100963359, 671426692077584384, 649499248320184320]
        roles = [interaction.guild.get_role(roleid) for roleid in roleids]
        for role in roles:
            if role not in interaction.user.roles:
                await interaction.user.add_roles(role, reason="User completed manual verification")
        await interaction.followup.send("You've been verified! You should now be able to talk.", ephemeral=True)

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """
    pass


class AutoMod(reminders_, polledition, AutoStatus, timer, NameLogging, timedrole, TimedUnlock, Verification, Freezenick, commands.Cog):
    """
    This file is just a placeholder for the various automod functions/modules.
    """
    def __init__(self, client):
        self.client = client
        self.freezenick.start()
        self.check_verification.start()
        self.timedrole.start()
        self.unlock.start()
        self.timer_loop.start()
        self.change_status.start()
        self.edit_polls.start()
        self.reminder_check.start()
        self.daily_potion_reset.start()
        self.verifyview = False
        self.status = None
        self.received_daily_potion = []

    async def add_item_count(self, item, user, amount):
        does_inventory_exist = await self.client.pool_pg.fetchrow("SELECT * FROM inventories WHERE user_id = $1",
                                                                  user.id)
        useritem_query = "SELECT {} FROM inventories WHERE user_id = $1".format(item)
        useritem = await self.client.pool_pg.fetchval(useritem_query, user.id)
        if does_inventory_exist:
            if useritem is None:
                useritem_query = "UPDATE inventories SET {} = $2 WHERE user_id = $1 RETURNING {}".format(item, item)
            else:
                useritem_query = "UPDATE inventories SET {} = {} + $2 WHERE user_id = $1 RETURNING {}".format(item, item, item)
        else:
            useritem_query = "INSERT INTO inventories (user_id, {}) VALUES ($1, $2) RETURNING {}".format(item, item)
        return await self.client.pool_pg.fetchval(useritem_query, user.id, amount, column=item)

    @commands.Cog.listener()
    async def on_command(self, ctx: DVVTcontext):
        if ctx.author.id not in self.received_daily_potion:
            entry = await self.client.pool_pg.fetchrow("SELECT * FROM userconfig WHERE user_id = $1", ctx.author.id)
            if entry is None:
                if discord.utils.get(ctx.author.roles, id=level_50_role):
                    await self.client.pool_pg.execute("INSERT INTO userconfig (user_id, received_daily_potion) VALUES ($1, $2)", ctx.author.id, True)
                    self.received_daily_potion = self.received_daily_potion + [ctx.author.id]
                    await self.add_item_count('dumbfightpotion', ctx.author, 1)
                    await ctx.reply("You have received `1` Dumbfight Potion as you're currently **Level 50**!")
            elif entry.get('received_daily_potion') is not True:
                if discord.utils.get(ctx.author.roles, id=level_50_role):
                    await self.client.pool_pg.execute("UPDATE userconfig SET received_daily_potion = $1 WHERE user_id = $2", True, ctx.author.id)
                    await self.add_item_count('dumbfightpotion', ctx.author, 1)
                    self.received_daily_potion.append(ctx.author.id)
                    await ctx.reply("You have received `1` Dumbfight Potion as you're currently **Level 50**!")
            elif entry.get('received_daily_potion') is True:
                self.received_daily_potion = self.received_daily_potion + [ctx.author.id]
            else:
                pass
        if (duration := await self.client.pool_pg.fetchval("SELECT dumbfight_rig_duration FROM userconfig WHERE user_id = $1", ctx.author.id)) is not None:
            if duration < time.time():
                await self.client.pool_pg.execute("UPDATE userconfig SET dumbfight_rig_duration = NULL, dumbfight_result = NULL WHERE user_id = $1", ctx.author.id)
                with contextlib.suppress(discord.HTTPException):
                    await ctx.reply(f"> **{ctx.author.name}**, the effects of the dumbfight potion has worn off.")

    @tasks.loop(hours=24)
    async def daily_potion_reset(self):
        self.received_daily_potion = []
        await self.client.pool_pg.execute("UPDATE userconfig SET received_daily_potion = $1", False)

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
        if not self.verifyview == True:
            self.client.add_view(verifyView())
            self.verifyview = True

    def cog_unload(self):
        self.freezenick.stop()
        self.check_verification.stop()
        self.timedrole.stop()
        self.unlock.start()
        self.timer_loop.stop()
        self.change_status.stop()
        self.edit_polls.cancel()