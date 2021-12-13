import discord
from discord.ext import commands, menus

from utils.buttons import confirm
from utils.errors import ArgumentBaseError
from utils.menus import CustomMenu
from utils.format import comma_number
from utils.converters import BetterInt
from utils import checks
from time import time

def get_emoji(category):
    name = category.lower().strip()
    if "owo" == name:
        emoji = "<:DVB_OwO:914573609580756992> "
    elif "deriver" == name:
        emoji = "<:DVB_Deriver:914573802229346395> "
    elif "pokemeow" == name:
        emoji = "<:DVB_PokeMeow:914573926250721371> "
    elif "pokeworld" == name:
        emoji = "<:DVB_PokeWorld:914574672455159838> "
    elif "poketwo" == name:
        emoji = "<:DVB_PokeTwo:915096051441082421> "
    elif "wicked" == name:
        emoji = "<:DVB_Wicked:914575135044939786> "
    else:
        emoji = ""
    return emoji

def format_donation(donation):
    emoji = get_emoji(donation[0])
    return f"{emoji}**{donation[0]}** - `{comma_number(donation[1])}`"


class UserDonations(menus.ListPageSource):
    def __init__(self, entries, title, author):
        self.title = title
        self.author = author
        super().__init__(entries, per_page=15)

    async def format_page(self, menu, page):
        embed = discord.Embed(color=menu.ctx.bot.embed_color, title=self.title, timestamp=discord.utils.utcnow())
        embed.set_author(name=self.author.display_name, icon_url=self.author.avatar.url)
        desc = ""
        for entry in page:
            if page[-1] == entry:
                desc += f"<:Reply:871808167011549244> {format_donation(entry)}"
            else:
                desc += f"<:ReplyCont:871807889587707976> {format_donation(entry)}\n"
        embed.description = desc
        return embed


class DonationLeaderboard(menus.ListPageSource):
    def __init__(self, entries, title, footer):
        self.title = title
        self.footer = footer
        super().__init__(entries, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=menu.ctx.bot.embed_color, timestamp=discord.utils.utcnow()).set_footer(text=self.footer)
        for entry in entries:
            embed.add_field(name=f"{entry[0]}", value=f"Donations: `{entry[1]}`", inline=False)
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed

class donations(commands.Cog):
    """Donation commands"""
    def __init__(self, client):
        self.client = client

    async def get_donation_count(self, member: discord.Member, category: str):
        """
        Gets the donation count for a user in a category.
        """
        result = await self.client.pool_pg.fetchval("SELECT value FROM donations.{} WHERE user_id = $1".format(f"guild{member.guild.id}_{category.lower()}"), member.id)
        if result is None:
            return 0
        else:
            return result

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="add-category")
    async def add_category(self, ctx, category_name:str = None):
        """
        Creates a donation category.
        """
        if category_name is None:
            return await ctx.send("Please enter a new category name.")
        if len(category_name) > 30:
            return await ctx.send("Category name is too long; it can only be 30 characters long.")

        if await self.client.pool_pg.fetchrow("SELECT * FROM donation_categories WHERE guild_id = $1 AND lower(category_name) = $2", ctx.guild.id, category_name.lower()) is not None:
            return await ctx.send(f"A category with the name `{category_name}` already exists.")
        else:
            confirmview = confirm(ctx, self.client, 15.0)
            confirmview.response = await ctx.send(f"Are you sure you want to create a category with the name `{category_name}`?", view=confirmview)
            await confirmview.wait()
            if confirmview.returning_value is None:
                return await confirmview.response.edit(content="Cancelled; I will not be creating the donation category..")
            elif confirmview.returning_value is False:
                return await confirmview.response.edit(content="Cancelled; I will not be creating the donation category.")
            else:
                async with ctx.typing():
                    await self.client.pool_pg.execute("INSERT INTO donation_categories VALUES($1, $2)", ctx.guild.id, category_name)
                    createdb_query = "CREATE TABLE donations.{}(user_id BIGINT PRIMARY KEY, value BIGINT)".format(f"guild{ctx.guild.id}_{category_name.lower()}")
                    await self.client.pool_pg.execute(createdb_query)
                    return await ctx.send(f"Category `{category_name}` created.")

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="remove-category")
    async def remove_category(self, ctx, category_name:str = None):
        """
        Removes an existing donation category.
        """
        if category_name is None:
            return await ctx.send("Please enter a category name to remove.")
        real_name = await self.client.pool_pg.fetchval("SELECT category_name FROM donation_categories WHERE guild_id = $1 AND lower(category_name) = $2", ctx.guild.id, category_name.lower())
        if not real_name:
            return await ctx.send(f"A category with the name `{category_name}` does not exist.")
        else:
            confirmview = confirm(ctx, self.client, 15.0)
            confirmview.response = await ctx.send(f"Are you sure you want to remove the category `{real_name}`?", view=confirmview)
            await confirmview.wait()
            if confirmview.returning_value is None:
                return await confirmview.response.edit(content="Cancelled; I will not be removing the category.")
            elif confirmview.returning_value is False:
                return await confirmview.response.edit(content="Cancelled; I will not be removing the category.")
            else:
                async with ctx.typing():
                    await self.client.pool_pg.execute("DELETE FROM donation_categories WHERE guild_id = $1 AND lower(category_name) = $2", ctx.guild.id, category_name.lower())
                    await self.client.pool_pg.execute("ALTER TABLE donations.{} RENAME TO old{}_{}".format(f"guild{ctx.guild.id}_{category_name.lower()}", round(time()), f"guild{ctx.guild.id}_{category_name.lower()}"))
                    return await ctx.send(f"Category `{category_name}` removed.")

    class DonationCategory(commands.Converter):
        async def convert(self, ctx, argument: str):
            try:
                real_name: str = await ctx.bot.pool_pg.fetchval("SELECT category_name FROM donation_categories WHERE guild_id = $1 AND lower(category_name) = $2", ctx.guild.id, argument.lower())
            except Exception as e:
                raise e
            else:
                if not real_name:
                    raise ArgumentBaseError(message=f"A category with the name `{argument}` does not exist.")
                else:
                    return real_name

    @commands.command(name="donationslb", aliases=['dlb'])
    async def donationslb(self, ctx, category_name: DonationCategory = None, users:int = None):
        """
        Shows the donation leaderboard of a category.

        You can say how many users
        """
        if category_name is None:
            return await ctx.send("Please enter a category name.")
        else:
            async with ctx.typing():
                if users is None:
                    users = 10
                query = "SELECT user_id, value FROM donations.{} ORDER BY value DESC".format(f"guild{ctx.guild.id}_{category_name.lower()}")
                leaderboard = await self.client.pool_pg.fetch(query)
                if len(leaderboard) == 0:
                    return await ctx.send("There are no donations to show in this category.")
                else:
                    title = f"{ctx.guild.name}'s Donation Leaderboard - {category_name} {get_emoji(category_name)}"
                    donations = []
                    for i, entry in enumerate(leaderboard):
                        if i < users:
                            member = ctx.guild.get_member(entry.get('user_id')) or entry.get('user_id')
                            value = comma_number(entry.get('value'))
                            donations.append((f"{i+1}. {member}", value))
                    footer = f"{len(leaderboard)} users have donated, amounting to a total {comma_number(sum([entry.get('value') for entry in leaderboard]))} donated"
                    if len(donations) <= 10:
                        leaderboard_embed = discord.Embed(title=title, color=self.client.embed_color).set_footer(text=footer)
                        for member, value in donations:
                            leaderboard_embed.add_field(name=member, value=f"Donations: `{value}`", inline=False)
                        return await ctx.send(embed=leaderboard_embed)
                    else:
                        pages = CustomMenu(source=DonationLeaderboard(donations, title, footer), clear_reactions_after=True, timeout=60.0)
                        return await pages.start(ctx)

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="donations", aliases=['d'])
    async def donations(self, ctx, member:discord.Member = None):
        """
        Shows a user's donations.
        """
        if member is None:
            member = ctx.author
        async with ctx.typing():
            categories = await self.client.pool_pg.fetch("SELECT * FROM donation_categories WHERE guild_id = $1", ctx.guild.id)
            if not categories:
                return await ctx.send("There are no donation categories set up for this server.")
            else:
                donations = []
                category_names = [category.get('category_name') for category in categories]
                for category in category_names:
                    count = await self.get_donation_count(member, category)
                    donations.append((category, count))
                title = f"Donations in {ctx.guild.name}"
                if len(donations) <= 15:
                    desc = ""
                    for donation in donations:
                        if donations[-1] == donation:
                            desc += f"<:Reply:871808167011549244> {format_donation(donation)}"
                        else:
                            desc += f"<:ReplyCont:871807889587707976> {format_donation(donation)}\n"
                    embed = discord.Embed(title=title, description=desc, color=self.client.embed_color, timestamp=discord.utils.utcnow())
                    embed.set_author(name=member.display_name, icon_url=member.avatar.url)
                    return await ctx.send(embed=embed)
                else:
                    pages = CustomMenu(source=UserDonations(donations, title, member), clear_reactions_after=True, timeout=60)
                    return await pages.start(ctx)




    @commands.command(name="mydonations", aliases=['myd'])
    async def mydonations(self, ctx):
        """
        Shows your own donations.
        """
        member = ctx.author
        async with ctx.typing():
            categories = await self.client.pool_pg.fetch("SELECT * FROM donation_categories WHERE guild_id = $1", ctx.guild.id)
            if not categories:
                return await ctx.send("There are no donation categories set up for this server.")
            else:
                donations = []
                category_names = [category.get('category_name') for category in categories]
                for category in category_names:
                    count = await self.get_donation_count(member, category)
                    donations.append((category, count))
                title = f"Donations in {ctx.guild.name}"
                if len(donations) <= 15:
                    desc = ""
                    for donation in donations:
                        if donations[-1] == donation:
                            desc += f"<:Reply:871808167011549244> {format_donation(donation)}"
                        else:
                            desc += f"<:ReplyCont:871807889587707976> {format_donation(donation)}\n"
                    embed = discord.Embed(title=title, description=desc, color=self.client.embed_color, timestamp=discord.utils.utcnow())
                    embed.set_author(name=member.display_name, icon_url=member.avatar.url)
                    return await ctx.send(embed=embed)
                else:
                    pages = CustomMenu(source=UserDonations(donations, title, member), clear_reactions_after=True, timeout=60)
                    return await pages.start(ctx)

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="adddonations", aliases=["ad"])
    async def adddonations(self, ctx, member:discord.Member = None, amount: BetterInt = None, *, category_name: str = None):
        """
        Add donations to a user.
        """
        if member is None:
            return await ctx.send("You must specify a member to add donations to.")
        if amount is None:
            return await ctx.send(f"You must specify an amount to add to {member.name}'s donations..")
        if category_name is None:
            return await ctx.send("You must specify a category to add the donations to.")
        if amount <= 0:
            return await ctx.send("You must specify an amount greater than 0 to be added to {}'s donations.".format(member.name))
        real_name = await self.client.pool_pg.fetchval("SELECT category_name FROM donation_categories WHERE guild_id = $1 AND lower(category_name) = $2", ctx.guild.id, category_name.lower())
        if not real_name:
            return await ctx.send(f"A category with the name `{category_name}` does not exist.")
        currentcount = await self.get_donation_count(member, category_name)
        QUERY = "INSERT INTO donations.{} VALUES ($1, $2) ON CONFLICT(user_id) DO UPDATE SET value=$2 RETURNING value".format(f"guild{ctx.guild.id}_{category_name.lower()}")
        newamount = await self.client.pool_pg.fetchval(QUERY, member.id, amount + currentcount, column='value')
        embed = discord.Embed(title=f"Updated {member.name}'s __{real_name}__ donations.", description=f"**Original amount**: `{comma_number(currentcount)}`\n**Amount added**: `{comma_number(amount)}`\n**New amount**: `{comma_number(newamount)}`", color=discord.Color.green(), timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(name="Success!", icon_url="https://cdn.discordapp.com/emojis/575412409737543694.gif?size=96")
        embed.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
        return await ctx.send(embed=embed)

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="removedonations", aliases=["rd"])
    async def removedonations(self, ctx, member:discord.Member = None, amount: BetterInt = None, *, category_name: str = None):
        """
        Remove donations from a user.
        """
        if member is None:
            return await ctx.send("You must specify a member to remove donations from.")
        if amount is None:
            return await ctx.send(f"You must specify an amount to remove from {member.name}'s donations..")
        if category_name is None:
            return await ctx.send("You must specify a category to remove the donations from.")
        if amount <= 0:
            return await ctx.send("You must specify an amount greater than 0 to be removed from {}'s donations.".format(member.name))
        real_name = await self.client.pool_pg.fetchval(
            "SELECT category_name FROM donation_categories WHERE guild_id = $1 AND lower(category_name) = $2",
            ctx.guild.id, category_name.lower())
        if not real_name:
            return await ctx.send(f"A category with the name `{category_name}` does not exist.")
        currentcount = await self.get_donation_count(member, category_name)
        if currentcount - amount < 0:
            return await ctx.send(f"You cannot remove more donations than the what {member.name} has in the {category_name} category.")
        QUERY = "INSERT INTO donations.{} VALUES ($1, $2) ON CONFLICT(user_id) DO UPDATE SET value=$2 RETURNING value".format(f"guild{ctx.guild.id}_{category_name.lower()}")
        newamount = await self.client.pool_pg.fetchval(QUERY, member.id, currentcount - amount, column='value')
        embed = discord.Embed(title=f"Updated {member.name}'s __{real_name}__ donations.", description=f"**Original amount**: `{comma_number(currentcount)}`\n**Amount removed**: `{comma_number(amount)}`\n**New amount**: `{comma_number(newamount)}`", color=discord.Color.orange(), timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(name="Success!", icon_url="https://cdn.discordapp.com/emojis/575412409737543694.gif?size=96")
        embed.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
        return await ctx.send(embed=embed)

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="setdonations", aliases=["sd"])
    async def setdonations(self, ctx, member:discord.Member = None, amount: BetterInt = None, *, category_name: str = None):
        """
        Set donations for a user to a certain amount.
        """
        if member is None:
            return await ctx.send("You must specify a member to set donations for.")
        if amount is None:
            return await ctx.send(f"You must specify an amount to set {member.name}'s donations to..")
        if category_name is None:
            return await ctx.send("You must specify a category to set the donations to.")
        if amount <= 0:
            return await ctx.send("You must specify an amount greater than 0 to be set to {}'s donations.".format(member.name))
        currentcount = await self.get_donation_count(member, category_name)
        QUERY = "INSERT INTO donations.{} VALUES ($1, $2) ON CONFLICT(user_id) DO UPDATE SET value=$2 RETURNING value".format(f"guild{ctx.guild.id}_{category_name.lower()}")
        newamount = await self.client.pool_pg.fetchval(QUERY, member.id, amount, column='value')
        embed = discord.Embed(title=f"Changed {member.name}'s **{category_name}** donations.", description=f"**Original amount**: `{comma_number(currentcount)}`\n**New amount**: `{comma_number(newamount)}`", color=discord.Color.blue(), timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(name="Success!", icon_url="https://cdn.discordapp.com/emojis/575412409737543694.gif?size=96")
        embed.set_footer(icon_url=ctx.guild.icon.url, text=ctx.guild.name)
        return await ctx.send(embed=embed)
