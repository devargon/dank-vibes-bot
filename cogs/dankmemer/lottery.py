import contextlib
from typing import Literal

import discord
from discord import SlashCommandGroup
from discord.ext import commands
from main import dvvt
from utils import checks
from utils.buttons import confirm
from utils.context import DVVTcontext

accepted_lottery_types = ['dank', 'karuta', 'owo']

def get_lotto_channel(guild_id: int, type_of_lottery: Literal['dank', 'karuta', 'owo']) -> int:
    if guild_id == 595457764935991326:
        if type_of_lottery == 'dank':
            lottery_chan_id = 731398659664511057
        elif type_of_lottery == 'karuta':
            lottery_chan_id = 887006001566462062
        elif type_of_lottery == 'owo':
            lottery_chan_id = 859761455242149919
        else:
            lottery_chan_id = None
    else:
        if type_of_lottery == 'dank':
            lottery_chan_id = 976756021907312640
        elif type_of_lottery == 'karuta':
            lottery_chan_id = 976756135400996925
        elif type_of_lottery == 'owo':
            lottery_chan_id = 976756118405652500
        else:
            lottery_chan_id = None
    return lottery_chan_id


def get_ping(guild_id: int, type_of_lottery: Literal['dank', 'karuta', 'owo']) -> str:
    if guild_id == 595457764935991326:
        if type_of_lottery == 'dank':
            ping = "<@&680131933778346011>"
        elif type_of_lottery == 'owo':
            ping = "<@&847538763412668456>"
        elif type_of_lottery == 'karuta':
            ping = "<@&886983702402457641>"
        else:
            ping = None
    else:
        if type_of_lottery == 'dank':
            ping = "<@&895815799812521994>"
        elif type_of_lottery == 'owo':
            ping = "<@&955387105373204490>"
        elif type_of_lottery == 'karuta':
            ping = "<@&976662248787415060>"
        else:
            ping = None
    return ping




class Lottery(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name="lottery", invoke_without_command=True)
    async def lottery(self, ctx: DVVTcontext, lottery_id: int = None, users: commands.Greedy[discord.Member] = None):
        """
        Lottery Management for Dank Vibes.
        Unlike Atlas, Dank Vibes Bot's lottery management allows for hosting multiple lotteries with a single command.
        Because of that, all lottery commands will require the input of a lottery ID, that's issued to you whenever you start a lottery.

        """
        if lottery_id is None:
            return await ctx.help()
        if not (lottery_obj := await self.client.db.fetchrow("SELECT * FROM lotteries WHERE lottery_id = $1", lottery_id)):
            await ctx.send(f"A lottery with the ID {lottery_id} doesn't exist.")
            return
        type_of_lottery = lottery_obj.get('lottery_type')
        if type_of_lottery not in ['dank', 'karuta', 'owo']:
            return await ctx.send("Invalid lottery type.")

        last_lottery_number = await self.client.db.fetchval("SELECT lottery_number FROM lottery_entries WHERE lottery_id = $1 ORDER BY lottery_number DESC LIMIT 1", lottery_id)
        if last_lottery_number is None:
            last_lottery_number = 0
        if users is None or len(users) == 0:
            return await ctx.send(f"**{type_of_lottery} lottery**'s last entered number: `{last_lottery_number}`")




        to_commit = []
        summary = []
        for user in users:
            next_lottery_number = last_lottery_number + 1
            while (reserved_entry := await self.client.db.fetchrow("SELECT * FROM reserved_entries WHERE lottery_number = $1 AND lottery_id = $2", next_lottery_number, lottery_id)) is not None:
                to_commit.append((lottery_id, next_lottery_number, reserved_entry.get('lottery_user')))
                us = self.client.get_user(reserved_entry.get('lottery_user'))
                us = str(us) if us is not None else reserved_entry.get('lottery_user')
                summary.append(f"<:DVB_True:887589686808309791> **{us}** entered as `{next_lottery_number}` (reserved)")
                last_lottery_number = next_lottery_number
                next_lottery_number += 1
            else:
                to_commit.append((lottery_id, next_lottery_number, user.id))
                summary.append(f"<:DVB_True:887589686808309791> **{user.name}** has entered as `{next_lottery_number}`")
                last_lottery_number = next_lottery_number
        await self.client.db.executemany("INSERT INTO lottery_entries(lottery_id, lottery_number, lottery_user) VALUES ($1, $2, $3)", to_commit)
        summary = '\n'.join(summary)
        embed = discord.Embed(title="Successfully added entries", description=summary, color=discord.Color.green())
        if len(summary) > 0:
            try:
                await ctx.reply(summary)
            except:
                await ctx.send(summary)
        lottery_chan_id = get_lotto_channel(ctx.guild.id, type_of_lottery)
        if (chan := ctx.guild.get_channel(lottery_chan_id)) is not None:
            for lottery_id, lottery_number, lottery_user_id in to_commit:
                us = self.client.get_user(lottery_user_id)
                us = f"{us.mention} (`{us}`)" if us is not None else lottery_user_id
                em = discord.Embed(description=f"{lottery_number}. {us}", color=discord.Color.random())
                await chan.send(embed=em)




    @checks.has_permissions_or_role(manage_roles=True)
    @lottery.command(name="start")
    async def lottery_start(self, ctx: DVVTcontext, lottery_type: str = None, max_tickets: int = None, *, entry_fee: str = None):
        """
        Starts a lottery.
        `lottery_type` needs to be one of `dank`, `karuta` or `owo`.
        """
        if lottery_type is None or max_tickets is None or entry_fee is None:
            return await ctx.help()
        lottery_type = lottery_type.lower()
        if lottery_type not in ['dank', 'karuta', 'owo']:
            return await ctx.send("<:DVB_False:887589731515392000> **Invalid lottery type**.\n`type` must be one of `dank`, `karuta`, or `owo`.")
        embed = discord.Embed(title=entry_fee, description=f"Holder: {ctx.author.mention}\nChannel: <#680002065950703646>\nMaximum Entries: `{max_tickets}`", color=self.client.embed_color)
        if lottery_type == 'owo':
            embed.add_field(name="Entry:", value=f"<a:dv_pointArrowOwO:837656328482062336> Give {ctx.author.mention} `{entry_fee}` in <#859761515761762304> to enter!")
        elif lottery_type == 'dank':
            embed.add_field(name="Entry:", value=f"<a:dv_pointArrowOwO:837656328482062336> Read the sticky message in <#680002065950703646> for information on how to enter!")
        elif lottery_type == 'karuta':
            embed.add_field(name="Entry:", value=f"<a:dv_pointArrowOwO:837656328482062336> Follow the format given in <#887006001566462062> and kindly wait for a <@&843756047964831765> to assist you!")
        ping = get_ping(ctx.guild.id, lottery_type)
        dank_required_roles = [663502776952815626, 684591962094829569, 608500355973644299]
        karuta_required_roles = [843756047964831765, 663502776952815626, 684591962094829569, 608500355973644299]
        owo_required_roles = [837595910661603330, 663502776952815626, 684591962094829569, 608500355973644299]
        if ctx.guild.id == 595457764935991326:
            if lottery_type == 'dank':
                if not any([ctx.guild.get_role(r_id) in ctx.author.roles for r_id in dank_required_roles]):
                    confirm_host_view = confirm(ctx,self.client, 30.0)
                else:
                    confirm_host_view = None
            elif lottery_type == 'karuta':
                if not any([ctx.guild.get_role(r_id) in ctx.author.roles for r_id in karuta_required_roles]):
                    confirm_host_view = confirm(ctx, self.client, 30.0)
                else:
                    confirm_host_view = None
            elif lottery_type == 'owo':
                if not any([ctx.guild.get_role(r_id) in ctx.author.roles for r_id in owo_required_roles]):
                    confirm_host_view = confirm(ctx, self.client, 30.0)
                else:
                    confirm_host_view = None
            else:
                confirm_host_view = None
            if confirm_host_view:
                confirm_host_embed = discord.Embed(title="It doesn't seem like you're a staff for this category.",
                                                   description=f"Are you sure you want to start a lottery for the `{lottery_type}` category?",
                                                   color=discord.Color.orange())
                confirm_host_view.response = await ctx.send(embed=confirm_host_embed, view=confirm_host_view)
                await confirm_host_view.wait()
                if confirm_host_view.returning_value is True:
                    confirm_host_embed.color = discord.Color.green()
                    await confirm_host_view.response.edit(embed=confirm_host_embed, delete_after=5.0)
                else:
                    confirm_host_embed.color = discord.Color.red()
                    await confirm_host_view.response.edit(embed=confirm_host_embed, delete_after=5.0)
                    return
        confirm_start_view = confirm(ctx, self.client, 30.0)
        confirm_start_embed = discord.Embed(title=f"Ready to start a {lottery_type} lottery?", description=f"Holder: {ctx.author.mention}\nChannel: <#680002065950703646>\nMaximum Entries: `{max_tickets}`", color=self.client.embed_color)
        confirm_start_view.response = await ctx.send(embed=confirm_start_embed, view=confirm_start_view)
        await confirm_start_view.wait()
        if confirm_start_view.returning_value is True:
            confirm_start_embed.color = discord.Color.green()
            await confirm_start_view.response.edit(embed=confirm_start_embed, delete_after=2.0)
        else:
            confirm_start_embed.color = discord.Color.red()
            await confirm_start_view.response.edit(embed=confirm_start_embed, delete_after=2.0)
            return
        lottery_id = await self.client.db.fetchval("INSERT INTO lotteries(lottery_type, guild_id, starter_id, lottery_entry) VALUES($1, $2, $3, $4) RETURNING lottery_id", lottery_type, ctx.guild.id, ctx.author.id, entry_fee, column='lottery_id')
        embed.set_footer(text=f"Lottery #{lottery_id} • {ctx.guild.name}")
        await ctx.send(ping, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True, everyone=False))
        with contextlib.suppress(Exception):
            dmembed = discord.Embed(title=f"You have just started a {lottery_type} lottery!",
                                    description=f"""> Your lottery's ID is {lottery_id}.
                                    <:ReplyCont:871807889587707976> Add new entries to the lottery with `{ctx.prefix}lottery {lottery_id} <multiple members>`
                                    <:ReplyCont:871807889587707976> Set reserved entries with `{ctx.prefix}lottery reserve {lottery_id} <member> <reserved_number>`
                                    <:Reply:871808167011549244> End the lottery with `{ctx.prefix}lottery end {lottery_id}`
                                    """, color=self.client.embed_color)
            await ctx.author.send(embed=dmembed)


    @checks.has_permissions_or_role(manage_roles=True)
    @lottery.command(name="reserve")
    async def lottery_reserve(self, ctx: DVVTcontext, lottery_id: int = None, user: discord.Member = None, lottery_number: int = None):
        """
        Reserve a lottery number!
        To view the reserved numbers for a lottery, specify **only** the `lottery_id`.
        Removing a reserved number is the same as adding it.
        """
        if lottery_id is None:
            return await ctx.help()
        if (lottery_db := await self.client.db.fetchrow("SELECT * FROM lotteries WHERE lottery_id=$1", lottery_id)) is None:
            return await ctx.send(f"No lottery found with ID `{lottery_id}`.")
        if user is None:
            embed = discord.Embed(title=f"Reserved entries for {lottery_db.get('lottery_type')} lottery #{lottery_id}", color=self.client.embed_color)
            entries_str = []
            for entry in await self.client.db.fetch("SELECT * FROM reserved_entries WHERE lottery_id=$1", lottery_id):
                if (us := self.client.get_user(entry.get('lottery_user'))) is not None:
                    us_placement = f"{us.name}#{us.discriminator}"
                else:
                    us_placement = f"{entry.get('lottery_user')}"
                entries_str.append(f"{us_placement}: `{entry.get('lottery_number')}`")
            embed.description = "\n".join(entries_str)
            embed.set_footer(text="To remove a reserved number, run the command again like you would add the entry.")
            return await ctx.send(embed=embed)
        if lottery_number is None:
            return await ctx.send(f"You must specify a lottery entry number to reserve (or remove).")
        if (num_reserved_entry := await self.client.db.fetchrow("SELECT * FROM reserved_entries WHERE lottery_id=$1 AND lottery_number = $2", lottery_id, lottery_number)) is not None:
            if num_reserved_entry.get('lottery_user') != user.id:
                us = self.client.get_user(num_reserved_entry.get('lottery_user'))
                us = f"{us} ({us.id})" if us is not None else num_reserved_entry.get('lottery_user')
                return await ctx.send(f"The lottery number `{lottery_number}` is already reserved for **{us}**.")
            await self.client.db.execute("DELETE FROM reserved_entries WHERE lottery_id=$1 AND lottery_user=$2 AND lottery_number = $3", lottery_id, user.id, lottery_number)
            return await ctx.send(f"Removed **{user}**'s `{lottery_number}` entry from the lottery's reserved entries.")
        else:
            await self.client.db.execute("INSERT INTO reserved_entries(lottery_id, lottery_user, lottery_number) VALUES($1, $2, $3)", lottery_id, user.id, lottery_number)
            return await ctx.send(f"Added **{user}**'s `{lottery_number}` entry to the lottery's reserved entries.")


    @checks.has_permissions_or_role(manage_roles=True)
    @lottery.command(name="makecount")
    async def lottery_makecount(self, ctx: DVVTcontext, lottery_id: int, count: int):
        """
        If you messed up, use this command to change the lottery's current entry number.
        This number should be the last number entered correctly.
        """
        confirmview = confirm(ctx, self.client, 30.0)
        confirmembed = discord.Embed(description=f"Are you sure you want to change the current entry number of **lottery #{lottery_id}** to `{count}`?\n\nThe last correctly entered entry will be `{count}`.\nThe next entry to be entered will be `{count+1}`, ", color=discord.Color.orange())
        confirmview.response = await ctx.send(embed=confirmembed, view=confirmview)
        await confirmview.wait()
        if confirmview.returning_value is not True:
            confirmembed.color = discord.Color.red()
            return await confirmview.response.edit(embed=confirmembed)
        else:
            confirmembed.color = discord.Color.green()
            confirmembed.description += f"\n\n<:DVB_True:887589686808309791> **Success!**"
            await self.client.db.execute("DELETE FROM lottery_entries WHERE lottery_id = $1 AND lottery_number > $2", lottery_id, count)
        return await confirmview.response.edit(embed=confirmembed)




    @checks.has_permissions_or_role(manage_roles=True)
    @lottery.command(name='end')
    async def lottery_end(self, ctx: DVVTcontext):
        pass
