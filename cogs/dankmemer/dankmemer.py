import json
import re
import time
import asyncio
from io import BytesIO
from typing import Tuple
import os

import discord
import operator

import pytz
from thefuzz import process

from cogs.dankmemer.lottery import Lottery
from main import dvvt
from utils import checks, buttons
import datetime
from discord.ext import commands, tasks, pages
from utils.format import print_exception, short_time, comma_number, stringnum_toint, number_to_emoji
from utils.buttons import *
from utils.specialobjects import DankItem
from .items import DankItems
import cogs.dankmemer


item_name_regex = re.compile(r"^(.+) \([\d,]*\)")
trade_val_re = re.compile(r"Average Value: \u23e3 ([\d,]*)")
server_coin_donate_re = re.compile(r"> You will donate \*\*\u23e3 ([\d,]*)\*\*")
server_item_donate_re = re.compile(r"\*\*(.*)\*\*")
serverpool_donate_log_channel_id = 871737314831908974 if os.getenv('state') == '1' else 1012700307383398430
dank_memer_id = 270904126974590976
cooldown_messages = ["Spam isn't cool fam",
                     'Woah now, slow it down',
                     'Take a chill pill',
                     'Hold your horses...',
                     'Take a breather...',
                     'Woah nelly, slow it down',
                     'Too spicy, take a breather'
                     ]

def print_dev(message):
    if os.getenv('state') == '0':
        print(message)
async def checkmark(message:discord.Message):
    try:
        await message.add_reaction("<:DVB_checkmark:955345523139805214>")
    except discord.NotFound:
        return None

def is_dank_slash_command(message: discord.Message, command: str):
    if message.author.id == dank_memer_id:
        if message._raw_data.get("interaction") is not None:
            if message._raw_data["interaction"].get("type") == 2:
                if message._raw_data["interaction"].get("name") == command:
                    return True
    return False


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
    try:
        await msg.add_reaction("<:DVB_crossmark:955345521151737896>")
    except Exception as e:
        pass


def switch_bool(boolean):
    if boolean is True:
        return False
    return True


def numberswitcher(no):
    if no == 1:
        return 0
    elif no == 0:
        return 1
    elif no == None:
        return 1
    else:
        return 0

class MockShiftView(discord.ui.View):
    def __init__(self, user: discord.Member):
        self.user = user
        super().__init__(timeout=180, disable_on_timeout=True)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return await interaction.response.send_message("not for u", ephemeral=True)
        return True

class MockShiftButton(discord.ui.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True

        await interaction.response.edit_message(view=self.view)
        await interaction.followup.send("Press **Dank Memer's button**, not me, you turd 😡", ephemeral=True)
        all_items_disabled = True
        for component in self.view.children:
            if isinstance(component, discord.ActionRow):
                for item in component.children:
                    if isinstance(item, discord.Button) or isinstance(item, discord.SelectMenu):
                        all_items_disabled = False
                        break
        if all_items_disabled:
            self.view.stop()


class ListOfStreamGames(discord.ui.Select):
    def __init__(self, current):
        self.current: Union[None, int] = current
        options = [
            discord.SelectOption(label="Apex Legends", value="0"),
            discord.SelectOption(label="COD MW2", value="1"),
            discord.SelectOption(label="CS GO", value="2"),
            discord.SelectOption(label="Dead by Daylight", value="3"),
            discord.SelectOption(label="Destiny 2", value="4"),
            discord.SelectOption(label="Dota 2", value="5"),
            discord.SelectOption(label="Elden Ring", value="6"),
            discord.SelectOption(label="Escape from Tarkov", value="7"),
            discord.SelectOption(label="FIFA 22", value="8"),
            discord.SelectOption(label="Fortnite", value="9"),
            discord.SelectOption(label="Grand Theft Auto V", value="10"),
            discord.SelectOption(label="Hearthstone", value="11"),
            discord.SelectOption(label="Just Chatting", value="12"),
            discord.SelectOption(label="League of Legends", value="13"),
            discord.SelectOption(label="Lost Ark", value="14"),
            discord.SelectOption(label="Minecraft", value="15"),
            discord.SelectOption(label="PUBG Battlegrounds", value="16"),
            discord.SelectOption(label="Rainbox Six Siege", value="17"),
            discord.SelectOption(label="Rocket League", value="18"),
            discord.SelectOption(label="Rust", value="19"),
            discord.SelectOption(label="Teamfight Tactics", value="20"),
            discord.SelectOption(label="Valorant", value="21"),
            discord.SelectOption(label="Warzone 2", value="22"),
            discord.SelectOption(label="World of Tanks", value="23"),
            discord.SelectOption(label="World of Warcraft", value="24"),
        ]
        if self.current is not None:
            options[self.current].default = True
        super().__init__(placeholder="Select today's trending game...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        for option in self.options:
            option.default = False
        index = int(self.values[0])
        self.options[index].default = True
        self.view.update = True
        self.view.trending_game = self.options[index].label
        self.current = index
        await interaction.response.edit_message(view=self.view)


class TrendingGameSetting(discord.ui.View):
    def __init__(self, index, trending_game, cog, ctx, client):
        self.active = True
        self.update = False
        self.cog: cogs.dankmemer.DankMemer = cog
        self.trending_game = trending_game
        self.index = index
        self.credits = ""
        self.ctx: DVVTcontext = ctx
        self.client = client
        self.response = None
        self.list_select = ListOfStreamGames(self.index)
        super().__init__(timeout=60)

        self.add_item(self.list_select)

    @discord.ui.button(label="Set Credits", style=discord.ButtonStyle.grey, emoji="🙋‍♂️", row=1)
    async def set_credits(self, button: discord.ui.Button, interaction: discord.Interaction):
        for c in self.children:
            c.disabled = True
        await interaction.response.edit_message(view=self)
        await self.ctx.send("Mention the user, give their username or username#discriminator.")
        try:
            m = await self.client.wait_for("message", check=lambda m: m.author.id == interaction.user.id and m.channel.id == self.ctx.channel.id, timeout=45)
        except asyncio.TimeoutError:
            await self.ctx.channel.send("You didn't respond on time.", delete_after=5)
        else:
            try:
                m_credits = await commands.MemberConverter().convert(self.ctx, m.content)
            except Exception as e:
                await interaction.response.send_message(f"Invalid member", delete_after=5)
            else:
                self.credits = str(m_credits)
                button.label = f"Set Credits ({m_credits})"
                self.update = True
        for c in self.children:
            c.disabled = False
        if self.active:
            await self.response.edit(view=self)

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.green, row=1)
    async def submit(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.update:
            if self.list_select.current is None:
                await interaction.response.send_message("You need to choose a trending game to submit.", ephemeral=True)
                return
            else:
                trending_game_str = self.trending_game
                if self.credits != "":
                    trending_game_str += f" (Credits: {self.credits})"
                self.cog.trending_game = (self.list_select.current, trending_game_str)
                await interaction.response.send_message(f"Trending game has been updated. This is how it will look like:\nThe current trending game to stream is **{self.cog.trending_game[1]}**!")
                for c in self.children:
                    c.disabled = True
                await self.response.edit(view=self)
                self.active = False
                self.stop()
        else:
            await interaction.response.send_message("There were no changes made, so nothing was updated.", ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(embed=discord.Embed(
                description="Only the author (`{}`) can interact with this message.".format(self.ctx.author),
                color=discord.Color.red()), ephemeral=True)
            return False
        else:
            return True

    async def on_timeout(self) -> None:
        for c in self.children:
            c.disabled = True
        await self.response.edit(view=self)
        await self.ctx.reply("The message has timed out. If you would still want to change the trending game, use `dv.trendinggame` again.")
        self.active = False
        self.stop()




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
            await self.client.db.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 1, self.context.author.id)
            await interaction.response.send_message("Got it. You will **now be DMed** for your enabled Dank Memer reminders, **with the exception** of **short** reminders (such as `hunt`, `dig`), which will still be sent in channels.", ephemeral=True)
        if self.values[0] == "Ping":
            await self.client.db.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 2, self.context.author.id)
            await interaction.response.send_message("Got it. You will **now be pinged in the channel where you used the command** for your enabled Dank Memer reminders.", ephemeral=True)
        if self.values[0] == "None":
            await self.client.db.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 0, self.context.author.id)
            await interaction.response.send_message("Got it. You will **not be reminded** for your Dank Memer actions.", ephemeral=True)

class dankreminders(discord.ui.View):
    def __init__(self, ctx: DVVTcontext, client, rmtimes, timeout, daily, weekly, monthly, lottery, work, hunt, fish, dig, crime, beg, search, scratch, horseshoe, pizza, drop, stream, postmeme, pet):
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
                          "<:DVB_workbadge:873110507605872650>",
                          "<:DVB_rifle:888404394805186571>", "<:DVB_fishing:888404317638369330>",
                          "<:DVB_shovel:888404340426031126>", "<:DVB_Crime:888404653711192067>",
                          "<:DVB_beg:888404456356610099>", "<:DVB_search:888405048260976660>",
                          "<:DVB_Scratch:1096020186450112512>", "<:DVB_Horseshoe:888404491647463454>",
                          "<:DVB_pizza:888404502280024145>", "<:DVB_sugarskull:904936096436215828>",
                          "🎮", "<:DVB_Laptop:915524266940854303>",
                          "<:DVB_pet:928236242469011476>"]
        labels = ["Claim daily", "Claim weekly",
                  "Claim monthly", "Enter the Lottery",
                  "Work",
                  "Hunt", "Fish",
                  "Dig", "Crime",
                  "Beg", "Search",
                  "Scratch-Off", "Use a horseshoe",
                  "Use a pizza", "Get drop items",
                  "Interact on stream", "Post memes",
                  "Interact with pet"]
        is_enabled = [daily, weekly, monthly, lottery, work, hunt, fish, dig, crime, beg, search, scratch, horseshoe, pizza, drop, stream, postmeme, pet]

        async def initialise_dank_reminders(user: Union[discord.Member, discord.User]):
            await self.client.db.execute("INSERT INTO remindersettings (member_id, method) VALUES ($1, $2) ON CONFLICT (member_id) DO UPDATE SET method = $2", user.id, 0)
            return await self.client.db.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", user.id)

        async def update_message(emoji, interaction: discord.Interaction):
            if str(emoji) == "<:DVB_calendar:873107952159059991>":
                await self.client.db.execute("UPDATE remindersettings SET daily = $1 WHERE member_id = $2", switch_bool(self.result.get('daily')), ctx.author.id)  # switches to enabled/disabled reminder
            elif str(emoji) == "<:DVB_week:876711052669247528>":
                await self.client.db.execute("UPDATE remindersettings SET weekly = $1 WHERE member_id = $2", switch_bool(self.result.get('weekly')), ctx.author.id)
            elif str(emoji) == "<:DVB_month:876711072030150707>":
                await self.client.db.execute("UPDATE remindersettings SET monthly = $1 WHERE member_id = $2", switch_bool(self.result.get('monthly')), ctx.author.id)
            elif str(emoji) == "<:DVB_lotteryticket:873110581085880321>":
                await self.client.db.execute("UPDATE remindersettings SET lottery = $1 WHERE member_id = $2", switch_bool(self.result.get('lottery')), ctx.author.id)
            elif str(emoji) == "<:DVB_workbadge:873110507605872650>":
                await self.client.db.execute("UPDATE remindersettings SET work = $1 WHERE member_id = $2", switch_bool(self.result.get('work')), ctx.author.id)
            elif str(emoji) == "<:DVB_rifle:888404394805186571>":
                await self.client.db.execute("UPDATE remindersettings SET hunt = $1 WHERE member_id = $2", switch_bool(self.result.get('hunt')), ctx.author.id)
            elif str(emoji) == "<:DVB_fishing:888404317638369330>":
                await self.client.db.execute("UPDATE remindersettings SET fish = $1 WHERE member_id = $2", switch_bool(self.result.get('fish')), ctx.author.id)
            elif str(emoji) == "<:DVB_shovel:888404340426031126>":
                await self.client.db.execute("UPDATE remindersettings SET dig = $1 WHERE member_id = $2", switch_bool(self.result.get('dig')), ctx.author.id)
            elif str(emoji) == "<:DVB_Crime:888404653711192067>":
                await self.client.db.execute("UPDATE remindersettings SET crime = $1 WHERE member_id = $2", switch_bool(self.result.get('crime')), ctx.author.id)
            elif str(emoji) == "<:DVB_beg:888404456356610099>":
                await self.client.db.execute("UPDATE remindersettings SET beg = $1 WHERE member_id = $2", switch_bool(self.result.get('beg')), ctx.author.id)
            elif str(emoji) == "<:DVB_search:888405048260976660>":
                await self.client.db.execute("UPDATE remindersettings SET search = $1 WHERE member_id = $2", switch_bool(self.result.get('search')), ctx.author.id)
            elif str(emoji) == "🔢":
                await self.client.db.execute("UPDATE remindersettings SET highlow = $1 WHERE member_id = $2", switch_bool(self.result.get('highlow')), ctx.author.id)
            elif str(emoji) == "<:DVB_Scratch:1096020186450112512>":
                await self.client.db.execute("UPDATE remindersettings SET scratch = $1 WHERE member_id = $2", switch_bool(self.result.get('scratch')), ctx.author.id)
            elif str(emoji) == "<:DVB_Horseshoe:888404491647463454>":
                await self.client.db.execute("UPDATE remindersettings SET horseshoe = $1 WHERE member_id = $2", switch_bool(self.result.get('horseshoe')), ctx.author.id)
            elif str(emoji) == "<:DVB_pizza:888404502280024145>":
                await self.client.db.execute("UPDATE remindersettings SET pizza = $1 WHERE member_id = $2", switch_bool(self.result.get('pizza')), ctx.author.id)
            elif str(emoji) == "<:DVB_sugarskull:904936096436215828>":
                await self.client.db.execute("UPDATE remindersettings SET drop = $1 WHERE member_id = $2", switch_bool(self.result.get('drop')), ctx.author.id)
            elif str(emoji) == "🎮":
                await self.client.db.execute("UPDATE remindersettings SET stream = $1 WHERE member_id = $2", switch_bool(self.result.get('stream')), ctx.author.id)
                if self.result.get('stream') != 1:
                    await interaction.response.send_message("__**Important!**__\nThis uses the username shown in the Stream Manager embed from Dank Memer to identify who used the command. If there're people with the same name as you, the reminder may not work.\nhttps://cdn.nogra.xyz/screenshots/Discord_cAJOC18PCV.png", ephemeral=True)
            elif str(emoji) == "<:DVB_Laptop:915524266940854303>":
                await self.client.db.execute("UPDATE remindersettings SET postmeme = $1 WHERE member_id = $2", switch_bool(self.result.get('postmeme')), ctx.author.id)
            elif str(emoji) == "<:DVB_pet:928236242469011476>":
                await self.client.db.execute("UPDATE remindersettings SET pet = $1 WHERE member_id = $2", switch_bool(self.result.get('pet')), ctx.author.id)
                if self.result.get('pet') != 1:
                    await interaction.response.send_message("__**Important!**__\nThis uses the username shown in your pet's embed from Dank Memer to identify who used the command. If there're people with the same username as you, the reminder may not work.\nhttps://cdn.nogra.xyz/screenshots/Discord_YVzJYHhFVa.png", ephemeral=True)
            elif str(emoji) == "🚀":
                await self.client.db.execute("UPDATE remindersettings SET adventure = $1 WHERE member_id = $2", switch_bool(self.result.get('adventure')), ctx.author.id)
            self.result = await self.client.db.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id)
            self.children[reminderemojis.index(str(emoji))].style = discord.ButtonStyle.red if is_enabled[reminderemojis.index(str(emoji))] is True else discord.ButtonStyle.green
            is_enabled[reminderemojis.index(str(emoji))] = False if is_enabled[reminderemojis.index(str(emoji))] is True else True
            if interaction.response.is_done():
                await interaction.followup.edit_message(message_id=interaction.message.id, view=self)
            else:
                await interaction.response.edit_message(view=self)

        async def change_view2(interaction):
            self.clear_items()
            self.add_item(VoteSetting(self.client, self.context, self.response))
            self.add_item(somebutton(label="Toggle reminders", style=discord.ButtonStyle.grey))
            await interaction.response.edit_message(view=self)

        async def change_view1(interaction):
            self.clear_items()
            for emoji in reminderemojis:
                self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[reminderemojis.index(emoji)] + f"{'' if self.rmtimes[reminderemojis.index(emoji)] is None else f' - {short_time(self.rmtimes[reminderemojis.index(emoji)])}'}", style=discord.ButtonStyle.green if is_enabled[ reminderemojis.index(emoji)] else discord.ButtonStyle.red))
            self.add_item(somebutton(label="Change Reminder type", style=discord.ButtonStyle.grey))
            await interaction.response.edit_message(view=self)

        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                if self.label == "Change Reminder type":
                    await change_view2(interaction)
                elif self.label == "Toggle reminders":
                    await change_view1(interaction)
                else:
                    await update_message(self.emoji, interaction)


        for emoji in reminderemojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[reminderemojis.index(emoji)] + f"{'' if self.rmtimes[reminderemojis.index(emoji)] is None else f' - {short_time(self.rmtimes[reminderemojis.index(emoji)])}'}", style=discord.ButtonStyle.green if is_enabled[reminderemojis.index(emoji)] else discord.ButtonStyle.red))
        self.add_item(somebutton(label="Change Reminder type", style=discord.ButtonStyle.grey))

        #self.add_item(VoteSetting(self.client, self.context, self.response))

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


def get_shared_user_name(embed: discord.Embed):
    if embed.fields is not None and len(embed.fields) > 0:
        if isinstance(embed.fields[0].name, str):
            if embed.fields[0].name.startswith("Shared"):
                ending = ["'s Wallet", "'s Pocket"]
            elif embed.fields[0].name.startswith("Gifted"):
                ending = " now has"
            else:
                raise ValueError
            userdetail_field = embed.fields[2].name
            if isinstance(userdetail_field, str):
                for ending_type in ending:
                    if userdetail_field.endswith(ending_type):
                        return userdetail_field[:-len(ending_type)]


class DankMemer(DankItems, Lottery, commands.Cog, name='dankmemer'):
    """
    Dank Memer utilities
    """
    def __init__(self, client):
        self.client:dvvt = client
        self.dankmemerreminders.start()
        self.dropreminder.start()
        self.fighters = {}
        self.trending_game: Tuple[int, str] = (None, None)
        self.reset_trending_game.start()
        self.reminders = {
            2: "daily",
            3: "weekly",
            4: "monthly",
            5: "lottery",
            6: "work",
            7: "redeem",
            8: "hunt",
            9: "fish",
            10: "dig",
            11: "crime",
            12: "beg",
            13: "search",
            14: "scratch",
            15: "highlow",
            17: "horseshoe",
            18: "pizza",
            20: "stream",
            21: "postmeme",
            22: "marriage",
            23: "pet",
            24: "adventure",
            1001: "stream",
            1002: "stream"
        } # for checking reminder settings


    async def wait_for_edit(self, message: discord.Message):
        def check_hl(payload_before, payload_after):
            return payload_after.id == message.id

        try:
            await self.client.wait_for("message_edit", check=check_hl, timeout=30.0)
        except asyncio.TimeoutError:
            return False
        else:
            return True


    def cog_unload(self):
        self.dankmemerreminders.stop()
        self.dropreminder.stop()
        self.reset_trending_game.stop()

    async def handle_reminder_entry(self, member_id, remindertype, channel_id, guild_id, time, uses_name: Optional[bool] = False):
        if uses_name:
            guild = self.client.get_guild(guild_id)
            member = guild.get_member(member_id)
            users_with_the_same_name = [m for m in guild.members if m.name == member.name]
            if len(users_with_the_same_name) > 1:
                for m in users_with_the_same_name:
                    query = "SELECT {} FROM remindersettings WHERE member_id = $1".format(self.reminders[remindertype])
                    if await self.client.db.fetchval(query, m.id) == 1:
                        member_id = m.id
                        break
        existing = await self.client.db.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member_id, remindertype)
        if len(existing) > 0:
            await self.client.db.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", time, member_id, remindertype)
        else:
            await self.client.db.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member_id, remindertype, channel_id, guild_id, time)

    @tasks.loop(hours=24.0)
    async def reset_trending_game(self):
        self.trending_game = (None, None)

    @reset_trending_game.before_loop
    async def wait_until_utc(self):
        await self.client.wait_until_ready()
        now = discord.utils.utcnow()
        next_run = now.replace(hour = 0, minute = 0, second = 0)
        if next_run <= now:
            next_run += datetime.timedelta(days=1)
        await discord.utils.sleep_until(next_run)


    @tasks.loop(seconds=5.0)
    async def dropreminder(self):
        try:
            await self.client.wait_until_ready()
            drop = await self.client.db.fetchrow("SELECT * FROM dankdrops WHERE time < $1", round(time.time()))
            if drop is None:
                return
            else:
                price = drop.get('price')
                guild = self.client.get_guild(drop.get('guild_id'))
                name = drop.get('name')
                enabled = await self.client.db.fetch("SELECT * FROM remindersettings WHERE drop = $1", True)
                # crafting messages
                msg = f"""
                <a:dv_pepeConfettiOwO:837712470902571008> An item from Dank Memer is dropping! <a:dv_pepeConfettiOwO:837712470902571008>\nItem: {name}\nCost: {price}\n\nYou can buy this item now! </drops:1011560371078832205>
                """
                dm_msg = f"""
                                <a:dv_pepeConfettiOwO:837712470902571008> An item from Dank Memer is dropping! <a:dv_pepeConfettiOwO:837712470902571008>\nItem: {name}\nCost: {price}\n\nHead to <@270904126974590976> to buy this item!
                                """
                if drop.get('time') == 1666490390:
                    msg.replace("You can buy this item now! </drops:1011560371078832205>", "You can buy this item in Dank Vibes, a Dank Memer partnered server! Run </drops:1011560371078832205>.")
                messages = []
                ids = [i.get('member_id') for i in enabled]
                tempmsg = f'{msg}\n\n'
                for i in ids:
                    member = guild.get_member(i)
                    if member is not None:
                        remindersettings = await self.client.db.fetchval("SELECT method FROM remindersettings WHERE member_id = $1", i)
                        if remindersettings == 1:
                            try:
                                await member.send(dm_msg)
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
                await self.client.db.execute("DELETE FROM dankdrops WHERE guild_id = $1 AND name = $2 AND price = $3 AND time = $4", drop.get('guild_id'), drop.get('name'), drop.get('price'), drop.get('time'))
        except Exception as error:
            traceback_error = print_exception(f'Ignoring exception in RealReminder task', error)
            embed = discord.Embed(color=0xffcccb,
                                  description=f"Error encountered on Drop reminders.\n```py\n{traceback_error}```",
                                  timestamp=discord.utils.utcnow())
            if len(embed) < 6000:
                await self.client.get_guild(871734809154707467).get_channel(871737028105109574).send(embed=embed)
            else:
                await self.client.get_guild(871734809154707467).get_channel(871737028105109574).send("There was an error in Drop reminders, check the log for details.")

    @tasks.loop(seconds=1.0)
    async def dankmemerreminders(self):
        try:
            await self.client.wait_until_ready()
            if self.client.maintenance.get(self.qualified_name):
                return
            results = await self.client.db.fetch("SELECT * FROM dankreminders where time < $1", round(time.time()))  # all reminders that are due for reminding
            if len(results) == 0:
                return
            for result in results:

                if result.get('remindertype') == 1001 or result.get('remindertype') == 1002: # stream subreminders
                    check_reminder_enabled_index = 20
                else:
                    check_reminder_enabled_index = result.get('remindertype')

                config = await self.client.db.fetchrow("SELECT member_id, method, daily, weekly, monthly, lottery, work, redeem, hunt, fish, dig, crime, beg, search, scratch, highlow, dailybox, horseshoe, pizza, drop, stream, postmeme, marriage, pet, adventure FROM remindersettings WHERE member_id = $1", result.get('member_id')) # get the user's configuration
                if config is None: # no config means user doesn't even use this reminder system lol
                    pass
                elif result.get('remindertype') not in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 1001, 1002]: # if the reminder type is not a valid one
                    pass
                elif config[check_reminder_enabled_index] is not True:  # activity specific reminder check
                    pass
                elif config.get('method') == 0:  # chose not to be reminded
                    pass
                elif config.get('method') in [1, 2]:  # DMs or Mentions
                    def dm_message(reminderaction):
                        if reminderaction == 2:
                            return "**claim your `/daily`** <:DVB_calendar:873107952159059991>"
                        elif reminderaction == 3:
                            return "**claim your `/weekly`** <:DVB_week:876711052669247528> "
                        elif reminderaction == 4:
                            return "**claim your `/monthly`** <:DVB_month:876711072030150707>\n**NOTE:** you need to have purchased the **Monthly Coins** upgrade in `/advancements upgrades` to use the command. (⏣ 15,000,000)"
                        elif reminderaction == 5:
                            return "**enter the `/lottery`** <:DVB_lotteryticket:873110581085880321>"
                        elif reminderaction == 6:
                            return "**work again** <:DVB_workbadge:873110507605872650>"
                        elif reminderaction == 7:
                            return "**redeem your Patreon perks** <:DVB_patreon:876628017194082395>"
                        elif reminderaction == 8:
                            return "`/hunt` <:DVB_rifle:888404394805186571> "
                        elif reminderaction == 9:
                            return "`/fish` <:DVB_fishing:888404317638369330>"
                        elif reminderaction == 10:
                            return "`/dig` <:DVB_shovel:888404340426031126>"
                        elif reminderaction == 11:
                            return "`/crime` <:DVB_Crime:888404653711192067>"
                        elif reminderaction == 12:
                            return "`/beg` <:DVB_beg:888404456356610099>"
                        elif reminderaction == 13:
                            return "`/search` <:DVB_search:888405048260976660>"
                        elif reminderaction == 14:
                            return "`/scratch` <:DVB_Scratch:1096020186450112512>"
                        elif reminderaction == 15:
                            return "`/highlow` 🔢"
                        elif reminderaction == 17:
                            return "**use a horseshoe** <:DVB_Horseshoe:888404491647463454>"
                        elif reminderaction == 18:
                            return "**use a pizza** <:DVB_pizza:888404502280024145>"
                        elif reminderaction == 20:
                            return "**Interact with your stream** 🎮"
                        elif reminderaction == 21:
                            return "`/postmemes` <:DVB_Laptop:915524266940854303>"
                        elif reminderaction == 22:
                            return "**interact with your marriage partner** <:DVB_Ring:928236453920669786>"
                        elif reminderaction == 23:
                            return "**interact with your pet** <:DVB_pet:928236242469011476>"
                        elif reminderaction == 24:
                            return "**continue your adventure** 🚀"
                        elif reminderaction == 1001:
                            return "**start a stream again** 🎮"
                        elif reminderaction == 1002:
                            return "**start a stream again** (for your stream streak) 🎮"
                    def ping_message(reminderaction):
                        if reminderaction == 2:
                            return "**claim your </daily:1011560370864930856>** <:DVB_calendar:873107952159059991>"
                        elif reminderaction == 3:
                            return "**claim your </weekly:1011560370948800549>** <:DVB_week:876711052669247528> "
                        elif reminderaction == 4:
                            return "**claim your </monthly:1011560370911072262>** <:DVB_month:876711072030150707>\n**NOTE:** you need to have purchased the **Monthly Coins** upgrade in `/advancements upgrades` to use the command. (⏣ 15,000,000)"
                        elif reminderaction == 5:
                            return "**enter the </lottery:1011560370911072260>** <:DVB_lotteryticket:873110581085880321>"
                        elif reminderaction == 6:
                            return "**</work shift:1011560371267579942>** <:DVB_workbadge:873110507605872650>"
                        elif reminderaction == 7:
                            return "**redeem your Patreon perks** <:DVB_patreon:876628017194082395>"
                        elif reminderaction == 8:
                            return "</hunt:1011560371171102760> <:DVB_rifle:888404394805186571> "
                        elif reminderaction == 9:
                            return "</fish:1011560371078832206> <:DVB_fishing:888404317638369330>"
                        elif reminderaction == 10:
                            return "</dig:1011560371078832204> <:DVB_shovel:888404340426031126>"
                        elif reminderaction == 11:
                            return "</crime:1011560371078832202> <:DVB_Crime:888404653711192067>"
                        elif reminderaction == 12:
                            return "</beg:1011560371041095699> <:DVB_beg:888404456356610099>"
                        elif reminderaction == 13:
                            return "</search:1011560371267579935> <:DVB_search:888405048260976660>"
                        elif reminderaction == 14:
                            return "</scratch:1011560371267579934> <:DVB_Scratch:1096020186450112512>"
                        elif reminderaction == 15:
                            return "</highlow:1011560370911072258> 🔢"
                        elif reminderaction == 17:
                            return "**</use:1011560371267579941> a horseshoe** <:DVB_Horseshoe:888404491647463454>"
                        elif reminderaction == 18:
                            return "**</use:1011560371267579941> a pizza** <:DVB_pizza:888404502280024145>"
                        elif reminderaction == 20:
                            return "**Interact with your </stream:1011560371267579938>** 🎮"
                        elif reminderaction == 21:
                            return "</postmemes:1011560370911072263> <:DVB_Laptop:915524266940854303>"
                        elif reminderaction == 22:
                            return "**interact with your marriage partner** <:DVB_Ring:928236453920669786>"
                        elif reminderaction == 23:
                            return "**interact with your </pets care:1011560371171102768>** <:DVB_pet:928236242469011476>"
                        elif reminderaction == 24:
                            return "**continue your </adventure:1011560371041095695>** 🚀"
                        elif reminderaction == 1001:
                            return "**start a </stream:1011560371267579938> again** 🎮"
                        elif reminderaction == 1002:
                            return "**start a </stream:1011560371267579938> again** (for your stream streak) 🎮"
                    try:
                        member = self.client.get_guild(result.get('guild_id')).get_member(result.get('member_id'))
                        channel = self.client.get_channel(result.get('channel_id'))
                    except AttributeError: # member is none or channel is none
                        pass
                    else:
                        if member is None or channel is None:
                            pass
                        elif config.get('method') == 1:  # DMs or is lottery/daily reminder
                            if result.get('remindertype') in [8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 21]:
                                try:
                                    await channel.send(f"{member.mention} You can now {ping_message(result.get('remindertype'))}")  # DM
                                except:
                                    await member.send(f"You can now {dm_message(result.get('remindertype'))} ({channel.mention})")  # DM
                            else:
                                try:
                                    await member.send(f"You can now {dm_message(result.get('remindertype'))} ({channel.mention})") # DM
                                except discord.Forbidden:
                                    try:
                                        await channel.send(f"{member.mention} {self.client.user.name} is unable to DM you.\nTo receive Dank Memer reminders properly, open your DMs or switch to ping reminders via `dv.drm ping`. Your reminders have been disabled for now.")
                                    except:
                                        pass
                                    await self.client.db.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 0, result.get('member_id')) # change reminder settings to None
                        elif config.get('method') == 2: # Mention
                            try:
                                await channel.send(f"{member.mention} you can now {ping_message(result.get('remindertype'))}")
                            except:
                                pass
                    await self.client.db.execute("INSERT into stats(member_id, remindertype, time) VALUES($1, $2, $3)", result.get('member_id'), result.get('remindertype'), result.get('time'))
                await self.client.db.execute("DELETE from dankreminders WHERE member_id = $1 and remindertype = $2 and channel_id = $3 and guild_id = $4 and time = $5", result.get('member_id'), result.get('remindertype'), result.get('channel_id'), result.get('guild_id'), result.get('time'))
        except Exception as error:
            traceback_error = print_exception(f'Ignoring exception in Reminder task', error)
            embed = discord.Embed(color=0xffcccb,
                                  description=f"Error encountered on a Reminder task.\n```py\n{traceback_error}```",
                                  timestamp=discord.utils.utcnow())
            if len(embed) > 6000:
                await self.client.get_guild(871734809154707467).get_channel(871737028105109574).send("There was en error with Dank reminders, check the log for more info.")
            else:
                await self.client.get_guild(871734809154707467).get_channel(871737028105109574).send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot and message.author.id != dank_memer_id:
            return
        if self.client.maintenance.get(self.qualified_name) and await self.client.db.fetchval("SELECT enabled FROM devmode WHERE user_id = $1", message.author.id) is not True:
            return
        if not message.guild:
            return
        #if message.guild.id != 1288032530569625660:
#            return
        """
        Serverevents Donate
        """
        if message.author.id == dank_memer_id and len(message.embeds) > 0 and message.reference is not None:
            guild_settings = await self.client.get_guild_settings(message.guild.id)
            if guild_settings.serverpool_donation_log is True:
                embed = message.embeds[0]
                if type(embed.description) == str and "Successfully donated!" in embed.description:
                    m_reference = message.reference
                    if m_reference.cached_message is None:
                        original_message = await message.channel.fetch_message(m_reference.channel_id)
                    else:
                        original_message = m_reference.cached_message
                    coins, item_count, item = None, None, None
                    if original_message.interaction.name == "serverevents donate" and len(original_message.embeds) > 0:
                        e = original_message.embeds[0]
                        coins_line = e.description.split('\n')[2]
                        coins_re = re.findall(server_coin_donate_re, coins_line)
                        if len(coins_re) > 0: # match for coins in embed found
                            try:
                                coins = int(coins_re[0].replace(',', ''))
                            except ValueError:
                                pass
                        else: #most likely item or error
                            item_str_raw = re.findall(server_item_donate_re, coins_line)
                            if len(item_str_raw) > 0:
                                items_raw_str = item_str_raw[0]
                                items_raw = items_raw_str.split(' ')
                                if len(items_raw) >= 3: # "<count> <emoji> <item name...>"
                                    item_count = int(items_raw[0].replace(',', '').strip())
                                    item_name_joined = ' '.join(items_raw[2:])
                                    item_name = item_name_joined.strip()
                                    a = await self.client.db.fetchrow("SELECT * FROM dankitems WHERE name = $1 OR plural_name = $1", item_name)
                                    if a is not None:
                                        item = DankItem(a)
                                    else:
                                        item = item_name
                        if (coins is not None) or (item is not None and item_count is not None):
                            embed = discord.Embed(title="Server Pool Donation", color=discord.Color.brand_green(), timestamp=discord.utils.utcnow())
                            embed.set_author(name=f"{original_message.interaction.user}", icon_url=original_message.interaction.user.display_avatar.url)
                            embed.set_footer(text=f"{original_message.interaction.user.id}")
                            if coins is not None:
                                embed.description = f"**\u23e3 {comma_number(coins)}**"
                                content = ""
                            else:
                                if isinstance(item, DankItem): # is a valid item that can be found in the database
                                    embed.description = f"**{comma_number(item_count)} {item.name}**\nWorth \u23e3 {comma_number(item_count*item.trade_value)}"
                                    embed.set_thumbnail(url=item.image_url)
                                    content = ""
                                else:
                                    embed.description = f"**{comma_number(item_count)} {item}**\nWorth \u23e3 0 (unknown item)"
                                    content = "<@312876934755385344>"
                            log_channel = self.client.get_channel(serverpool_donate_log_channel_id)
                            if log_channel is not None:
                                webh = await self.client.get_webhook(log_channel)
                                view = SingleURLButton(message.jump_url, f"Jump to Message in #{message.channel.name}", None)
                                try:
                                    await webh.send(content=content, username=self.client.user.name, avatar_url=self.client.user.display_avatar.url, embed=embed, view=view)
                                except Exception as a:
                                    print(a)

        """
        Let's update trade values first
        """
        def get_item_details(m: discord.Message) -> Union[tuple, None]:
            item_name = None
            item_worth = None
            item_type = None
            item_thumbnail_url = None
            if len(m.embeds) != 1:
                print_dev(f"Message {m.id} has {len(m.embeds)} embeds, expected 1")
                return
            embed = m.embeds[0]
            if type(embed.title) != str:
                print_dev(f"Message {m.id} has an embed with a non-string title")
                return
            item_name = embed.title
            if type(embed.fields) == list:
                if embed.footer is not None and type(embed.footer.text) == str:
                    if "|" in embed.footer.text:
                        item_type_format = embed.footer.text.split('|')[-1].strip()
                    else:
                        item_type_format = embed.footer.text
                    item_type = " ".join(item_type_format.split(" ")[1:])
                else:
                    print_dev(f"Message {m.id} has an embed with a non-string footer")
                    return
                if embed.fields != None and len(embed.fields) > 0:
                    supposed_market_field = embed.fields[0]
                    if supposed_market_field.name == "Market":
                        item_worth_raw = re.findall(trade_val_re, supposed_market_field.value)
                        print_dev(item_worth_raw)
                        if len(item_worth_raw) > 0:
                            item_worth = int(item_worth_raw[0].replace(',', ''))
                        else:
                            print_dev("Trade value regex found no results")
                            return
                    else:
                        print_dev(f"Message {m.id} has an embed with a non-market field")
                        return
            else:
                print_dev(f"Message {m.id} has an embed with non-list fields")
                return
            print_dev(f"Message {m.id} item_name={item_name}, item_worth={item_worth}, item_type={item_type}")
            if item_name is None or item_worth is None or item_type is None:
                return
            if type(embed.thumbnail.url) == str:
                item_thumbnail_url = embed.thumbnail.url
            return item_name, item_worth, item_type, item_thumbnail_url
        if (item := get_item_details(message)) is not None:
            item_name, item_worth, item_type,  item_thumnail_url = item
            existing_item = await self.client.db.fetchrow("SELECT * FROM dankitems WHERE name = $1", item_name)
            if existing_item is not None:
                if existing_item.get('overwrite') is not True:
                    if existing_item.get('trade_value') != item_worth:
                        await self.client.db.execute("UPDATE dankitems SET name = $1, trade_value = $2, type = $3, image_url = $4, last_updated = $5 WHERE name = $1", item_name, item_worth, item_type, item_thumnail_url, round(time.time()))
                else:
                    pass
            else:
                new_idcode = ''.join([i for i in item_name if i.isalpha()])
                await self.client.db.execute("INSERT INTO dankitems (name, idcode, type, image_url, trade_value, last_updated, overwrite) VALUES ($1, $2, $3, $4, $5, $6, $7)", item_name, new_idcode, item_type, item_thumnail_url, item_worth, round(time.time()), False)
        """
        Daily reminder
        """
        if is_dank_slash_command(message, 'daily'):
            member = message.interaction_metadata.user
            now = discord.utils.utcnow()
            next_reminder_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            nextdailytime = round(next_reminder_time.timestamp())
            await self.handle_reminder_entry(member.id, 2, message.channel.id, message.guild.id, nextdailytime)
            with contextlib.suppress(discord.HTTPException):
                await clock(message)
        """
        Weekly Reminder
        """
        if is_dank_slash_command(message, 'weekly'):
            member = message.interaction_metadata.user
            today = datetime.date.today()
            days_ahead = 0 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_weekly_date = today + datetime.timedelta(days_ahead)
            next_weekly_datetime = datetime.datetime.combine(next_weekly_date, datetime.time.min, tzinfo=pytz.UTC)
            nextweeklytime = next_weekly_datetime.timestamp()
            await self.handle_reminder_entry(member.id, 3, message.channel.id, message.guild.id, nextweeklytime, uses_name=True)
            with contextlib.suppress(discord.HTTPException):
                await clock(message)
        """
        Monthly Reminder
        """
        if is_dank_slash_command(message, 'monthly'):
            if len(message.embeds) == 0 or ("You can buy the ability" not in message.embeds[0].description):
                member = message.interaction_metadata.user
                now = discord.utils.utcnow()
                next_monthly_datetime = (now.replace(day=1) + datetime.timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                nextmonthlytime = next_monthly_datetime.timestamp()
                await self.handle_reminder_entry(member.id, 4, message.channel.id, message.guild.id, nextmonthlytime, uses_name=True)
                with contextlib.suppress(discord.HTTPException):
                    await clock(message)
        """
        Lottery reminder
        """
        if is_dank_slash_command(message, "lottery") and len(message.embeds) > 0 and message.embeds[0].title == "Pending Confirmation" and "tryna buy" in message.embeds[0].description:
            member = message.interaction_metadata.user
            def check_lottery(payload_before, payload_after):
                return message.id == payload_after.id
            try:
                before, newedit = await self.client.wait_for("message_edit", check=check_lottery, timeout=20)
            except asyncio.TimeoutError:
                return await crossmark(message)
            else:
                if not newedit.embeds[0].title:
                    return
                if newedit.embeds[0].title == "Action Canceled" or message.embeds[0].title == "Action Canceled":
                    return await message.add_reaction("<:DVB_crossmark:955345521151737896>")
                if newedit.embeds[0].title == "Action Confirmed":
                    now = discord.utils.utcnow()
                    now = now + datetime.timedelta(hours=1)
                    now = now.replace(minute=0, second=0, microsecond=0)
                    nextlotterytime = round(now.timestamp()) + 30
                    await self.handle_reminder_entry(member.id, 5, message.channel.id, message.guild.id, nextlotterytime)
                    with contextlib.suppress(discord.HTTPException):
                        await clock(newedit)
        """
        Hunting Reminder
        """
        if is_dank_slash_command(message, 'hunt') and message.embeds[0].title not in cooldown_messages:
            member = message.interaction.user
            nexthunttime = round(time.time()) + 25
            await self.handle_reminder_entry(member.id, 8, message.channel.id, message.guild.id, nexthunttime)
        """
        Fishing Reminder
        """
        if is_dank_slash_command(message, 'fish') and message.embeds[0].title not in cooldown_messages:
            member = message.interaction.user
            nextfishtime = round(time.time()) + 25
            await self.handle_reminder_entry(member.id, 9, message.channel.id, message.guild.id, nextfishtime)
        """
        Dig Reminder
        """
        if is_dank_slash_command(message, 'dig') and message.embeds[0].title not in cooldown_messages:
            member = message.interaction.user
            nextdigtime = round(time.time()) + 25
            await self.handle_reminder_entry(member.id, 10, message.channel.id, message.guild.id, nextdigtime)
        """
        Highlow Reminder
        """
        # this requires advanced coding because the cooldown only occurs after the user "guessed" the number
        if is_dank_slash_command(message, 'highlow') and message.embeds[0].title not in cooldown_messages:
            if await self.wait_for_edit(message) is not True:
                return await crossmark(message)
            else:
                member = message.interaction.user
                nexthighlowtime = round(time.time()) + 15
                await self.handle_reminder_entry(member.id, 15, message.channel.id, message.guild.id, nexthighlowtime)
        """
        Snakeeyes Reminder
        """
        if is_dank_slash_command(message, 'snakeeyes') and message.embeds[0].title not in cooldown_messages:
            member = message.interaction.user
            nextsnakeeyestime = round(time.time()) + 5
            await self.handle_reminder_entry(member.id, 14, message.channel.id, message.guild.id, nextsnakeeyestime)
        """
        Search Reminder
        """
        if is_dank_slash_command(message, 'search') and message.embeds[0].title not in cooldown_messages:
            if await self.wait_for_edit(message) is not True:
                return await crossmark(message)
            else:
                member = message.interaction.user
                nextsearchtime = round(time.time()) + 15
                await self.handle_reminder_entry(member.id, 13, message.channel.id, message.guild.id, nextsearchtime)
        """
        Crime Reminder
        """
        if is_dank_slash_command(message, 'crime') and message.embeds[0].title not in cooldown_messages:
            if await self.wait_for_edit(message) is not True:
                return await crossmark(message)
            else:
                member = message.interaction.user
                nextcrimetime = round(time.time()) + 15
                await self.handle_reminder_entry(member.id, 11, message.channel.id, message.guild.id, nextcrimetime)
        """
        Beg Reminder
        """
        if is_dank_slash_command(message, 'beg') and message.embeds[0].title not in cooldown_messages:
            member = message.interaction.user
            nextbegtime = round(time.time()) + 25
            await self.handle_reminder_entry(member.id, 12, message.channel.id, message.guild.id, nextbegtime)
        """
        Horseshoe Reminder
        """
        if is_dank_slash_command(message, 'use'):
            if type(message.embeds[0].description) == str and "Lucky Horseshoe" in message.embeds[0].description and "15 minutes" in message.embeds[0].description:
                member = message.interaction.user
                nexthorseshoetime = round(time.time()) + 900
                await self.handle_reminder_entry(member.id, 17, message.channel.id, message.guild.id, nexthorseshoetime)
                with contextlib.suppress(discord.HTTPException):
                    await message.add_reaction('<:DVB_Horseshoe:888404491647463454>')
        """
        Pizza Reminder
        """
        if is_dank_slash_command(message, 'use'):
            if type(message.embeds[0].description) == str and "perfect slice of pizza" in message.embeds[0].description and "the next hour" in message.embeds[0].description:
                member = message.interaction.user
                nextpizzatime = round(time.time()) + 3600
                await self.handle_reminder_entry(member.id, 18, message.channel.id, message.guild.id, nextpizzatime)
                with contextlib.suppress(discord.HTTPException):
                    await message.add_reaction('<:DVB_pizza:888404502280024145>')
        """
        Postmeme reminder
        """
        if is_dank_slash_command(message, 'postmemes') and message.embeds[0].title not in cooldown_messages:
            await self.wait_for_edit(message)
            member = message.interaction.user
            nextpostmemetime = round(time.time()) + 45
            await self.handle_reminder_entry(member.id, 21, message.channel.id, message.guild.id, nextpostmemetime)

        """
        Stream Start Reminder
        """
        if is_dank_slash_command(message, "stream"):
            if len(message.embeds) > 0:
                embed = message.embeds[0]
                if len(embed.fields) == 6:
                    if embed.fields[1].name == "Last Live":
                        field_value = embed.fields[1].value
                        try:
                            timestamp_of_ended_stream = int(field_value.split(':')[1])
                        except:
                            pass
                        else:
                            member = message.interaction.user
                            timestamp_to_restart_stream = timestamp_of_ended_stream + 1800
                            if timestamp_to_restart_stream > round(time.time()):
                                await self.handle_reminder_entry(member.id, 1001, message.channel.id, message.guild.id, timestamp_to_restart_stream, uses_name=True)
                                await clock(message)


    @commands.Cog.listener()
    async def on_message_edit(self, beforemsg: discord.Message, aftermsg: discord.Message):
        #
        """
        Work Reminder
        """
        if beforemsg.author.id != dank_memer_id:
            return
        if len(beforemsg.embeds) == 0 or len(aftermsg.embeds) == 0:
            return
        if is_dank_slash_command(beforemsg, 'work shift'):
            member = aftermsg.interaction_metadata.user
            if type(aftermsg.embeds[0].title) == str and ("Terrible work!" in aftermsg.embeds[0].title or "Great work!" in aftermsg.embeds[0].title):
                nextworktime = round(time.time()) + 3600
                await self.handle_reminder_entry(member.id, 6, aftermsg.channel.id, aftermsg.guild.id, nextworktime)
                with contextlib.suppress(discord.HTTPException):
                    await checkmark(aftermsg)

                if beforemsg.embeds[0] and beforemsg.embeds[0].description and aftermsg.embeds[0] and aftermsg.embeds[0].description:

                    if beforemsg.embeds[0].description.startswith("Look at each color next to the words closely!"):
                        description_lines = beforemsg.embeds[0].description.split("\n")
                        color_words = []
                        color_word_regex = r"<:([a-zA-Z0-9_]+):\d+>|`([^`]+)`"
                        for line in description_lines[1:]:
                            results = re.findall(color_word_regex, line)
                            if len(results) > 0:
                                # results is example [('White', ''), ('', 'domestic')]
                                # We need to convert it to ['White', 'domestic']
                                color_words.append([results[0][0], results[1][1]])
                        print(f"Detected the following words: {color_words}")
                        correct_result = None
                        for regex_result in color_words:
                            print(f"Checking if {regex_result[1]} is in {aftermsg.embeds[0].description}")
                            if regex_result[1] in aftermsg.embeds[0].description:
                                correct_result = regex_result
                                break
                        if correct_result:
                            print(f"found a correct result: {correct_result}")
                            view = None
                            if aftermsg.components:
                                actionrow1 = aftermsg.components[0]
                                if isinstance(actionrow1, discord.ActionRow) and actionrow1.children:
                                    print("Found a view with children. Creating a mock view")
                                    view = MockShiftView(member)
                                    for row_item_component in actionrow1.children:
                                        if isinstance(row_item_component, discord.Button):
                                            correct_button = row_item_component.label.lower() == correct_result[0].lower()
                                            new_button = MockShiftButton(
                                                style=discord.ButtonStyle.green if correct_button else discord.ButtonStyle.grey,
                                                label=row_item_component.label,
                                                disabled=not correct_button,
                                                custom_id=None
                                            )
                                            view.add_item(new_button)
                            await aftermsg.reply(embed=discord.Embed(description=f"Select **{correct_result[0]}**", color=self.client.embed_color), view=view)
                        else:
                            print_dev("Result was not found")

                    if beforemsg.embeds[0].description.startswith("Remember words order!") and aftermsg.embeds[0].description.startswith("Click the buttons in correct order!"):
                        list_of_words = []
                        word_regex = r"`([^`]+)`"
                        for line in beforemsg.embeds[0].description.split("\n")[1:]:
                            results = re.findall(word_regex, line)
                            if len(results) > 0:
                                list_of_words.append(results[0].lower())
                        message_content = ["Correct order:"]
                        for index, word in enumerate(list_of_words):
                            message_content.append(f"{index}. **{word}**")
                        embed = discord.Embed(description="\n".join(message_content), color=self.client.embed_color)
                        view = None
                        if aftermsg.components:
                            actionrow1 = aftermsg.components[0]
                            if isinstance(actionrow1, discord.ActionRow) and actionrow1.children:
                                view = MockShiftView(member)
                                for row_item_component in actionrow1.children:
                                    if isinstance(row_item_component, discord.Button):
                                        is_button_part_of_list = row_item_component.label.lower() in list_of_words
                                        emoji = number_to_emoji(list_of_words.index(row_item_component.label.lower())+1) if is_button_part_of_list else None
                                        new_button = MockShiftButton(style=discord.ButtonStyle.grey, label=row_item_component.label, disabled=False, custom_id = None, url = None, emoji = emoji)
                                        view.add_item(new_button)
                        await aftermsg.reply(embed=embed, view=view)

                    if beforemsg.embeds[0].description.startswith("Look at the emoji closely!"):
                        lines = beforemsg.embeds[0].description.split("\n")
                        emoji_from_string = lines[1]
                        try:
                            emoji_converted = emoji_from_string.encode('utf-16', 'surrogatepass').decode('utf-16')
                        except (ValueError, TypeError, UnicodeEncodeError) as e:
                            print(f"Conversion failed: {e}")
                        else:
                            view = None
                            embed = discord.Embed(title=emoji_converted, color=self.client.embed_color).set_author(name="Select this emoji!")
                            if aftermsg.components and len(aftermsg.components) == 2:
                                view = MockShiftView(member)
                                for row in aftermsg.components:
                                    if isinstance(row, discord.ActionRow):
                                        for row_item_component in row.children:
                                            if isinstance(row_item_component, discord.Button):
                                                emoji_name = row_item_component.emoji.name if row_item_component.emoji else None
                                                correct_button = emoji_name == emoji_converted

                                                new_button = MockShiftButton(
                                                    style=discord.ButtonStyle.green if correct_button else discord.ButtonStyle.grey,
                                                    label=row_item_component.label,
                                                    emoji=row_item_component.emoji,
                                                    disabled=not correct_button,
                                                    custom_id=None
                                                )
                                                view.add_item(new_button)
                            await aftermsg.reply(embed=embed, view=view)




        """
        Scratch reminder
        """
        if is_dank_slash_command(beforemsg, 'scratch'):
            afterembed = aftermsg.embeds[0]
            if afterembed.author.name.endswith("Scratch-Off") and afterembed.description:
                timestamp_pattern = r"<t:(\d+):R>"
                match = re.search(timestamp_pattern, afterembed.description)
                if match:
                    timestamp = int(match.group(1))
                    nextscratchtime = timestamp + 60
                    member = aftermsg.interaction.user
                    await self.handle_reminder_entry(member.id, 14, aftermsg.channel.id, aftermsg.guild.id, nextscratchtime)
                    with contextlib.suppress(discord.HTTPException):
                        await checkmark(aftermsg)


        """
        Stream reminder
        """
        if is_dank_slash_command(beforemsg, 'stream'):
            afterembed = aftermsg.embeds[0]
            if afterembed.author.name.endswith('Stream Manager'):
                def is_in_stream_section(message: discord.Message):
                    button_labels = ["Run AD", "Read Chat", "Collect Donations", "View Setup", "End Stream"]
                    if len(message.components) > 0:
                        for com in message.components:
                            if isinstance(com, discord.ActionRow):
                                for index, i in enumerate(com.children): #buttons
                                    if not isinstance(i, discord.Button):
                                        return False
                                    if i.disabled is True:
                                        return False
                                    if i.label not in button_labels:
                                        return False
                            else:
                                if com.disabled is True:
                                    return False
                    return True
                def is_selecting_stream_game(message: discord.Message):
                    if type(message.embeds[0].description) == str and "What game do you want to stream" in message.embeds[0].description:
                        choose_view = message.components
                        if isinstance(choose_view[0], discord.ActionRow):
                            row = choose_view[0]
                            if isinstance(row.children[0], discord.SelectMenu):
                                select = row.children[0]
                                for i in select.options:
                                    if i.default is True and i.label != "Apex Legends": #apex legends is always the default
                                        return False
                                return True
                    return False
                if is_selecting_stream_game(aftermsg):
                    if self.trending_game[1] is not None:
                        try:
                            await beforemsg.reply("The current trending game to stream is **{}**!".format(self.trending_game[1]), delete_after=10.0)
                        except discord.HTTPException:
                            await beforemsg.channel.send("The current trending game to stream is **{}**!".format(self.trending_game[1]), delete_after=10.0)
                elif is_in_stream_section(aftermsg):
                    member = aftermsg.interaction.user
                    minutes_between_next_interaction = 10
                    interact_minutes_re_search = re.search(r"You can interact with your stream every `(\d+)` minute", afterembed.description)
                    if interact_minutes_re_search:
                        minutes_between_next_interaction = int(interact_minutes_re_search.group(1)) or 10
                    nextstreamtime = round(time.time()) + minutes_between_next_interaction * 60
                    await self.handle_reminder_entry(member.id, 20, aftermsg.channel.id, aftermsg.guild.id, nextstreamtime, uses_name=True)

                    now = discord.utils.utcnow()
                    next_reminder_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
                    nextdailystreamtime = round(next_reminder_time.timestamp())
                    await self.handle_reminder_entry(member.id, 1002, aftermsg.channel.id, aftermsg.guild.id, nextdailystreamtime, uses_name=True)

                    await checkmark(beforemsg)
        """
        Pet reminder
        """
        if is_dank_slash_command(beforemsg, 'pets care'):
            if type(beforemsg.embeds[0].title) == str and beforemsg.embeds[0].title.startswith(f"{beforemsg.interaction.user.name}'s"):
                member = beforemsg.interaction.user
                nextpettime = round(time.time()) + 43200
                await self.handle_reminder_entry(member.id, 23, aftermsg.channel.id, aftermsg.guild.id, nextpettime, uses_name=True)
                await checkmark(beforemsg)

    @commands.cooldown(1, 20, commands.BucketType.user)
    @checks.not_in_gen()
    @commands.command(name="dankreminders", aliases=["dankrm", "drm"])
    async def dankreminders(self, ctx):
        """
        Shows your reminders for Dank Memer and allows you to enable/disable them.
        Change your type of reminder via the select menu.
        """
        result = await self.client.db.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id) # gets the configuration for user to check if they have used dank reminder before
        if result is None:
            await self.client.db.execute("INSERT into remindersettings VALUES ($1, $2)", ctx.author.id, 1) # creates new entry for settings
            result = await self.client.db.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id)
        reminders = await self.client.db.fetch("SELECT * FROM dankreminders WHERE member_id = $1 and guild_id = $2", ctx.author.id, ctx.guild.id) # gets user's reminders
        dailytime, lotterytime, worktime, weeklytime, monthlytime, hunttime, fishtime, digtime, searchtime, crimetime, begtime, scratchtime, horseshoetime, pizzatime, droptime, pmtime, streamtime, pettime = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
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
                scratchtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 15:
                highlowtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 17:
                horseshoetime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 18:
                pizzatime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 20:
                streamtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 21:
                pmtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 23:
                pettime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 24:
                adventuretime = round(reminder.get('time')-time.time())
        remindertimes = [dailytime or None, weeklytime or None, monthlytime or None, lotterytime or None, worktime or None, hunttime or None, fishtime or None, digtime or None, crimetime or None, begtime or None, searchtime or None, scratchtime or None, horseshoetime or None, pizzatime or None, droptime or None, streamtime or None, pmtime or None, pettime or None]
        newview = dankreminders(ctx, self.client, remindertimes, 15.0, result.get('daily'), result.get('weekly'), result.get('monthly'), result.get('lottery'), result.get('work'), result.get('hunt'), result.get('fish'), result.get('dig'), result.get('crime'), result.get('beg'), result.get('search'), result.get('scratch'), result.get('horseshoe'), result.get('pizza'), result.get('drop'), result.get('stream'), result.get('postmeme'), result.get('pet'))
        message = await ctx.send(f"**{ctx.author}'s Dank Memer Reminders**\nSelect the button that corresponds to the reminder to enable/disable it.\n\nYou're currently {'reminded via **DMs**' if result.get('method') == 1 else 'reminded via **ping**' if result.get('method') == 2 else 'not reminded'} for your reminders.", view=newview)
        newview.response = message
        newview.result = result
        newview.rmtimes = remindertimes

    @checks.dev()
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
        await self.client.db.execute("INSERT INTO dankdrops VALUES($1, $2, $3, $4)", ctx.guild.id, item, price, droptime)
        await ctx.send("Reminder set!")

    @checks.admoon()
    @commands.command(name="drops")
    async def drops(self, ctx):
        """
        Lists all the drops that are currently set.
        """
        drops = await self.client.db.fetch("SELECT * FROM dankdrops WHERE guild_id=$1", ctx.guild.id)
        if not drops:
            return await ctx.send("No drops are currently set.")
        embed = discord.Embed(title="Dank Memer Drops", color=discord.Color.blue())
        for drop in drops:
            embed.add_field(name=drop.get("name"), value=f"Cost: {drop.get('price')}\nDrop Time: <t:{drop.get('time')}>")
        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="trendinggame")
    async def trendinggame(self, ctx, *, game: str = None):
        """
        Set the current trending game.
        """
        if game is None:
            trendinggame_view = TrendingGameSetting(self.trending_game[0], self.trending_game[1], self, ctx, self.client)
            trendinggame_view.response = await ctx.send("The current trending game is **{}**".format(self.trending_game[1]), view=trendinggame_view)
        else:
            await ctx.send("I've set the current trending game. This is how it will look like:\n\nThe current trending game to stream is **{}**!\n\n**ALERT**: Please use `dv.trendinggame` and use the select menu to set today's trending game, it's more easier that way. Adding an argument for this command will soon be deprecated.".format(game))
