import contextlib
import time
import asyncio
import discord
from discord import ui
import operator
from utils import checks, buttons
from datetime import datetime
from discord.ext import commands, tasks
from utils.format import print_exception, short_time
from .betting import betting
from utils.context import DVVTcontext
from utils.buttons import *

async def checkmark(message:discord.Message):
    try:
        await message.add_reaction("<:checkmark:841187106654519296>")
    except discord.NotFound:
        return None

async def clock(message:discord.Message):
    try:
        await message.add_reaction("⏰")
    except:
        return

def emojioutput(truefalse):  # shows the enabled or disabled emoji for 0 or 1 values
    if truefalse == 0:
        return "<:DVB_disabled:872003709096321024>"
    elif truefalse == 1:
        return "<:DVB_enabled:872003679895560193>"
    else:
        return "error"

def truefalse(value):  # shows the enabled or disabled emoji for 0 or 1 values
    return value == 1

async def crossmark(msg):
    await msg.add_reaction("<:crossmark:841186660662247444>")

def numberswitcher(no):
    if no == 1:
        return 0
    elif no == 0:
        return 1
    else:
        return 0

class VoteSetting(discord.ui.Select):
    def __init__(self, client, context, response):
        self.client = client
        self.response = response
        self.context = context
        options = [
            discord.SelectOption(label = "DM", description = f"{self.client.user.name} will DM you to remind you to perform Dank Memer commands.", emoji = discord.PartialEmoji.from_str("<:DVB_Letter:884743813166407701>"), default = False),
            discord.SelectOption(label = "Ping", description = f"{self.client.user.name} will ping you in the channel where you used Dank Memer.", emoji = discord.PartialEmoji.from_str("<:DVB_Ping:883744614295674950>"), default =False),
            discord.SelectOption(label = "None", description = f"{self.client.user.name} will not remind you for your Dank Memer reminders.", emoji = discord.PartialEmoji.from_str("<:DVB_None:884743780027219989>"), default = False)
        ]
        super().__init__(placeholder='Change how you want to be reminded...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "DM":
            await self.client.pool_pg.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 1, self.context.author.id)
            await interaction.response.send_message("Got it. You will **now be DMed** for your enabled Dank Memer reminders, **with the exception** of **short** reminders (such as `hunt`, `dig`), which will still be sent in channels.", ephemeral=True)
        if self.values[0] == "Ping":
            await self.client.pool_pg.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 2, self.context.author.id)
            await interaction.response.send_message("Got it. You will **now be pinged in the channel where you used the command** for your enabled Dank Memer reminders.", ephemeral=True)
        if self.values[0] == "None":
            await self.client.pool_pg.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 0, self.context.author.id)
            await interaction.response.send_message("Got it. You will **not be reminded** for your Dank Memer actions.", ephemeral=True)

class dankreminders(discord.ui.View):
    def __init__(self, ctx: DVVTcontext, client, rmtimes, timeout, daily, weekly, monthly, lottery, work, apple, donor, hunt, fish, di, highlow, se, search, crime, beg, dailybox, horseshoe, pizza, drop):
        self.value = None
        self.timeout = timeout
        self.context = ctx
        self.response = None
        self.result = None
        self.rmtimes = rmtimes
        self.client = client
        super().__init__(timeout=timeout)
        reminderemojis = ["<:DVB_calendar:873107952159059991>", "<:DVB_week:876711052669247528>",
                          "<:DVB_month:876711072030150707>", "<:DVB_lotteryticket:873110581085880321>",
                          "<:DVB_workbadge:873110507605872650>", "<:DVB_apple:876627457275469867>",
                          "<:DVB_patreon:876628017194082395>", "<:DVB_rifle:888404394805186571>",
                          "<:DVB_fishing:888404317638369330>", "<:DVB_shovel:888404340426031126>",
                          "🔢", "<a:DVB_snakeeyes:888404298608812112>", "<:DVB_search:888405048260976660>",
                          "<:DVB_Crime:888404653711192067>", "<:DVB_beg:888404456356610099>",
                          "<a:DVB_DailyBox:888404475470024785>", "<:DVB_Horseshoe:888404491647463454>",
                          "<:DVB_pizza:888404502280024145>", "<:DVB_sugarskull:904936096436215828>"]
        labels = ["Claim daily", "Claim weekly", "Claim monthly", "Enter the Lottery", "Work", "Use an apple",
                  "Redeem donor rewards", "Hunt", "Fish", "Dig", "Highlow", "Snakeeyes", "Search", "Crime", "Beg",
                  "Use a dailybox", "Use a horseshoe", "Use a pizza", "Get drop items"]
        is_enabled = [daily, weekly, monthly, lottery, work, apple, donor, hunt, fish, di, highlow, se, search, crime, beg, dailybox, horseshoe, pizza, drop]

        async def update_message(emoji):
            if str(emoji) == "<:DVB_calendar:873107952159059991>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET daily = $1 WHERE member_id = $2", numberswitcher(self.result.get('daily')), ctx.author.id)  # switches to enabled/disabled reminder
            elif str(emoji) == "<:DVB_lotteryticket:873110581085880321>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET lottery = $1 WHERE member_id = $2", numberswitcher(self.result.get('lottery')), ctx.author.id)
            elif str(emoji) == "<:DVB_workbadge:873110507605872650>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET work = $1 WHERE member_id = $2", numberswitcher(self.result.get('work')), ctx.author.id)
            elif str(emoji) == "<:DVB_week:876711052669247528>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET weekly = $1 WHERE member_id = $2", numberswitcher(self.result.get('weekly')), ctx.author.id)
            elif str(emoji) == "<:DVB_month:876711072030150707>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET monthly = $1 WHERE member_id = $2", numberswitcher(self.result.get('monthly')), ctx.author.id)
            elif str(emoji) == "<:DVB_apple:876627457275469867>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET apple = $1 WHERE member_id = $2", numberswitcher(self.result.get('apple')), ctx.author.id)
            elif str(emoji) == "<:DVB_patreon:876628017194082395>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET redeem = $1 WHERE member_id = $2", numberswitcher(self.result.get('redeem')), ctx.author.id)
            elif str(emoji) == "<:DVB_rifle:888404394805186571>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET hunt = $1 WHERE member_id = $2", numberswitcher(self.result.get('hunt')), ctx.author.id)
            elif str(emoji) == "<:DVB_fishing:888404317638369330>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET fish = $1 WHERE member_id = $2", numberswitcher(self.result.get('fish')), ctx.author.id)
            elif str(emoji) == "<:DVB_shovel:888404340426031126>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET dig = $1 WHERE member_id = $2", numberswitcher(self.result.get('dig')), ctx.author.id)
            elif str(emoji) == "🔢":
                await self.client.pool_pg.execute("UPDATE remindersettings SET highlow = $1 WHERE member_id = $2", numberswitcher(self.result.get('highlow')), ctx.author.id)
            elif str(emoji) == "<a:DVB_snakeeyes:888404298608812112>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET snakeeyes = $1 WHERE member_id = $2", numberswitcher(self.result.get('snakeeyes')), ctx.author.id)
            elif str(emoji) == "<:DVB_search:888405048260976660>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET search = $1 WHERE member_id = $2", numberswitcher(self.result.get('search')), ctx.author.id)
            elif str(emoji) == "<:DVB_Crime:888404653711192067>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET crime = $1 WHERE member_id = $2", numberswitcher(self.result.get('crime')), ctx.author.id)
            elif str(emoji) == "<:DVB_beg:888404456356610099>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET beg = $1 WHERE member_id = $2", numberswitcher(self.result.get('beg')), ctx.author.id)
            elif str(emoji) == "<a:DVB_DailyBox:888404475470024785>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET dailybox = $1 WHERE member_id = $2", numberswitcher(self.result.get('dailybox')), ctx.author.id)
            elif str(emoji) == "<:DVB_Horseshoe:888404491647463454>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET horseshoe = $1 WHERE member_id = $2", numberswitcher(self.result.get('horseshoe')), ctx.author.id)
            elif str(emoji) == "<:DVB_pizza:888404502280024145>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET pizza = $1 WHERE member_id = $2", numberswitcher(self.result.get('pizza')), ctx.author.id)
            elif str(emoji) == "<:DVB_sugarskull:904936096436215828>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET drop = $1 WHERE member_id = $2", numberswitcher(self.result.get('drop')), ctx.author.id)
            self.result = await self.client.pool_pg.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id)
            self.children[reminderemojis.index(str(emoji))].style = discord.ButtonStyle.red if is_enabled[reminderemojis.index(str(emoji))] == True else discord.ButtonStyle.green
            is_enabled[reminderemojis.index(str(emoji))] = False if is_enabled[reminderemojis.index(str(emoji))] == True else True
            await self.response.edit(view=self)

        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await update_message(self.emoji)
        for emoji in reminderemojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label = labels[reminderemojis.index(emoji)] + f"{'' if self.rmtimes[reminderemojis.index(emoji)] is None else f' - {short_time(self.rmtimes[reminderemojis.index(emoji)])}'}", style=discord.ButtonStyle.green if is_enabled[reminderemojis.index(emoji)] else discord.ButtonStyle.red))

        self.add_item(VoteSetting(self.client, self.context, self.response))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        ctx = self.context
        author = ctx.author
        if interaction.user != author:
            await interaction.response.send_message("These are not your Dank Reminders. To set your own Dank Reminders, type `dv.dankreminder`.", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        for b in self.children:
            b.disabled = True
        await self.response.edit(view=self)

class DankMemer(betting, commands.Cog, name='dankmemer'):
    """
    Dank Memer utilities
    """
    def __init__(self, client):
        self.client = client
        self.dankmemerreminders.start()
        self.fighters = {}

    def cog_unload(self):
        self.dankmemerreminders.stop()

    @tasks.loop(seconds=1.0)
    async def dankmemerreminders(self):
        try:
            await self.client.wait_until_ready()
            results = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where time < $1", round(time.time())) # all reminders that are due for reminding
            if len(results) == 0:
                return
            for result in results:
                config = await self.client.pool_pg.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", result.get('member_id')) # get the user's configuration
                if config is None: # no config means user doesn't even use this reminder system lol
                    pass
                elif result.get('remindertype') not in [2, 3, 4, 6 , 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]: # since 2 3 4 5 corresponds to the respective reminders, if somehow an invalid number is inserted it skips straight to deleting
                    pass
                elif config[result.get('remindertype')] == 0: # activity specific reminder check
                    pass
                elif config.get('method') == 0: # chose not to be reminded
                    pass
                elif config.get('method') in [1, 2]: # DMs or Mentions
                    def message(reminderaction):
                        if reminderaction == 2:
                            return "**claim your daily** <:DVB_calendar:873107952159059991>"
                        elif reminderaction == 3:
                            return "**enter the lottery** <:DVB_lotteryticket:873110581085880321>"
                        elif reminderaction == 4:
                            return "**work again** <:DVB_workbadge:873110507605872650>"
                        elif reminderaction == 5:
                            return "**use a lifesaver** <:DVB_lifesaver:873110547854405722>"
                        elif reminderaction == 6:
                            return "**use an apple** <:DVB_apple:876627457275469867>"
                        elif reminderaction == 7:
                            return "**redeem your Patreon perks** <:DVB_patreon:876628017194082395>"
                        elif reminderaction == 8:
                            return "**claim your weekly** <:DVB_week:876711052669247528> "
                        elif reminderaction == 9:
                            return "**claim your monthly** <:DVB_month:876711072030150707> "
                        elif reminderaction == 10:
                            return "`pls hunt` <:DVB_rifle:888404394805186571> "
                        elif reminderaction == 11:
                            return "`pls fish` <:DVB_fishing:888404317638369330>"
                        elif reminderaction == 12:
                            return "`pls dig` <:DVB_shovel:888404340426031126>"
                        elif reminderaction == 13:
                            return "`pls highlow` 🔢"
                        elif reminderaction == 14:
                            return "`pls snakeeyes` <a:DVB_snakeeyes:888404298608812112>"
                        elif reminderaction == 15:
                            return "`pls search` <:DVB_search:888405048260976660>"
                        elif reminderaction == 16:
                            return "`pls crime` <:DVB_Crime:888404653711192067>"
                        elif reminderaction == 17:
                            return "`pls beg` <:DVB_beg:888404456356610099>"
                        elif reminderaction == 18:
                            return "**use a dailybox** <a:DVB_DailyBox:888404475470024785>"
                        elif reminderaction == 19:
                            return "**use a horseshoe** <:DVB_Horseshoe:888404491647463454>"
                        elif reminderaction == 20:
                            return "**use a pizza** <:DVB_pizza:888404502280024145>"
                        elif reminderaction == 21:
                            return "**A special item is dropping**!\nYou can now buy **1 Sugar Skull** for **⏣ 500,000**."
                    try:
                        member = self.client.get_guild(result.get('guild_id')).get_member(result.get('member_id'))
                        channel = self.client.get_channel(result.get('channel_id'))
                    except AttributeError: # member is none or channel is none
                        pass
                    else:
                        if member is None or channel is None:
                            pass
                        elif config.get('method') == 1:  # DMs or is lottery/daily reminder
                            if result.get('remindertype') in range(10, 21):
                                try:
                                    await channel.send(f"{member.mention} You can now {message(result.get('remindertype'))}")  # DM
                                except:
                                    await member.send(f"{member.mention} You can now {message(result.get('remindertype'))} ({channel.mention})")  # DM
                            else:
                                try:
                                    await member.send(f"{member.mention} You can now {message(result.get('remindertype'))} ({channel.mention})") # DM
                                except discord.Forbidden:
                                    try:
                                        await channel.send(f"{member.mention} {self.client.user.name} is unable to DM you.\nTo receive Dank Memer reminders properly, open your DMs or switch to ping reminders via `dv.drm ping`. Your reminders have been disabled for now.")
                                    except:
                                        pass
                                    await self.client.pool_pg.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 0, result.get('member_id')) # change reminder settings to None
                        elif config.get('method') == 2: # Mention
                            try:
                                await channel.send(f"{member.mention} you can now {message(result.get('remindertype'))}")
                            except:
                                pass
                    await self.client.pool_pg.execute("INSERT into stats(member_id, remindertype, time) VALUES($1, $2, $3)", result.get('member_id'), result.get('remindertype'), result.get('time'))
                await self.client.pool_pg.execute("DELETE from dankreminders WHERE member_id = $1 and remindertype = $2 and channel_id = $3 and guild_id = $4 and time = $5", result.get('member_id'), result.get('remindertype'), result.get('channel_id'), result.get('guild_id'), result.get('time'))
        except Exception as error:
            traceback_error = print_exception(f'Ignoring exception in Reminder task', error)
            embed = discord.Embed(color=0xffcccb,
                                  description=f"Error encountered on a Reminder task.\n```py\n{traceback_error}```",
                                  timestamp=discord.utils.utcnow())
            await self.client.get_guild(871734809154707467).get_channel(871737028105109574).send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot and message.author.id != 270904126974590976:
            return
        if self.client.maintenance.get(self.qualified_name):
            return
        if not message.guild:
            return
        #if message.guild.id != 595457764935991326:
#            return
        """
        Refer to https://discord.com/channels/871734809154707467/871737332431216661/873142587001827379 to all message events here
        """
        if message.content.lower() in ["pls daily", "pls 24hr"]:
            if not message.author.bot:
                def check_daily(payload):
                    if len(payload.embeds) == 0 or payload.author.id == message.author.id or not payload.author.bot or message.channel != payload.channel or payload.author.id != 270904126974590976:
                        return False
                    else:
                        return payload.embeds[0].title and payload.embeds[0].title == f"{message.author.name}'s Daily Coins"
                try:
                    botresponse = await self.client.wait_for("message", check=check_daily, timeout=10)
                except asyncio.TimeoutError:
                    return await checkmark(message)
                else:
                    member = message.author
                    nextdailytime = round(time.time())
                    while nextdailytime % 86400 != 0:
                        nextdailytime += 1
                    existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 2)
                    if len(existing) > 0:
                        await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextdailytime, member.id, 2)
                    else:
                        await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 2, message.channel.id, message.guild.id, nextdailytime)
                    with contextlib.suppress(discord.HTTPException):
                        await botresponse.add_reaction("⏰")
            else:
                pass

        if "pls weekly" in message.content.lower():
            if not message.author.bot:
                def check_weekly(payload):
                    if len(payload.embeds) == 0 or payload.author.id == message.author.id or not payload.author.bot or message.channel != payload.channel or payload.author.id != 270904126974590976:
                        return False
                    else:
                        return payload.embeds[0].title and payload.embeds[0].title == f"Here are yer weekly coins, {message.author.name}" or payload.embeds[0].title == f"Here are your weekly coins, {message.author.name}"
                try:
                    botresponse = await self.client.wait_for("message", check=check_weekly, timeout=10)
                except asyncio.TimeoutError:
                    return await checkmark(message)
                else:
                    member = message.author
                    nextweeklytime = round(time.time()) + 604800
                    existing = await self.client.pool_pg.fetch(
                        "SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 8)
                    if len(existing) > 0:
                        await self.client.pool_pg.execute(
                            "UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextweeklytime,
                            member.id, 8)
                    else:
                        await self.client.pool_pg.execute(
                            "INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)",
                            member.id, 8, message.channel.id, message.guild.id, nextweeklytime)
                    with contextlib.suppress(discord.HTTPException):
                        await botresponse.add_reaction("⏰")
            else:
                pass

        if "pls monthly" in message.content.lower():
            if not message.author.bot:
                def check_monthly(payload):
                    if len(payload.embeds) == 0 or payload.author.id == message.author.id or not payload.author.bot or message.channel != payload.channel or payload.author.id != 270904126974590976:
                        return False
                    else:
                        return payload.embeds[0].title and payload.embeds[0].title == f"Here are yer monthly coins, {message.author.name}" or payload.embeds[0].title == f"Here are your monthly coins, {message.author.name}"
                try:
                    botresponse = await self.client.wait_for("message", check=check_monthly, timeout=10)
                except asyncio.TimeoutError:
                    await checkmark(message)
                else:
                    member = message.author
                    nextmonthlytime = round(time.time()) + 2592000
                    existing = await self.client.pool_pg.fetch(
                        "SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 9)
                    if len(existing) > 0:
                        await self.client.pool_pg.execute(
                            "UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3",
                            nextmonthlytime,
                            member.id, 9)
                    else:
                        await self.client.pool_pg.execute(
                            "INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)",
                            member.id, 9, message.channel.id, message.guild.id, nextmonthlytime)
                    with contextlib.suppress(discord.HTTPException):
                        await botresponse.add_reaction("⏰")
            else:
                pass

        if len(message.embeds) > 0 and len(message.mentions) > 0 and message.embeds[0].title and message.embeds[0].description and message.embeds[0].title == "Pending Confirmation" and "tryna buy a lottery ticket" in message.embeds[0].description:
            member = message.mentions[0]
            def check_lottery(payload_before, payload_after):
                return payload_before.author == message.author and payload_after.author == message.author and payload_before.id == message.id and payload_after.id == message.id and len(message.embeds) > 0
            try:
                newedit = await self.client.wait_for("message_edit", check=check_lottery, timeout=20)
            except asyncio.TimeoutError:
                return await checkmark(message)
            else:
                if not message.embeds[0].title:
                    return
                if message.embeds[0].title == "Action Canceled" or message.embeds[0].title == "Action Canceled":
                    return await message.add_reaction("<:crossmark:841186660662247444>")
                if message.embeds[0].title == "Action Confirmed":
                    nextlotterytime = round(time.time())
                    while nextlotterytime % 3600 != 0:
                        nextlotterytime += 1
                    nextlotterytime += 30
                    existing = await self.client.pool_pg.fetch(
                        "SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 3)
                    if len(existing) > 0:
                        await self.client.pool_pg.execute(
                            "UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3",
                            nextlotterytime, member.id, 3)
                    else:
                        await self.client.pool_pg.execute(
                            "INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)",
                            member.id, 3, message.channel.id, message.guild.id, nextlotterytime)
                    with contextlib.suppress(discord.HTTPException):
                        await message.add_reaction("⏰")
        """
        Redeem Reminder
        """
        if "pls redeem" in message.content.lower():
            def check_redeem(payload):
                return payload.author.bot and len(payload.embeds) > 0 and payload.channel == message.channel and payload.author.id == 270904126974590976
            try:
                redeemresponse = await self.client.wait_for("message", check=check_redeem, timeout = 15)
            except asyncio.TimeoutError:
                return await checkmark(message)
            else:
                if redeemresponse.embeds[0].title and f"{message.author.name} has redeemed their" in redeemresponse.embeds[0].title:
                    member = message.author
                    nextredeemtime = round(time.time()) + 604800
                    existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 7)
                    if len(existing) > 0:
                        await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextredeemtime, member.id, 7)
                    else:
                        await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 7, message.channel.id, message.guild.id, nextredeemtime)
                    with contextlib.suppress(discord.HTTPException):
                        await message.add_reaction("⏰")
                else:
                    return await message.add_reaction("<:crossmark:841186660662247444>")
        """
        Hunting Reminder
        """
        if message.content.startswith("You went hunting") and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nexthunttime = round(time.time()) + 30
            existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 10)
            if len(existing) > 0:
                await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nexthunttime, member.id, 10)
            else:
                await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 10, message.channel.id, message.guild.id, nexthunttime)
        """
        Fishing Reminder
        """
        if (message.content.startswith("You cast out your line") or message.content.startswith("LMAO you found nothing.")) and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextfishtime = round(time.time()) + 30
            existing = await self.client.pool_pg.fetch(
                "SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 11)
            if len(existing) > 0:
                await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextfishtime, member.id, 11)
            else:
                await self.client.pool_pg.execute(
                    "INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 11, message.channel.id, message.guild.id, nextfishtime)
        """
        Dig Reminder
        """
        if (message.content.startswith("You dig in the dirt") or message.content.startswith("LMAO you found nothing in the ground.")) and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextdigtime = round(time.time()) + 30
            existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 12)
            if len(existing) > 0:
                await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextdigtime, member.id, 12)
            else:
                await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 12, message.channel.id, message.guild.id, nextdigtime)
        """
        Highlow Reminder
        """
        if message.content.lower().startswith("pls hl") or message.content.lower().startswith("pls highlow") and not message.author.bot:
            def check_hl(payload):
                return payload.author.bot and len(payload.embeds) > 0 and payload.channel == message.channel and payload.author.id == 270904126974590976 and message.author.mentioned_in(payload)
            try:
                botresponse = await self.client.wait_for("message", check=check_hl, timeout = 5.0)
            except asyncio.TimeoutError:
                return await crossmark(message)
            else:
                if botresponse.embeds[0].author.name == f"{message.author.name}'s high-low game":
                    def check_hl(payload_before, payload_after):
                        return payload_after.id == botresponse.id
                    try:
                        await self.client.wait_for("message_edit", check=check_hl, timeout=30.0)
                    except asyncio.TimeoutError:
                        return await crossmark(botresponse)
                    else:
                        member = message.author
                        nexthighlowtime = round(time.time()) + 20
                        existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 13)
                        if len(existing) > 0:
                            await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3",nexthighlowtime, member.id, 13)
                        else:
                            await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 13, message.channel.id, message.guild.id, nexthighlowtime)
        """
        Snakeeyes Reminder
        """
        if message.content.lower().startswith("pls snakeeyes") or message.content.lower().startswith("pls se ") and not message.author.bot and not message.content.lower().startswith("pls search"):
            content = message.content.split()
            if len(content) < 3:
                return await crossmark(message)
            if content[2] == 'max':
                pass
            else:
                try:
                    content = int(content[2])
                except ValueError:
                        return await crossmark(message)
                else:
                    if content < 50:
                        return await crossmark(message)
            def check_snakeeyes(payload):
                return len(payload.embeds) > 0 and payload.author.id == 270904126974590976 and message.author.mentioned_in(payload) and payload.embeds[0].author.name == f"{message.author.name}'s snake eyes game"
            try:
                await self.client.wait_for('message', check=check_snakeeyes, timeout=30.0)
            except asyncio.TimeoutError:
                return await crossmark(message)
            else:
                member = message.author
                nextsnakeeyestime = round(time.time()) + 5
                existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 14)
                if len(existing) > 0:
                    await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextsnakeeyestime, member.id, 14)
                else:
                    await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)",member.id, 14, message.channel.id, message.guild.id, nextsnakeeyestime)
        """
        Search Reminder
        """
        if "Where do you want to search?" in message.content and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextsearchtime = round(time.time()) + 20
            existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 15)
            if len(existing) > 0:
                await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextsearchtime, member.id, 15)
            else:
                await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 15, message.channel.id, message.guild.id, nextsearchtime)
        """
        Crime Reminder
        """
        if "What crime do you want to commit?" in message.content and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextcrimetime = round(time.time()) + 20
            existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 16)
            if len(existing) > 0:
                await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextcrimetime, member.id, 16)
            else:
                await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 16, message.channel.id, message.guild.id, nextcrimetime)
        """
        Beg Reminder
        """
        if message.content.lower().startswith("pls beg") and not message.author.bot:
            def check_beg(payload):
                return len(payload.embeds) > 0 and message.author.mentioned_in(payload) and payload.author.id == 270904126974590976
            try:
                botresponse = await self.client.wait_for('message', check=check_beg, timeout = 5.0)
            except asyncio.TimeoutError:
                return await crossmark(message)
            else:
                if botresponse.embeds[0].description.startswith("Stop begging so much"):
                    return await crossmark(botresponse)
                else:
                    member = message.author
                    nextbegtime = round(time.time()) + 30
                    existing = await self.client.pool_pg.fetch(
                        "SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 17)
                    if len(existing) > 0:
                        await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3",nextbegtime, member.id, 17)
                    else:
                        await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 17, message.channel.id, message.guild.id, nextbegtime)
        """
        Horseshoe Reminder
        """
        if message.content.startswith("You equip your lucky horseshoe") and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nexthorseshoetime = round(time.time()) + 900
            existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 19)
            if len(existing) > 0:
                await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nexthorseshoetime, member.id, 19)
            else:
                await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 19, message.channel.id, message.guild.id, nexthorseshoetime)
        """
        Pizza Reminder
        """
        if message.content.startswith("You eat the perfect slice of pizza.") and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextpizzatime = round(time.time()) + 3600
            existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 20)
            if len(existing) > 0:
                await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextpizzatime, member.id, 20)
            else:
                await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 20, message.channel.id, message.guild.id, nextpizzatime)
        """
        Daily Box Reminder
        """
        if len(message.embeds) > 0 and message.author.id == 270904126974590976 and message.embeds[0].title and message.embeds[0].title=="Opening Daily Box":
            def check_dailybox(payload_before, payload_after):
                return payload_after.id == message.id
            try:
                botresponse = await self.client.wait_for("message_edit", check=check_dailybox, timeout=10.0)
                botresponse = botresponse[1]
            except asyncio.TimeoutError:
                return await crossmark(message)
            else:
                if botresponse.embeds:
                    if botresponse.embeds[0].title:
                        for member in message.guild.members:
                            if botresponse.embeds[0].title == f"{member.name}'s Loot Haul!":
                                nextdailyboxtime = round(time.time()) + 600
                                existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 18)
                                if len(existing) > 0:
                                    await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextdailyboxtime, member.id, 18)
                                else:
                                    await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 18, message.channel.id, message.guild.id, nextdailyboxtime)
                return await checkmark(message)
        """
        Work Reminder
        """
        if len(message.embeds) > 0 and message.author.id == 270904126974590976 and len(message.mentions) > 0 and  message.embeds[0].description and (message.embeds[0].description.startswith("**TERRIBLE work!**") or message.embeds[0].description.startswith("**Great work!**")):
                member = message.mentions[0]
                nextworktime = round(time.time()) + 3600
                existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 4)
                if len(existing) > 0:
                    await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextworktime, member.id, 4)
                else:
                    await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 4, message.channel.id, message.guild.id, nextworktime)
                with contextlib.suppress(discord.HTTPException):
                    await message.add_reaction("⏰")

        if len(message.mentions) > 0 and "You've eaten an apple!" in message.content and message.author.bot:
            member = message.mentions[0]
            nextappletime = round(time.time()) + 86400
            existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 6)
            if len(existing) > 0:
                await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextappletime, member.id, 6)
            else:
                await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 6, message.channel.id, message.guild.id, nextappletime)
            with contextlib.suppress(discord.HTTPException):
                await message.add_reaction("⏰")

    @checks.dev()
    @commands.command(name="drmstats", aliases = ["dankreminderstats, statistics"])
    async def statistics(self, ctx, argument = None):
        """
        Shows dev-only statistics for Dank Memer reminders.
        """
        if argument and argument.lower() == "reset":
            alltime = await self.client.pool_pg.fetch("SELECT * from stats")
            embed = discord.Embed(title="Reset Dank reminder database?", description=f"{len(alltime)} entries will be deleted. Are you sure?", color=discord.Color.red())
            confirmview = confirm(ctx, self.client, 15.0)
            message = await ctx.send(embed=embed, view=confirmview)
            confirmview.response = message
            await confirmview.wait()
            if confirmview.returning_value is None:
                embed.description, embed.color = "You didn't react on time.", discord.Color.red()
                return await message.edit(embed=embed)
            elif confirmview.returning_value is False:
                embed.description, embed.color = "Command stopped.", discord.Color.red()
                return await message.edit(embed=embed)
            elif confirmview.returning_value is True:
                async with ctx.typing():
                    await self.client.pool_pg.execute("DELETE FROM stats") # delete statistics database
                    embed.description, embed.color = "Database has been reset :,)", discord.Color.green()
                    await message.edit(embed=embed)
                    return await message.delete(delay=10)
        def remindertype(num):
            if num == 2:
                return "Daily"
            if num == 3:
                return "Lottery"
            if num == 4:
                return "Work"
            if num == 5:
                return "Lifesaver"
            if num == 6:
                return "Apple"
            if num == 7:
                return "Patreon"
            if num == 8:
                return "Weekly"
            if num == 9:
                return "Monthly"
            if num == 10:
                return "Hunt"
            if num == 11:
                return "Fish"
            if num == 12:
                return "Dig"
            if num == 13:
                return "Highlow"
            if num == 14:
                return "Snakeeyes"
            if num == 15:
                return "Search"
            if num == 16:
                return "Crime"
            if num == 17:
                return "Beg"
            if num == 18:
                return "DailyBox"
            if num == 19:
                return "Horseshoe"
            if num == 20:
                return "Pizza"
            else:
                return "None"
        """
        Shows statistics for Dank Memer reminders for this bot.
        """
        timecounter = time.perf_counter()
        timenow = round(time.time())
        alltime = await self.client.pool_pg.fetch("SELECT * from stats") # gets all entries from all time
        twentyfourhour = await self.client.pool_pg.fetch("SELECT * from stats WHERE time > $1", timenow - 86400) # gets all entries from the last 24 hours
        week = await self.client.pool_pg.fetch("SELECT * from stats WHERE time > $1",timenow - 604800) # gets all entries from the past week
        users = {} # result will be something like {321892489470410763: 123, 650647680837484556: 456}
        reminders = {} # result will be something like {Lottery: 123, Work: 45, Lifesaver: 67, Daily: 89}
        for entry in alltime:
            if entry.get('member_id') not in users:
                users[entry.get('member_id')] = 1
            else:
                users[entry.get('member_id')] += 1
            if remindertype(entry.get('remindertype')) not in reminders:
                reminders[remindertype(entry.get('remindertype'))] = 1
            else:
                reminders[remindertype(entry.get('remindertype'))] += 1
        sortusers = sorted(users.items(), key=operator.itemgetter(1), reverse=True) # sorts dict by descending
        listof = [f"<@{user[0]}>: {user[1]}" for user in sortusers[:3]] # makes it into a list that is readable
        listof = "\n".join(listof) # makes top 3 users into string
        sortreminders = sorted(reminders.items(), key=operator.itemgetter(1), reverse=True) # sorts dict by descending
        listofreminders = [f"{reminder[0]}: {reminder[1]}" for reminder in sortreminders[:3]]
        listofreminders = "\n".join(listofreminders) # makes top 3 reminder types into string
        daily = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 2)) # number of daily reminders served
        lottery = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 3)) # number of lottery reminders served
        work = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 4)) # number of work reminders served
        apple = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 6)) # number of lifesavers reminders served
        redeem = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 7))
        weekly = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 8))
        monthly = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 9))
        hunt = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 10))
        fish = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 11))
        dig = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 12))
        highlow = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 13))
        snakeeyes = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 14))
        search = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 15))
        crime = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 16))
        beg = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 17))
        dailybox = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 18))
        horseshoe = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 19))
        pizza = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 20))

        onhold = len(await self.client.pool_pg.fetch("SELECT * FROM dankreminders"))
        embed = discord.Embed(title="Dank Memer Reminder Statistics", description=f"Fetched in {round(time.perf_counter() - timecounter, 3)} seconds.", color = self.client.embed_color, timestamp= discord.utils.utcnow())
        embed.add_field(name="Top 3 reminder types:", value=listof or "None", inline=True)
        embed.add_field(name="Top 3 reminder users:", value=listofreminders or "None", inline=True)
        embed.add_field(name="Number of activated settings", value=str(len(await self.client.pool_pg.fetch("SELECT * FROM remindersettings"))), inline=False)
        embed.add_field(name="History statistics", value=f"Since dawn of time: `{len(alltime)}`\nPast 24 hours: `{len(twentyfourhour)}`\nPast week: `{len(week)}`\nOn hold:`{onhold}`", inline=True)
        embed.add_field(name="History statistics",value=f"Daily: `{daily}`\nLottery: `{lottery}`\nWork: `{work}`\nApple:`{apple}`\nPatreon: `{redeem}`\nWeekly: `{weekly}`\nMonthly: `{monthly}`\nHunt: `{hunt}`\nFish: `{fish}`\nDig: `{dig}`\nHighlow: `{highlow}`\nSnakeeyes: `{snakeeyes}`\nSearch: `{search}`\nCrime: `{crime}`\nBeg: `{beg}`\nDailybox: `{dailybox}`\nHorseshoe: `{horseshoe}`\nPizza: `{pizza}`", inline=True)
        await ctx.send(embed=embed)


    @checks.not_in_gen()
    @commands.command(name="dankreminders", aliases = ["dankrm", "drm"])
    async def dankreminders(self, ctx):
        """
        Shows your reminders for Dank Memer and allows you to enable/disable them.
        Change your type of reminder via the select menu.
        """
        result = await self.client.pool_pg.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id) # gets the configuration for user to check if they have used dank reminder before
        if result is None:
            await self.client.pool_pg.execute("INSERT into remindersettings VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)", ctx.author.id, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0) # creates new entry for settings
            result = await self.client.pool_pg.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id)
        reminders = await self.client.pool_pg.fetch("SELECT * FROM dankreminders WHERE member_id = $1 and guild_id = $2", ctx.author.id, ctx.guild.id) # gets user's reminders
        dailytime, lotterytime, worktime, appletime, redeemtime, weeklytime, monthlytime, hunttime, fishtime, digtime, highlowtime, snakeeyestime, searchtime, crimetime, begtime, dailyboxtime, horseshoetime, pizzatime, droptime = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
        for reminder in reminders:
            if reminder.get('remindertype') == 2:
                dailytime = round(reminder.get('time')-time.time()) # time in discord time format
            if reminder.get('remindertype') == 3:
                lotterytime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 4:
                worktime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 6:
                appletime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 7:
                redeemtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 8:
                weeklytime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 9:
                monthlytime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 10:
                hunttime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 11:
                fishtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 12:
                digtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 13:
                highlowtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 14:
                snakeeyestime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 15:
                searchtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 16:
                crimetime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 17:
                begtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 18:
                dailyboxtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 19:
                horseshoetime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 20:
                pizzatime = round(reminder.get('time')-time.time())
        remindertimes = [dailytime or None, weeklytime or None, monthlytime or None, lotterytime or None, worktime or None, appletime or None, redeemtime or None, hunttime or None, fishtime or None, digtime or None, highlowtime or None, snakeeyestime or None, searchtime or None, crimetime or None, begtime or None, dailyboxtime or None, horseshoetime or None, pizzatime or None, droptime or None]
        newview = dankreminders(ctx, self.client, remindertimes, 15.0, truefalse(truefalse(result.get('daily'))), truefalse(result.get('weekly')), truefalse(result.get('monthly')), truefalse(result.get('lottery')), truefalse(result.get('work')), truefalse(result.get('apple')), truefalse(result.get('redeem')), truefalse(result.get('hunt')), truefalse(result.get('fish')), truefalse(result.get('dig')), truefalse(result.get('highlow')), truefalse(result.get('snakeeyes')), truefalse(result.get('search')), truefalse(result.get('crime')), truefalse(result.get('beg')), truefalse(result.get('dailybox')), truefalse(result.get('horseshoe')), truefalse(result.get('pizza')), truefalse(result.get('drop')))
        message = await ctx.send(f"**{ctx.author}'s Dank Memer Reminders**\nSelect the button that corresponds to the reminder to enable/disable it.\n\nYou're currently {'reminded via **DMs**' if result.get('method') == 1 else 'reminded via **ping**' if result.get('method') == 2 else 'not reminded'} for your reminders.\nTo see the duration of your reminders in timestamp format, use `dv.dankcooldown` or `dv.dcd`.", view=newview)
        newview.response = message
        newview.result = result
        newview.rmtimes = remindertimes

    @checks.admoon()
    @commands.command(name="reminddrop")
    async def reminddrop(self, ctx, timetodrop:int, *, msg: str):
        """
        Sets a Drop reminder.
        """
        if time is None:
            return await ctx.send("Epoch time when drop happens needs to be specified.")
        if msg is None:
            return await ctx.send("A message needs to be accompanied.")
        duration = timetodrop - round(time.time())
        if duration < 0:
            return await ctx.send("Invalid time.")
        await ctx.checkmark()
        await asyncio.sleep(duration)
        enabled = await self.client.pool_pg.fetch("SELECT * FROM remindersettings WHERE drop = $1", 1)
        #crafting messages
        messages = []
        ids = [i.get('member_id') for i in enabled]
        tempmsg = ''
        for i in ids:
            member = ctx.guild.get_member(i)
            if member is not None:
                remindersettings = await self.client.pool_pg.fetchval("SELECT method FROM remindersettings WHERE member_id = $1", i)
                if remindersettings == True:
                    try:
                        await member.send(f"{msg}")
                    except:
                        if len(tempmsg) + len(msg) < 1800:
                            tempmsg += f"{member.mention}"
                        else:
                            tempmsg += f" {msg}"
                            messages.append(tempmsg)
                            tempmsg = f"{member.mention}"
                elif len(tempmsg) + len(msg) < 1800:
                    tempmsg += f"{member.mention}"
                else:
                    tempmsg += f" {msg}"
                    messages.append(tempmsg)
                    tempmsg = f"{member.mention}"
        tempmsg += f" {msg}"
        messages.append(tempmsg)
        channel_id = 873616122388299837 if ctx.guild.id == 871734809154707467 else 614945340617130004
        channel = self.client.get_channel(channel_id)
        for message in messages:
            await channel.send(message)



    @checks.not_in_gen()
    @commands.command(name="dankcooldowns", aliases=["dankcd", "dcd"])
    async def dankcooldowns(self, ctx):
        """
        Shows the existing reminders for Dank memer.
        """
        reminders = await self.client.pool_pg.fetch("SELECT * FROM dankreminders WHERE member_id = $1 and guild_id = $2", ctx.author.id, ctx.guild.id)  # gets user's reminders
        dailytime, lotterytime, worktime, appletime, redeemtime, weeklytime, monthlytime, hunttime, fishtime, digtime, highlowtime, snakeeyestime, searchtime, crimetime, begtime, dailyboxtime, horseshoetime, pizzatime = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
        for reminder in reminders:
            if reminder.get('remindertype') == 2:
                dailytime = f"<t:{reminder.get('time')}:R>"  # time in discord time format
            if reminder.get('remindertype') == 3:
                lotterytime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 4:
                worktime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 6:
                appletime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 7:
                redeemtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 8:
                weeklytime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 9:
                monthlytime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 10:
                hunttime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 11:
                fishtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 12:
                digtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 13:
                highlowtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 14:
                snakeeyestime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 15:
                searchtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 16:
                crimetime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 17:
                begtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 18:
                dailyboxtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 19:
                horseshoetime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 20:
                pizzatime = f"<t:{reminder.get('time')}:R>"
        remindertimes = [dailytime or "**Ready!**", weeklytime or "**Ready!**", monthlytime or "**Ready!**",
                         lotterytime or "**Ready!**", worktime or "**Ready!**", appletime or "**Ready!**", redeemtime or "**Ready!**",
                         hunttime or "**Ready!**", fishtime or "**Ready!**", digtime or "**Ready!**", highlowtime or "**Ready!**",
                         snakeeyestime or "**Ready!**", searchtime or "**Ready!**", crimetime or "**Ready!**", begtime or "**Ready!**",
                         dailyboxtime or "**Ready!**", horseshoetime or "**Ready!**", pizzatime or "**Ready!**"]
        embed = discord.Embed(title="Your Dank Memer reminders", description="**Select the button that corresponds to the reminder to enable/disable it.**\nChange how you want to be reminded with the select menu.", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        embed.description = embed.description + f"""\nClaim daily <:DVB_calendar:873107952159059991>: {remindertimes[0]}
Claim weekly <:DVB_week:876711052669247528>: {remindertimes[1]}
Claim monthly <:DVB_month:876711072030150707>: {remindertimes[2]}
Enter the lottery <:DVB_lotteryticket:873110581085880321>: {remindertimes[3]}
Work <:DVB_workbadge:873110507605872650>: {remindertimes[4]}
Use an apple <:DVB_apple:876627457275469867>: {remindertimes[5]}
Redeem donor rewards <:DVB_patreon:876628017194082395>: {remindertimes[6]}
Hunt <:DVB_rifle:888404394805186571>: {remindertimes[7]}
Fish <:DVB_fishing:888404317638369330>: {remindertimes[8]}
Dig <:DVB_shovel:888404340426031126>: {remindertimes[9]}
Highlow 🔢: {remindertimes[10]}
Snakeeyes <a:DVB_snakeeyes:888404298608812112>: {remindertimes[11]}
Search <:DVB_search:888405048260976660>: {remindertimes[12]}
Crime <:DVB_Crime:888404653711192067>: {remindertimes[13]}
Beg <:DVB_beg:888404456356610099> : {remindertimes[14]}
Use a dailybox <a:DVB_DailyBox:888404475470024785>: {remindertimes[15]}
Use a Horseshoe <:DVB_Horseshoe:888404491647463454>: {remindertimes[16]}
Use a Pizza <:DVB_pizza:888404502280024145>: : {remindertimes[17]}"""
        if ctx.author.id == 650647680837484556:
            embed.description = embed.description + "\nSlap Frenzy <a:DVB_pandaslap:876631217750048798>: **Always Ready**\nBonk Blu <a:DVB_bonk:877196623506194452>: **Always Ready**"
        embed.set_footer(text="To enable/disable reminders, use dv.dankreminder instead.", icon_url=ctx.guild.icon.url)
        await ctx.send(embed=embed)