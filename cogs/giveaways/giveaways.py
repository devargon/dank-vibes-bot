import asyncio
from time import time
from datetime import datetime
import typing
from utils import checks
from utils.errors import ArgumentBaseError
from utils.format import comma_number, plural, stringtime_duration, grammarformat
from utils.time import humanize_timedelta
import os
import random
from utils.buttons import confirm

voteid = 874897331252760586 if os.getenv('state') == '1' else 683884762997587998

import discord
from discord.ext import commands, tasks, menus
from utils.menus import CustomMenu

class GiveawayList(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=menu.ctx.bot.embed_color, timestamp=discord.utils.utcnow())
        for entry in entries:
            embed.add_field(name=f"{entry[0]}", value=entry[1], inline=False)
        embed.set_footer(text=f"{len(entries)} giveaways | Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed

class GiveawayView(discord.ui.View):
    def __init__(self, client):
        super().__init__(timeout=None)
        self.client = client

    @discord.ui.button(emoji=discord.PartialEmoji.from_str("<a:dv_iconOwO:837943874973466664>"), label="Join giveaway", style=discord.ButtonStyle.green, custom_id="dvb:giveawayjoin")
    async def JoinGiveaway(self, button: discord.ui.Button, interaction: discord.Interaction):
        giveawaymessage = interaction.message
        is_giveaway_valid = await self.client.pool_pg.fetchrow("SELECT * FROM giveaways WHERE message_id = $1 AND time > $2", giveawaymessage.id, round(time()))
        if is_giveaway_valid == None:
            return await interaction.response.send_message("It appears that this giveaway doesn't exist or has ended.", ephemeral=True)
        if (await self.client.pool_pg.fetchrow("SELECT * FROM giveawayentrants WHERE user_id = $1 and message_id = $2", interaction.user.id, giveawaymessage.id)) is not None:
            await interaction.response.send_message("You've already joined this giveaway!", ephemeral=True)
        else:
            await self.client.pool_pg.execute("INSERT INTO giveawayentrants VALUES($1, $2)", giveawaymessage.id, interaction.user.id)
            await interaction.response.send_message("You've successfully joined the giveaway!", ephemeral=True)
        entrant_no = await self.client.pool_pg.fetchval("SELECT COUNT(DISTINCT user_id) FROM giveawayentrants WHERE message_id = $1", giveawaymessage.id)
        giveawayembed = giveawaymessage.embeds[0]
        giveawayembed.set_field_at(-1, name="Entrants", value=comma_number(entrant_no))
        await giveawaymessage.edit(embed=giveawayembed)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str("<:DVB_plus1:911608605759901766>"), label="Extra Entry", custom_id="dvb:giveawayextraentry")
    async def ExtraEntry(self, button: discord.ui.Button, interaction: discord.Interaction):
        giveawaymessage = interaction.message
        is_giveaway_valid = await self.client.pool_pg.fetchrow("SELECT * FROM giveaways WHERE message_id = $1 AND time > $2", giveawaymessage.id, round(time()))
        if is_giveaway_valid == None:
            return await interaction.response.send_message("It appears that this giveaway doesn't exist or has ended.", ephemeral=True)
        voterole = interaction.guild.get_role(voteid)
        if voterole is None:
            await interaction.response.send_message("The Vibing Dankster role is invalid.", ephemeral=True)
            return
        number_of_entries = len(await self.client.pool_pg.fetch("SELECT * FROM giveawayentrants WHERE user_id = $1 and message_id = $2", interaction.user.id, giveawaymessage.id))
        if number_of_entries == 0:
            return await interaction.response.send_message("Join the giveaway first before claiming your extra entry!", ephemeral=True)
        elif number_of_entries == 1:
            if voterole not in interaction.user.roles:
                return await interaction.response.send_message(f"You need to vote for {interaction.guild.name} to have an **extra entry** in this giveaway.\nYou can do so [here](https://top.gg/servers/595457764935991326/vote)!", ephemeral=True)
            else:
                await self.client.pool_pg.execute("INSERT INTO giveawayentrants VALUES($1, $2)", giveawaymessage.id, interaction.user.id)
                await interaction.response.send_message("You've claimed your extra entry! You now have **2** entries in this giveaway!", ephemeral=True)
        else:
            await interaction.response.send_message("You've already claimed your extra entry in this giveaway.", ephemeral=True)

class giveaways(commands.Cog):
    """
    Giveaway commands
    """
    def __init__(self, client):
        self.client = client
        self.giveawayview_added = False
        self.end_giveaways.start()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.giveawayview_added:
            self.client.add_view(GiveawayView(self.client))
            self.giveawayview_added = True
            #self.change_entrantcount.start()

    @tasks.loop(seconds=5.0)
    async def change_entrantcount(self):
        await self.client.wait_until_ready()
        giveaways = await self.client.pool_pg.fetch("SELECT * FROM giveaways WHERE time > $1", round(time()))
        if len(giveaways) > 0:
            for giveaway in giveaways:
                message = await self.client.get_channel(giveaway.get("channel_id")).fetch_message(giveaway.get("message_id"))
                entrant_no = await self.client.pool_pg.fetchval("SELECT COUNT(DISTINCT user_id) FROM giveawayentrants WHERE message_id = $1", giveaway.get("message_id"))
                giveawayembed = message.embeds[0]
                giveawayembed.set_field_at(-1, name="Entrants", value=comma_number(entrant_no))
                await message.edit(embed=giveawayembed)


    @tasks.loop(seconds=3.0)
    async def end_giveaways(self):
        try:
            await self.client.wait_until_ready()
            ended_giveaways = await self.client.pool_pg.fetch("SELECT * FROM giveaways WHERE time < $1 AND active = $2", round(time()), True)
            if len(ended_giveaways) > 0:
                for giveaway in ended_giveaways:
                    guild = self.client.get_guild(giveaway.get("guild_id"))
                    if guild is not None:
                        channel = guild.get_channel(giveaway.get("channel_id"))
                        if channel is not None:
                            try:
                                gawmessage = await self.client.get_channel(giveaway.get("channel_id")).fetch_message(giveaway.get("message_id"))
                            except:
                                pass
                            else:
                                entrant_no = await self.client.pool_pg.fetchval("SELECT COUNT(DISTINCT user_id) FROM giveawayentrants WHERE message_id = $1", giveaway.get("message_id"))
                                view = discord.ui.View.from_message(gawmessage)
                                for b in view.children:
                                    if isinstance(b, discord.ui.Button):
                                            b.disabled = True
                                giveawayembed = gawmessage.embeds[0]
                                giveawayembed.set_author(url="https://cdn.discordapp.com/attachments/871737314831908974/911294206872526879/ezgif-3-53092e7bef9b.png", name="This giveaway has ended!")
                                entries = await self.client.pool_pg.fetch("SELECT * FROM giveawayentrants WHERE message_id = $1", giveaway.get("message_id"))
                                winners = []
                                while len(winners) != giveaway.get("winners") and len(entries) > 0:
                                    winner = random.choice(entries)
                                    if winner.get("user_id") not in winners:
                                        member = guild.get_member(winner.get("user_id"))
                                        if member is not None:
                                            winners.append(member)
                                    entries.remove(winner)
                                if len(winners) == 0:
                                    await channel.send(f"I could not find a winner from the **{giveaway.get('name')}** giveaway.\nhttps://discord.com/channels/{guild.id}/{channel.id}/{giveaway.get('message_id')}")
                                else:
                                    giveawayembed.add_field(name="Winners", value=f"{grammarformat([winner.mention for winner in winners])}", inline=False)
                                    #print("editing giveaway message embed")
                                    await gawmessage.edit(embed=giveawayembed, view=view)
                                    message = f"{random.choice(guild.emojis)} **{entrant_no}** user(s) entered, {grammarformat([winner.mention for winner in winners])} snagged away **{giveaway.get('name')}**!\nhttps://discord.com/channels/{guild.id}/{channel.id}/{giveaway.get('message_id')}"
                                    #print("sending winner message")
                                    await channel.send(message)
                                    winembed = discord.Embed(title=f"You've won the {giveaway.get('name')} giveaway!", description="The prize should be given to you within 24 hours. If you have not received it by then, contact a mod in <#870880772985344010>.", color=self.client.embed_color, timestamp=discord.utils.utcnow())
                                    winembed.set_author(name=guild.name, icon_url=guild.icon.url)
                                    for winner in winners:
                                        try:
                                            #print("DMing winner")
                                            await winner.send(embed=winembed)
                                        except:
                                            pass
                                    host = guild.get_member(giveaway.get("host_id"))
                                    if host is not None:
                                        hostembed = discord.Embed(
                                            title=f"Your {giveaway.get('name')} giveaway has ended!",
                                            description=f"{grammarformat([f'{winner} ({winner.id})' for winner in winners])} won the giveaway.",
                                            url=f"https://discord.com/channels/{guild.id}/{channel.id}/{giveaway.get('message_id')}",
                                            color=self.client.embed_color, timestamp = discord.utils.utcnow())
                                        try:
                                            #print("DMing host")
                                            await host.send(embed=hostembed)
                                        except:
                                            pass
                        else:
                            pass
                            #print("channel is none")
                    else:
                        pass
                        #print("guild is none")
                     #print("clearing data in database")
                    await self.client.pool_pg.execute("UPDATE giveaways SET active = $2 WHERE message_id = $1", giveaway.get("message_id"), False)
            else:
                return
        except Exception as e:
            embed = discord.Embed(title="Error in giveaways", description=f"```py\n{e}\n```", color=self.client.embed_color)
            await self.client.get_channel(871737028105109574).send(embed=embed)


    class RoleFlags(commands.FlagConverter, case_insensitive=True, delimiter=' ', prefix='--'):
        channel: typing.Optional[discord.TextChannel]
        time: typing.Optional[str]
        prize: typing.Optional[str]
        winner: typing.Optional[str]
        msg: typing.Optional[str]
        noping: typing.Optional[str]


    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name='trophy', aliases=['tro'])
    async def trophy_giveaway(self, ctx, *, flags: RoleFlags):
        """
        Starts a trophy giveaway.

        Available flags:
        `--time <time>` The duration of the giveaway, default is 24 hours.
        `--prize <prize>` The prize for the giveaway, default is <a:dv_iconOwO:837943874973466664> **1 Pepe Trophy**.
        `--winner <number>` Number of winners, default is 1.
        `--msg <msg>` Message accompanied with the ping, default is enter the giveaway above
        `--noping True` If you do not want the bot to ping
        """
        channel = ctx.channel
        if os.getenv('state') == "0" and channel.id not in [630587061665267713, 803039330310029362, 882280305233383474]:
            return await ctx.send("This command can only be used in certain channels.")
        if flags.time is None:
            duration = 86400
        else:
            duration = stringtime_duration(flags.time)
            if duration is None:
                return await ctx.send("You did not provide a valid time.")
        if flags.prize is None:
            prize = "<a:dv_iconOwO:837943874973466664> 1 Pepe Trophy"
        else:
            prize = flags.prize[:127]
        if flags.winner is None:
            winner = 1
        else:
            try:
                winner = int(flags.winner)
            except ValueError:
                return await ctx.send("You did not provide a valid number of winners.")
        if winner < 1:
            return await ctx.send("You must have at least one winner.")
        elif winner > 80:
            return await ctx.send("You cannot have more than 80 winners.")
        if len(prize) > 70:
            return await ctx.send("The prize's name cannot be longer than 70 characters.")
        if flags.msg is not None and len(flags.msg) > 1000:
            return await ctx.send("The message that accompanies the ping cannot be longer than 1000 characters.")
        if duration > 2592000:
            return await ctx.send("The giveaway cannot last longer than 30 days.")
        ends_at = round(time()) + duration
        end_at_datetime = datetime.fromtimestamp(ends_at)
        description = f"Press the button to enter!\nHosted by: {ctx.author.mention}\nDuration: **{humanize_timedelta(seconds=duration)}**\nEnds <t:{ends_at}:F> (<t:{ends_at}:R>)"
        embed = discord.Embed(title=prize, description=description, color=self.client.embed_color, timestamp=end_at_datetime)
        embed.add_field(name="Entrants", value="0")
        if prize == "<a:dv_iconOwO:837943874973466664> 1 Pepe Trophy":
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/718136428219072662.gif")
        embed.set_footer(text=f"{plural(winner):winner} can win this giveaway, which ends at")
        giveawaymessage = await channel.send(embed=discord.Embed(title="<a:DVB_Loading:909997219644604447> Initializing giveaway...", color=self.client.embed_color))
        await self.client.pool_pg.execute("INSERT INTO giveaways VALUES($1, $2, $3, $4, $5, $6, $7, $8)", ctx.guild.id, channel.id, giveawaymessage.id, ends_at, prize, ctx.author.id, winner, True)
        await giveawaymessage.edit(embed=embed, view=GiveawayView(self.client))
        if flags.noping is not None:
            return
        pingrole = 758174135276142593 if os.getenv('state') == '0' else 895815588289581096
        author_said_yes = False
        pingmsg = await ctx.send(f"Do you want to ping <@&{pingrole}>? Say `yes` within **20 seconds** `[0/2]`")
        try:
            msg = await self.client.wait_for('message', timeout=20.0, check=lambda m: not m.author.bot and m.channel == ctx.channel and m.content == 'yes')
        except asyncio.TimeoutError:
            await ctx.send("Two people did not say `yes`. I will not be pinging the role.", delete_after=5.0)
        else:
            await msg.delete()
            if msg.author.id == ctx.author.id:
                author_said_yes = True
            await pingmsg.edit(content=f"Do you want to ping <@&{pingrole}>? Say `yes` within **60 seconds** `[1/2]`")
            try:
                msg = await self.client.wait_for('message', timeout=60.0, check=lambda m: not m.author.bot and m.channel == ctx.channel and m.content == 'yes' and m.author.id != ctx.author.id if author_said_yes else m.author.id == ctx.author.id)
            except asyncio.TimeoutError:
                await ctx.send("Two people did not say `yes`. I will not be pinging the role.", delete_after=5.0)
            else:
                await msg.delete()
                await pingmsg.edit(content=f"Do you want to ping <@&{pingrole}>? Say `yes` within **60 seconds** `[2/2]`", delete_after=2.0)
                if flags.msg is None:
                    if prize == "<a:dv_iconOwO:837943874973466664> 1 Pepe Trophy":
                        additional_message = "Enter the daily trophy giveaway above! <:DVB_Trophy:911244980599804015>"
                    else:
                        additional_message = f"React to the giveaway above ♡"
                else:
                    additional_message = flags.msg
                await ctx.send(f"<@&{pingrole}> {additional_message}", allowed_mentions=discord.AllowedMentions(everyone=False, roles=True, users=True))

    @checks.has_permissions_or_role(administrator=True)
    @commands.group(name="giveaway", aliases=['g'], invoke_without_command=True)
    async def giveaway(self, ctx):
        await ctx.help()

    @checks.has_permissions_or_role(administrator=True)
    @giveaway.command(name="start", aliases=['s'], usage="[duration] [winner] <requirement> [prize]")
    async def giveaway_start(self, ctx):
        """
        Starts a new giveaway.
        """
        return await ctx.send("i'm not really a giveaway bot so here's a youtube video instead <https://www.youtube.com/watch?v=dQw4w9WgXcQ>")

    @checks.has_permissions_or_role(administrator=True)
    @giveaway.command(name="cancel", aliases=['c'])
    async def giveaway_cancel(self, ctx, messasge_ID=None):
        """
        Cancels a giveaway. No winners will be announced.
        """
        return await ctx.send("i'm not really a giveaway bot so here's a youtube video instead <https://www.youtube.com/watch?v=dQw4w9WgXcQ>")

    @checks.has_permissions_or_role(administrator=True)
    @giveaway.command(name="end", aliases=['e'])
    async def giveaway_end(self, ctx, message_ID=None):
        """
        Ends a giveaway earlier than the end time, but winners will be announced.
        """
        return await ctx.send("i'm not really a giveaway bot so here's a youtube video instead <https://www.youtube.com/watch?v=dQw4w9WgXcQ>")

    class BetterMessageID(commands.Converter):
        async def convert(self, ctx, argument):
            if argument is None:
                raise ArgumentBaseError(message="1You need to provide a message link or ID.")
            try:
                return int(argument)
            except ValueError:
                if not (argument.startswith('https') and 'discord.com/channels/' in argument):
                    raise ArgumentBaseError(message="2You did not provide a valid message link or ID. A message link should start with `https://discord.com/channels/`, `https://ptb.discord.com/channels/` or `https://canary.discord.com/channels/`.")
                split = argument.split('/')
                if split[4] == '@me':
                    raise ArgumentBaseError(message="3You provided a message from DMs, I need a message from a channel.")
                else:
                    try:
                        channel_id = int(split[5])
                    except:
                        raise ArgumentBaseError(message="4You did not provide a valid message link or ID. A message link should start with `https://discord.com/channels/`, `https://ptb.discord.com/channels/` or `https://canary.discord.com/channels/`.")
                    channel = ctx.guild.get_channel(channel_id)
                    if channel is None:
                        raise ArgumentBaseError(message="4You did not provide a valid message link or ID.")
                    else:
                        try:
                            message_id = int(split[6])
                            if channel.get_partial_message(message_id) is not None:
                                return message_id
                        except:
                            raise ArgumentBaseError(message="5You did not provide a valid message link or ID.")


    @checks.has_permissions_or_role(administrator=True)
    @giveaway.command(name="reroll", aliases=["r"])
    async def giveaway_reroll(self, ctx, message_ID: BetterMessageID = None, winner: int = None):
        """
        Rerolls a giveaway.
        """
        giveaway = await self.client.pool_pg.fetchrow("SELECT * FROM giveaways WHERE message_id = $1", message_ID)
        if winner is None:
            winnernum = 1
        else:
            winnernum = winner
        if giveaway is None:
            return await ctx.send("I couldn't find a giveaway with that message ID.")
        if giveaway.get('guild_id') != ctx.guild.id:
            return await ctx.send("I couldn't find a giveaway with that message ID.")
        if giveaway.get('time') > time() or giveaway.get('active') == True:
            return await ctx.send("You can't reroll a giveaway that hasn't ended yet 😂🤣")
        entries = await self.client.pool_pg.fetch("SELECT * FROM giveawayentrants WHERE message_id = $1", message_ID)
        winners = []
        while len(winners) != winnernum and len(entries) > 0:
            winner = random.choice(entries)
            if winner.get("user_id") not in winners:
                member = ctx.guild.get_member(winner.get("user_id"))
                if member is not None:
                    winners.append(member)
            entries.remove(winner)
        channel = self.client.get_channel(giveaway.get("channel_id"))
        if len(winners) == 0:
            await channel.send(
                f"I could reroll for a winner from the **{giveaway.get('name')}** giveaway.\nhttps://discord.com/channels/{ctx.guild.id}/{channel.id}/{giveaway.get('message_id')}")
        else:
            message = f"Congratulations, {grammarformat([winner.mention for winner in winners])}! You snagged away **{giveaway.get('name')}** after a reroll!\nhttps://discord.com/channels/{ctx.guild.id}/{channel.id}/{giveaway.get('message_id')}"
            await channel.send(message)


    @checks.has_permissions_or_role(administrator=True)
    @giveaway.command(name="active", aliases = ['a'])
    async def giveaway_active(self, ctx):
        """
        Lists active giveaways.
        """
        giveaways = await self.client.pool_pg.fetch("SELECT * FROM giveaways WHERE guild_id=$1", ctx.guild.id)
        embed = discord.Embed(title="All giveaways", color=self.client.embed_color)
        if len(giveaways) == 0:
            embed.description = "There are no active giveaways."
            return await ctx.send(embed=embed)
        else:
            giveaway_list = []
            for index, giveaway in enumerate(giveaways):
                channel = ctx.guild.get_channel(giveaway.get('channel_id'))
                if channel is None:
                    channel = "Unknown channel"
                message_link = f"https://discord.com/channels/{ctx.guild.id}/{giveaway.get('channel_id')}/{giveaway.get('message_id')}"
                host = self.client.get_user(giveaway.get('host_id'))
                if host is None:
                    host = "Unknown host"
                prize = f"{index+1}. {giveaway.get('name')}"
                description = f"Hosted by **{host.mention if type(host) != str else host}** in **{channel.mention if type(channel) != str else channel}**\nEnds **<t:{giveaway.get('time')}>**\n[Jump to giveaway]({message_link})"
                giveaway_list.append((prize, description))
            if len(giveaway_list) <= 10:
                for giveaway_details in giveaway_list:
                    embed.add_field(name=giveaway_details[0], value=giveaway_details[1], inline=False)
                return await ctx.send(embed=embed)
            else:
                pages = CustomMenu(source=GiveawayList(giveaway_list, embed.title), clear_reactions_after=True, timeout=60)
                return await pages.start(ctx)

    def cog_unload(self):
        self.end_giveaways.stop()