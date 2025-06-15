import asyncio
import difflib
import operator
import time

from utils.buttons import confirm
from utils.converters import BetterInt
from utils.format import comma_number, proper_userf
import discord
from discord.ext import commands
import random
from discord.ext import menus
from utils import checks
from utils.menus import CustomMenu
import math
from utils.format import plural, get_image
from PIL import Image
import asyncio
from io import BytesIO
from main import dvvt

from utils.time import humanize_timedelta
from custom_emojis import DVB_TRUE, DVB_FALSE


class DisplayItems(menus.ListPageSource):
    def __init__(self, entries, title, description):
        self.title = title
        self.description = description
        super().__init__(entries, per_page=7)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, description=self.description, color=menu.ctx.bot.embed_color, timestamp=discord.utils.utcnow())
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=True)
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed

class karutaevent(discord.ui.View):
    wrong_buttons = []

    def __init__(self, client, emoji_array, correct_emoji):
        self.response = None
        self.zombieno = 20
        self.pressed_data = {}
        self.wrong_buttons = []
        self.returning_value = None
        super().__init__(timeout=10.0)

        async def update_stat(user):
            if random.choice([False, False, False, False, False, False, False, True]):
                random.shuffle(self.children)
                await self.response.edit(view=self)
            if self.zombieno <= 0:
                return
            response = self.response
            embed = response.embeds[0]
            embed_desc = embed.description or ''
            embed_desc = embed_desc.replace('🧟', '')
            embed_desc = embed_desc.replace('\n', '')
            if self.zombieno == 1:
                self.zombieno -= 1
                if user not in self.pressed_data:
                    self.pressed_data[user] = 1
                else:
                    self.pressed_data[user] = self.pressed_data[user] + 1
                for b in self.children:
                    b.disabled = True
            else:
                self.zombieno -= 1
                if user not in self.pressed_data:
                    self.pressed_data[user] = 1
                else:
                    self.pressed_data[user] = self.pressed_data[user] + 1
                if self.zombieno % 7 == 0:
                    embed.description = embed_desc + f"\n\n{self.zombieno * '🧟'}"
                    await self.response.edit(embed=embed)
            if self.zombieno == 0:
                for b in self.children:
                    b.disabled = True
                self.returning_value = [self.pressed_data, karutaevent.wrong_buttons]
                karutaevent.wrong_buttons = []
                embed.description = embed_desc + "\n\n**The zombies have been defeated!**"
                await self.response.edit(embed=embed, view=self)
                self.stop()
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                #await interaction.response.defer()
                if interaction.user in karutaevent.wrong_buttons:
                    await interaction.response.send_message("You were killed by the zombies and can't futher interact with them.", ephemeral=True)
                elif str(self.emoji) == correct_emoji:
                    await update_stat(interaction.user)
                else:
                    karutaevent.wrong_buttons.append(interaction.user)
                    await interaction.response.send_message("Oh no! You selected the wrong button and were killed by the zombies. :(", ephemeral=True)

        for emoji in emoji_array:
            self.add_item(somebutton(emoji=emoji, style=discord.ButtonStyle.grey))

    async def on_timeout(self) -> None:
        self.returning_value = self.pressed_data, karutaevent.wrong_buttons
        for b in self.children:
            b.disabled = True
        await self.response.edit(view=self)
        karutaevent.wrong_buttons = []
        self.stop()


class ItemGames(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
        self.karutaconfig = ''
        self.karutaevent_isrunning = False

    async def get_item_name(self, name):
        item_names = await self.client.db.fetch("SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = $1", 'inventories')
        items = [i.get('column_name') for i in item_names if i.get('column_name') != 'user_id']
        for character in list(name):
            if character.isalpha():
                name.replace(character, '')
        lst = difflib.get_close_matches(name, items, n=1, cutoff=0.4)
        if len(lst) == 0:
            return None
        return lst[0]

    async def get_item_count(self, item, user):
        useritem_query = "SELECT {} FROM inventories WHERE user_id = $1".format(item)
        useritem = await self.client.db.fetchval(useritem_query, user.id)
        if useritem is None:
            return 0
        return useritem

    async def add_item_count(self, item, user, amount):
        does_inventory_exist = await self.client.db.fetchrow("SELECT * FROM inventories WHERE user_id = $1", user.id)
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

    async def remove_item_count(self, item, user, amount):
        if amount < 0:
            amount = abs(amount)
        does_inventory_exist = await self.client.db.fetchrow("SELECT * FROM inventories WHERE user_id = $1", user.id)
        useritem_query = "SELECT {} FROM inventories WHERE user_id = $1".format(item)
        useritem = await self.client.db.fetchval(useritem_query, user.id)
        if does_inventory_exist:
            if useritem is None:
                useritem_query = "UPDATE inventories SET {} = $2 WHERE user_id = $1 RETURNING {}".format(item, item)
                return await self.client.db.fetchval(useritem_query, user.id, -abs(amount), column=item)
            else:
                newcount = does_inventory_exist.get(item) - amount
                useritem_query = "UPDATE inventories SET {} = {} - $2 WHERE user_id = $1 RETURNING {}".format(item, item, item)
                return await self.client.db.fetchval(useritem_query, user.id, amount, column=item)
        else:
            useritem_query = "INSERT INTO inventories (user_id, {}) VALUES ($1, $2) RETURNING {}".format(item, item)
            return await self.client.db.fetchval(useritem_query, user.id, amount*-1, column=item)


    async def get_leaderboard(self, guild, query, top):
        leaderboard = []
        counts = await self.client.db.fetch(query, top)
        for count in counts:
            member = guild.get_member(count[0])
            name = member.name if member is not None else count[0]
            leaderboard.append((name, count[1]))
        if len(leaderboard) <= 10:
            embed = discord.Embed(color=self.client.embed_color, timestamp=discord.utils.utcnow())
            for index, position in enumerate(leaderboard, 1):
                embed.add_field(name=f"#{index} {position[0]}", value=f"**{comma_number(position[1])} skulls 💀**", inline=False)
            return embed
        ranks = []
        for index, position in enumerate(leaderboard, 1):
            ranks.append((f"#{index} {position[0]}", position[1]))
        return ranks

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name="inventory", aliases=['inv'], invoke_without_command=True)
    async def inventory(self, ctx, member: discord.Member = None):
        """
        Check out your inventory in Dank Vibes Bot!
        """
        if member is None:
            member = ctx.author
        result = await self.client.db.fetchrow("SELECT * FROM inventories WHERE user_id = $1", member.id)
        if result is None:
            invpage = "There is nothing in your inventory."
        else:
            item_names = await self.client.db.fetch("SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = $1", 'inventories')
            items = [i.get('column_name') for i in item_names if i.get('column_name') != 'user_id']
            invpage = ""
            itemdetails = await self.client.db.fetch("SELECT * FROM iteminfo")
            for item in items:
                item_count = result.get(item) or 0
                if item_count > 0:
                    item_name = None
                    item_emoji = None
                    item_hidden = None
                    for i in itemdetails:
                        if i.get('name') == item:
                            item_name = i.get('fullname')
                            item_emoji = i.get('emoji')
                            item_hidden = i.get('hidden')
                    if item_hidden != True:
                        if item_name is None or item_emoji is None:
                            invpage += f"`{comma_number(item_count)}` - **This item is missing important details, hence it cannot be displayed.**\n"
                        else:
                            invpage += f"{item_emoji} **{item_name}** • {comma_number(item_count)}\n"
        embed = discord.Embed(description=invpage, color=self.client.embed_color)
        embed.set_author(name=f"{proper_userf(member)}'s Inventory", icon_url=member.display_avatar.url)
        embed.set_footer(text="Use dv.inv info [item] to know more about an item.")
        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="give", aliases=['share', 'trade'])
    async def item_give(self, ctx, member: discord.Member = None, item: str = None, num: BetterInt = None):
        """
        Share some of your items with someone! During events, this command may not work for certain items.
        """
        if member is None:
            return await ctx.send("Specify a member to give items.")
        if item is None:
            return await ctx.send(f"Specify a item to give {proper_userf(member)}.")
        itemname = await self.get_item_name(item)
        if itemname is None:
            return await ctx.send(f"There is no item names `{item}`.")
        if member == ctx.author:
            details = await self.client.db.fetchrow("SELECT image FROM iteminfo WHERE name=$1", itemname)
            member_avatar = await member.display_avatar.with_format('png').read()
            emoji = details.get('image')
            if emoji is None:
                return await ctx.send("An error encountered while trying to get the details of this item.")
            emoji_bytes = await get_image(emoji)
            loop = asyncio.get_event_loop()
            def generate():
                main = Image.open("assets/spiderman.jpg")
                backg = main.copy()
                ima2 = Image.open(BytesIO(member_avatar)).convert('RGBA')
                ima2 = ima2.resize((94, 94))
                backg.paste(ima2, (86, 0), ima2)
                backg.paste(ima2, (568, 4), ima2)
                emoji = Image.open(BytesIO(emoji_bytes)).convert('RGBA')
                emoji = emoji.resize((71, 71))
                backg.paste(emoji, (203, 86), emoji)
                backg.paste(emoji, (411, 131), emoji)
                b = BytesIO()
                backg.save(b, format="png", optimize=True, quality=25)
                b.seek(0)
                file = discord.File(fp=b, filename="audacity.png")
                return file

            file = await loop.run_in_executor(None, generate)
            return await ctx.send(file=file)
        if num is None:
            num = 1
        if num < 1:
            return await ctx.send(f"You can't give less than 1 {itemname}.")
        user_itemcount = await self.get_item_count(itemname, ctx.author)
        if user_itemcount < num:
            return await ctx.send(f"You don't have enough `{itemname}` to share to {proper_userf(member)}.")
        member_itemcount = await self.get_item_count(itemname, member)
        if member_itemcount + num > 9223372036854775807:
            return await ctx.send(f"{proper_userf(member)} can only hold a maximum of 9,223,372,036,854,775,807 {itemname}.")
        details = await self.client.db.fetchrow("SELECT image, fullname FROM iteminfo WHERE name=$1", itemname)
        if details is None:
            item_url = None
            name = None
        else:
            item_url = details.get('image')
            name = details.get('fullname')
        if itemname == "argonphallicobject" and ctx.author.id == 560251854399733760:
            usernewcount = await self.add_item_count(itemname, ctx.author, num)
            return await ctx.send(f"# OwO What's this?\n\n**{ctx.author}** was about to give **{member}** {num} **{name}**, but **{ctx.author}** loves **{name}** SO much that he decided to make more of it himself. **{ctx.author}** now has `{usernewcount}` {name or itemname}.")
        membernewcount = await self.add_item_count(itemname, member, num)
        usernewcount = await self.remove_item_count(itemname, ctx.author, num)
        embed = discord.Embed(title=f"You gave {proper_userf(member)} {num} of your {name or itemname}!", description=f"You now have `{usernewcount}` {name or itemname}.\n{proper_userf(member)} now has `{membernewcount}` {name or itemname}.", color=discord.Color.green(), timestamp=discord.utils.utcnow())
        if item_url:
            embed.set_thumbnail(url=item_url)
        try:
            await ctx.message.reply(embed=embed)
        except:
            await ctx.send(embed=embed)


    @checks.dev()
    @inventory.command(name="edit", aliases=["devgive", "dg"])
    async def item_edit(self, ctx, member: discord.Member = None, item: str = None, num:int = None):
        """
        Developer Utilities - Edit the item count of a user.
        """
        if member is None:
            return await ctx.send("Specify a member to give items.")
        if item is None:
            return await ctx.send(f"Specify a item to give {proper_userf(member)}.")
        itemname = await self.get_item_name(item)
        if itemname is None:
            return await ctx.send(f"There is no item named `{item}`.")
        if num is None:
            num = 1
        existing_inv = await self.client.db.fetchrow("SELECT * FROM inventories WHERE user_id = $1", member.id)
        if existing_inv is None:
            insquery = ["INSERT", "INTO", "inventories(user_id,", itemname, ")", "VALUES(", str(member.id), ",", str(num), ")"]
            modifiedno = num
        else:
            count = existing_inv.get(itemname) or 0
            insquery = ["UPDATE", "INVENTORIES", "SET", itemname, "=", str(count+num), "WHERE", "user_id", "=", str(member.id)]
            modifiedno = count + num
        await self.client.db.execute(' '.join(insquery))
        return await ctx.send(f"{DVB_TRUE} I successfully gave {proper_userf(member)} {num} {itemname}s, they now have {modifiedno} {itemname}s.")

    @inventory.command(name="items")
    async def items(self, ctx):
        """
        See all the items that you can get in Dank Vibes Bot!
        """
        count = await self.client.db.fetchval("SELECT COUNT(*) FROM iteminfo")
        if count == 0:
            embed = discord.Embed(title="Items you can get", description="There are no items.", color=self.client.embed_color)
        else:
            embed = discord.Embed(title="Items you can get", description=f"Here are all the items you can get. There are {count} of them!", color=self.client.embed_color)
            items = await self.client.db.fetch("SELECT name, fullname, emoji, description FROM iteminfo")
            results = []
            for item in items:
                query = "SELECT SUM({}) FROM inventories".format(item.get('name'))
                in_circulation = await self.client.db.fetchval(query)
                results.append((f"{item.get('emoji')} {item.get('fullname')}", f"{item.get('description')}\nIn circulation: `{comma_number(in_circulation or 0)}`"))
            pages = CustomMenu(source=DisplayItems(results, "Items you can get", f"Here are all the items you can get. There are {count} of them!"), clear_reactions_after=True, timeout=30)
            return await pages.start(ctx)

    @inventory.command(name="info", aliases=['item'])
    async def item_info(self, ctx, *, item: str = None):
        """
        Know more about an item.
        """
        if item is None:
            return await ctx.send("You need to specify the item you want to know about.")
        itemname = await self.get_item_name(item)
        if itemname is None:
            return await ctx.send(f"There is no item named `{item}`.")
        itemdata = await self.client.db.fetchrow("SELECT * FROM iteminfo WHERE name = $1", itemname)
        if itemdata is None:
            return await ctx.send("An error occured while trying to get the data for this item.")
        embed = discord.Embed(title=itemdata.get('fullname') or "No item name", description=itemdata.get('description') or "No description", color=self.client.embed_color)
        embed.set_author(name="Item information")
        embed.set_thumbnail(url=itemdata.get('image'))
        query = ["SELECT", itemname, "FROM", "inventories", "WHERE", "user_id", "=", "$1"]
        query = " ".join(query)
        num = await self.client.db.fetchrow(query, ctx.author.id)
        quantity = 0 if num is None else num.get(itemname) or 0
        embed.add_field(name="ID", value=f"`{itemname}`")
        embed.set_footer(text=f"You own {quantity} of this item.")
        await ctx.send(embed=embed)

    @commands.command(name="use")
    async def use(self, ctx, item: str = None, *, args: str = None):
        """
        Use an item in your inventory.
        """
        if item is None:
            return await ctx.send("You need to specify the item you want to know about.")
        itemname = await self.get_item_name(item)
        if itemname is None:
            return await ctx.send(f"There is no item named `{item}`.")
        itemdata = await self.client.db.fetchrow("SELECT * FROM iteminfo WHERE name = $1", itemname)
        if itemdata is None:
            return await ctx.send("An error occured while trying to get the data for this item.")
        if itemdata.get('usable') is not True:
            return await ctx.send(f"**{itemdata.get('fullname')}** isn't a usable item lol")
        count = await self.get_item_count(itemname, ctx.author)
        if count < 1:
            return await ctx.send(f"You don't have any **{itemdata.get('fullname')}**s to use.")
        if itemdata.get('usable') is True:
            if itemname == 'dumbfightpotion':
                if await self.client.db.fetchval("SELECT dumbfight_result FROM userconfig WHERE user_id = $1", ctx.author.id) is None:
                    confirmview = confirm(ctx, self.client, 20.0)
                    embed = discord.Embed(title=f"Are you sure you want to use a {itemdata.get('fullname')}?", description="Drinking a dumbfight potion might cause you to lose or win your dumbfights for the next 2 hours.")
                    try:
                        confirmview.response = await ctx.reply(embed=embed, view=confirmview)
                    except:
                        confirmview.response = await ctx.send(embed=embed, view=confirmview)
                    await confirmview.wait()
                    if confirmview.returning_value is not True:
                        embed.color, embed.description= discord.Color.red(), "You decided not to use the dumbfight potion."
                        await confirmview.response.edit(embed=embed)
                    else:
                        embed.color = discord.Color.green()
                        await confirmview.response.edit(embed=embed)
                        userconf = await self.client.db.fetchrow("SELECT * FROM userconfig WHERE user_id = $1", ctx.author.id)
                        if userconf is None or userconf.get('dumbfight_result') is None and await self.get_item_count(itemname, ctx.author) > 0:
                            remaining = await self.remove_item_count(itemname, ctx.author, 1)
                            msgstatus = await ctx.send(f"{ctx.author} is gulping down the dumbfight potion...")
                            result = random.choice([True, False])
                            if userconf is None:
                                await self.client.db.execute("INSERT INTO userconfig(user_id, dumbfight_result, dumbfight_rig_duration) VALUES($1, $2, $3)", ctx.author.id, result, round(time.time())+14400)
                            else:
                                await self.client.db.execute("UPDATE userconfig SET dumbfight_result = $1, dumbfight_rig_duration = $2 WHERE user_id = $3", result, round(time.time())+7200, ctx.author.id)
                            await asyncio.sleep(3.0)
                            if result is True:
                                await msgstatus.edit(content=f"**{ctx.author.name}** finished the dumbfight potion in one gulp.\nThey are now immune from losing dumbfights for 2 hours! They now have {remaining} Dumbfight Potions left.")
                            else:
                                await msgstatus.edit(content=f"Alas! The dumbfight potion that **{ctx.author.name}** drank was a bad one, and **{ctx.author.name}** was poisoned 🤒.\nThey will lose all dumbfights for the next 2 hours. They now have {remaining} Dumbfight Potions left.")
                        else:
                            return await ctx.send("It appears that you already have a active dumbfight potion in effect. (1)")
                else:
                    return await ctx.send("It appears that you already have a active dumbfight potion in effect. (2)")
            elif itemname == 'raizelsushi':
                if args is not None:
                    try:
                        number_eaten = int(args)
                    except ValueError:
                        number_eaten = 1
                else:
                    number_eaten = 1
                current_amt = await self.get_item_count(itemname, ctx.author)
                if current_amt >= number_eaten:
                    remaining = await self.remove_item_count(itemname, ctx.author, number_eaten)
                    if number_eaten == 1:
                        how_author_ate = "picks up a pair of chopsticks, and eats a single sushi."
                    elif number_eaten < 10:
                        how_author_ate = f"picks up a pair of chopsticks, and slowly eats {number_eaten} sushis."
                    elif number_eaten < 50:
                        how_author_ate = f"gets their friend to help feed them {number_eaten} sushis."
                    elif number_eaten < 75:
                        how_author_ate = f"gets 5 of their friends to help feed them {number_eaten} sushis."
                    elif number_eaten < 100:
                        how_author_ate = f"assembles a whole party to help feed them {number_eaten} sushis."
                    else:
                        how_author_ate = f"takes the whole plate of {number_eaten} sushis and STUFFS IT DOWN THEIR THROAT. How are they still alive??"
                    await ctx.send(f"**{ctx.author}** {how_author_ate}\nThey now have {remaining} Raizel Sushi left.")
                else:
                    return await ctx.send("I understand you are craving for sushis, but you don't have that many Raizel's Sushi to eat.")
            elif itemname == 'snipepill':
                if await self.client.db.fetchval("SELECT snipe_res_result FROM userconfig WHERE user_id = $1", ctx.author.id) is None:
                    confirmview = confirm(ctx, self.client, 20.0)
                    embed = discord.Embed(title=f"Are you sure you want to use a {itemdata.get('fullname')}?", description="Consuming a Snipe Pill might help to hide your sniped messages or make them worse, for a random period of time.")
                    try:
                        confirmview.response = await ctx.reply(embed=embed, view=confirmview)
                    except:
                        confirmview.response = await ctx.send(embed=embed, view=confirmview)
                    await confirmview.wait()
                    if confirmview.returning_value is not True:
                        embed.color, embed.description = discord.Color.red(), "You decided not to use the Snipe Pill.."
                        await confirmview.response.edit(embed=embed)
                    else:
                        embed.color = discord.Color.green()
                        await confirmview.response.edit(embed=embed)
                        userconf = await self.client.db.fetchrow("SELECT * FROM userconfig WHERE user_id = $1", ctx.author.id)
                        if userconf is None or userconf.get('snipe_res_result') is None and await self.get_item_count(itemname, ctx.author) > 0:
                            remaining = await self.remove_item_count(itemname, ctx.author, 1)
                            result = random.choice([True, True, False])
                            if result is True:
                                duration = random.randint(60, 300)
                            else:
                                duration = 86400
                            await self.client.db.execute("INSERT INTO userconfig (user_id, snipe_res_result, snipe_res_duration) VALUES($1, $2, $3) ON CONFLICT(user_id) DO UPDATE SET snipe_res_result = $2, snipe_res_duration = $3", ctx.author.id, result, round(time.time()) + duration)
                            if result is True:
                                msg = f"**{ctx.author.name}** consumed the pill without any problems. Trying to snipe **{ctx.author.name}**'s messages will show gibberish text instead for **{humanize_timedelta(seconds=duration)}**."
                            else:
                                msg = f"**{ctx.author.name}** consumed the pill without **realising it had expired**, but it was too late. All of **{ctx.author.name}**'s sniped messages will be OwOified for **{humanize_timedelta(seconds=duration)}**."
                            await ctx.send(f"{msg}\nThey now have {remaining} Snipe Pills left.")
                        else:
                            return await ctx.send("It appears that you already have an active Snipe Pill in effect. (1)")
                else:
                    return await ctx.send("It appears that you already have an active Snipe Pill in effect. (2)")

            elif itemname == 'canisterofclowngas':
                if ctx.channel.id in self.client.clownmode:
                    return await ctx.send("The clown gas haven't worn off in this channel. If you use it now, the effects would be more potent and everyone might stay as a clown permanently (as if they aren't already).")
                if await self.get_item_count(itemname, ctx.author) > 0:
                    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
                    original_overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
                    overwrite.send_messages = False
                    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
                    msgstatus = await ctx.send(
                        f"**{ctx.author.name}** slowly places a canister containing something unknown in the center of {ctx.channel.mention}. No one notices as **{ctx.author.name}** quietly leaves the channel, leaving the canister sitting in the channel.")
                    await asyncio.sleep(6.0)
                    await msgstatus.edit(content="<:clown_gas_can:958622707568771072>")
                    await asyncio.sleep(3.0)
                    await msgstatus.add_reaction("⚠️")
                    remaining = await self.remove_item_count(itemname, ctx.author, 1)
                    now = round(time.time())
                    self.client.clownmode[ctx.channel.id] = now + self.client.clown_duration
                    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=original_overwrite)
                    msgstatus2 = await ctx.send(
                        f"A yellowish gas starts coming out of the canister. Without warning, everyone in the channel turns into a clown for {humanize_timedelta(seconds=self.client.clown_duration)}. 🤡\n{ctx.author} now has {remaining} Cans of clown gas left.")
            elif itemname == 'wickedrusteze':
                for command in self.client.commands:
                    command.reset_cooldown(ctx)
                    if isinstance(command, commands.Group):
                        for subcommand in command.commands:
                            subcommand.reset_cooldown(ctx)
                await ctx.send("You took a bath in Rust-eze Medicated Bumper Ointment and wiped away all your cooldowns! ")

        else:
            return await ctx.send(f"**{itemdata.get('fullname')}** isn't a usable item lol")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.webhook_id is not None:
            return
        if message.channel.id in self.client.clownmode:
            if self.client.clownmode[message.channel.id] < round(time.time()):
                del self.client.clownmode[message.channel.id]
                return await message.channel.send(f"The clown gas has dissipated away, and everyone is back to normal. {message.author.mention} quickly kicks away the canister, and life goes on as normal.")
            webhook = await self.client.get_webhook(message.channel)
            clown_avatar = self.client.clownprofiles.get(message.author.id, None)
            if clown_avatar is None:
                list_of_clown_avatars = [
                    "https://cdn.nogra.xyz/images/clowns/imp_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/woozy_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/relieved_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/pensive_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/original_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/neutral_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/weary_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/skeptical_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/nerd_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/flushed_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/sunglasses_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/smirk_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/sleeping_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/rolling_eyes_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/heart_eyes_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/grimace_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/floating_heart_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/crying_clown.png",
                    "https://cdn.nogra.xyz/images/clowns/angry_clown.png",
                ]
                clown_avatar = random.choice(list_of_clown_avatars)
                self.client.clownprofiles[message.author.id] = clown_avatar
            disp_name = message.author.display_name
            if len(message.attachments) > 0:
                embeds = []
                for attachment in message.attachments:
                    embed = discord.Embed(color=self.client.embed_color,
                                          description=f"📂 [{attachment.filename}]({attachment.proxy_url})").set_author(
                        icon_url=clown_avatar, name=disp_name)
                    if attachment.height is not None:
                        embed.set_image(url=attachment.url)
                    embeds.append(embed)
            else:
                embeds = None
            await message.delete()
            if embeds is not None:
                await webhook.send(content=message.content, embeds=embeds, username=disp_name, avatar_url=clown_avatar)
            else:
                if len(message.content) > 0:
                    await webhook.send(content=message.content, username=disp_name, avatar_url=clown_avatar)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='itemleaderboard', aliases=['ilb', 'itemlb'])
    async def itemleaderboard(self, ctx, *, item: str = None):
        """
        Shows the leaderboard for a certain item!
        """
        if item is None:
            all_items = await self.client.db.fetch("SELECT name FROM iteminfo")
            all_items = [item.get('name') for item in all_items]
            all_inventories = await self.client.db.fetch("SELECT * FROM inventories")
            invs = {}
            for inv in all_inventories:
                totalitemcount = 0
                for item in all_items:
                    totalitemcount += inv.get(item) or 0
                invs[inv.get('user_id')] = totalitemcount
            sorted_invs = sorted(invs.items(), key=lambda x: x[1], reverse=True)
            sorted_invs = sorted_invs[:10]
            finalresult = []
            for i in sorted_invs:
                user = self.client.get_user(i[0])
                if user is None:
                    user = i[0]
                finalresult.append((user, i[1]))
            itemname = "item"
            title = f"Total Inventory Leaderboard"
            embed = discord.Embed(title=title, color=self.client.embed_color)
            embed.set_author(name="Dank Vibes")
            embed.set_footer(text="Use dv.inv ilb [item] to see the leaderboard for an item.")
        else:
            itemname = await self.get_item_name(item)
            if itemname is None:
                return await ctx.send(f"There is no item named `{item}`.")
            async with ctx.typing():
                query = f"SELECT user_id, {itemname} FROM inventories WHERE {itemname} IS NOT null and {itemname} != 0 ORDER BY {itemname} DESC LIMIT 10"
                result = await self.client.db.fetch(query)
                if result is None:
                    return await ctx.send("An error occured while trying to get the data for this item.")
                if len(result) == 0:
                    return await ctx.send(f"There are no members who've gotten a {itemname} yet..")
                itemdetails = await self.client.db.fetchrow("SELECT fullname, image FROM iteminfo WHERE name = $1", itemname)
                if itemdetails is None:
                    return await ctx.send("An error occured while trying to get the data for this item.")
                finalresult = []
                for user in result:
                    user_id = user.get('user_id')
                    user_name = self.client.get_user(user_id)
                    if user_name is None:
                        user_name = user_id
                    user_itemcount = user.get(itemname)
                    finalresult.append((user_name, user_itemcount))
                title = f"Item Leaderboard for {itemdetails.get('fullname') or item} 🎖"
                embed = discord.Embed(title=title, color=self.client.embed_color)
                embed.set_author(name="Dank Vibes")
                embed.set_thumbnail(url=itemdetails.get('image'))
                embed.set_footer(text="Use dv.inv info [item] to know more about an item.")
        for i, result in enumerate(finalresult):
            user = result[0]
            count = result[1]
            user_disp = user if type(user) == int else proper_userf(user)
            embed.add_field(name=f"{i + 1}. {user_disp} {'🥇' if i == 0 else '🥈' if i == 1 else '🥉' if i == 2 else ''}", value=f"{comma_number(count)} {itemname}s", inline=False)
        await ctx.send(embed=embed)