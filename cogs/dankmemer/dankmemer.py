import re
import time
import asyncio
from typing import Tuple

import discord
import operator

from thefuzz import process

from cogs.dankmemer.lottery import Lottery
from main import dvvt
from utils import checks, buttons
from datetime import datetime, timedelta
from discord.ext import commands, tasks, pages
from utils.format import print_exception, short_time, comma_number, stringnum_toint
from utils.buttons import *
import cogs.dankmemer


item_name_regex = re.compile(r"^\*\*(.+)\*\*")
trade_val_re = re.compile(r"^\*\*TRADE\*\* - \u23e3 ([\d,]*)")

async def checkmark(message:discord.Message):
    try:
        await message.add_reaction("<:DVB_checkmark:955345523139805214>")
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
    try:
        await msg.add_reaction("<:DVB_crossmark:955345521151737896>")
    except Exception as e:
        pass


def numberswitcher(no):
    if no == 1:
        return 0
    elif no == 0:
        return 1
    elif no == None:
        return 1
    else:
        return 0
class ListOfStreamGames(discord.ui.Select):
    def __init__(self, current):
        self.current: Union[None, int] = current
        options = [
            discord.SelectOption(label="Lost Ark", value="0"),
            discord.SelectOption(label="Animal Crossing", value="1"),
            discord.SelectOption(label="Apex Legends", value="2"),
            discord.SelectOption(label="Battlefield 5", value="3"),
            discord.SelectOption(label="Counter-Strike Global Offensive", value="4"),
            discord.SelectOption(label="PUBG", value="5"),
            discord.SelectOption(label="Dark Souls II", value="6"),
            discord.SelectOption(label="Destiny 2: The Witch Queen", value="7"),
            discord.SelectOption(label="Diablo II", value="8"),
            discord.SelectOption(label="Dota 2", value="9"),
            discord.SelectOption(label="FIFA 22", value="10"),
            discord.SelectOption(label="Fortnite", value="11"),
            discord.SelectOption(label="Forza Horizon 5", value="12"),
            discord.SelectOption(label="Genshin Impact", value="13"),
            discord.SelectOption(label="Get Stuffed", value="14"),
            discord.SelectOption(label="Grand Theft Auto V", value="15"),
            discord.SelectOption(label="Hearthstone", value="16"),
            discord.SelectOption(label="League of Legends", value="17"),
            discord.SelectOption(label="Mario", value="18"),
            discord.SelectOption(label="Minecraft", value="19"),
            discord.SelectOption(label="Dying Light 2", value="20"),
            discord.SelectOption(label="Overwatch", value="21"),
            discord.SelectOption(label="Phasmophobia", value="22"),
            discord.SelectOption(label="Rocket League", value="23"),
            discord.SelectOption(label="Valorant", value="24"),
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
    def __init__(self, ctx: DVVTcontext, client, rmtimes, timeout, daily, weekly, monthly, lottery, work, donor, hunt, fish, dig, crime, beg, search, se, highlow, horseshoe, pizza, drop, stream, postmeme, marriage, pet, adventure):
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
                          "<a:DVB_snakeeyes:888404298608812112>", "🔢", "<:DVB_Horseshoe:888404491647463454>",
                          "<:DVB_pizza:888404502280024145>", "<:DVB_sugarskull:904936096436215828>", "🎮", "<:DVB_Laptop:915524266940854303>", "<:DVB_Ring:928236453920669786>", "<:DVB_pet:928236242469011476>", "🚀"]
        labels = ["Claim daily", "Claim weekly",
                  "Claim monthly", "Enter the Lottery",
                  "Work", "Redeem donor rewards",
                  "Hunt", "Fish",
                  "Dig", "Crime",
                  "Beg", "Search",
                  "Snakeeyes", "Highlow", "Use a horseshoe",
                  "Use a pizza", "Get drop items", "Interact on stream", "Post memes", "Marriage Interaction", "Interact with pet", "(NEW) Adventure Interaction"]
        is_enabled = [daily, weekly, monthly, lottery, work, donor, hunt, fish, dig, crime, beg, search, se, highlow, horseshoe, pizza, drop, stream, postmeme, marriage, pet, adventure]

        async def initialise_dank_reminders(user: Union[discord.Member, discord.User]):
            await self.client.db.execute("INSERT INTO remindersettings (member_id, method) VALUES ($1, $2) ON CONFLICT (member_id) DO UPDATE SET method = $2", user.id, 0)
            return await self.client.db.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", user.id)

        async def update_message(emoji, interaction: discord.Interaction):
            if str(emoji) == "<:DVB_calendar:873107952159059991>":
                await self.client.db.execute("UPDATE remindersettings SET daily = $1 WHERE member_id = $2", numberswitcher(self.result.get('daily')), ctx.author.id)  # switches to enabled/disabled reminder
            elif str(emoji) == "<:DVB_week:876711052669247528>":
                await self.client.db.execute("UPDATE remindersettings SET weekly = $1 WHERE member_id = $2", numberswitcher(self.result.get('weekly')), ctx.author.id)
            elif str(emoji) == "<:DVB_month:876711072030150707>":
                await self.client.db.execute("UPDATE remindersettings SET monthly = $1 WHERE member_id = $2", numberswitcher(self.result.get('monthly')), ctx.author.id)
            elif str(emoji) == "<:DVB_lotteryticket:873110581085880321>":
                await self.client.db.execute("UPDATE remindersettings SET lottery = $1 WHERE member_id = $2", numberswitcher(self.result.get('lottery')), ctx.author.id)
            elif str(emoji) == "<:DVB_workbadge:873110507605872650>":
                await self.client.db.execute("UPDATE remindersettings SET work = $1 WHERE member_id = $2", numberswitcher(self.result.get('work')), ctx.author.id)
            elif str(emoji) == "<:DVB_patreon:876628017194082395>":
                await self.client.db.execute("UPDATE remindersettings SET redeem = $1 WHERE member_id = $2", numberswitcher(self.result.get('redeem')), ctx.author.id)
            elif str(emoji) == "<:DVB_rifle:888404394805186571>":
                await self.client.db.execute("UPDATE remindersettings SET hunt = $1 WHERE member_id = $2", numberswitcher(self.result.get('hunt')), ctx.author.id)
            elif str(emoji) == "<:DVB_fishing:888404317638369330>":
                await self.client.db.execute("UPDATE remindersettings SET fish = $1 WHERE member_id = $2", numberswitcher(self.result.get('fish')), ctx.author.id)
            elif str(emoji) == "<:DVB_shovel:888404340426031126>":
                await self.client.db.execute("UPDATE remindersettings SET dig = $1 WHERE member_id = $2", numberswitcher(self.result.get('dig')), ctx.author.id)
            elif str(emoji) == "<:DVB_Crime:888404653711192067>":
                await self.client.db.execute("UPDATE remindersettings SET crime = $1 WHERE member_id = $2", numberswitcher(self.result.get('crime')), ctx.author.id)
            elif str(emoji) == "<:DVB_beg:888404456356610099>":
                await self.client.db.execute("UPDATE remindersettings SET beg = $1 WHERE member_id = $2", numberswitcher(self.result.get('beg')), ctx.author.id)
            elif str(emoji) == "<:DVB_search:888405048260976660>":
                await self.client.db.execute("UPDATE remindersettings SET search = $1 WHERE member_id = $2", numberswitcher(self.result.get('search')), ctx.author.id)
            elif str(emoji) == "<a:DVB_snakeeyes:888404298608812112>":
                await self.client.db.execute("UPDATE remindersettings SET snakeeyes = $1 WHERE member_id = $2", numberswitcher(self.result.get('snakeeyes')), ctx.author.id)
            elif str(emoji) == "🔢":
                await self.client.db.execute("UPDATE remindersettings SET highlow = $1 WHERE member_id = $2", numberswitcher(self.result.get('highlow')), ctx.author.id)
            elif str(emoji) == "<:DVB_Horseshoe:888404491647463454>":
                await self.client.db.execute("UPDATE remindersettings SET horseshoe = $1 WHERE member_id = $2", numberswitcher(self.result.get('horseshoe')), ctx.author.id)
            elif str(emoji) == "<:DVB_pizza:888404502280024145>":
                await self.client.db.execute("UPDATE remindersettings SET pizza = $1 WHERE member_id = $2", numberswitcher(self.result.get('pizza')), ctx.author.id)
            elif str(emoji) == "<:DVB_sugarskull:904936096436215828>":
                await self.client.db.execute("UPDATE remindersettings SET drop = $1 WHERE member_id = $2", numberswitcher(self.result.get('drop')), ctx.author.id)
            elif str(emoji) == "🎮":
                await self.client.db.execute("UPDATE remindersettings SET stream = $1 WHERE member_id = $2", numberswitcher(self.result.get('stream')), ctx.author.id)
                if self.result.get('stream') != 1:
                    await interaction.response.send_message("__**Important!**__\nThis uses the username shown in the Stream Manager embed from Dank Memer to identify who used the command. If there're people with the same name as you, the reminder may not work.\nhttps://cdn.nogra.xyz/screenshots/Discord_cAJOC18PCV.png", ephemeral=True)
            elif str(emoji) == "<:DVB_Laptop:915524266940854303>":
                await self.client.db.execute("UPDATE remindersettings SET postmeme = $1 WHERE member_id = $2", numberswitcher(self.result.get('postmeme')), ctx.author.id)
            elif str(emoji) == "<:DVB_Ring:928236453920669786>":
                if self.result.get('marriage') != 1:
                    await interaction.response.send_message("__**Important!**__\nMarriage reminders aren't working at the moment. Please use `dv.remind` instead.", ephemeral=True)
                await self.client.db.execute("UPDATE remindersettings SET marriage = $1 WHERE member_id = $2", numberswitcher(self.result.get('marriage')), ctx.author.id)
            elif str(emoji) == "<:DVB_pet:928236242469011476>":
                await self.client.db.execute("UPDATE remindersettings SET pet = $1 WHERE member_id = $2", numberswitcher(self.result.get('pet')), ctx.author.id)
                if self.result.get('pet') != 1:
                    await interaction.response.send_message("__**Important!**__\nThis uses the username shown in your pet's embed from Dank Memer to identify who used the command. If there're people with the same username as you, the reminder may not work.\nhttps://cdn.nogra.xyz/screenshots/Discord_YVzJYHhFVa.png", ephemeral=True)
            elif str(emoji) == "🚀":
                await self.client.db.execute("UPDATE remindersettings SET adventure = $1 WHERE member_id = $2", numberswitcher(self.result.get('adventure')), ctx.author.id)
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


class DankMemer(Lottery, commands.Cog, name='dankmemer'):
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
            14: "snakeeyes",
            15: "highlow",
            17: "horseshoe",
            18: "pizza",
            20: "stream",
            21: "postmeme",
            22: "marriage",
            23: "pet",
            24: "adventure"
        }


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
            next_run += timedelta(days=1)
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
                enabled = await self.client.db.fetch("SELECT * FROM remindersettings WHERE drop = $1", 1)
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
                        remindersettings = await self.client.db.fetchval("SELECT method FROM remindersettings WHERE member_id = $1", i)
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
                check_reminder_enabled_index = 20 if result.get('remindertype') == 1001 else result.get('remindertype')
                config = await self.client.db.fetchrow("SELECT member_id, method, daily, weekly, monthly, lottery, work, redeem, hunt, fish, dig, crime, beg, search, snakeeyes, highlow, dailybox, horseshoe, pizza, drop, stream, postmeme, marriage, pet, adventure FROM remindersettings WHERE member_id = $1", result.get('member_id')) # get the user's configuration
                if config is None: # no config means user doesn't even use this reminder system lol
                    pass
                elif result.get('remindertype') not in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 1001]: # if the reminder type is not a valid one
                    pass
                elif config[check_reminder_enabled_index] != 1:  # activity specific reminder check
                    pass
                elif config.get('method') == 0:  # chose not to be reminded
                    pass
                elif config.get('method') in [1, 2]:  # DMs or Mentions
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
                        elif reminderaction == 17:
                            return "**use a horseshoe** <:DVB_Horseshoe:888404491647463454>"
                        elif reminderaction == 18:
                            return "**use a pizza** <:DVB_pizza:888404502280024145>"
                        elif reminderaction == 20:
                            return "**Interact with your stream** 🎮"
                        elif reminderaction == 21:
                            return "`pls pm` <:DVB_Laptop:915524266940854303>"
                        elif reminderaction == 22:
                            return "**interact with your marriage partner** <:DVB_Ring:928236453920669786>"
                        elif reminderaction == 23:
                            return "**interact with your pet** <:DVB_pet:928236242469011476>"
                        elif reminderaction == 24:
                            return "**continue your adventure** 🚀"
                        elif reminderaction == 1001:
                            return "**start a stream again** 🎮"
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
                                    await self.client.db.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 0, result.get('member_id')) # change reminder settings to None
                        elif config.get('method') == 2: # Mention
                            try:
                                await channel.send(f"{member.mention} you can now {message(result.get('remindertype'))}")
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
    async def on_message(self, message):
        if message.author.bot and message.author.id != 270904126974590976:
            return
        if self.client.maintenance.get(self.qualified_name) and await self.client.db.fetchval("SELECT enabled FROM devmode WHERE user_id = $1", message.author.id) is not True:
            return
        if not message.guild:
            return
        #if message.guild.id != 595457764935991326:
#            return
        """
        Let's update trade values first
        """
        def get_item_details(m: discord.Message) -> Union[tuple, None]:
            item_name = None
            item_code = None
            item_worth = None
            item_type = None
            item_thumbnail_url = None
            if len(m.embeds) != 1:
                return
            embed = m.embeds[0]
            if type(embed.title) != str:
                return
            item_name_matches = re.findall(item_name_regex, embed.title)
            if len(item_name_matches) != 1:
                return
            item_name = item_name_matches[0]
            if type(embed.fields) == list:
                for field in embed.fields:
                    if field.name == "ID":
                        item_code = field.value.replace('`', '')
                    if field.name == "Type":
                        item_type = field.value.replace('`', '')
            else:
                return
            if type(embed.description) == str:

                desc_split = embed.description.splitlines()[-1]
                item_val_matches = re.findall(trade_val_re, desc_split)
                if len(item_val_matches) != 1:
                    return
                else:
                    item_worth = int(item_val_matches[0].replace(',', ''))
            if item_name is None or item_code is None or item_worth is None or item_type is None:
                return
            if item_code == 'cutters':
                item_code = 'boltcutters'
            if type(embed.thumbnail.url) == str:
                item_thumbnail_url = embed.thumbnail.url
            return item_name, item_code, item_worth, item_type, item_thumbnail_url
        if (item := get_item_details(message)) is not None:
            item_name, item_code, item_worth, item_type,  item_thumnail_url = item
            existing_item = await self.client.db.fetchrow("SELECT * FROM dankitems WHERE idcode = $1", item_code)
            if existing_item is not None:
                if existing_item.get('overwrite') is not True:
                    if existing_item.get('trade_value') != item_worth:
                        await self.client.db.execute("UPDATE dankitems SET name = $1, trade_value = $2, type = $3, image_url = $4, last_updated = $5 WHERE idcode = $6", item_name, item_worth, item_type, item_thumnail_url, round(time.time()), item_code)
                else:
                    pass
            else:
                await self.client.db.execute("INSERT INTO dankitems (name, idcode, type, image_url, trade_value, last_updated, overwrite) VALUES ($1, $2, $3, $4, $5, $6, $7)", item_name, item_code, item_type, item_thumnail_url, item_worth, round(time.time()), False)
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
                    await self.handle_reminder_entry(member.id, 2, message.channel.id, message.guild.id, nextdailytime, uses_name=True)
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
                    await self.handle_reminder_entry(member.id, 3, message.channel.id, message.guild.id, nextweeklytime, uses_name=True)
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
                    await self.handle_reminder_entry(member.id, 4, message.channel.id, message.guild.id, nextmonthlytime, uses_name=True)
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
                    return await message.add_reaction("<:DVB_crossmark:955345521151737896>")
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
                    await self.handle_reminder_entry(member.id, 7, message.channel.id, message.guild.id, nextredeemtime, uses_name=True)
                    with contextlib.suppress(discord.HTTPException):
                        await clock(message)
                else:
                    await crossmark(message)
        """
        Hunting Reminder
        """
        if (message.content.startswith("You went hunting") or message.content.startswith("Imagine going into the woods") or message.content.startswith("You might be the only hunter")) and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nexthunttime = round(time.time()) + 25
            await self.handle_reminder_entry(member.id, 8, message.channel.id, message.guild.id, nexthunttime)
        """
        Fishing Reminder
        """
        if (message.content.startswith("You cast out your line") or message.content.startswith("LMAO you found nothing.") or message.content.startswith("Awh man, no fis")) and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextfishtime = round(time.time()) + 25
            await self.handle_reminder_entry(member.id, 9, message.channel.id, message.guild.id, nextfishtime)
        """
        Dig Reminder
        """
        if (message.content.startswith("You dig in the dirt") or message.content.startswith("LMAO you found nothing in the ground.")) and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextdigtime = round(time.time()) + 25
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
                        nexthighlowtime = round(time.time()) + 15
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
            nextsearchtime = round(time.time()) + 15
            existing = await self.client.db.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 13)
            if len(existing) > 0:
                await self.client.db.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextsearchtime, member.id, 13)
            else:
                await self.client.db.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 13, message.channel.id, message.guild.id, nextsearchtime)
        """
        Crime Reminder
        """
        if "What crime do you want to commit?" in message.content and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextcrimetime = round(time.time()) + 15
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
                    nextbegtime = round(time.time()) + 25
                    await self.handle_reminder_entry(member.id, 12, message.channel.id, message.guild.id, nextbegtime)
        """
        Horseshoe Reminder
        """
        if message.content.startswith("You equip your lucky horseshoe") and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nexthorseshoetime = round(time.time()) + 1800
            await self.handle_reminder_entry(member.id, 17, message.channel.id, message.guild.id, nexthorseshoetime)
        """
        Pizza Reminder
        """
        if message.content.startswith("You eat the perfect slice of pizza.") and message.author.id == 270904126974590976 and len(message.mentions) > 0:
            member = message.mentions[0]
            nextpizzatime = round(time.time()) + 7200
            await self.handle_reminder_entry(member.id, 18, message.channel.id, message.guild.id, nextpizzatime)
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
        """
        Marriage reminder
        """
        if message.author.id == 270904126974590976:
            if len(message.mentions) > 0:
                if len(message.embeds) > 0:
                    try:
                        user_name = get_shared_user_name(message.embeds[0])
                    except ValueError:
                        return
                    if user_name:
                        partner_id = await self.client.db.fetchval("SELECT m_partner FROM remindersettings WHERE member_id = $1", message.mentions[0].id)
                        partner = self.client.get_user(partner_id)
                        if partner is not None:
                            if user_name == partner.name:
                                timetomarriage = round(time.time()) + 54000
                                await self.handle_reminder_entry(message.mentions[0].id, 22, message.channel.id, message.guild.id, timetomarriage, uses_name=True)
                                await message.add_reaction('<:DVB_Ring:928236453920669786>')
        """
        Stream Start Reminder
        """
        if message.author.id == 270904126974590976:
            if len(message.embeds) > 0:
                embed = message.embeds[0]
                if type(embed.footer.text) == str:
                    if "Wait at least half an hour to stream again!" in embed.footer.text:
                        if embed.author:
                            if type(embed.author.name) == str:
                                if embed.author.name.endswith('Stream Manager'):
                                    def get_member():
                                        for member in message.guild.members:
                                            if embed.author.name == f"{member.name}'s Stream Manager":
                                                return member
                                        return None
                                    member = get_member()
                                    if member:
                                        if embed.fields is not None:
                                            field_value = embed.fields[1].value
                                            try:
                                                timestamp_of_ended_stream = int(field_value.split(':')[1])
                                            except:
                                                pass
                                            else:
                                                timestamp_to_restart_stream = timestamp_of_ended_stream + 1800
                                                if timestamp_to_restart_stream > round(time.time()):
                                                    await self.handle_reminder_entry(member.id, 1001, message.channel.id, message.guild.id, timestamp_to_restart_stream, uses_name=True)
                                                    await message.add_reaction("<:DVB_True:887589686808309791>")


    @commands.Cog.listener()
    async def on_message_edit(self, beforemsg, aftermsg):
        if beforemsg.author.id != 270904126974590976:
            return
        if len(beforemsg.embeds) == 0 or len(aftermsg.embeds) == 0:
            return
        async def check_for_adventure():
            if len(beforemsg.mentions) > 0:
                if len(beforemsg.embeds) > 0:
                    embed = beforemsg.embeds[0]
                    if isinstance(embed.author.name, str) or isinstance(embed.title, str) or embed.fields is not None:
                        return
                    if len(beforemsg.components) > 0:
                        def find_one_enabled_component(mtarget):
                            view = discord.ui.View.from_message(mtarget)
                            for component in view.children:
                                if component.disabled is False:
                                    return True
                            return False
                        def find_all_disabled_component(mtarget):
                            view = discord.ui.View.from_message(mtarget)
                            for component in view.children:
                                if component.disabled is True:
                                    pass
                                else:
                                    return False
                            return True
                        if not find_one_enabled_component(beforemsg):
                            return False
                        if not find_all_disabled_component(aftermsg):
                            return False
                        target = beforemsg.mentions[0]
                        await self.handle_reminder_entry(target.id, 24, beforemsg.channel.id, beforemsg.guild.id, round(time.time()) + 120)
                        await beforemsg.add_reaction('🚀')
                    else:
                        return False
        await check_for_adventure()
        beforeembed = beforemsg.embeds[0]
        afterembed = aftermsg.embeds[0]
        if beforeembed.author:
            if not beforeembed.author.name:
                return
            if beforeembed.author.name.endswith('Stream Manager'):
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
                    def check_start_not_stream():
                        for children in beforeview.children:
                            if not isinstance(children, discord.ui.Button):
                                return False
                        button = beforeview.children[0]
                        if not (button.label.lower() == "go live" and button.disabled is False):
                            return False
                        button = beforeview.children[1]
                        if not (button.label.lower() == "view setup" and button.disabled is False):
                            return False
                        button = beforeview.children[2]
                        if not (button.label.lower() == "end interaction" and button.disabled is False):
                            return False
                        return True
                    if not check_start_not_stream():
                        return
                    def check_start_selecting_stream():
                        item = afterview.children[0]
                        if not isinstance(item, discord.ui.Select):
                            return False
                        if item.placeholder.lower() != "select a game...":
                            return False
                        item = afterview.children[1]
                        if not isinstance(item, discord.ui.Button):
                            return False
                        if not (item.label.lower() == "go live" and item.disabled is True):
                            return False
                        item = afterview.children[2]
                        if not isinstance(item, discord.ui.Button):
                            return False
                        if not (item.label.lower() == "go back" and item.disabled is False):
                            return False
                        return True
                    if check_start_selecting_stream():
                        if self.trending_game[1] is not None:
                            try:
                                return await beforemsg.reply("The current trending game to stream is **{}**!".format(self.trending_game[1]), delete_after=10.0)
                            except Exception as e:
                                await beforemsg.channel.send("The current trending game to stream is **{}**!".format(self.trending_game[1]), delete_after=10.0)
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
                await self.handle_reminder_entry(member.id, 20, aftermsg.channel.id, aftermsg.guild.id, nextstreamtime, uses_name=True)
                await checkmark(beforemsg)
        elif beforeembed.footer is not None and beforeembed.title is not None and isinstance(beforeembed.title, str):
            def get_member():
                for member in beforemsg.guild.members:
                    if beforeembed.title.startswith(f"{member.name}'s"):
                        return member
                return None
            member = get_member()
            if not member:
                return
            if isinstance(beforeembed.footer.text, str) and "You can't increase a stat" in beforeembed.footer.text:
                beforeview = discord.ui.View.from_message(beforemsg)
                afterview = discord.ui.View.from_message(aftermsg)
                if beforeview is None or afterview is None:
                    return
                def check_before_view():
                    buttons = {5: "Train", 6: "Change Name", 7: "Prestige", 8: "Browse Store", 9: "End Interaction"}
                    for button in buttons:
                        try:
                            item = beforeview.children[button]
                        except IndexError:
                            return False
                        if not isinstance(item, discord.ui.Button):
                            return False
                        if item.label != buttons[button]:
                            return False
                        if item.disabled is True:
                            return False
                    return True
                if not check_before_view():
                    return
                def check_after_view():
                    buttons = {5: "Train", 6: "Change Name", 7: "Prestige", 8: "Browse Store", 9: "End Interaction"}
                    for button in buttons:
                        try:
                            item = afterview.children[button]
                        except IndexError:
                            return False
                        if not isinstance(item, discord.ui.Button):
                            return False
                        if item.label != buttons[button]:
                            return False
                        if item.disabled is False:
                            return False
                    return True
                if not check_after_view():
                    return
                nextpettime = round(time.time()) + 43200
                await self.handle_reminder_entry(member.id, 23, aftermsg.channel.id, aftermsg.guild.id, nextpettime, uses_name=True)
                await checkmark(beforemsg)

    @commands.group(name="dankitems", aliases=['items'], invoke_without_command=True)
    async def dankitems(self, ctx, item: str = None):
        """
        Fetches values of Dank Memer Items for donations. These values are based off trade values cached from Dank Memer, or manually set.
        """
        items = await self.client.db.fetch("SELECT * FROM dankitems ORDER BY name")
        if item is not None:
            item = item.lower()
            result, ratio = process.extractOne(item, [i.get('idcode') for i in items])
            if ratio > 65:
                for checking_item in items:
                    if checking_item.get('idcode') == result:
                        name = checking_item.get('name')
                        type = checking_item.get('type')
                        image_url = checking_item.get('image_url')
                        trade_value = checking_item.get('trade_value')
                        last_updated = checking_item.get('last_updated')
                        overwrite = checking_item.get('overwrite')
                        embed = discord.Embed(
                            title=name,
                            description=f"```\n⏣ {comma_number(trade_value)}\n```",
                            color=self.client.embed_color,
                            timestamp=datetime.fromtimestamp(last_updated))
                        field_details = f"**Type**: {type}\n**ID**: `{result}`"
                        if overwrite is True:
                            field_details += f"\nThis item's value is preset, not cached from Dank Memer."
                        embed.add_field(name="Details", value=field_details, inline=False)
                        embed.set_thumbnail(url=image_url)
                        embed.set_footer(text=f"Last updated")
                        await ctx.send(embed=embed)
                        return
            else:
                return await ctx.send(f"<:DVB_False:887589731515392000> I could not find an item with the name `{item}`.")
        else:
            if len(items) == 0:
                return await ctx.send("There are no cached Dank Memer items to display.")
            else:
                items_sorted = {}
                for item in items:
                    name = item.get('name')
                    idcode = item.get('idcode')
                    type = item.get('type')
                    trade_value = item.get('trade_value')
                    if type in items_sorted.keys():
                        items_sorted[type].append((name, idcode, trade_value))
                    else:
                        items_sorted[type] = [(name, idcode, trade_value)]
                all_items = []
                pagegroups = []
                for type, lst in items_sorted.items():
                    embeds = []
                    for chunked_list in discord.utils.as_chunks(lst, 10):
                        desc = []
                        for name, idcode, trade_value in chunked_list:
                            all_items.append(f"**{name}** `{idcode}`: [⏣ {comma_number(trade_value)}](http://a/)")
                            desc.append(f"**{name}** `{idcode}`: [⏣ {comma_number(trade_value)}](http://a/)")
                        embed = discord.Embed(title=f"{type} Items", description="\n".join(desc), color=self.client.embed_color)
                        embeds.append(embed)
                    pagegroups.append(discord.ext.pages.PageGroup(pages=embeds, label=type, author_check=True, disable_on_timeout=True, description = None))
                all_items_embeds = []
                for all_items_chunked in discord.utils.as_chunks(all_items, 10):
                    embed = discord.Embed(title="All Items", description="\n".join(all_items_chunked), color=self.client.embed_color)
                    all_items_embeds.append(embed)
                pagegroups.append(discord.ext.pages.PageGroup(pages=all_items_embeds, label="All Items", author_check=True, disable_on_timeout=True, description = None))
                paginator = pages.Paginator(pages=pagegroups, show_menu=True, menu_placeholder="Dank Memer Item Categories", )
                await paginator.send(ctx)

    @checks.has_permissions_or_role(manage_roles=True)
    @dankitems.command(name='set', aliases=['setvalue'])
    async def dankitems_set_value(self, ctx, item: str, value: str):
        """
        Set the value of a Dank Memer item, overwriting it and preventing it from being updated automatically.
        """
        items = await self.client.db.fetch("SELECT * FROM dankitems")
        if item is not None:
            item = item.lower()
            result, ratio = process.extractOne(item, [i.get('idcode') for i in items])
            if ratio > 65:
                for checking_item in items:
                    if checking_item.get('idcode') == result:
                        item = checking_item
                    else:
                        continue
        if type(item) == str:
            return await ctx.send(f"<:DVB_False:887589731515392000> I could not find an item with the name `{item}`.")
        processed_value = stringnum_toint(value)
        if processed_value is None:
            if value.lower() == 'none':
                processed_value = None
            else:
                return await ctx.send("<:DVB_False:887589731515392000> The value needs to be a number or `none`.")
        if processed_value is not None:
            await self.client.db.execute("UPDATE dankitems SET trade_value = $1, overwrite = True, last_updated = $2 WHERE idcode = $3", processed_value, round(time.time()), item.get('idcode'))
            await ctx.send(f"<:DVB_True:887589686808309791> Set the value of **{item.get('name')}** to `⏣ {comma_number(processed_value)}`.\nTo reset it to Dank Memer trade values, use set `none` as the value.")
        else:
            await self.client.db.execute("UPDATE dankitems SET trade_value = 0, overwrite = False, last_updated = $1 WHERE idcode = $2", round(time.time()), item.get('idcode'))
            await ctx.send(f"<:DVB_True:887589686808309791> Set the value of **{item.get('name')}** to `⏣ 0`.\nPlease run `pls shop {item.get('idcode')}` to update the {item.get('name')} to the current Dank Memer trade value.")





    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='itemcalc', aliases=['ic'])
    async def item_calc(self, ctx: DVVTcontext, *, arg: str = None):
        """
        Calculates the total donation value of multiple Dank Memer items.
        The items should be entered in this format: `[item count] <item name> [item count] <item name> ...`
        Example: `dv.ic 1 pepe 3 tro`
        """
        if arg is None:
            return await ctx.send("You need to provide a list of Dank items to calculate the total worth.")
        all_dank_items = await self.client.db.fetch("SELECT * FROM dankitems")
        item_names = []
        item_codes = []
        item_worth = []
        for item in all_dank_items:
            item_names.append(item.get('name'))
            item_codes.append(item.get('idcode'))
            item_worth.append(item.get('trade_value'))
        items = []
        errors = []
        input_count = None
        input_name = None
        for item in arg.split(' '):
            if item.isdigit():
                input_count = int(item)
            else:
                item = item.lower()
                result, ratio = process.extractOne(item, item_codes)
                if ratio > 65:
                    item_index = item_codes.index(result)
                    if input_count is None:
                        input_count = 1
                    items.append((item_names[item_index], item_worth[item_index], input_count))
                    input_count = None
                else:
                    errormsg = f"`{item}`: Unable to find item"
                    if errormsg not in errors:
                        errors.append(errormsg)
        if len(errors) > 0:
            errorembed = discord.Embed(title="Encountered some errors when parsing:", description="\n".join(errors)[:3999], color=self.client.embed_color)
            await ctx.send(embed=errorembed)
        if len(items) > 0:
            total_worth = 0
            item_calc_result = []
            for item in items:
                total_worth += item[1] * item[2]
                item_calc_result.append(f"`{item[2]}` **{item[0]}**: `⏣ {comma_number(item[1] * item[2])}`")
            item_summary_embed = discord.Embed(title=f"Detected items", description="", color=self.client.embed_color)
            for item in item_calc_result:
                if len(item_summary_embed.description) + len(item) > 2000:
                    await ctx.send(embed=item_summary_embed)
                    item_summary_embed = discord.Embed(title=f"Detected items", description="", color=self.client.embed_color)
                item_summary_embed.description += f"{item}\n"
            if len(item_summary_embed.description) > 0:
                await ctx.send(embed=item_summary_embed)
            final_embed = discord.Embed(title="Total worth:", description=f"```\n⏣ {comma_number(total_worth)}\n```", color=self.client.embed_color)
            await ctx.send(embed=final_embed)
        else:
            await ctx.send(embed=discord.Embed(title="You didn't input any items.", color=discord.Color.red()))

        




    @checks.not_in_gen()
    @commands.command(name="dankreminders", aliases=["dankrm", "drm"])
    async def dankreminders(self, ctx):
        """
        Shows your reminders for Dank Memer and allows you to enable/disable them.
        Change your type of reminder via the select menu.
        """
        result = await self.client.db.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id) # gets the configuration for user to check if they have used dank reminder before
        if result is None:
            await self.client.db.execute("INSERT into remindersettings VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24)", ctx.author.id, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0) # creates new entry for settings
            result = await self.client.db.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id)
        reminders = await self.client.db.fetch("SELECT * FROM dankreminders WHERE member_id = $1 and guild_id = $2", ctx.author.id, ctx.guild.id) # gets user's reminders
        dailytime, lotterytime, worktime, redeemtime, weeklytime, monthlytime, hunttime, fishtime, digtime, highlowtime, snakeeyestime, searchtime, crimetime, begtime, horseshoetime, pizzatime, droptime, pmtime, streamtime, marriagetime, pettime, adventuretime = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
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
            if reminder.get('remindertype') == 17:
                horseshoetime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 18:
                pizzatime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 20:
                streamtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 21:
                pmtime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 22:
                marriagetime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 23:
                pettime = round(reminder.get('time')-time.time())
            if reminder.get('remindertype') == 24:
                adventuretime = round(reminder.get('time')-time.time())
        remindertimes = [dailytime or None, weeklytime or None, monthlytime or None, lotterytime or None, worktime or None, redeemtime or None, hunttime or None, fishtime or None, digtime or None, crimetime or None, begtime or None, searchtime or None, snakeeyestime or None, highlowtime or None, horseshoetime or None, pizzatime or None, droptime or None, streamtime or None, pmtime or None, marriagetime or None, pettime or None, adventuretime or None]
        newview = dankreminders(ctx, self.client, remindertimes, 15.0, truefalse(result.get('daily')), truefalse(result.get('weekly')), truefalse(result.get('monthly')), truefalse(result.get('lottery')), truefalse(result.get('work')), truefalse(result.get('redeem')), truefalse(result.get('hunt')), truefalse(result.get('fish')), truefalse(result.get('dig')), truefalse(result.get('crime')), truefalse(result.get('beg')), truefalse(result.get('search')), truefalse(result.get('snakeeyes')), truefalse(result.get('highlow')), truefalse(result.get('horseshoe')), truefalse(result.get('pizza')), truefalse(result.get('drop')), truefalse(result.get('stream')), truefalse(result.get('postmeme')), truefalse(result.get('marriage')), truefalse(result.get('pet')), truefalse(result.get('adventure')))
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

    @commands.cooldown(5, 1, commands.BucketType.user)
    @commands.command(name='setmarriagepartner', aliases=['smp', 'mp', 'marriagepartner'])
    async def set_marriage_partner(self, ctx, user: discord.Member = None):
        """
        Sets (or changes) your current Dank Memer marriage partner (for marriage reminders).
        To reset your marriage partner to None, do not specify a user.
        """
        existing_partner = await self.client.db.fetchval("SELECT m_partner FROM remindersettings WHERE member_id = $1", ctx.author.id)
        confirmview = confirm(ctx, self.client, 10.0)
        if user is None:
            if existing_partner is None:
                return await ctx.send("You don't even have a marriage partner set 🤨")
            existing_partner = self.client.get_user(existing_partner) or None
            embed = discord.Embed(title="Pending changes", description=f"Are you sure you want to reset your marriage partner?\n\nYour current partner is {existing_partner}.")
            confirmview.response = await ctx.send(embed=embed, view=confirmview)
            await confirmview.wait()
            if confirmview.returning_value is not True:
                embed.color, embed.description = discord.Color.red(), "No changes were made."
            else:
                await self.client.db.execute("UPDATE remindersettings SET m_partner = $1 WHERE member_id = $2", None, ctx.author.id)
                embed.color, embed.description = discord.Color.green(), "Your marriage partner has been reset. We hope this wasn't the result of a divorce."
            await confirmview.response.edit(embed=embed)
            return
        else:
            if existing_partner is not None:
                existing_partner = self.client.get_user(existing_partner) or None
                embed = discord.Embed(title=f"You already have a marriage partner set.", description=f"Do you want to change your marriage partner to {user}?\n\nYour current partner is {existing_partner}.", color=discord.Color.orange())
                confirmview.response = await ctx.send(embed=embed, view=confirmview)
                await confirmview.wait()
                if confirmview.returning_value is None or confirmview.returning_value is not True:
                    embed.color, embed.description = discord.Color.red(), "Aight, we are not changing anything today."
                    return await confirmview.response.edit(embed=embed)
                await self.client.db.execute("UPDATE remindersettings SET m_partner = $1 WHERE member_id = $2", user.id, ctx.author.id)
            else:
                await self.client.db.execute("INSERT INTO remindersettings(member_id, m_partner) VALUES($1, $2) ON CONFLICT(member_id) DO UPDATE SET m_partner=$2", ctx.author.id, user.id)
                embed = discord.Embed(title="Setting marriage partner...")
                confirmview.response = await ctx.send(embed=embed)
            embed.color, embed.description = discord.Color.green(), f"Your marriage partner is now set to **{user}**! When you share coins with or gift items to your partner, I will remind you to do it again in a few hours."
            embed.set_footer(text="Make sure you have enabled marriage reminders via the `dankreminders` command.")
            await confirmview.response.edit(embed=embed)



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


    @checks.not_in_gen()
    @commands.command(name="dankcooldowns", aliases=["dankcd", "dcd"])
    async def dankcooldowns(self, ctx):
        """
        Shows the existing reminders for Dank Memer.
        """
        reminders = await self.client.db.fetch("SELECT * FROM dankreminders WHERE member_id = $1 and guild_id = $2", ctx.author.id, ctx.guild.id)  # gets user's reminders
        dailytime, lotterytime, worktime, redeemtime, weeklytime, monthlytime, hunttime, fishtime, digtime, highlowtime, snakeeyestime, searchtime, crimetime, begtime, horseshoetime, pizzatime, streamtime, pmtime, marriagetime, pettime, adventuretime = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
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
            if reminder.get('remindertype') == 17:
                horseshoetime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 18:
                pizzatime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 20:
                streamtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 21:
                pmtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 22:
                marriagetime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 23:
                pettime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 24:
                adventuretime = f"<t:{reminder.get('time')}:R>"
        remindertimes = [dailytime or "**Ready!**", weeklytime or "**Ready!**", monthlytime or "**Ready!**",
                         lotterytime or "**Ready!**", worktime or "**Ready!**", redeemtime or "**Ready!**",
                         hunttime or "**Ready!**", fishtime or "**Ready!**", digtime or "**Ready!**", crimetime or "**Ready!**",
                         begtime or "**Ready!**", searchtime or "**Ready!**", snakeeyestime or "**Ready!**",
                         highlowtime or "**Ready!**", horseshoetime or "**Ready!**", pizzatime or "**Ready!**", streamtime or "**Ready!**", pmtime or "**Ready!**", marriagetime or "**Ready!**", pettime or "**Ready!**", adventuretime or "**Ready!**"]
        embed = discord.Embed(title="Your Dank Memer reminders", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        embed.description = f"""\nClaim daily <:DVB_calendar:873107952159059991>: {remindertimes[0]}
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
Use a Horseshoe <:DVB_Horseshoe:888404491647463454>: {remindertimes[14]}
Use a Pizza <:DVB_pizza:888404502280024145>: {remindertimes[15]}
Stream 🎮: {remindertimes[16]}
Post memes <:DVB_Laptop:915524266940854303>: {remindertimes[17]}
Marriage 💍: {remindertimes[18]}
Pet <:DVB_pet:928236242469011476>: {remindertimes[19]}
Adventure 🚀: {remindertimes[20]}"""
        if ctx.author.id == 650647680837484556:
            embed.description = embed.description + "\nSlap Frenzy <a:DVB_pandaslap:876631217750048798>: **Always Ready**\nBonk Blu <a:DVB_bonk:877196623506194452>: **Always Ready**"
        embed.set_footer(text="To enable/disable reminders, use dv.dankreminder instead.", icon_url=ctx.guild.icon.url)
        await ctx.send(embed=embed)