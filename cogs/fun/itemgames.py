import asyncio
import difflib
import operator
from utils.format import print_exception, comma_number
import discord
from discord.ext import commands
from utils.context import DVVTcontext
import random
from discord.ext import menus
from utils import checks
from utils.menus import CustomMenu
import math
from utils.format import plural

items = ['skull', 'argonphallicobject', 'llamaspit', 'slicefrenzycake', 'wickedrusteze']

def get_item_name(name):
    lst = difflib.get_close_matches(name, items, n=1, cutoff=0.4)
    if len(lst) == 0:
        return None
    return lst[0]

class ItemLeaderboard(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=menu.ctx.bot.embed_color, timestamp=discord.utils.utcnow())
        for entry in entries:
            embed.add_field(name=f"{entry[0]}", value=f"**⏣ {comma_number(entry[1])}**", inline=False)
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
        self.client = client
        self.karutaconfig = ''
        self.karutaevent_isrunning = False

    async def get_leaderboard(self, guild, query, top):
        leaderboard = []
        counts = await self.client.pool_pg.fetch(query, top)
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

    @checks.has_permissions_or_role(administrator=True)
    @commands.group(name="inventory", aliases=['inv'], invoke_without_command=True)
    async def inventory(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        result = await self.client.pool_pg.fetchrow("SELECT * FROM inventories WHERE user_id = $1", member.id)
        if result is None:
            invpage = "There is nothing in your inventory."
        else:
            invpage = ""
            itemdetails = await self.client.pool_pg.fetch("SELECT * FROM iteminfo")
            indexes = {}
            for i, item in enumerate(itemdetails):
                indexes[i] = [item.get('fullname'), item.get('emoji')]
            for index, i in enumerate(result[1:]):
                itemcount = 0 if i is None else i or 0
                if itemcount > 0:
                    stritemcount = comma_number(0 if i is None else i or 0)
                    try:
                        invpage += f"{indexes[index][1]} **{indexes[index][0]}** • {stritemcount}\n"
                    except KeyError:
                        invpage += f"`{stritemcount}` **This item is missing important details, hence it cannot be shown.**"
        embed = discord.Embed(description=invpage, color=self.client.embed_color)
        embed.set_author(name=f"{member}'s Inventory", icon_url=member.display_avatar.url)
        embed.set_footer(text="Use dv.inv info [item] to know more about an item.")
        await ctx.send(embed=embed)

    @checks.dev()
    @inventory.command(name="give", aliases=["devgive", "dg"])
    async def item_give(self, ctx, member: discord.Member = None, item: str = None, num:int = None):
        if member is None:
            return await ctx.send("Specify a member to give items.")
        if item is None:
            return await ctx.send(f"Specify a item to give {member}.")
        itemname = get_item_name(item)
        if itemname is None:
            return await ctx.send(f"There is no item names `{item}`.")
        if num is None:
            num = 1
        existing_inv = await self.client.pool_pg.fetchrow("SELECT * FROM inventories WHERE user_id = $1", member.id)
        if existing_inv is None:
            insquery = ["INSERT", "INTO", "inventories(user_id,", itemname, ")", "VALUES(", str(member.id), ",", str(num), ")"]
            modifiedno = num
        else:
            count = existing_inv.get(itemname) or 0
            insquery = ["UPDATE", "INVENTORIES", "SET", itemname, "=", str(count+num), "WHERE", "user_id", "=", str(member.id)]
            modifiedno = count + num
        await self.client.pool_pg.execute(' '.join(insquery))
        return await ctx.send(f"<:DVB_True:887589686808309791> I successfully gave {member} {num} {itemname}s, they now have {modifiedno} {itemname}s.")

    @inventory.command(name="info", aliases=['item'])
    async def item_info(self, ctx, item: str = None):
        if item is None:
            return await ctx.send("You need to specify the item you want to know about.")
        itemname = get_item_name(item)
        if itemname is None:
            return await ctx.send(f"There is no item names `{item}`.")
        itemdata = await self.client.pool_pg.fetchrow("SELECT * FROM iteminfo WHERE name = $1", itemname)
        if itemdata is None:
            return await ctx.send("An error occured while trying to get the data for this item.")
        embed = discord.Embed(title=itemdata.get('fullname') or "No item name", description=itemdata.get('description') or "No description", color=self.client.embed_color)
        embed.set_author(name="Item information")
        embed.set_thumbnail(url=itemdata.get('image'))
        query = ["SELECT", itemname, "FROM", "inventories", "WHERE", "user_id", "=", "$1"]
        query = " ".join(query)
        num = await self.client.pool_pg.fetchrow(query, ctx.author.id)
        quantity = 0 if num is None else num.get(itemname) or 0
        embed.set_footer(text=f"You own {quantity} of this item.")
        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name='skullleaderboard', aliases=['slb', 'skulllb'])
    async def skullleaderboard(self, ctx, *, arg: str = None):
        """
        Shows the Skull leaderboard for Dank Vibes.
        """
        await ctx.send("This command is deprecated and will be removed in a later update. Use `dv.itemlb` instead!")
        async with ctx.typing():
            arg = "total 5" if arg is None else arg
            number = [int(i) for i in arg.split() if i.isdigit()]
            top = 5 if len(number) == 0 else number[0]
            title = "Skull Leaderboard 🎖"
            query = "SELECT user_id, skull FROM inventories WHERE skull IS NOT null ORDER BY skull DESC LIMIT $1"
            leaderboard = await self.get_leaderboard(ctx.guild, query, top)
            if isinstance(leaderboard, discord.Embed):
                leaderboard.title = title
                return await ctx.send(embed=leaderboard)
            else:
                pages = CustomMenu(source=ItemLeaderboard(leaderboard, title), clear_reactions_after=True, timeout=60)
                return await pages.start(ctx)


    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name='itemleaderboard', aliases=['ilb', 'itemlb'])
    async def itemleaderboard(self, ctx, *, item: str = None):
        """
        Shows the Skull leaderboard for Dank Vibes.
        You can specify how many members you want to see on the leaderboard.
        """
        if item is None:
            return await ctx.send("You need to specify the item you want to know about.")
        itemname = get_item_name(item)
        if itemname is None:
            return await ctx.send(f"There is no item named `{item}`.")
        async with ctx.typing():
            query = f"SELECT user_id, {itemname} FROM inventories WHERE {itemname} IS NOT null and {itemname} != 0 ORDER BY {itemname} DESC LIMIT 10"
            result = await self.client.pool_pg.fetch(query)
            if result is None:
                return await ctx.send("An error occured while trying to get the data for this item.")
            if len(result) == 0:
                return await ctx.send(f"There are no members who've gotten a {itemname} yet..")
            itemdetails = await self.client.pool_pg.fetchrow("SELECT fullname, image FROM iteminfo WHERE name = $1", itemname)
            if itemdetails is None:
                return await ctx.send("An error occured while trying to get the data for this item.")
            title = f"Item Leaderboard for {itemdetails.get('fullname') or item} 🎖"
            embed = discord.Embed(title=title, color=self.client.embed_color)
            embed.set_author(name="Dank Vibes")
            embed.set_thumbnail(url=itemdetails.get('image'))
            embed.set_footer(text="Use dv.inv info [item] to know more about an item.")

            for i in range(len(result)):
                user = self.client.get_user(result[i].get('user_id'))
                if user is None:
                    user = result[i].get('user_id')
                count = result[i].get(f'{itemname}')
                embed.add_field(name=f"{i + 1}. {user} {'🥇' if i == 0 else '🥈' if i == 1 else '🥉' if i == 2 else ''}", value=f"{plural(count):{itemname}}", inline=False)
            await ctx.send(embed=embed)