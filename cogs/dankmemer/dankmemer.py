import contextlib
import time
import asyncio
import discord
from discord import ui
import operator
from utils import checks, buttons
from datetime import datetime, timedelta
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
    elif no == None:
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
    def __init__(self, ctx: DVVTcontext, client, rmtimes, timeout, daily, weekly, monthly, lottery, work, donor, hunt, fish, dig, crime, beg, search, se, highlow, dailybox, horseshoe, pizza, drop, stream, postmeme):
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
                          "<:DVB_workbadge:873110507605872650>", "<:DVB_patreon:876628017194082395>",
                          "<:DVB_rifle:888404394805186571>", "<:DVB_fishing:888404317638369330>",
                          "<:DVB_shovel:888404340426031126>", "<:DVB_Crime:888404653711192067>",
                          "<:DVB_beg:888404456356610099>", "<:DVB_search:888405048260976660>",
                          "<a:DVB_snakeeyes:888404298608812112>", "🔢",
                          "<a:DVB_DailyBox:888404475470024785>", "<:DVB_Horseshoe:888404491647463454>",
                          "<:DVB_pizza:888404502280024145>", "<:DVB_sugarskull:904936096436215828>", "🎮", "<:DVB_Laptop:915524266940854303>"]
        labels = ["Claim daily", "Claim weekly",
                  "Claim monthly", "Enter the Lottery",
                  "Work", "Redeem donor rewards",
                  "Hunt", "Fish",
                  "Dig", "Crime",
                  "Beg", "Search",
                  "Snakeeyes", "Highlow",
                  "Use a dailybox", "Use a horseshoe",
                  "Use a pizza", "Get drop items", "(NEW!) Interact on stream", "(NEW!) Post memes"]
        is_enabled = [daily, weekly, monthly, lottery, work, donor, hunt, fish, dig, crime, beg, search, se, highlow, dailybox, horseshoe, pizza, drop, stream, postmeme]

        async def update_message(emoji, interaction: discord.Interaction):
            if str(emoji) == "<:DVB_calendar:873107952159059991>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET daily = $1 WHERE member_id = $2", numberswitcher(self.result.get('daily')), ctx.author.id)  # switches to enabled/disabled reminder
            elif str(emoji) == "<:DVB_week:876711052669247528>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET weekly = $1 WHERE member_id = $2", numberswitcher(self.result.get('weekly')), ctx.author.id)
            elif str(emoji) == "<:DVB_month:876711072030150707>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET monthly = $1 WHERE member_id = $2", numberswitcher(self.result.get('monthly')), ctx.author.id)
            elif str(emoji) == "<:DVB_lotteryticket:873110581085880321>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET lottery = $1 WHERE member_id = $2", numberswitcher(self.result.get('lottery')), ctx.author.id)
            elif str(emoji) == "<:DVB_workbadge:873110507605872650>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET work = $1 WHERE member_id = $2", numberswitcher(self.result.get('work')), ctx.author.id)
            elif str(emoji) == "<:DVB_patreon:876628017194082395>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET redeem = $1 WHERE member_id = $2", numberswitcher(self.result.get('redeem')), ctx.author.id)
            elif str(emoji) == "<:DVB_rifle:888404394805186571>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET hunt = $1 WHERE member_id = $2", numberswitcher(self.result.get('hunt')), ctx.author.id)
            elif str(emoji) == "<:DVB_fishing:888404317638369330>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET fish = $1 WHERE member_id = $2", numberswitcher(self.result.get('fish')), ctx.author.id)
            elif str(emoji) == "<:DVB_shovel:888404340426031126>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET dig = $1 WHERE member_id = $2", numberswitcher(self.result.get('dig')), ctx.author.id)
            elif str(emoji) == "<:DVB_Crime:888404653711192067>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET crime = $1 WHERE member_id = $2", numberswitcher(self.result.get('crime')), ctx.author.id)
            elif str(emoji) == "<:DVB_beg:888404456356610099>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET beg = $1 WHERE member_id = $2", numberswitcher(self.result.get('beg')), ctx.author.id)
            elif str(emoji) == "<:DVB_search:888405048260976660>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET search = $1 WHERE member_id = $2", numberswitcher(self.result.get('search')), ctx.author.id)
            elif str(emoji) == "<a:DVB_snakeeyes:888404298608812112>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET snakeeyes = $1 WHERE member_id = $2", numberswitcher(self.result.get('snakeeyes')), ctx.author.id)
            elif str(emoji) == "🔢":
                await self.client.pool_pg.execute("UPDATE remindersettings SET highlow = $1 WHERE member_id = $2", numberswitcher(self.result.get('highlow')), ctx.author.id)
            elif str(emoji) == "<a:DVB_DailyBox:888404475470024785>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET dailybox = $1 WHERE member_id = $2", numberswitcher(self.result.get('dailybox')), ctx.author.id)
            elif str(emoji) == "<:DVB_Horseshoe:888404491647463454>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET horseshoe = $1 WHERE member_id = $2", numberswitcher(self.result.get('horseshoe')), ctx.author.id)
            elif str(emoji) == "<:DVB_pizza:888404502280024145>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET pizza = $1 WHERE member_id = $2", numberswitcher(self.result.get('pizza')), ctx.author.id)
            elif str(emoji) == "<:DVB_sugarskull:904936096436215828>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET drop = $1 WHERE member_id = $2", numberswitcher(self.result.get('drop')), ctx.author.id)
            elif str(emoji) == "🎮":
                if self.result.get('stream') != 1:
                    await interaction.response.send_message("__**Important!**__\nThe stream reminder is currently in Beta stage, and might not work at times.\nThe reminder is working when I react to your Stream Manager message with <:checkmark:841187106654519296> after you **run an Ad, Read chat or collect donations**. Otherwise, something went wrong.\n\nFeel free to report bugs in <#870880772985344010>!", ephemeral=True)
                await self.client.pool_pg.execute("UPDATE remindersettings SET stream = $1 WHERE member_id = $2", numberswitcher(self.result.get('stream')), ctx.author.id)
            elif str(emoji) == "<:DVB_Laptop:915524266940854303>":
                await self.client.pool_pg.execute("UPDATE remindersettings SET postmeme = $1 WHERE member_id = $2", numberswitcher(self.result.get('postmeme')), ctx.author.id)
            self.result = await self.client.pool_pg.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id)
            self.children[reminderemojis.index(str(emoji))].style = discord.ButtonStyle.red if is_enabled[reminderemojis.index(str(emoji))] is True else discord.ButtonStyle.green
            is_enabled[reminderemojis.index(str(emoji))] = False if is_enabled[reminderemojis.index(str(emoji))] is True else True
            await self.response.edit(view=self)

        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await update_message(self.emoji, interaction)


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
        self.dropreminder.start()
        self.fighters = {}
        self.trending_game = None
        self.reset_trending_game.start()


    def cog_unload(self):
        self.dankmemerreminders.stop()
        self.dropreminder.stop()
        self.reset_trending_game.stop()

    async def handle_reminder_entry(self, member_id, remindertype, channel_id, guild_id, time):
        existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member_id, remindertype)
        if len(existing) > 0:
            await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", time, member_id, remindertype)
        else:
            await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member_id, remindertype, channel_id, guild_id, time)

    @tasks.loop(hours=24.0)
    async def reset_trending_game(self):
        self.trending_game = None

    @reset_trending_game.before_loop
    async def wait_until_utc(self):
        await self.client.wait_until_ready()
        now = discord.utils.utcnow()
        next_run = now.replace(hour = 0, minute = 0, second = 0)
        if next_run <= now:
            next_run += timedelta(days=1)
        await discord.utils.sleep_until(next_run)


    @tasks.loop(seconds=5.0)
    async def dropreminder(self):
        try:
            await self.client.wait_until_ready()
            drop = await self.client.pool_pg.fetchrow("SELECT * FROM dankdrops WHERE time < $1", round(time.time()))
            if drop is None:
                return
            else:
                price = drop.get('price')
                guild = self.client.get_guild(drop.get('guild_id'))
                name = drop.get('name')
                enabled = await self.client.pool_pg.fetch("SELECT * FROM remindersettings WHERE drop = $1", 1)
                # crafting messages
                msg = f"""
                <a:dv_pepeConfettiOwO:837712470902571008> An item from Dank Memer is dropping! <a:dv_pepeConfettiOwO:837712470902571008>\nItem: {name}\nCost: {price}\n\nYou can buy this item now!
                """
                messages = []
                ids = [i.get('member_id') for i in enabled]
                tempmsg = f'{msg}\n\n'
                for i in ids:
                    member = self.client.get_user(i)
                    if member is not None:
                        remindersettings = await self.client.pool_pg.fetchval("SELECT method FROM remindersettings WHERE member_id = $1", i)
                        if remindersettings == 1:
                            try:
                                await member.send(msg)
                            except:
                                if len(tempmsg) + len(msg) < 1800:
                                    tempmsg += f"{member.mention}"
                                else:
                                    messages.append(tempmsg)
                                    tempmsg = f"{msg}\n\n{member.mention}"
                        elif len(tempmsg) + len(msg) < 1800:
                            tempmsg += f"{member.mention}"
                        else:
                            messages.append(tempmsg)
                            tempmsg = f"{msg}\n\n{member.mention}"
                messages.append(tempmsg)
                channel_id = 873616122388299837 if guild.id == 871734809154707467 else 614945340617130004
                channel = self.client.get_channel(channel_id)
                for message in messages:
                    await channel.send(message)
                await self.client.pool_pg.execute("DELETE FROM dankdrops WHERE guild_id = $1 AND name = $2 AND price = $3 AND time = $4", drop.get('guild_id'), drop.get('name'), drop.get('price'), drop.get('time'))
        except:
            pass

    @tasks.loop(seconds=1.0)
    async def dankmemerreminders(self):
        try:
            await self.client.wait_until_ready()
            if self.client.maintenance.get(self.qualified_name):
                return
            results = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where time < $1", round(time.time())) # all reminders that are due for reminding
            if len(results) == 0:
                return
            for result in results:
                config = await self.client.pool_pg.fetchrow("SELECT member_id, method, daily, weekly, monthly, lottery, work, redeem, hunt, fish, dig, crime, beg, search, snakeeyes, highlow, dailybox, horseshoe, pizza, drop, stream, postmeme FROM remindersettings WHERE member_id = $1", result.get('member_id')) # get the user's configuration
                if config is None: # no config means user doesn't even use this reminder system lol
                    pass
                elif result.get('remindertype') not in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21]: # if the reminder type is not a valid one
                    pass
                elif config[result.get('remindertype')] != 1: # activity specific reminder check
                    pass
                elif config.get('method') == 0: # chose not to be reminded
                    pass
                elif config.get('method') in [1, 2]: # DMs or Mentions
                    def message(reminderaction):
                        if reminderaction == 2:
                            return "**claim your daily** <:DVB_calendar:873107952159059991>"
                        elif reminderaction == 3:
                            return "**claim your weekly** <:DVB_week:876711052669247528> "
                        elif reminderaction == 4:
                            return "**claim your monthly** <:DVB_month:876711072030150707> "
                        elif reminderaction == 5:
                            return "**enter the lottery** <:DVB_lotteryticket:873110581085880321>"
                        elif reminderaction == 6:
                            return "**work again** <:DVB_workbadge:873110507605872650>"
                        elif reminderaction == 7:
                            return "**redeem your Patreon perks** <:DVB_patreon:876628017194082395>"
                        elif reminderaction == 8:
                            return "`pls hunt` <:DVB_rifle:888404394805186571> "
                        elif reminderaction == 9:
                            return "`pls fish` <:DVB_fishing:888404317638369330>"
                        elif reminderaction == 10:
                            return "`pls dig` <:DVB_shovel:888404340426031126>"
                        elif reminderaction == 11:
                            return "`pls crime` <:DVB_Crime:888404653711192067>"
                        elif reminderaction == 12:
                            return "`pls beg` <:DVB_beg:888404456356610099>"
                        elif reminderaction == 13:
                            return "`pls search` <:DVB_search:888405048260976660>"
                        elif reminderaction == 14:
                            return "`pls snakeeyes` <a:DVB_snakeeyes:888404298608812112>"
                        elif reminderaction == 15:
                            return "`pls highlow` 🔢"
                        elif reminderaction == 16:
                            return "**use a dailybox** <a:DVB_DailyBox:888404475470024785>"
                        elif reminderaction == 17:
                            return "**use a horseshoe** <:DVB_Horseshoe:888404491647463454>"
                        elif reminderaction == 18:
                            return "**use a pizza** <:DVB_pizza:888404502280024145>"
                        elif reminderaction == 20:
                            return "**Interact with your stream** 🎮"
                        elif reminderaction == 21:
                            return "`pls pm` <:DVB_Laptop:915524266940854303>"
                    try:
                        member = self.client.get_guild(result.get('guild_id')).get_member(result.get('member_id'))
                        channel = self.client.get_channel(result.get('channel_id'))
                    except AttributeError: # member is none or channel is none
                        pass
                    else:
                        if member is None or channel is None:
                            pass
                        elif config.get('method') == 1:  # DMs or is lottery/daily reminder
                            if result.get('remindertype') in [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 21]:
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
                    return await crossmark(message)
                else:
                    member = message.author
                    nextdailytime = round(time.time())
                    while nextdailytime % 86400 != 0:
                        nextdailytime += 1
                    await self.handle_reminder_entry(member.id, 2, message.channel.id, message.guild.id, nextdailytime)
                    with contextlib.suppress(discord.HTTPException):
                        await clock(message)
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
                    return await crossmark(message)
                else:
                    member = message.author
                    nextweeklytime = round(time.time()) + 604800
                    await self.handle_reminder_entry(member.id, 3, message.channel.id, message.guild.id, nextweeklytime)
                    with contextlib.suppress(discord.HTTPException):
                        await clock(botresponse)
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
                    return await crossmark(message)
                else:
                    member = message.author
                    nextmonthlytime = round(time.time()) + 2592000
                    await self.handle_reminder_entry(member.id, 4, message.channel.id, message.guild.id, nextmonthlytime)
                    with contextlib.suppress(discord.HTTPException):
                        await clock(botresponse)
            else:
                pass

        if len(message.embeds) > 0 and len(message.mentions) > 0 and message.embeds[0].title and message.embeds[0].description and message.embeds[0].title == "Pending Confirmation" and "tryna buy a lottery ticket" in message.embeds[0].description:
            member = message.mentions[0]
            def check_lottery(payload_before, payload_after):
                return payload_before.author == message.author and payload_after.author == message.author and payload_before.id == message.id and payload_after.id == message.id and len(message.embeds) > 0
            try:
                newedit = await self.client.wait_for("message_edit", check=check_lottery, timeout=20)
            except asyncio.TimeoutError:
                return await crossmark(message)
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
                    await self.handle_reminder_entry(member.id, 5, message.channel.id, message.guild.id, nextlotterytime)
                    with contextlib.suppress(discord.HTTPException):
                        await clock(message)
        """
        Redeem Reminder
        """
        if "pls redeem" in message.content.lower():
            def check_redeem(payload):
                return payload.author.bot and len(payload.embeds) > 0 and payload.channel == message.channel and payload.author.id == 270904126974590976
            try:
                redeemresponse = await self.client.wait_for("message", check=check_redeem, timeout = 15)
            except asyncio.TimeoutError:
                return await crossmark(message)
            else:
                if redeemresponse.embeds[0].title and f"{message.author.name} has redeemed their" in redeemresponse.embeds[0].title:
                    member = message.author
                    nextredeemtime = round(time.time()) + 604800
                    await self.handle_reminder_entry(member.id, 7, message.channel.id, message.guild.id, nextredeemtime)
                    with contextlib.suppress(discord.HTTPException):
                        await clock(message)
                else:
                    await crossmark(message)
        """
        Hunting Reminder
        """
        if message.content.startswith("You went hunting") and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nexthunttime = round(time.time()) + 30
            await self.handle_reminder_entry(member.id, 8, message.channel.id, message.guild.id, nexthunttime)
        """
        Fishing Reminder
        """
        if (message.content.startswith("You cast out your line") or message.content.startswith("LMAO you found nothing.")) and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextfishtime = round(time.time()) + 30
            await self.handle_reminder_entry(member.id, 9, message.channel.id, message.guild.id, nextfishtime)
        """
        Dig Reminder
        """
        if (message.content.startswith("You dig in the dirt") or message.content.startswith("LMAO you found nothing in the ground.")) and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextdigtime = round(time.time()) + 30
            await self.handle_reminder_entry(member.id, 10, message.channel.id, message.guild.id, nextdigtime)
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
                        await self.handle_reminder_entry(member.id, 15, message.channel.id, message.guild.id, nexthighlowtime)
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
                await self.handle_reminder_entry(member.id, 14, message.channel.id, message.guild.id, nextsnakeeyestime)
        """
        Search Reminder
        """
        if "Where do you want to search?" in message.content and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextsearchtime = round(time.time()) + 20
            existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 13)
            if len(existing) > 0:
                await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextsearchtime, member.id, 13)
            else:
                await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 13, message.channel.id, message.guild.id, nextsearchtime)
        """
        Crime Reminder
        """
        if "What crime do you want to commit?" in message.content and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextcrimetime = round(time.time()) + 20
            await self.handle_reminder_entry(member.id, 11, message.channel.id, message.guild.id, nextcrimetime)
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
                    await self.handle_reminder_entry(member.id, 12, message.channel.id, message.guild.id, nextbegtime)
        """
        Horseshoe Reminder
        """
        if message.content.startswith("You equip your lucky horseshoe") and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nexthorseshoetime = round(time.time()) + 900
            await self.handle_reminder_entry(member.id, 17, message.channel.id, message.guild.id, nexthorseshoetime)
        """
        Pizza Reminder
        """
        if message.content.startswith("You eat the perfect slice of pizza.") and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextpizzatime = round(time.time()) + 3600
            await self.handle_reminder_entry(member.id, 18, message.channel.id, message.guild.id, nextpizzatime)
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
                                await self.handle_reminder_entry(member.id, 16, message.channel.id, message.guild.id, nextdailyboxtime)
                return await checkmark(message)
        """
        Work Reminder
        """
        if len(message.embeds) > 0 and message.author.id == 270904126974590976 and len(message.mentions) > 0 and message.embeds[0].description and (message.embeds[0].description.startswith("**TERRIBLE work!**") or message.embeds[0].description.startswith("**Great work!**")):
                member = message.mentions[0]
                nextworktime = round(time.time()) + 3600
                await self.handle_reminder_entry(member.id, 6, message.channel.id, message.guild.id, nextworktime)
                with contextlib.suppress(discord.HTTPException):
                    await checkmark(message)
        """
        Postmeme reminder
        """
        if message.author.id == 270904126974590976:
            if len(message.mentions) > 0:
                if len(message.embeds) > 0:
                    if message.embeds[0].author:
                        if message.embeds[0].author.name.endswith("meme posting session"):
                            member = message.mentions[0]
                            nextpostmemetime = round(time.time()) + 30
                            await self.handle_reminder_entry(member.id, 21, message.channel.id, message.guild.id, nextpostmemetime)

    @commands.Cog.listener()
    async def on_message_edit(self, beforemsg, aftermsg):
        if beforemsg.author.id != 270904126974590976:
            return
        if len(beforemsg.embeds) == 0 or len(aftermsg.embeds) == 0:
            return
        beforeembed = beforemsg.embeds[0]
        afterembed = aftermsg.embeds[0]
        if not beforeembed.author:
            return
        if not beforeembed.author.name:
            return
        if not beforeembed.author.name.endswith('Stream Manager'):
            return
        def get_member():
            for member in beforemsg.guild.members:
                if beforeembed.author.name == f"{member.name}'s Stream Manager":
                    return member
            return None
        member = get_member()
        if not member:
            return
        beforeview = discord.ui.View.from_message(beforemsg)
        afterview = discord.ui.View.from_message(aftermsg)
        def check_before_view():
            for button in beforeview.children:
                if not isinstance(button, discord.ui.Button):
                    return False
                if button.label.lower() == 'run ad' and button.disabled is False:
                    pass
                elif button.label.lower() == "read chat" and button.disabled is False:
                    pass
                elif button.label.lower() == "collect donations" and button.disabled is False:
                    pass
                elif button.label.lower() == "end stream" and button.disabled is False:
                    pass
                elif button.label.lower() == "view setup" and button.disabled is False:
                    pass
                elif button.label.lower() == "end interaction" and button.disabled is False:
                    pass
                else:
                    return False
            return True
        if not check_before_view():
            print('did not fulfill have not interacted with stream')
            def check_start_not_stream():
                for button in beforeview.children:
                    if not isinstance(button, discord.ui.Button):
                        return False
                    if button.label.lower() == "go live" and button.disabled is False:
                        pass
                    elif button.label.lower() == "view setup" and button.disabled is False:
                        pass
                    elif button.label.lower() == "end interaction" and button.disabled is False:
                        pass
                    else:
                        return False
                return True
            if not check_start_not_stream():
                return
            def check_start_selecting_stream():
                for button in beforeview.children:
                    if isinstance(button, discord.ui.Select):
                        print(button.placeholder.lower())
                        if button.placeholder.lower() == "select a game":
                            pass
                    elif isinstance(button, discord.ui.Button):
                        if button.label.lower() == "go live" and button.disabled is True:
                            pass
                        elif button.label.lower() == "go back" and button.disabled is False:
                            pass
                    else:
                        return False
                return True
            if check_start_selecting_stream():
                if self.trending_game is not None:
                    return await beforemsg.reply("The current trending game to stream is **{}**!".format(self.trending_game), delete_after=10.0)
            return
        def check_after_view():
            for button in afterview.children:
                if not isinstance(button, discord.ui.Button):
                    return False
                if button.label.lower() == 'run ad' and button.disabled is True:
                    pass
                elif button.label.lower() == "read chat" and button.disabled is True:
                    pass
                elif button.label.lower() == "collect donations" and button.disabled is True:
                    pass
                elif button.label.lower() == "end stream" and button.disabled is False:
                    pass
                elif button.label.lower() == "view setup" and button.disabled is False:
                    pass
                elif button.label.lower() == "end interaction" and button.disabled is False:
                    pass
                else:
                    return False
            return True
        if not check_after_view():
            return
        nextstreamtime = round(time.time()) + 600
        await self.handle_reminder_entry(member.id, 20, aftermsg.channel.id, aftermsg.guild.id, nextstreamtime)
        await checkmark(beforemsg)
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
                return "Weekly"
            if num == 4:
                return "Monthly"
            if num == 5:
                return "Lottery"
            if num == 6:
                return "Work"
            if num == 7:
                return "Patreon"
            if num == 8:
                return "Hunt"
            if num == 9:
                return "Fish"
            if num == 10:
                return "Dig"
            if num == 11:
                return "Crime"
            if num == 12:
                return "Beg"
            if num == 13:
                return "Search"
            if num == 14:
                return "Snakeeyes"
            if num == 15:
                return "Highlow"
            if num == 16:
                return "Dailybox"
            if num == 17:
                return "Horseshoe"
            if num == 18:
                return "Pizza"
            if num == 19:
                return "Drop items"
            if num == 20:
                return "Stream"
            if num == 21:
                return "Postmeme"
            else:
                return "None"
        """
        Shows statistics for Dank Memer reminders for this bot.
        """
        timecounter = time.perf_counter()
        timenow = round(time.time())
        alltime = await self.client.pool_pg.fetch("SELECT * from stats") # gets all entries from all time
        twentyfourhour = await self.client.pool_pg.fetch("SELECT * from stats WHERE time > $1", timenow - 86400) # gets all entries from the last 24 hours
        week = await self.client.pool_pg.fetch("SELECT * from stats WHERE time > $1", timenow - 604800) # gets all entries from the past week
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
        daily = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 2))
        weekly = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 3))
        monthly = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 4))
        lottery = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 5))
        work = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 6))
        redeem = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 7))
        hunt = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 8))
        fish = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 9))
        dig = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 10))
        crime = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 11))
        beg = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 12))
        search = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 13))
        snakeeyes = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 14))
        highlow = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 15))
        dailybox = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 16))
        horseshoe = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 17))
        pizza = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 18))
        stream = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 20))
        postmeme = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 21))

        onhold = len(await self.client.pool_pg.fetch("SELECT * FROM dankreminders"))
        embed = discord.Embed(title="Dank Memer Reminder Statistics", description=f"Fetched in {round(time.perf_counter() - timecounter, 3)} seconds.", color = self.client.embed_color, timestamp= discord.utils.utcnow())
        embed.add_field(name="Top 3 reminder types:", value=listof or "None", inline=True)
        embed.add_field(name="Top 3 reminder users:", value=listofreminders or "None", inline=True)
        embed.add_field(name="Number of activated settings", value=str(len(await self.client.pool_pg.fetch("SELECT * FROM remindersettings"))), inline=False)
        embed.add_field(name="History statistics", value=f"Since dawn of time: `{len(alltime)}`\nPast 24 hours: `{len(twentyfourhour)}`\nPast week: `{len(week)}`\nOn hold:`{onhold}`", inline=True)
        embed.add_field(name="History statistics",value=f"Daily: `{daily}`\nLottery: `{lottery}`\nWork: `{work}`\nPatreon: `{redeem}`\nWeekly: `{weekly}`\nMonthly: `{monthly}`\nHunt: `{hunt}`\nFish: `{fish}`\nDig: `{dig}`\nHighlow: `{highlow}`\nSnakeeyes: `{snakeeyes}`\nSearch: `{search}`\nCrime: `{crime}`\nBeg: `{beg}`\nDailybox: `{dailybox}`\nHorseshoe: `{horseshoe}`\nPizza: `{pizza}`", inline=True)
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
        dailytime, lotterytime, worktime, redeemtime, weeklytime, monthlytime, hunttime, fishtime, digtime, highlowtime, snakeeyestime, searchtime, crimetime, begtime, dailyboxtime, horseshoetime, pizzatime, droptime, pmtime, streamtime = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
        for reminder in reminders:
            if reminder.get('remindertype') == 2:
                dailytime = round(reminder.get('time')-time.time()) # time in discord time format
            if reminder.get('remindertype') == 3:
                weeklytime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 4:
                monthlytime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 5:
                lotterytime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 6:
                worktime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 7:
                redeemtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 8:
                hunttime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 9:
                fishtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 10:
                digtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 11:
                crimetime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 12:
                begtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 13:
                searchtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 14:
                snakeeyestime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 15:
                highlowtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 16:
                dailyboxtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 17:
                horseshoetime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 18:
                pizzatime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 20:
                streamtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 21:
                pmtime = round(reminder.get('time')-time.time())
        remindertimes = [dailytime or None, weeklytime or None, monthlytime or None, lotterytime or None, worktime or None, redeemtime or None, hunttime or None, fishtime or None, digtime or None, crimetime or None, begtime or None, searchtime or None, snakeeyestime or None, highlowtime or None, dailyboxtime or None, horseshoetime or None, pizzatime or None, droptime or None, streamtime or None, pmtime or None]
        newview = dankreminders(ctx, self.client, remindertimes, 15.0, truefalse(result.get('daily')), truefalse(result.get('weekly')), truefalse(result.get('monthly')), truefalse(result.get('lottery')), truefalse(result.get('work')), truefalse(result.get('redeem')), truefalse(result.get('hunt')), truefalse(result.get('fish')), truefalse(result.get('dig')), truefalse(result.get('crime')), truefalse(result.get('beg')), truefalse(result.get('search')), truefalse(result.get('snakeeyes')), truefalse(result.get('highlow')), truefalse(result.get('dailybox')), truefalse(result.get('horseshoe')), truefalse(result.get('pizza')), truefalse(result.get('drop')), truefalse(result.get('stream')), truefalse(result.get('postmeme')))
        message = await ctx.send(f"**{ctx.author}'s Dank Memer Reminders**\nSelect the button that corresponds to the reminder to enable/disable it.\n\nYou're currently {'reminded via **DMs**' if result.get('method') == 1 else 'reminded via **ping**' if result.get('method') == 2 else 'not reminded'} for your reminders.\nTo see the duration of your reminders in timestamp format, use `dv.dankcooldown` or `dv.dcd`.", view=newview)
        newview.response = message
        newview.result = result
        newview.rmtimes = remindertimes

    @checks.admoon()
    @commands.command(name="reminddrop")
    async def reminddrop(self, ctx):
        """
        Sets a Drop reminder.
        """
        await ctx.send("Setting up a drop reminder: **Step 1 of 3**:\nState the item that is being dropped. Use this format: `**ItemName** ItemEmoji`")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            item = await self.client.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long to respond. Cancelling reminder setup.")
        if item.content.lower() == "cancel":
            return await ctx.send("Cancelling reminder setup.")
        item = item.content.strip()
        await ctx.send("Setting up a drop reminder: **Step 2 of 3**:\nState the price of the item that is being dropped. Use this format: `**⏣ 1,234**` or `Likely **⏣ 1,234**` or `**Unknown**`")
        try:
            price = await self.client.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long to respond. Cancelling reminder setup.")
        if price.content.lower() == "cancel":
            return await ctx.send("Cancelling reminder setup.")
        price = price.content.strip()
        await ctx.send("Setting up a drop reminder: **Step 3 of 3**:\nState the time when the item will be dropped. It should be in epoch time.")
        try:
            droptime = await self.client.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long to respond. Cancelling reminder setup.")
        if droptime.content.lower() == "cancel":
            return await ctx.send("Cancelling reminder setup.")
        try:
            droptime = int(droptime.content)
        except ValueError:
            return await ctx.send("That's not a valid time. Cancelling reminder setup.")
        msg = f"<a:dv_pepeConfettiOwO:837712470902571008> An item from Dank Memer is dropping! <a:dv_pepeConfettiOwO:837712470902571008>\nItem: {item}\nCost: {price}\n\nYou can buy this item now!"
        confirmview = confirm(ctx, self.client, 10.0)
        confirmview.response = await ctx.send(f"I will send this message at <t:{droptime}>. Do you want to proceed?\n\n{msg}", view=confirmview)
        await confirmview.wait()
        if confirmview.returning_value == None:
            return await ctx.send("Cancelling reminder setup.")
        if confirmview.returning_value == False:
            return await ctx.send("Cancelling reminder setup.")
        await self.client.pool_pg.execute("INSERT INTO dankdrops VALUES($1, $2, $3, $4)", ctx.guild.id, item, price, droptime)
        await ctx.send("Reminder set!")

    @checks.admoon()
    @commands.command(name="drops")
    async def drops(self, ctx):
        """
        Lists all the drops that are currently set.
        """
        drops = await self.client.pool_pg.fetch("SELECT * FROM dankdrops WHERE guild_id=$1", ctx.guild.id)
        if not drops:
            return await ctx.send("No drops are currently set.")
        embed = discord.Embed(title="Dank Memer Drops", color=discord.Color.blue())
        for drop in drops:
            embed.add_field(name=drop.get("item"), value=f"Cost: {drop.get('price')}\nDrop Time: <t:{drop.get('time')}>")
        await ctx.send(embed=embed)

    @checks.admoon()
    @commands.command(name="trendinggame")
    async def trendinggame(self, ctx, *, game: str = None):
        """
        Set the current trending game.
        """
        if game is None:
            return await ctx.send("The current trending game is **{}**".format(self.trending_game))
        self.trending_game = game
        await ctx.send("I've set the current trending game. This is how it will look like:\n\nThe current trending game to stream is **{}**!".format(game))


    @checks.not_in_gen()
    @commands.command(name="dankcooldowns", aliases=["dankcd", "dcd"])
    async def dankcooldowns(self, ctx):
        """
        Shows the existing reminders for Dank memer.
        """
        reminders = await self.client.pool_pg.fetch("SELECT * FROM dankreminders WHERE member_id = $1 and guild_id = $2", ctx.author.id, ctx.guild.id)  # gets user's reminders
        dailytime, lotterytime, worktime, redeemtime, weeklytime, monthlytime, hunttime, fishtime, digtime, highlowtime, snakeeyestime, searchtime, crimetime, begtime, dailyboxtime, horseshoetime, pizzatime, streamtime, pmtime = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
        for reminder in reminders:
            if reminder.get('remindertype') == 2:
                dailytime = f"<t:{reminder.get('time')}:R>"  # time in discord time format
            if reminder.get('remindertype') == 3:
                weeklytime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 4:
                monthlytime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 5:
                lotterytime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 6:
                worktime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 7:
                redeemtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 8:
                hunttime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 9:
                fishtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 10:
                digtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 11:
                crimetime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 12:
                begtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 13:
                searchtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 14:
                snakeeyestime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 15:
                highlowtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 16:
                dailyboxtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 17:
                horseshoetime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 18:
                pizzatime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 20:
                streamtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 21:
                pmtime = f"<t:{reminder.get('time')}:R>"
        remindertimes = [dailytime or "**Ready!**", weeklytime or "**Ready!**", monthlytime or "**Ready!**",
                         lotterytime or "**Ready!**", worktime or "**Ready!**", redeemtime or "**Ready!**",
                         hunttime or "**Ready!**", fishtime or "**Ready!**", digtime or "**Ready!**", crimetime or "**Ready!**",
                         begtime or "**Ready!**", searchtime or "**Ready!**", snakeeyestime or "**Ready!**",
                         highlowtime or "**Ready!**", dailyboxtime or "**Ready!**", horseshoetime or "**Ready!**", pizzatime or "**Ready!**", streamtime or "**Ready!**", pmtime or "**Ready!**"]
        embed = discord.Embed(title="Your Dank Memer reminders", description="**Select the button that corresponds to the reminder to enable/disable it.**\nChange how you want to be reminded with the select menu.", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        embed.description = embed.description + f"""\nClaim daily <:DVB_calendar:873107952159059991>: {remindertimes[0]}
Claim weekly <:DVB_week:876711052669247528>: {remindertimes[1]}
Claim monthly <:DVB_month:876711072030150707>: {remindertimes[2]}
Enter the lottery <:DVB_lotteryticket:873110581085880321>: {remindertimes[3]}
Work <:DVB_workbadge:873110507605872650>: {remindertimes[4]}
Redeem donor rewards <:DVB_patreon:876628017194082395>: {remindertimes[5]}
Hunt <:DVB_rifle:888404394805186571>: {remindertimes[6]}
Fish <:DVB_fishing:888404317638369330>: {remindertimes[7]}
Dig <:DVB_shovel:888404340426031126>: {remindertimes[8]}
Crime <:DVB_Crime:888404653711192067>: {remindertimes[9]}
Beg <:DVB_beg:888404456356610099> : {remindertimes[10]}
Search <:DVB_search:888405048260976660>: {remindertimes[11]}
Snakeeyes <a:DVB_snakeeyes:888404298608812112>: {remindertimes[12]}
Highlow 🔢: {remindertimes[13]}
Use a dailybox <a:DVB_DailyBox:888404475470024785>: {remindertimes[14]}
Use a Horseshoe <:DVB_Horseshoe:888404491647463454>: {remindertimes[15]}
Use a Pizza <:DVB_pizza:888404502280024145>: {remindertimes[16]}
Stream 🎮: {remindertimes[17]}
Post memes <:DVB_Laptop:915524266940854303>: {remindertimes[18]}"""
        embed.description = embed.description + f"""\nClaim daily <:DVB_calendar:873107952159059991>: {remindertimes[0]}"""
        if ctx.author.id == 650647680837484556:
            embed.description = embed.description + "\nSlap Frenzy <a:DVB_pandaslap:876631217750048798>: **Always Ready**\nBonk Blu <a:DVB_bonk:877196623506194452>: **Always Ready**"
        embed.set_footer(text="To enable/disable reminders, use dv.dankreminder instead.", icon_url=ctx.guild.icon.url)
        await ctx.send(embed=embed)