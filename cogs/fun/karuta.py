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

items = ['skull', 'argonphallicobject', 'llamaspit']

def get_item_name(name):
    lst = difflib.get_close_matches(name, items, n=1, cutoff=0.4)
    if len(lst) == 0:
        return None
    return lst[0]

class SkullLeaderboard(menus.ListPageSource):
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


class karuta(commands.Cog):
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

    @commands.Cog.listener()
    async def on_message(self, message):
        # sourcery skip: none-compare, remove-pass-body, remove-redundant-fstring, switch
        try:
            if self.karutaevent_isrunning:
                return
            if self.karutaconfig == '':
                self.karutaconfig = await self.client.pool_pg.fetchrow("SELECT * FROM karutaeventconfig")
            if self.karutaconfig is None:
                return
            if self.karutaconfig.get('channel_id') is None or self.karutaconfig.get('channel_id') == '':
                return
            whitelisted_channel_ids = self.karutaconfig.get('channel_id').split(',')
            if str(message.channel.id) not in whitelisted_channel_ids:
                return
            if self.karutaconfig.get('percentage_chance') is None:
                return
            if message.author.bot:
                return
            context = await self.client.get_context(message)
            if context.valid == True:
                return
            randomdec = random.random()
            if message.content.lower() == "k d forcespawn" and message.author.id == 650647680837484556:
                pass
            elif randomdec >= self.karutaconfig.get('percentage_chance'):
                return
            emojis = [("🔨", "⛏️", "🪓",),
                      ("🙈", "🙉", "🙊",),
                      ("🎃", "👽", "🤡",),
                      ("🐟", "🐬", "🐳",),
                      ("⭕", "🚫", "❌",),
                      ("🙂", "🙃", "😐",),
                      ("🌘", "🌒", "🌔",),
                      ("🃏", "🎴", "🀄",),
                      ("☘️", "🍀", "🍃",),
                      ("🌼", "🌻", "🌷",)
                      ]
            selected_pattern = emojis[random.randint(0, 9)]
            chosen_emoji = selected_pattern[random.randint(0, 2)]
            doubledrop = random.choice([False, False, False, False, False, False, False, True])
            maxdrop = random.choice([False, False, False, False, False, False, False, False, False, False, False, False, True])
            msg = ''
            if doubledrop:
                msg += "Killing this horde of zombies will award you with **twice** the number of skulls! 💀\n"
            if maxdrop:
                msg += "Killing this horde of zombies will award **everyone** with the maximum number of skulls! 💀"
            embed = discord.Embed(title="A new horde of zombies are incoming!",
                                  description=f"Click {chosen_emoji} to fight the incoming zombies!\n\n🧟🧟🧟🧟🧟🧟🧟🧟🧟🧟🧟🧟🧟🧟🧟🧟🧟🧟🧟🧟\n",
                                  color=self.client.embed_color).set_thumbnail(
                url="https://cdn.nogra.me/core/zombie.gif")
            self.karutaevent_isrunning = True
            msg = await message.channel.send(msg, embed=embed)
            karutaview = karutaevent(self.client, selected_pattern, chosen_emoji)
            await asyncio.sleep(2.0)
            await msg.edit(view=karutaview)
            karutaview.response = msg
            await karutaview.wait()
            summary = ''
            if karutaview.returning_value == None:
                await asyncio.sleep(1.0)
            buttons_clicked = karutaview.returning_value[0]
            failed_users = karutaview.returning_value[1]
            buttons_clicked = sorted(buttons_clicked.items(), key=operator.itemgetter(1), reverse=True)
            if len(buttons_clicked) < 4:
                quarter = None
                first_place = 0
                second_place = 1
            else:
                quarter = math.ceil(len(buttons_clicked)/4)
                first_place = quarter - 1
                second_place = first_place + quarter
            await message.guild.get_member(650647680837484556).send(f"{quarter, first_place, second_place}")
            for count, i in enumerate(buttons_clicked):
                if count <= first_place:
                    skull = 3 if doubledrop != True else 6
                elif count <= second_place:
                    skull = 2 if doubledrop != True else 4
                else:
                    skull = 1 if doubledrop != True else 2
                if maxdrop:
                    skull = 6 if doubledrop else 3
                inv = await self.client.pool_pg.fetchrow("SELECT * FROM inventories WHERE user_id = $1", i[0].id)
                if i[0] in failed_users:
                    pass
                elif inv is None:
                    await self.client.pool_pg.execute("INSERT INTO inventories VALUES($1, $2, $3)", i[0].id, skull, 0)
                else:
                    current = inv.get('skull') or 0
                    await self.client.pool_pg.execute("UPDATE inventories SET skull = $1 WHERE user_id = $2", current+skull, i[0].id)
                summary += f"⚔️ {i[0].mention} killed **{i[1]}** zombie{'s' if i[1] != 1 else ''} {f'and got **{skull}** skulls! 💀' if i[0] not in failed_users else 'but **died** afterwards, rest in peace.'}\n"
            for i in failed_users:
                if i in [j[0] for j in buttons_clicked]:
                    pass
                else:
                    summary += f"🪦{i.mention} **died**, rest in peace.\n"
            try:
                await msg.reply(embed=discord.Embed(title="Summary", description=summary if summary != '' else "**What a disgrace!**\nNo one fought the zombies and they will haunt the children tonight 😈", color=self.client.embed_color, timestamp=discord.utils.utcnow()).set_footer(text="You can see how many skulls you have with dv.inv"))
            except discord.HTTPException:
                await message.channel.send(embed=discord.Embed(title="Summary", description=summary if summary != '' else "**What a disgrace!**\nNo one fought the zombies and they will haunt the children tonight 😈", color=self.client.embed_color, timestamp=discord.utils.utcnow()))
            self.karutaevent_isrunning = False
        except Exception as e:
            full_error = print_exception(f'Ignoring exception in Karuta message events', e)
            await self.client.get_channel(871737028105109574).send(embed=discord.Embed(description=f"```py\n{full_error}\n```"))

    @checks.has_permissions_or_role(administrator=True)
    @commands.group(name="karutaconfig", aliases=['kconfig'], invoke_without_command=True)
    async def karutaconfig(self, ctx):
        if self.karutaconfig is None or self.karutaconfig == '':
            channel = "Not set"
            rate = "Not set"
        else:
            whitelisted_channels = self.karutaconfig.get('channel_id')
            if whitelisted_channels is None:
                channel = "Not set"
            else:
                whitelisted_channels = whitelisted_channels.split(',')
                channel = []
                for i in whitelisted_channels:
                    chan = ctx.guild.get_channel(int(i))
                    if chan is None:
                        channel.append(f"{i} (unknown or deleted channel)")
                    else:
                        channel.append(chan.mention)
            rate = self.karutaconfig.get('percentage_chance')
        embed = discord.Embed(title="Karuta Event Configuration",
                              description=f"**Channel** to send Karuta events: {','.join(channel) if type(channel) == list else channel}\n**Rate** of events spawning: {round(rate, 4)*100 if type(rate) != str else 'Not set'}%",
                              color=self.client.embed_color)
        embed.add_field(name="To change/update the configuratin:",
                        value="Use `kconfig channel [channel]` to add/remove a channel where Karuta events are spawned.\nUse `kconfig rate [rate_in_decimals]` to change the rate of events spawning.")
        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(administrator=True)
    @karutaconfig.command(name="channel", aliases=['chan'])
    async def config_channel(self, ctx, channel: discord.TextChannel = None):
        """
        Change the channel where Karuta events will spawn.
        """
        if channel is None:
            return await ctx.send("You need to specify a channel where Karuta halloween events will be sent.")
        if self.karutaconfig is None:
            await self.client.pool_pg.execute("INSERT INTO karutaeventconfig VALUES($1, $2)", channel.id, None)
        else:
            whitelisted_channels = self.karutaconfig.get('channel_id')
            if whitelisted_channels is None:
                whitelisted_channels = (str(channel.id))
                await ctx.send(f"{channel.mention} has been added as a channel to spawn Halloween events.")
                await self.client.pool_pg.execute("UPDATE karutaeventconfig SET channel_id = $1", whitelisted_channels)
                self.karutaconfig = await self.client.pool_pg.fetchrow("SELECT * FROM karutaeventconfig")
                return
            whitelisted_channels = whitelisted_channels.split(',')
            if str(channel.id) in whitelisted_channels:
                whitelisted_channels.remove(str(channel.id))
                await ctx.send(f"Halloween events will no longer spawn in {channel.mention}.")
            else:
                whitelisted_channels.append(str(channel.id))
                await ctx.send(f"{channel.mention} has been added as a channel to spawn Halloween events.")
            await self.client.pool_pg.execute("UPDATE karutaeventconfig SET channel_id = $1", ','.join(whitelisted_channels) if type(whitelisted_channels) == list else whitelisted_channels)
        self.karutaconfig = await self.client.pool_pg.fetchrow("SELECT * FROM karutaeventconfig")

    @commands.has_guild_permissions(administrator=True)
    @karutaconfig.command(name="rate")
    async def config_rate(self, ctx, rate: str = None):
        """
        Change the rate of Karuta events spawning.
        The rate can only be between `0.01` and `0.99` (both inclusive).
        """
        if rate is None:
            return await ctx.send("You need to specify the rate of Karuta events spawning.")
        try:
            rate = float(rate)
        except ValueError:
            return await ctx.send(f"{rate} isn't a valid number.")
        if rate > 0.99 or rate < 0.01:
            return await ctx.send(
                "The rate of events spawning can only be more than `0.01` or less than `0.99` (both inclusive).")
        if self.karutaconfig is None:
            await self.client.pool_pg.execute("INSERT INTO karutaeventconfig VALUES($1, $2)", None, rate)
        else:
            await self.client.pool_pg.execute("UPDATE karutaeventconfig SET percentage_chance = $1", rate)
        await ctx.send(f"Karuta events now have a chance of {rate}/1 spawning.")
        self.karutaconfig = await self.client.pool_pg.fetchrow("SELECT * FROM karutaeventconfig")

    @checks.has_permissions_or_role(administrator=True)
    @commands.group(name="inventory", aliases=['inv'], invoke_without_command=True)
    async def inventory(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        result = await self.client.pool_pg.fetchrow("SELECT * FROM inventories WHERE user_id = $1", member.id)
        skulls = comma_number(0 if result is None else result.get('skull') or 0)
        invpage = f"💀 Skulls • {skulls}"
        argon = 0 if result is None else result.get('argonphallicobject') or 0
        if argon != 0:
            invpage += f"\n<:DVB_argonphallicobject:902134179863605258> Argon-based Phallic Object • {comma_number(argon)}"
        spit = 0 if result is None else result.get('llamaspit') or 0
        if spit != 0:
            invpage += f"\n🦙 Llama's Spit • {comma_number(spit)}"
        embed = discord.Embed(description=invpage, color=self.client.embed_color)
        embed.set_author(name=f"{member}'s Halloween Stash", icon_url=member.display_avatar.url)
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
        print(query)
        num = await self.client.pool_pg.fetchrow(query, ctx.author.id)
        quantity = 0 if num is None else num.get(itemname) or 0
        embed.set_footer(text=f"You own {quantity} of this item.")
        await ctx.send(embed=embed)


    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name='skullleaderboard', aliases=['slb', 'skulllb'])
    async def skullleaderboard(self, ctx, *, arg: str = None):
        """
        Shows the Skull leaderboard for Dank Vibes.
        You can specify how many members you want to see on the leaderboard.
        """
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
                pages = CustomMenu(source=SkullLeaderboard(leaderboard, title), clear_reactions_after=True, timeout=60)
                return await pages.start(ctx)