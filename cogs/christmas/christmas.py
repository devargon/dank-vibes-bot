import discord
from discord.ext import commands, menus

from utils import checks
from utils.menus import CustomMenu
from utils.format import human_join

import os
import time
import random
import asyncio
import operator
from typing import Optional

from .removingaccess import RemovingAccess

modchannel = 743174564778868796 if os.getenv('state') == '0' else 871737314831908974

something = ["Custom Role", "Free Odd Eye Raffle Entry", "+1 Amari Level", "+2 Amari Level", "+3 Amari Level",
             "Access to reaction snipe", "Access to #general-spam (25x/50x multi)", "Create a private channel",
             "1x/2x role multiplier", "Access to #reaction-logs", "Access to #dyno-message-logs",
             "Join a surprise heist", "Use slash commands", "Access to `dv.dm`", "Access to `-paint`",
             "Use Color roles", "Access to `dv.es`"]
weights = [1, 2, 2, 2, 1, 3, 2, 2, 2, 3, 3, 3, 2, 3, 3, 3, 3, ]


def format_channel(list_of_channels, split: Optional[bool] = False):
    """
    Formats a list of channels into a string.
    """
    if not split:
        if len(list_of_channels) > 70:
            return ", ".join(list_of_channels[:70]) + f" and {len(list_of_channels) - 70}"
        else:
            return human_join(list_of_channels, ', ', 'and')
    else:
        if len(list_of_channels) > 35:
            return "\n".join(list_of_channels[:35]) + f"\n**And {len(list_of_channels) - 35} more...**"
        else:
            return "\n".join(list_of_channels)


class ListPerks(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=10)

    async def format_page(self, menu, page):
        embed = discord.Embed(color=menu.ctx.bot.embed_color, title=self.title, timestamp=discord.utils.utcnow())
        for entry in page:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        return embed


class Game1Candy(discord.ui.View):
    def __init__(self, candyno):
        self.candyno = candyno
        self.winner = None
        self.response: discord.Message = None
        self.candyclaims = {}
        super().__init__(timeout=20.0)

        async def manage_candies(interaction: discord.Interaction):
            user = interaction.user
            if user not in self.candyclaims:
                self.candyclaims[user] = 1
            else:
                self.candyclaims[user] = self.candyclaims[user] + 1
            self.candyno -= 1
            if self.candyno == 0:
                for b in self.children:
                    b.disabled = True
                embed = self.response.embeds[0]
                embed.set_footer(text="This game has ended and candies can no longer be collected.")
                try:
                    await self.response.edit(content="This game has ended and candies can no longer be collected.", embed=embed, view=self)
                except:
                    pass
                self.stop()

        class Candy(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await manage_candies(interaction)

        self.add_item(Candy(style=discord.ButtonStyle.blurple, label="Grab a candy!", disabled=False, emoji="🍬"))

    async def on_timeout(self) -> None:
        for b in self.children:
            b.disabled = True
        embed = self.response.embeds[0]
        embed.set_footer(text="This game has ended and candies can no longer be collected.")
        try:
            await self.response.edit(content="This game has ended and candies can no longer be collected.", embed=embed, view=self)
        except:
            pass

class Game2Grinch(discord.ui.View):
    def __init__(self):
        self.grinch_position = ["<:DVB_Blank:918464127779876924>", "<:DVB_Grinch:918461400039432254>", "<:DVB_Blank:918464127779876924>"]
        self.grinchHP = 20
        self.response: discord.Message = None
        self.grinch_hits = {}
        super().__init__(timeout=20.0)

        async def manage_candies(custom_id, interaction: discord.Interaction):
            user = interaction.user
            current_grinch_index = self.grinch_position.index("<:DVB_Grinch:918461400039432254>")
            if int(custom_id) == current_grinch_index:
                if user not in self.grinch_hits:
                    self.grinch_hits[user] = 1
                else:
                    self.grinch_hits[user] = self.grinch_hits[user] + 1
                self.grinchHP -= 1
            if self.grinchHP == 0:
                for b in self.children:
                    b.disabled = True
                embed = self.response.embeds[0]
                embed.set_footer(text="This game has ended and you can no longer attack the Grinch.")
                try:
                    await self.response.edit(content="This game has ended and you can no longer attack the Grinch.", embed=embed, view=self)
                except:
                    pass
                self.stop()
            else:
                if random.choice([False, False, False, False, False, False, False, True]):
                    current_position = self.grinch_position
                    random.shuffle(current_position)
                    self.grinch_position = current_position
                    embed = self.response.embeds[0]
                    embed.description = f"⛄⛄⛄\n{''.join(self.grinch_position)}\n\nClick on the correct snowball facing the Grinch to hit him with it!"
                    try:
                        await self.response.edit(embed=embed)
                    except:
                        self.stop()

        class HitGrinch(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await manage_candies(self.custom_id, interaction)
        for i in range(0, 3):
            self.add_item(HitGrinch(style=discord.ButtonStyle.blurple, disabled=False, emoji=discord.PartialEmoji.from_str("<:DVB_snowball:918096323906007060>"), custom_id=str(i)))

    async def on_timeout(self) -> None:
        for b in self.children:
            b.disabled = True
        embed = self.response.embeds[0]
        embed.set_footer(text="This game has ended and you can no longer attack the Grinch.")
        try:
            await self.response.edit(content="This game has ended and you can no longer attack the Grinch.", embed=embed, view=self)
        except:
            pass


class Game3FirstToClick(discord.ui.View):
    def __init__(self, emoji):
        self.response: discord.Message = None
        self.isclicked = False
        self.ItemEmoji = emoji
        self.winner = None
        super().__init__(timeout=20.0)

        async def manage_game(button: discord.ui.Button, interaction: discord.Interaction):
            if self.isclicked:
                await interaction.response.send_message("Too late! Someone else has clicked the button already.", ephemeral=True)
            else:
                self.winner = interaction.user
                button.style = discord.ButtonStyle.green
                button.disabled = True
                try:
                    await self.response.edit(view=self)
                except:
                    pass
                self.stop()

        class GrabItem(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await manage_game(self, interaction)

        self.add_item(GrabItem(style=discord.ButtonStyle.grey, disabled=True, emoji=self.ItemEmoji))

    async def on_timeout(self) -> None:
        for b in self.children:
            b.disabled = True
        embed = self.response.embeds[0]
        embed.set_footer(text="This game has ended and you can no pick up the item.")
        try:
            await self.response.edit(content="This game has ended and you can no pick up the item.", embed=embed, view=self)
        except:
            pass


class ChooseCurrencyPrize(discord.ui.View):
    def __init__(self, member, prizes):
        self.member = member
        self.prizes = prizes
        self.prize = None
        self.response = None
        super().__init__(timeout=15.0)

        async def manage_prize(label):
            self.prize = label
            for b in self.children:
                if b.label == label:
                    b.style = discord.ButtonStyle.green
                else:
                    b.style = discord.ButtonStyle.grey
                b.disabled = True
            try:
                await self.response.edit(view=self)
            except:
                pass
            self.stop()

        class Prize(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await manage_prize(self.label)

        for prize in self.prizes:
            self.add_item(Prize(emoji=discord.PartialEmoji.from_str(prize[0]), label=prize[1], style=discord.ButtonStyle.blurple))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.member:
            await interaction.response.send_message("These aren't your prizes to claim 😑", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        for b in self.children:
            b.disabled = True
        try:
            await self.response.edit(content="You failed to claim your prize.", view=self)
        except:
            pass


class ChoosePrize(discord.ui.View):
    def __init__(self, prizes, member):
        self.member = member
        self.prizes = prizes
        self.prize = None
        self.response = None
        super().__init__(timeout=15.0)

        async def manage_prize(custom_id):
            self.index = int(custom_id)
            self.prize = self.prizes[self.index]
            for index, b in enumerate(self.children):
                if isinstance(b, discord.ui.Button):
                    b.disabled = True
                    if b.custom_id == custom_id:
                        b.style = discord.ButtonStyle.green
                    else:
                        b.style = discord.ButtonStyle.grey
                    b.emoji = "<a:NormieBoxOpen:861390923451727923>"
                    b.label = f"{self.prizes[index]}"
            try:
                await self.response.edit(view=self)
            except:
                pass
            self.stop()

        class Prize(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await manage_prize(self.custom_id)

        for i in range(0, 3):
            self.add_item(Prize(emoji=discord.PartialEmoji.from_str("<a:NormieBoxClosed:861390901405679626>"), custom_id=str(i), label="Click on me!", style=discord.ButtonStyle.blurple))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.member:
            await interaction.response.send_message("These aren't your prizes to claim 😑", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        for b in self.children:
            b.disabled = True
        try:
            await self.response.edit(content="You failed to claim your prize.", view=self)
        except:
            pass


class Christmas(RemovingAccess, commands.Cog, name="christmas"):
    """
    Christmas Celebration Features
    """
    def __init__(self, client):
        self.client = client
        self.rate = {}
        self.ignoredchannels = {}
        self.ignoredcategories = {}
        self.remind_perk_removal.start()
        self.command_removal.start()

    async def manage_prize(self, message, prize, member):
        if prize == "Custom Role":
            await message.channel.send("You chose the **Custom Role**!\nYou will be able to keep this Custom Role for 2 days. Please wait until an admin DMs you with more information.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a custom role for 2 days\n{message.jump_url}")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, "Custom Role Perk", round(time.time()) + 172800)

        elif prize == "Free Odd Eye Raffle Entry":
            await message.channel.send("You chose the **Free Odd Eye Raffle Entry**!\nYou can redeem a free Odd Eye entry.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) can get a free odd eye raffle entry.\n{message.jump_url}")

        elif prize == "+1 Amari Level":
            await message.channel.send("You chose the **+1 Amari Level**!\nYour extra level will be added to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won **+1 Amari Level**.\n{message.jump_url}")

        elif prize == "+2 Amari Level":
            await message.channel.send("You chose the **+2 Amari Level**!\nYour extra level will be added to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won **+2 Amari Level**\n{message.jump_url}")

        elif prize == "+3 Amari Level":
            await message.channel.send("You chose the **+3 Amari Level**!\nYour extra level will be added to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **+3 Amari Level**\n{message.jump_url}")

        elif prize == "Access to reaction snipe":
            await message.channel.send("You chose the **Access to reaction snipe**!\nYou can start using `dv.rs` until your access is automatically removed in 2 days.")
            await self.client.pool_pg.execute("INSERT INTO commandaccess(member_id, command, until) VALUES($1, $2, $3)", member.id, "reactionsnipe", round(time.time()) + 172800)

        elif prize == "Access to #general-spam (25x/50x multi)":
            await message.channel.send("You chose the **Access to #general-spam (25x/50x multi)**!\nYour access to the channel will be given as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won **Access to #general-spam\n{message.jump_url}")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Create a private channel":
            await message.channel.send("You chose the **Create a private channel**!\nYou will be given access to create a private channel in <#763458133116059680> as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Create a private channel**\n{message.jump_url}")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "1x/2x role multiplier":
            await message.channel.send("You chose the **1x/2x role multiplier**!\nMessages you sent will have an additional multiplier in AmariBot for 2 days. This perk will be given to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **1x/2x role multiplier**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Access to #reaction-logs":
            await message.channel.send("You chose the **Access to #reaction-logs**!\nYou will be given access to <#847710145001029672> as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Access to #reaction-logs**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Access to #dyno-message-logs":
            await message.channel.send("You chose the **Access to #dyno-message-logs**!\nYou will be given access to <#880990535282724926> as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Access to #dyno-message-logs**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Join a surprise heist":
            await message.channel.send("You chose the **Join a surprise heist**!\nFurther details will be given on how you'll be able to access the surprise heists.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Join a surprise heist**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Use slash commands":
            await message.channel.send("You chose the **Use slash commands**!You will be able to use bots' Slash Commands for 2 days. This access will be given to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Use slash commands**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Access to `dv.dm`":
            await message.channel.send("You chose the **Access to `dv.dm`**!\nActing like a messenger, Dank Vibes Bot anonymously will DM your target on your behalf. You can do so for two days!")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Access to `dv.dm`**\n*Sent for tracking purposes*")
            await self.client.pool_pg.execute("INSERT INTO commandaccess VALUES($1, $2, $3)", member.id, "dm", round(time.time()) + 172800)

        elif prize == "Access to `-paint`":
            await message.channel.send("You chose the **Access to `-paint`**!\nYou will be able to make other peoples' color roles change for a short period of time! This access will be given to you as soon as possible.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Access to `-paint`**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Use Color roles":
            await message.channel.send("You chose the **Use Color roles**!\nYou will be able to grab exclusive color roles in <#641497978112180235>.")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Use Color roles**")
            await self.client.pool_pg.execute("INSERT INTO perkremoval VALUES($1, $2, $3)", member.id, prize, round(time.time()) + 172800)

        elif prize == "Access to `dv.es`":
            await message.channel.send("You chose the **Access to `dv.es`**!\nYou will be able to see what a user's message was before they edited it for two days!")
            await self.client.get_channel(modchannel).send(f"{member.mention} ({member.id}) has won a **Access to `dv.es`**\n*Sent for tracking purposes*")
            await self.client.pool_pg.execute("INSERT INTO commandaccess VALUES($1, $2, $3)", member.id, "editsnipe", round(time.time()) + 172800)

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Main event handler for christmas games.
        """
        if self.client.maintenance.get(self.qualified_name):
            return
        if message.author.bot:
            return
        guildid = str(message.guild.id)
        """
        Caching the rate for the guild.
        """
        if guildid not in self.rate:
            rate = await self.client.pool_pg.fetchval("SELECT percentage FROM christmaseventconfig WHERE guild_id = $1", message.guild.id)
            if rate is None:
                rate = 0
            self.rate[guildid] = rate
        """
        Caching the ignored categories for the guild
        """
        if guildid not in self.ignoredcategories:
            ignoredcategories = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmascat WHERE guild_id = $1", message.guild.id)
            if len(ignoredcategories) == 0:
                ignoredcategories = []
                self.ignoredcategories[guildid] = ignoredcategories
            else:
                ids = [entry.get('category_id') for entry in ignoredcategories]
                self.ignoredcategories[guildid] = ids
        """
        Caching the ignored channels for the guild
        """
        if guildid not in self.ignoredchannels:
            ignoredchannels = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmaschan WHERE guild_id = $1", message.guild.id)
            if len(ignoredchannels) == 0:
                ignoredchannels = []
                self.ignoredchannels[guildid] = ignoredchannels
            else:
                ids = [entry.get('channel_id') for entry in ignoredchannels]
                self.ignoredchannels[guildid] = ids
        rate = self.rate[guildid]
        if rate == 0 or rate is None:
            return
        context = await self.client.get_context(message)
        if context.valid is True:
            return
        denominator = 1
        while rate < 1:
            rate *= 10
            denominator *= 10
        if not random.randint(0, denominator) <= rate:
            return
        if message.channel.id in self.ignoredchannels[guildid]:
            return
        if message.channel.category_id in self.ignoredcategories[guildid]:
            return
        game = random.choice([0, 1, 2])
        if game == 0:
            candycount = random.randint(10, 20)
            gameview = Game1Candy(candycount)
            modrole = discord.utils.get(message.guild.roles, name="Mod")
            if modrole is None:
                PersonGivingCandy = self.client.user
            else:
                PersonGivingCandy = random.choice(modrole.members)
            embed = discord.Embed(title=f"{PersonGivingCandy} is giving out {candycount} free candies to everyone!", description=f"Press the button below to get candies!\nThe person with the highest number of candies gets to win something!", color=self.client.embed_color).set_thumbnail(url="https://cdn.discordapp.com/emojis/784042462364041216.gif?size=96")
            gamemessage = await message.channel.send("A new event is happening!", embed=embed, view=gameview)
            gameview.response = gamemessage
            await gameview.wait()
            if len(gameview.candyclaims) == 0:
                try:
                    return await gamemessage.reply(f"Looks like no one claimed their candies... **{PersonGivingCandy}**'s sad now :(")
                except:
                    return await message.channel.send(f"Looks like no one claimed their candies... **{PersonGivingCandy}**'s sad now :(")
            candyclaims = sorted(gameview.candyclaims.items(), key=operator.itemgetter(1), reverse=True)
            winner = candyclaims[0][0]
            selected_prizes = random.choices(something, weights=weights, k=3)
            while selected_prizes[0] == selected_prizes[1] or selected_prizes[1] == selected_prizes[2] or selected_prizes[0] == selected_prizes[2]:
                selected_prizes = random.choices(something, weights=weights, k=3)
            prizeview = ChoosePrize(selected_prizes, winner)
            prizeview.response = await message.channel.send(f"{winner.mention} You've won by collecting the highest number of candies (`{candyclaims[0][1]}`) among the other {len(candyclaims)-1} participants!\nChoose a prize below to redeem.", view=prizeview)
            await prizeview.wait()
            await self.manage_prize(prizeview.response, prizeview.prize, winner)

        elif game == 1:
            gameview = Game2Grinch()
            embed = discord.Embed(title="Help! The Grinch is coming to attempt to distrupt the Christmas celebrations!", description=f"⛄⛄⛄\n<:DVB_Blank:918464127779876924><:DVB_Grinch:918461400039432254><:DVB_Blank:918464127779876924>\n\nClick on the correct snowball facing the Grinch to hit him with it!", color=self.client.embed_color).set_thumbnail(url="https://cdn.discordapp.com/attachments/871737314831908974/918476839255699456/unknown.png")
            gameview.response = await message.channel.send("A new event is happening!", embed=embed)
            await asyncio.sleep(2.0)
            await gameview.response.edit(view=gameview)
            await gameview.wait()
            if len(gameview.grinch_hits) == 0:
                try:
                    return await gameview.response.reply("**Nobody bothered to attack the Grinch!**\nYour Christmas celebrations are now ruined... <:DVB_Grinch:918461400039432254>")
                except:
                    return await message.channel.send("**Nobody bothered to attack the Grinch!**\nYour Christmas celebrations are now ruined... <:DVB_Grinch:918461400039432254>")
            else:
                grinch_hits = sorted(gameview.grinch_hits.items(), key=operator.itemgetter(1), reverse=True)
                winner = grinch_hits[0][0]
                summary = []
                for hit in grinch_hits:
                    summary.append(f"**{hit[0]}** hit the Grinch `{hit[1]}` times.")
                    embed = discord.Embed(title="Summary", description="\n".join(summary), color=self.client.embed_color)
                try:
                    await gameview.response.reply(embed=embed)
                except:
                    await message.channel.send(embed=embed)
                prizes = random.choices([["<:DankMemer:898501160992911380>", "Dank Memer"], ["<:currency:898494174557515826>", "Mudae"], ["<:TT_karutaOwO:913784526268932156>", "Karuta"], ["<:OwO:898501205360271380>", "OwO"], ["<:Pokemon:898501263849816064>", "Pokemon Bots"]], k=3)
                while prizes[0] == prizes[1] or prizes[1] == prizes[2] or prizes[0] == prizes[2]:
                    prizes = random.choices([["<:DankMemer:898501160992911380>", "Dank Memer"], ["<:currency:898494174557515826>", "Mudae"], ["<:TT_karutaOwO:913784526268932156>", "Karuta"], ["<:OwO:898501205360271380>", "OwO"], ["<:Pokemon:898501263849816064>", "Pokemon Bots"]], k=3)
                prizeview = ChooseCurrencyPrize(winner, prizes)
                prizeview.response = await gameview.response.reply(f"{winner.mention} You've won by hitting the Grinch with the most snowballs!\nChoose a prize below.", view=prizeview)
                await prizeview.wait()
                prize = prizeview.prize
                if prize is not None:
                    await message.channel.send(f"You chose to receive bot currency for **{prize}**. Your prize will be given to you as soon as possible!")
                    await self.client.get_channel(modchannel).send(f"{winner.mention} ({winner.id}) has won **{prize}** bot currency\n{message.jump_url}")

        elif game == 2:
            item_names = await self.client.pool_pg.fetch("SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = $1", 'inventories')
            items = [i.get('column_name') for i in item_names if i.get('column_name') != 'user_id']
            chosen_item = random.choice(items)
            itemdata = await self.client.pool_pg.fetchrow("SELECT * FROM iteminfo WHERE name = $1", chosen_item)
            if itemdata is None:
                return await message.channel.send("An error occured while trying to get the data for an item.")
            name = itemdata.get('fullname')
            emoji = itemdata.get('emoji')
            gameview = Game3FirstToClick(emoji)
            embed = discord.Embed(title=f"**{self.client.user.name}** is dropping an item!", description=f"Grab it before anyone else does by clicking on the button!", color=self.client.embed_color).set_thumbnail(url=itemdata.get('image'))
            gameview.response = await message.channel.send(embed=embed, view=gameview)
            await asyncio.sleep(2.0)
            gameview.children[0].disabled = False
            gameview.children[0].style = discord.ButtonStyle.blurple
            await gameview.response.edit(view=gameview)
            await gameview.wait()
            embed.set_footer(text=f"The game has ended and you can no longer collect the item.")
            if gameview.winner is None:
                return
            user = gameview.winner
            item = chosen_item
            amount = 1
            does_inventory_exist = await self.client.pool_pg.fetchrow("SELECT * FROM inventories WHERE user_id = $1", user.id)
            useritem_query = "SELECT {} FROM inventories WHERE user_id = $1".format(item)
            useritem = await self.client.pool_pg.fetchval(useritem_query, user.id)
            if does_inventory_exist:
                if useritem is None:
                    useritem_query = "UPDATE inventories SET {} = $2 WHERE user_id = $1 RETURNING {}".format(item, item)
                else:
                    useritem_query = "UPDATE inventories SET {} = {} + $2 WHERE user_id = $1 RETURNING {}".format(item, item, item)
            else:
                useritem_query = "INSERT INTO inventories (user_id, {}) VALUES ($1, $2) RETURNING {}".format(item, item)
            await self.client.pool_pg.fetchval(useritem_query, user.id, amount, column=item)
            embed.description = f"{gameview.winner.mention} ({gameview.winner}) was the first to click! They've gotten **a {name}** {emoji}."
            await gameview.response.edit(content=f"The game has ended and you can no longer collect the item.", embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name='christmasconfig', aliases=['xmasconfig'], invoke_without_command=True)
    async def christmasconfig(self, ctx):
        """
        Shows the configuration for Christmas games or changes it.

        An accepted rate is between 0 (0%) to 1 (100%), but the lowest rate must have a maximum of 2 decimal points, otherwise the bot may read the rate as 0 instead.
        """
        extrasummary = ""
        guildid = str(ctx.guild.id)
        if guildid not in self.rate:
            rate = await self.client.pool_pg.fetchval("SELECT percentage FROM christmaseventconfig WHERE guild_id = $1", ctx.guild.id)
            if rate is None:
                rate = 0
            self.rate[guildid] = rate
        else:
            rate = self.rate[guildid]
        if rate > 1:
            result = "**spawn on every message sent**"
        elif rate == 0:
            result = "**not spawn**"
        else:
            result = f"have a **{round(rate*100, 2)}**% chance of spawning when a message is sent"
        embed = discord.Embed(title="Christmas Event Config for {}".format(ctx.guild.name), description=f"Chistmas game events will {result}.")
        array = []
        cached_channels = []
        deleted_channels = []
        if guildid not in self.ignoredchannels:
            ignoredchannels = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmaschan WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredchannels) == 0:
                ignoredchannels = []
                self.ignoredchannels[guildid] = ignoredchannels
                array = ["None"]
                deleted_channels = []
            else:
                extrasummary = ""
                ids = [entry.get('channel_id') for entry in ignoredchannels]
        else:
            ids = [channel_id for channel_id in self.ignoredchannels[guildid]]
        if array != ["None"]:
            for channel_id in ids:
                channel = ctx.guild.get_channel(channel_id)
                if channel is not None:
                    array.append(channel.mention)
                    cached_channels.append(channel.id)
                else:
                    await self.client.pool_pg.execute("DELETE FROM ignoredchristmaschan WHERE channel_id = $1", channel_id)
                    deleted_channels.append(str(channel_id))
            if guildid not in self.ignoredchannels or cached_channels != self.ignoredchannels[guildid]:
                self.ignoredchannels[guildid] = cached_channels
        embed.add_field(name="Ignored Channels", value=format_channel(array, split=True) if len(array) > 0 else "None")
        if len(deleted_channels) > 0:
            extrasummary += f"\n\n**These channels do not exist and were deleted from the list of ignored channels:** {', '.join(deleted_channels)}"
        array = []
        cached_categories = []
        deleted_categories = []
        if guildid not in self.ignoredcategories:
            ignoredcategories = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmascat WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredcategories) == 0:
                ignoredcategories = []
                self.ignoredcategories[guildid] = ignoredcategories
                array = ["None"]
            else:
                array = []
                categoryids = [entry.get('category_id') for entry in ignoredcategories]
                for entry in ignoredcategories:
                    category_id = entry.get('category_id')
                    category = ctx.guild.get_channel(category_id)
                    if category is not None and isinstance(category, discord.CategoryChannel):
                        array.append(f"{category.name} ({category_id})")
                        cached_categories.append(category.id)
                    else:
                        await self.client.pool_pg.execute("DELETE FROM ignoredchristmascat WHERE category_id = $1", category_id)
                        deleted_categories.append(category_id)
        else:
            categoryids = [category_id for category_id in self.ignoredcategories[guildid]]
            if guildid in self.ignoredcategories or array != ["None"]:
                for category_id in categoryids:
                    category = ctx.guild.get_channel(category_id)
                    if category is not None and isinstance(category, discord.CategoryChannel):
                        array.append(category.name)
                        cached_categories.append(category.id)
                    else:
                        await self.client.pool_pg.execute("DELETE FROM ignoredchristmascat WHERE category_id = $1", category_id)
                        deleted_categories.append(str(category_id))
            if guildid not in self.ignoredcategories or cached_categories != self.ignoredcategories[guildid]:
                self.ignoredcategories[guildid] = cached_categories
        embed.add_field(name="Ignored Categories", value=format_channel(array, split=True) if len(array) > 0 else "None")
        if len(deleted_categories) > 0:
            extrasummary += f"\n\n**These categories are invalid and were deleted from the list of ignored categories:** {', '.join(deleted_categories)}"
        if extrasummary:
            embed.add_field(name="Also..", value=extrasummary, inline=False)
        embed.set_thumbnail(url=random.choice(['https://cdn.discordapp.com/emojis/568124063675973632.gif?size=96',
                                                'https://cdn.discordapp.com/emojis/893450958326091777.png?size=96',
                                                'https://cdn.discordapp.com/emojis/817909791287934986.png?size=96',
                                                'https://cdn.discordapp.com/emojis/694973517862666360.png?size=96',
                                                'https://cdn.discordapp.com/emojis/694973517816397824.png?size=96',
                                                'https://cdn.discordapp.com/emojis/694973517677985792.png?size=96',
                                                'https://cdn.discordapp.com/emojis/733017031493943718.gif?size=96',
                                                'https://cdn.discordapp.com/emojis/706107990024913007.gif?size=96',
                                                'https://cdn.discordapp.com/emojis/643747917017907240.gif?size=96',
                                                'https://cdn.discordapp.com/emojis/766099048217313281.png?size=96',
                                                'https://cdn.discordapp.com/emojis/722195328799080459.png?size=96',
                                                'https://cdn.discordapp.com/emojis/679800699625799740.png?size=96',
                                                'https://cdn.discordapp.com/emojis/706107989047771239.gif?size=96',
                                                'https://cdn.discordapp.com/emojis/893449040421855242.png?size=96']))

        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @christmasconfig.command(name="rate", aliases=["r"])
    async def rate_config(self, ctx, rate: str = None):
        """
        Sets the percentage that events will have a chance to spawn.
        """
        if rate is None:
            return await ctx.send("Please specify a rate between 0 and 1. To see the current rate set, use `dv.xmasconfig`.")
        try:
            rate = float(rate)
        except ValueError:
            await ctx.send("The rate must be a number between 0 to 100.")
        else:
            if rate > 1:
                rate = 1
            elif rate < 0:
                rate = 0
            if rate >= 1:
                additional = "**Events will now spawn on each message sent.**"
            elif rate <= 0:
                additional = "**Events will not spawn.**"
            else:
                additional = ""
            await self.client.pool_pg.execute("UPDATE christmaseventconfig SET PERCENTAGE = $1 WHERE guild_id = $2", rate, ctx.guild.id)
            guildid = str(ctx.guild.id)
            self.rate[guildid] = rate
            await ctx.send(f"The rate has been set to {rate * 100}%.\n{additional}")
            denominator = 1
            if rate == 0:
                return
            now = time.perf_counter()
            while rate < 1:
                rate *= 10
                denominator *= 10
            averagetries = []
            var = 0
            while len(averagetries) < 5 and time.perf_counter() - now < 5:
                if time.perf_counter() - now < 5:
                    if random.randint(0, denominator) <= rate:
                        averagetries.append(var)
                        var = 0
                    else:
                        var += 1
                else:
                    break
            embed = discord.Embed(title="Chance Calculator")
            value = ""
            if len(averagetries) == 0:
                value = "There was not enough time to calculate the chance of games spawning."
            for i in averagetries:
                value += f"`-` Game instance created after {i} tries\n"
            averagemessages = round(sum(averagetries) / len(averagetries))
            value += f"\nEvents will spawn on an average of every {averagemessages} messages sent."
            embed.description = value
            await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @christmasconfig.command(name="ignorechannel", aliases=["ichan"])
    async def ignore_channel_config(self, ctx, channels: commands.Greedy[discord.TextChannel]):
        """
        This adds channels that Dank Vibes Bot will not spawn events in. You can specify multiple channels in this command.
        """
        guildid = str(ctx.guild.id)
        if guildid not in self.ignoredchannels:
            ignoredchannels = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmaschan WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredchannels) == 0:
                ignoredchannels = []
                self.ignoredchannels[guildid] = ignoredchannels
            else:
                ids = [entry.get('channel_id') for entry in ignoredchannels]
                self.ignoredchannels[guildid] = ids
        if len(channels) == 0:
            await ctx.send("You must specify at least one channel.")
            return
        if guildid not in self.ignoredchannels:
            self.ignoredchannels[guildid] = []
        ignoredchannels = self.ignoredchannels[guildid]
        added_channels = []
        already_added = []
        for channel in channels:
            if channel.id in ignoredchannels:
                already_added.append(channel.mention)
            else:
                await self.client.pool_pg.execute("INSERT INTO ignoredchristmaschan (guild_id, channel_id) VALUES ($1, $2)", ctx.guild.id, channel.id)
                ignoredchannels.append(channel.id)
                added_channels.append(channel.mention)
        self.ignoredchannels[guildid] = ignoredchannels
        if len(added_channels) > 0:
            added_channel_string = format_channel(added_channels)
        else:
            added_channel_string = ""
        if len(already_added) > 0:
            already_added_string = format_channel(already_added)
        else:
            already_added_string = ""
        embed = discord.Embed(title="Success!", description=f"{added_channel_string} will now be ignored by the bot." if len(added_channel_string) > 0 else "", color=discord.Color.green())
        if already_added_string:
            embed.add_field(name="Already Added", value=f"{already_added_string} was aleady in the list of ignored channels.", inline=False)
            embed.color = discord.Color.yellow()
        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @christmasconfig.command(name="unignorechannel", aliases=["uichan"])
    async def unignore_channel_config(self, ctx, channels: commands.Greedy[discord.TextChannel]):
        """
        This removes channels from the list of channels that Dank Vibes Bot will not spawn events in. You can specify multiple channels in this command.
        """
        guildid = str(ctx.guild.id)
        if guildid not in self.ignoredchannels:
            ignoredchannels = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmaschan WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredchannels) == 0:
                ignoredchannels = []
                self.ignoredchannels[guildid] = ignoredchannels
            else:
                ids = [entry.get('channel_id') for entry in ignoredchannels]
                self.ignoredchannels[guildid] = ids
        if len(channels) == 0:
            await ctx.send("You must specify at least one channel.")
            return
        ignoredchannels = self.ignoredchannels[guildid]
        removed_channels = []
        not_exist = []
        for channel in channels:
            if channel.id not in ignoredchannels:
                not_exist.append(channel.mention)
            else:
                await self.client.pool_pg.execute("DELETE FROM ignoredchristmaschan WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, channel.id)
                ignoredchannels.remove(channel.id)
                removed_channels.append(channel.mention)
        self.ignoredchannels[guildid] = ignoredchannels
        if len(removed_channels) > 0:
            added_channel_string = format_channel(removed_channels)
        else:
            added_channel_string = ""
        if len(not_exist) > 0:
            already_added_string = format_channel(not_exist)
        else:
            already_added_string = ""
        embed = discord.Embed(title="Success!", description=f"{added_channel_string} has been removed from the list of ignored channels." if len(added_channel_string) > 0 else "", color=discord.Color.green())
        if already_added_string:
            embed.add_field(name="Already Removed", value=f"{already_added_string} were not in the list of ignored channels.", inline=False)
            embed.color = discord.Color.yellow()
        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @christmasconfig.command(name="ignorecategory", aliases=["icat"])
    async def ignore_category_config(self, ctx, categories: commands.Greedy[discord.CategoryChannel]):
        """
        sets categories which channels inside will be ignored. You can provide a name, or the ID of the category.
        """
        guildid = str(ctx.guild.id)
        if guildid not in self.ignoredcategories:
            ignoredcategories = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmascat WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredcategories) == 0:
                ignoredcategories = []
                self.ignoredcategories[guildid] = ignoredcategories
            else:
                ids = [entry.get('category_id') for entry in ignoredcategories]
                self.ignoredcategories[guildid] = ids
        if len(categories) == 0:
            await ctx.send("You must specify at least one category.")
            return
        ignoredcategories = self.ignoredcategories[guildid]
        added_categories = []
        already_added = []
        for category in categories:
            if category.id not in ignoredcategories:
                await self.client.pool_pg.execute("INSERT INTO ignoredchristmascat (guild_id, category_id) VALUES ($1, $2)", ctx.guild.id, category.id)
                ignoredcategories.append(category.id)
                added_categories.append(category.name)
            else:
                already_added.append(category.mention)
        self.ignoredcategories[guildid] = ignoredcategories
        if len(added_categories) > 0:
            added_category_string = format_channel(added_categories)
        else:
            added_category_string = ""
        if len(already_added) > 0:
            already_added_string = format_channel(already_added)
        else:
            already_added_string = ""
        embed = discord.Embed(title="Success!", description=f"Channels inside **{added_category_string}** will be ignored by the bot.", color=discord.Color.green())
        if already_added_string:
            embed.add_field(name="Already Added", value=f"**{already_added_string}** were already in the list of ignored categories.", inline=False)
            embed.color = discord.Color.yellow()
        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @christmasconfig.command(name="unignorecategory", aliases=["uicat"])
    async def unignore_category_config(self, ctx, categories: commands.Greedy[discord.CategoryChannel]):
        """
        Removes categories set in the list of ignored categories.
        """
        guildid = str(ctx.guild.id)
        if guildid not in self.ignoredcategories:
            ignoredcategories = await self.client.pool_pg.fetch("SELECT * FROM ignoredchristmascat WHERE guild_id = $1", ctx.guild.id)
            if len(ignoredcategories) == 0:
                ignoredcategories = []
                self.ignoredcategories[guildid] = ignoredcategories
            else:
                ids = [entry.get('category_id') for entry in ignoredcategories]
                self.ignoredcategories[guildid] = ids
        if len(categories) == 0:
            await ctx.send("You must specify at least one category.")
            return
        ignoredcategories = self.ignoredcategories[guildid]
        removed_categories = []
        not_exist = []
        for category in categories:
            if category.id in ignoredcategories:
                await self.client.pool_pg.execute("DELETE FROM ignoredchristmascat WHERE guild_id = $1 AND category_id = $2", ctx.guild.id, category.id)
                ignoredcategories.remove(category.id)
                removed_categories.append(category.name)
            else:
                not_exist.append(category.name)
        self.ignoredcategories[guildid] = ignoredcategories
        if len(removed_categories) > 0:
            removed_category_string = format_channel(removed_categories)
        else:
            removed_category_string = ""
        if len(not_exist) > 0:
            not_exist_string = format_channel(not_exist)
        else:
            not_exist_string = ""
        embed = discord.Embed(title="Success!", description=f"**{removed_category_string}** has been removed from the list of ignored categories.", color=discord.Color.green())
        if not_exist_string:
            embed.add_field(name="Not Exist", value=f"**{not_exist_string}** were not in the list of ignored categories.", inline=False)
            embed.color = discord.Color.yellow()
        await ctx.send(embed=embed)

    @checks.dev()
    @commands.command(name="prizechoice", aliases=['pc'])
    async def set_prize_choice(self, ctx, member: discord.Member = None):
        """
        Manually allows someone to claim a prize.
        """
        message = ctx.message
        if member is None:
            return await message.add_reaction("❌")
        selected_prizes = random.choices(something, weights=weights, k=3)
        while selected_prizes[0] == selected_prizes[1] or selected_prizes[1] == selected_prizes[2]:
            selected_prizes = random.choices(something, weights=weights, k=3)
        prizeview = ChoosePrize(selected_prizes, member)
        embed = discord.Embed(title="You won the minigame!", description=f"Choose one of the prizes to redeem below!", color=self.client.embed_color)
        prizeview.response = await message.channel.send(embed=embed, view=prizeview)
        await prizeview.wait()
        await self.manage_prize(ctx.message, prizeview.prize, member)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="existingperks", aliases=['ep'])
    async def existing_perks(self, ctx):
        """
        List the perks that currently exist on members.
        """
        entries = await self.client.pool_pg.fetch("SELECT * FROM perkremoval")
        commandentries = await self.client.pool_pg.fetch("SELECT * FROM commandaccess")
        if len(entries) == 0 and len(commandentries) == 0:
            return await ctx.send("There are no existing perks that are currently in use.")
        perks = []
        for entry in entries:
            member = ctx.guild.get_member(entry.get('member_id'))
            if member is None:
                displaymember = entry.get('member_id')
            else:
                displaymember = f"{member.mention} ({member.id})"
            perks.append((f"External: {entry.get('perk')}", f"**User**: {displaymember}\n**Until**: <t:{entry.get('until')}>"))
        for entry in commandentries:
            member = ctx.guild.get_member(entry.get('member_id'))
            if member is None:
                displaymember = entry.get('member_id')
            else:
                displaymember = f"{member.mention} ({member.id})"
            perks.append((f"Dank Vibes Bot: `{entry.get('command')}`", f"**User**: {displaymember}\n**Until**: <t:{entry.get('until')}>"))
        pages = CustomMenu(source=ListPerks(something, "Existing Perks"), clear_reactions_after=True, timeout=60)
        return await pages.start(ctx)

    def cog_unload(self) -> None:
        self.remind_perk_removal.stop()
        self.command_removal.stop()
