import contextlib
import random
from typing import Literal, Optional

import discord
from discord import SlashCommandGroup
from discord.ext import commands
from main import dvvt
from utils import checks
from utils.buttons import confirm
from utils.context import DVVTcontext

accepted_lottery_types = ['dank', 'karuta', 'owo']

class GoldPotTemplateModal(discord.ui.Modal):
    def __init__(self, client, lottery_type: Literal['dank', 'karuta', 'owo'], lotto_entries, winner:Optional[discord.User] = None, default_winner_option: Optional[str] = None, default_prize: Optional[str] = None):
        self.client = client
        self.winner = winner
        self.default_winner_option = default_winner_option
        self.default_prize = default_prize
        super().__init__(title="Generate Gold Pot Template", custom_id=f"lotto-template:{lottery_type}:{lotto_entries}")
        if self.winner is not None:
            if self.default_winner_option is not None:
                self.add_item(discord.ui.InputText(label="Lottery Winner",
                                                   placeholder="MUST be a Discord User ID. Leave this blank if user can't be found.",
                                                   required=False, value=self.default_winner_option,
                                                   style=discord.InputTextStyle.short))
            else:
                self.add_item(discord.ui.InputText(label="Lottery Winner", placeholder="MUST be a Discord User ID. Leave this blank if user can't be found.", required=False, value=str(winner.id), style=discord.InputTextStyle.short))
        if self.default_prize is not None:
            self.add_item(discord.ui.InputText(label="Lottery Prize", required=False, value=default_prize, style=discord.InputTextStyle.short))
        else:
            self.add_item(discord.ui.InputText(label="Lottery Prize", style=discord.InputTextStyle.short))

    async def callback(self, interaction: discord.Interaction):
        remarks = []
        lottery_type, lotto_entries = self.custom_id.split(':')[1], self.custom_id.split(':')[2]
        try:
            winner_id = int(self.children[0].value)
        except ValueError:
            if len(self.children[0].value) == 0:
                user = None
            else:
                remarks.append(f"<:DVB_False:887589731515392000> Invalid User: `{self.children[0].value}`")
                user = None
        else:
            if (user := self.client.get_user(winner_id)) is None:
                remarks.append(f"<:DVB_False:887589731515392000> Invalid User: `{self.children[0].value}`")

        prize = self.children[1].value
        if lottery_type == 'owo':
            emoji = ('<a:dv_fabledGemOwO:859773160357232651>', '<:dv_newOwO:859772980875886602>')
        elif lottery_type == 'karuta':
            emoji = ('<a:dv_bunbunDanceOwO:837749889496514570>', '<a:dv_aFishieOwO:837741744253829190>')
        else:
            emoji = ('<a:dv_pepeHypeOwO:837712517261688832>', '<:dv_panMoneyOwO:837713209796460564>')
        embeds = []
        if user is not None:
            us_display = f"**{user.name}** ({user.mention})"
        else:
            us_display = "**USERNAME** (<@ID>)"
        embeds.append(discord.Embed(title="Coin Prize Template", description=f"```\n{emoji[0]} **{lotto_entries}** users entered, {us_display} snagged an easy {emoji[1]} **{prize}** {emoji[1]}\n```", color=0xFFD700))
        if lottery_type == 'dank':
            embeds.append(discord.Embed(title="Item Prize Template", description=f"```\n{emoji[0]} **{lotto_entries}** users entered, {us_display} easily snagged **{prize}** worth {emoji[1]} **⏣ ** {emoji[1]}\n```", color=0xFFD700))
        if len(remarks) > 0:
            remarks = "**Warning**:\n\n" + "\n".join(remarks)
            await interaction.response.send_message(remarks, embeds=embeds)
        else:
            await interaction.response.send_message(embeds=embeds)


class LottoTemplateView(discord.ui.View):
    def __init__(self, client, lottery_type, lotto_entries, winner):
        self.client = client
        self.lottery_type = lottery_type
        self.lotto_entries = lotto_entries
        self.winner = winner
        super().__init__(timeout=None)

    @discord.ui.button(label="Generate Lottery Win Template")
    async def generate_lottery_template(self, button:discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(GoldPotTemplateModal(self.client, self.lottery_type, self.lotto_entries, self.winner))




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

    async def check_non_hoster_consent(self, ctx: DVVTcontext, lottery_hoster: int):
        if ctx.author.id != lottery_hoster:
            us = self.client.get_user(lottery_hoster)
            us = f"{us}" if us else str(lottery_hoster)
            confirmview = confirm(ctx, self.client, 30.0)
            confirmembed = discord.Embed(title="You are not the host of this lottery.", description=f"{us} is the host of this lottery, are you sure you want to continue?", color=discord.Color.orange())
            confirmview.response = await ctx.send(embed=confirmembed, view=confirmview)
            await confirmview.wait()
            if confirmview.returning_value is not True:
                confirmembed.color=discord.Color.red()
                await confirmview.response.edit(embed=confirmembed)
                return False
            else:
                confirmembed.color = discord.Color.green()
                await confirmview.response.edit(embed=confirmembed)
                return True
        else:
            return True




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
        if lottery_id > 2147483647 or (lottery_obj := await self.client.db.fetchrow("SELECT * FROM lotteries WHERE lottery_id = $1 AND active = $2", lottery_id, True)) is None:
            await ctx.send(f"<:DVB_False:887589731515392000> An active lottery with the ID {lottery_id} doesn't exist.")
            return
        type_of_lottery = lottery_obj.get('lottery_type')
        if type_of_lottery not in ['dank', 'karuta', 'owo']:
            return await ctx.send("Invalid lottery type.")

        await self.check_non_hoster_consent(ctx, lottery_obj.get('starter_id'))

        last_lottery_number = await self.client.db.fetchval("SELECT lottery_number FROM lottery_entries WHERE lottery_id = $1 ORDER BY lottery_number DESC LIMIT 1", lottery_id)
        if last_lottery_number is None:
            last_lottery_number = 0
        if users is None or len(users) == 0:
            return await ctx.send(f"**{type_of_lottery} lottery**'s last entered number: `{last_lottery_number}`")




        to_commit = []
        summary = []
        for user in users:
            next_lottery_number = last_lottery_number + 1
            while (reserved_entry := await self.client.db.fetchrow("SELECT * FROM lottery_reserved_entries WHERE lottery_number = $1 AND lottery_id = $2", next_lottery_number, lottery_id)) is not None:
                to_commit.append((lottery_id, next_lottery_number, reserved_entry.get('lottery_user')))
                us = self.client.get_user(reserved_entry.get('lottery_user'))
                us = str(us) if us is not None else reserved_entry.get('lottery_user')
                summary.append(f"<:DVB_True:887589686808309791> **{us}** entered as `{next_lottery_number}` (reserved)")
                last_lottery_number = next_lottery_number
                next_lottery_number += 1
            else:
                to_commit.append((lottery_id, next_lottery_number, user.id))
                if user.display_name != user.name:
                    summary.append(f"<:DVB_True:887589686808309791> **{user.name}** a.k.a. **{user.display_name}** entered as `{next_lottery_number}`")
                else:
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
        if lottery_id > 2147483647 or (lottery_db := await self.client.db.fetchrow("SELECT * FROM lotteries WHERE lottery_id = $1 AND active = $2", lottery_id, True)) is None:
            await ctx.send(f"<:DVB_False:887589731515392000> An active lottery with the ID {lottery_id} doesn't exist.")
            return
        if user is None:
            embed = discord.Embed(title=f"Reserved entries for {lottery_db.get('lottery_type')} lottery #{lottery_id}", color=self.client.embed_color)
            entries_str = []
            for entry in await self.client.db.fetch("SELECT * FROM lottery_reserved_entries WHERE lottery_id=$1", lottery_id):
                if (us := self.client.get_user(entry.get('lottery_user'))) is not None:
                    us_placement = f"{us.name}#{us.discriminator}"
                else:
                    us_placement = f"{entry.get('lottery_user')}"
                entries_str.append(f"{us_placement}: `{entry.get('lottery_number')}`")
            embed.description = "\n".join(entries_str)
            embed.set_footer(text="To remove a reserved number, run the command again like you would add the entry.")
            return await ctx.send(embed=embed)

        if await self.check_non_hoster_consent(ctx, lottery_db.get('starter_id')) is True:
            if lottery_number is None:
                return await ctx.send(f"You must specify a lottery entry number to reserve (or remove).")
            if (num_reserved_entry := await self.client.db.fetchrow("SELECT * FROM lottery_reserved_entries WHERE lottery_id=$1 AND lottery_number = $2", lottery_id, lottery_number)) is not None:
                if num_reserved_entry.get('lottery_user') != user.id:
                    us = self.client.get_user(num_reserved_entry.get('lottery_user'))
                    us = f"{us} ({us.id})" if us is not None else num_reserved_entry.get('lottery_user')
                    return await ctx.send(f"The lottery number `{lottery_number}` is already reserved for **{us}**.")
                await self.client.db.execute("DELETE FROM lottery_reserved_entries WHERE lottery_id=$1 AND lottery_user=$2 AND lottery_number = $3", lottery_id, user.id, lottery_number)
                return await ctx.send(f"Removed **{user}**'s `{lottery_number}` entry from the lottery's reserved entries.")
            else:
                await self.client.db.execute("INSERT INTO lottery_reserved_entries(lottery_id, lottery_user, lottery_number) VALUES($1, $2, $3)", lottery_id, user.id, lottery_number)
                return await ctx.send(f"Added **{user}**'s `{lottery_number}` entry to the lottery's reserved entries.")


    @checks.has_permissions_or_role(manage_roles=True)
    @lottery.command(name="makecount")
    async def lottery_makecount(self, ctx: DVVTcontext, lottery_id: int, count: int):
        """
        If you messed up, use this command to change the lottery's current entry number.
        This number should be the last number entered correctly.
        """
        if lottery_id > 2147483647 or (
        lotto_object := await self.client.db.fetchrow("SELECT * FROM lotteries WHERE lottery_id = $1 AND active = $2", lottery_id, True)) is None:
            await ctx.send(f"<:DVB_False:887589731515392000> An active lottery with the ID {lottery_id} doesn't exist.")
            return

        if await self.check_non_hoster_consent(ctx, lotto_object.get('starter_id')) is True:
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
    async def lottery_end(self, ctx: DVVTcontext, lottery_id: int):
        """
        Ends a lottery.
        """
        if lottery_id > 2147483647 or (
        lotto_object := await self.client.db.fetchrow("SELECT * FROM lotteries WHERE lottery_id = $1 AND active = $2",
                                                     lottery_id, True)) is None:
            await ctx.send(f"<:DVB_False:887589731515392000> An active lottery with the ID {lottery_id} doesn't exist.")
            return

        if await self.check_non_hoster_consent(ctx, lotto_object.get('starter_id')) is True:
            max_lotto_no = await self.client.db.fetchval("SELECT MAX(lottery_number) FROM lottery_entries WHERE lottery_id = $1", lottery_id)
            confirmview = confirm(ctx, self.client, 30.0)
            confirmembed = discord.Embed(title=f"Are you sure you want to end lottery #{lottery_id}?\n\nNumber of entries: {max_lotto_no}\n", description="Any unadded reserved lottery entries will be added automatically.", color=discord.Color.orange())
            confirmview.response = await ctx.send(embed=confirmembed, view=confirmview)
            await confirmview.wait()
            if confirmview.returning_value is not True:
                confirmembed.color = discord.Color.red()
                return await confirmview.response.edit(embed=confirmembed)
            else:
                confirmembed.color = discord.Color.green()
                await confirmview.response.edit(embed=confirmembed)
                remaining_reserved_entries = await self.client.db.fetch("SELECT * FROM lottery_reserved_entries WHERE lottery_id = $1 AND lottery_number > $2 ORDER BY lottery_number", lottery_id, max_lotto_no)

                type_of_lottery = lotto_object.get('lottery_type')
                if len(remaining_reserved_entries) > 0:
                    for reserved_entry in remaining_reserved_entries:
                        max_lotto_no += 1
                        await self.client.db.execute("INSERT INTO lottery_entries(lottery_id, lottery_number, lottery_user) VALUES ($1, $2, $3)", lottery_id, max_lotto_no, reserved_entry.get('lottery_user'))
                        lottery_chan_id = get_lotto_channel(ctx.guild.id, type_of_lottery)
                        if (chan := ctx.guild.get_channel(lottery_chan_id)) is not None:
                            us = self.client.get_user(reserved_entry.get('lottery_user'))
                            us = f"{us.mention} (`{us}`)" if us is not None else reserved_entry.get('lottery_user')
                            em = discord.Embed(description=f"{max_lotto_no}. {us}", color=discord.Color.random())
                            await chan.send(embed=em)
                        await ctx.send(f"User `{reserved_entry.get('lottery_user')}` has been added to the back of the lottery since they have a reserved number.")
                if max_lotto_no < 1:
                    the_chosen_one = 0
                else:
                    the_chosen_one = random.randint(1, max_lotto_no)
                await self.client.db.execute("UPDATE lotteries SET active = $1 WHERE lottery_id = $2", False, lottery_id)
                lottery_win_embed = discord.Embed(title=f"{max_lotto_no} users participated!", color=self.client.embed_color)
                lottery_win_embed.set_footer(text=f"Lottery #{lottery_id} • {ctx.guild.name}", icon_url=ctx.guild.icon.url)
                lottery_win_embed.set_thumbnail(url=ctx.guild.icon.url)
                lottery_win_embed.add_field(name="Winning Ticket Number:", value=f"```\n{the_chosen_one}\n```")
                if (channel := ctx.guild.get_channel(get_lotto_channel(ctx.guild.id, lotto_object.get('lottery_type')))) is not None:
                    await channel.send(embed=lottery_win_embed)
                with contextlib.suppress(discord.Forbidden):
                    if the_chosen_one == 0:
                        await ctx.author.send("Looks like no one joined your lottery.", view=LottoTemplateView(self.client, lotto_object.get('lottery_type'), 0, None))
                    else:
                        us = self.client.get_user(await self.client.db.fetchval("SELECT lottery_user FROM lottery_entries WHERE lottery_number = $1 AND lottery_id = $2", the_chosen_one, lottery_id))
                        if lotto_object.get('lottery_type') == 'owo':
                            msg = f"A winner for the lottery #{lottery_id} in {ctx.guild.name} has been chosen in <#859761455242149919>."
                        elif lotto_object.get('lottery_type') == 'dank':
                            msg = f"A winner for the lottery #{lottery_id} in {ctx.guild.name} has been chosen in <#731398659664511057>, Don't forget to echo the following text in <#680001973352923156>:"
                        elif lotto_object.get('lottery_type') == 'karuta':
                            msg = f"A winner for the lottery #{lottery_id} in {ctx.guild.name} has been chosen in <#887006001566462062>."
                        else:
                            msg = f"Generate a template to be sent to show the winner of this lottery."
                        await ctx.author.send(msg, view=LottoTemplateView(self.client, lotto_object.get('lottery_type'), max_lotto_no, us))
