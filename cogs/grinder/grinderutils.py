import asyncio
import os
import aiohttp
import discord
from typing import Optional
from main import dvvt
from utils.menus import CustomMenu
from discord import Webhook
from discord.ext import commands, menus
from utils import checks
import re
import time
from utils.format import comma_number, stringnum_toint, proper_userf
from utils.buttons import confirm
from utils.converters import BetterInt
from datetime import datetime, timedelta

from utils.specialobjects import DankItem

guildid = 871734809154707467 if os.getenv('state') == '1' else 595457764935991326
grinderteamID = 896052592797417492 if os.getenv('state') == '1' else 827270880182009956
grinder5mID = 896052612284166204 if os.getenv('state') == '1' else 859494328422367273
grinder3mroleID = 931905577473409174 if os.getenv('state') == '1' else 931172654696788010
argon = 650647680837484556
donochannel = 871737314831908974 if os.getenv('state') == '1' else 862574856846704661
logchannel = 871737332431216661 if os.getenv('state') == '1' else 896693789312319508
holder = 827080569501777942 if os.getenv('state') == '1' else 798238834340528149
grinderlogID = 896068443093229579 if os.getenv('state') == '1' else 862433139921911809
webhook_url = 'https://canary.discord.com/api/webhooks/932261660322832415/gSkRlKsA1wtHHQxU0TGt_eTIzcPysnZ5G-yiaEXHMQlkAODYg9YboU_9sEIZghysIdB4' if os.getenv('state') == '1' else 'https://discord.com/api/webhooks/922933444370104330/DxlVMQ7rxdk__R6Ej8SPWpaTXWprKcUVb606Hfo91PvFnA-5xXdMi3RuyQdIngZdU3Rf'
server_coin_donate_re = re.compile(r"> You will donate \*\*\u23e3 ([\d,]*)\*\*")
server_item_donate_re = re.compile(r"\*\*(.*)\*\*")


class GrinderLeaderboard(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=menu.ctx.bot.embed_color, timestamp=discord.utils.utcnow())
        for entry in entries:
            embed.add_field(name=f"{entry[0]}", value=f"**⏣ {comma_number(entry[1])}**", inline=False)
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed

class Grinderutils(commands.Cog, name='grinderutils'):
    """
    GrinderUtils commands
    """
    def __init__(self, client):
        self.client: dvvt = client
        self.waitlist = []
        #self.daily_owo_reset.start()

    async def get_donation_count(self, member: discord.Member, category: str):
        """
        Gets the donation count for a user in a category.
        """
        result = await self.client.db.fetchval("SELECT value FROM donations.{} WHERE user_id = $1".format(f"guild{member.guild.id}_{category.lower()}"), member.id)
        if result is None:
            return 0
        else:
            return result

    def cog_unload(self):
        pass
        #self.daily_owo_reset.stop()

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
                embed.add_field(name=f"#{index} {position[0]}", value=f"**⏣ {comma_number(position[1])}**", inline=False)
            return embed
        ranks = []
        for index, position in enumerate(leaderboard, 1):
            ranks.append((f"#{index} {position[0]}", position[1]))
        return ranks

    def is_3m_grinder(self, member):
        if discord.utils.get(member.roles, id=grinder3mroleID) is not None:
            return True
        return False

    def is_5m_grinder(self, member):
        if discord.utils.get(member.roles, id=grinder5mID) is not None:
            return True
        return False

    def is_trial_grinder(self, member):
        if discord.utils.get(member.roles, id=grinderteamID) is not None:
            return True

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='grindercheck', usage='[member]', aliases=['gcheck', 'gc'])
    async def grindercheck(self, ctx, member: discord.Member = None):
        """
        Shows you or a member's grinder statistics.
        """
        if member is None:
            member = ctx.author
        if ctx.author.id not in [argon] and ctx.author.guild_permissions.manage_roles != True:
            member = ctx.author
        result = await self.client.db.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", member.id)
        embed = discord.Embed(color=self.client.embed_color, timestamp=discord.utils.utcnow())
        tier = "5M Grinder" if self.is_5m_grinder(member) else "3M Grinder" if self.is_3m_grinder(member) else "Trial Grinder (3M/5M)" if self.is_trial_grinder(member) else None
        tier = "**" + tier + "**" if tier is not None else None
        tier = f"Tier: {tier}\n" if tier is not None else None
        if ctx.author.guild_permissions.manage_roles:
            in_advance = f"`⏣ {comma_number(result.get('advance_amt'))}`" if result and result.get('advance_amt') is not None else "`⏣ 0`"
            embed.add_field(name='Grinder contributions', value=f"{tier or ''}Today: `⏣ {comma_number(result.get('today')) if result else 0}` \nThis Week: `⏣ {comma_number(result.get('past_week')) if result else 0}`\nLast Week: `⏣ {comma_number(result.get('last_week')) if result else 0}`\nThis Month: `⏣ {comma_number(result.get('past_month')) if result else 0}`\nAll Time: `⏣ {comma_number(result.get('all_time')) if result else 0}`\nAdvance Balance: {in_advance}", inline=True)
        else:
            embed.add_field(name='Grinder contributions', value=f"{tier or ''}Today: `⏣ {comma_number(result.get('today')) if result else 0}` \nThis Week: `⏣ {comma_number(result.get('past_week')) if result else 0}`\nLast Week: `⏣ {comma_number(result.get('last_week')) if result else 0}`\nThis Month: `⏣ {comma_number(result.get('past_month')) if result else 0}`\nAll Time: `⏣ {comma_number(result.get('all_time')) if result else 0}`", inline=True)
        embed.add_field(name='Last Logged', value=f"<t:{result.get('last_dono_time')}>\n[Jump to logged message]({result.get('last_dono_msg')})" if result else "[<t:0>](https://www.youtube.com/watch?v=dQw4w9WgXcQ)", inline=True)
        if self.is_5m_grinder(member):
            if result and result.get('today') >= 35000000:
                value = f"<:DVB_True:887589686808309791> Yes"
            else:
                value = f"<:DVB_False:887589731515392000> No\nTo complete your requirement, you have to send `⏣ {comma_number(35000000 - result.get('today') if result else 35000000)}` to {self.client.get_user(holder)}."
        elif self.is_3m_grinder(member):
            if result and result.get('today') >= 21000000:
                value = f"<:DVB_True:887589686808309791> Yes"
            else:
                value = f"<:DVB_False:887589731515392000> No\nTo complete your requirement, you have to send `⏣ {comma_number(21000000 - result.get('today') if result else 21000000)}` to {self.client.get_user(holder)}."
        elif self.is_trial_grinder(member):
            if result and result.get('today') >= 21000000:
                if result.get('today') >= 5000000:
                    value = f"<:DVB_True:887589686808309791> Yes"
                else:
                    value = f"<:DVB_True:887589686808309791> Yes **if on 3M Tier**"
            else:
                value=f"<:DVB_False:887589731515392000> No\nTo complete your requirement, you have to send `⏣ {comma_number(35000000-result.get('today') if result else 35000000)}`, or `⏣ {comma_number(21000000-result.get('today') if result else 21000000)}` (if you're on the 3M Tier) to {self.client.get_user(holder)}."
        else:
            value = "You are not a Grinder."
        embed.add_field(name='Has fulfilled requirement?', value=value, inline=False)
        total = await self.client.db.fetchrow("SELECT SUM(all_time) FROM grinderdata")
        embed.set_footer(text=f"A total ⏣ {comma_number(int(total.get('sum')))} grinded so far! · {ctx.guild.name}")
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @checks.is_bav_or_mystic()
    @commands.command(name="glog")
    async def grinder_log(self, ctx, member: discord.Member = None, number: BetterInt = None):
        """
            Adds or removes a certain amount of coins from a grinder's data. To change it to a specific amount, use `gset` instead.
        """
        if member is None or number is None:
            return await ctx.send("The correct usage of this command is `glog [member] [amount to add]`.")
        if number is None:
            return await ctx.send("There was a problem converting your requested sum to a number. You might have input an incorrect number.")
        result = await self.client.db.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", member.id)
        if result is None:
            await self.client.db.execute("INSERT INTO grinderdata VALUES($1, $2, $3, $4, $5, $6, $7, $8)",
                                              member.id, number, number, 0, number, number, round(time.time()),
                                              ctx.message.jump_url)
            today = number
        else:
            today = await self.client.db.fetchval(
                "UPDATE grinderdata SET today = $1, past_week = $2, last_week = $3, past_month = $4, all_time = $5, last_dono_time = $6, last_dono_msg = $7 WHERE user_id = $8 RETURNING today",
                result.get('today') + number, result.get('past_week') + number, result.get('last_week'),
                result.get('past_month') + number, result.get('all_time') + number, round(time.time()),
                ctx.message.jump_url, member.id, column='today')
        await ctx.send(f"<:DVB_checkmark:955345523139805214> `⏣ {comma_number(number)}` successfully logged for **{proper_userf(member)}** ({member.id})!\nNew value: `⏣ {comma_number(today)}`")
        add_donations_cmd = self.client.get_command('adddonations')
        ctx = await self.client.get_context(ctx.message)
        ctx.author = ctx.guild.get_member(264019387009204224)
        await add_donations_cmd(ctx, member=member, amount=number, category_name='dank')


    @checks.is_bav_or_mystic()
    @commands.command(name="gedit")
    async def grinder_edit(self, ctx, member: discord.Member = None, number: BetterInt = None):
        """
            Adds or removes a certain amount of coins from a grinder's data. To change it to a specific amount, use `gset` instead.
        """
        if member is None or number is None:
            return await ctx.send("The correct usage of this command is `gedit [member] [amount to add]`.")
        if number is None:
            return await ctx.send("There was a problem converting your requested sum to a number. You might have input an incorrect number.")
        confirmview = confirm(ctx, self.client, 10.0)
        embed = discord.Embed(title="Action awaiting confirmation", description=f"Do you want this amount to be added to {proper_userf(member)}'s daily, weekly and monthly stats? Otherwise, it will only be added in 'all time'.", color=self.client.embed_color)
        message = await ctx.send(embed=embed, view=confirmview)
        confirmview.response = message
        await confirmview.wait()
        if confirmview.returning_value is None:
            embed.color, embed.description = discord.Color.red(), "Action timeout. Nothing has been done."
            return await message.edit(embed=embed)
        result = await self.client.db.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", member.id)
        if confirmview.returning_value == False:
            embed.color, embed.description = discord.Color.green(), f"{proper_userf(member)}'s grinder statistics has been updated for **all time**. "
            if result is None:
                await self.client.db.execute("INSERT INTO grinderdata VALUES($1, $2, $3, $4, $5, $6, $7, $8)", member.id, 0, 0, 0, 0, number, round(time.time()), ctx.message.jump_url)
            else:
                await self.client.db.execute("UPDATE grinderdata SET all_time = $1, last_dono_time = $2, last_dono_msg = $3 WHERE user_id = $4", result.get('all_time') + number, round(time.time()), ctx.message.jump_url, member.id)
            await message.edit(embed=embed)
        elif confirmview.returning_value == True:
            embed.color, embed.description = discord.Color.green(), f"All of {proper_userf(member)}'s grinder statistics has been updated."
            if result is None:
                await self.client.db.execute("INSERT INTO grinderdata VALUES($1, $2, $3, $4, $5, $6, $7, $8)", member.id, number, number, 0, number, number, round(time.time()), ctx.message.jump_url)
            else:
                await self.client.db.execute("UPDATE grinderdata SET today = $1, past_week = $2, last_week = $3, past_month = $4, all_time = $5, last_dono_time = $6, last_dono_msg = $7 WHERE user_id = $8", result.get('today') + number, result.get('past_week') + number, result.get('last_week'), result.get('past_month') + number, result.get('all_time') + number, round(time.time()), ctx.message.jump_url, member.id)
            await message.edit(embed=embed)
        add_donations_cmd = self.client.get_command('adddonations')
        ctx = await self.client.get_context(ctx.message)
        ctx.author = ctx.guild.get_member(264019387009204224)
        await add_donations_cmd(ctx, member=member, amount=number, category_name='dank')

    @checks.is_bav_or_mystic()
    @commands.command(name="gset")
    async def grinder_set(self, ctx, member: discord.Member = None, number: BetterInt = None):
        """
        Sets the coins a grinder has donated to a specific amount. To add or remove coins, use `gedit` instead.
        """
        if member is None or number is None:
            return await ctx.send("The correct usage of this command is `gset [member] [amount to add]`.")
        if number is None:
            return await ctx.send("There was a problem converting your requested sum to a number. You might have input an incorrect number.")
        confirmview = confirm(ctx, self.client, 10.0)
        embed = discord.Embed(title="Action awaiting confirmation", description=f"Do you want {proper_userf(member)}'s all time coins donated to be `⏣ {comma_number(number)}`? This will not change their daily, weekly and monthly statistics (to ensure consistency accross the data).", color=self.client.embed_color)
        message = await ctx.send(embed=embed, view=confirmview)
        confirmview.response = message
        await confirmview.wait()
        if confirmview.returning_value is None:
            embed.color, embed.description = discord.Color.red(), "Action timeout. Nothing has been done."
            return await message.edit(embed=embed)
        result = await self.client.db.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", member.id)
        if confirmview.returning_value == False:
            embed.color, embed.description = discord.Color.red(), f"Action cancelled."
            return await message.edit(embed=embed)
        elif confirmview.returning_value == True:
            embed.color, embed.description = discord.Color.green(), f"All of {proper_userf(member)}'s grinder statistics has been updated. BTW, I did not automatically add them to the Dank Memer weekly donation leaderboard."
            if result is None:
                await self.client.db.execute("INSERT INTO grinderdata VALUES($1, $2, $3, $4, $5, $6, $7, $8)", member.id, 0, 0, 0, 0, number, round(time.time()), ctx.message.jump_url)
            else:
                await self.client.db.execute("UPDATE grinderdata SET all_time = $1, last_dono_time = $2, last_dono_msg = $3 WHERE user_id = $4", number, round(time.time()), ctx.message.jump_url, member.id)
            await message.edit(embed=embed)


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != 270904126974590976 or len(message.embeds) == 0 or message.channel.id != donochannel or message.reference is None:
            return
        embed = message.embeds[0]
        if type(embed.description) == str and "Successfully donated!" in embed.description:
            m_reference = message.reference
            if m_reference.cached_message is None:
                original_message = await message.channel.fetch_message(m_reference.channel_id)
            else:
                original_message = m_reference.cached_message
            coins, item_count, item = None, None, None
            member = original_message.interaction.user
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
                    if coins is not None:
                        amt = coins
                    else:
                        if item.name != "Pepe Trophy":
                            return await message.channel.send(f"⚠️ {member.mention}, only **Pepe Trophies** are accepted as grinder donations.")
                        else:
                            amt = item_count * item.trade_value
                    member = message.guild.get_member(member.id)
                    if not (discord.utils.get(member.roles, id=grinderteamID) or discord.utils.get(member.roles, id=grinder3mroleID) or discord.utils.get(member.roles, id=grinder5mID)):
                        return await message.channel.send("You don't have the required roles or the roles declared are invalid.")
                    result = await self.client.db.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", member.id)
                    if result is None:
                        await self.client.db.execute("INSERT INTO grinderdata VALUES($1, $2, $3, $4, $5, $6, $7, $8)", member.id, amt, amt, 0, amt, amt, round(time.time()), message.jump_url)
                    else:
                        await self.client.db.execute("UPDATE grinderdata SET today = $1, past_week = $2, past_month = $3, all_time = $4, last_dono_time = $5, last_dono_msg = $6 WHERE user_id = $7", result.get('today') + amt, result.get('past_week') + amt, result.get('past_month') + amt, result.get('all_time') + amt, round(time.time()), message.jump_url, member.id)
                    total = await self.client.db.fetchrow("SELECT SUM(all_time) FROM grinderdata")
                    logembed = discord.Embed(description=f"**Grinder**: {member.mention}\n**Amount**: `⏣ {comma_number(amt)}`\nClick [here]({message.jump_url}) to view.\n`⏣ {comma_number(int(total.get('sum')))}` total grinded by grinders!", color=self.client.embed_color, timestamp=discord.utils.utcnow())
                    logembed.set_footer(text=f"{message.guild.name} Grinder Log", icon_url=message.guild.icon.url)
                    await self.client.get_channel(grinderlogID).send(f"A grinder transaction by `{proper_userf(member)} ({member.id})` has been logged.", embed=logembed)
                    chan_msgs = [f"{member.mention}, your donation of **⏣ {comma_number(amt)}** has been logged. Thank you for your contributions to Dank Vibes!"]
                    add_donations_cmd = self.client.get_command('adddonations')
                    ctx = await self.client.get_context(message)
                    ctx.author = message.guild.get_member(264019387009204224)
                    await add_donations_cmd(ctx, member=member, amount=amt, category_name='dank')
                    if result is None:
                        old = 0
                    else:
                        old = result.get('today')
                    if old + amt < 21000000:
                        chan_msgs.append(f"\nNote: You are still **⏣ {comma_number(21000000 - old - amt)}** away from completing the minimum Grinder Tier (3M).")
                    await message.channel.send("\n".join(chan_msgs))
                    if old + amt >= 21000000:
                        has_completed_3m = True
                    else:
                        has_completed_3m = False
                    if old + amt >= 35000000:
                        has_completed_5m = True
                    else:
                        has_completed_5m = False
                    if has_completed_3m == True:
                        if has_completed_5m is not True:
                            msg = f"<:DVB_True:887589686808309791> **You have qualified for the 3M Grinder Tier!**\nThe **3M Grinder Tier role** has been assigned to you. You can now enjoy your perks! <3\n\nYou can still qualify for the **5M Grinder Tier** by donating another **⏣ {comma_number(35000000 - old - amt)}**."
                        else:
                            msg = f"<:DVB_True:887589686808309791> **You have qualified for both the 3M and 5M Grinder Tier!**\nBoth the **3M Grinder Tier** and **5M Grinder Tier** role has been assigned to you. You can now enjoy your perks! <3"
                        try:
                            await member.send(msg)
                        except:
                            await message.channel.send(f"{member.mention} {msg}")
                    currentcount = await self.get_donation_count(member, 'dank')
                    amount = amt
                    QUERY = "INSERT INTO donations.{} VALUES ($1, $2) ON CONFLICT(user_id) DO UPDATE SET value=$2 RETURNING value".format(f"guild{message.guild.id}_dank")
                    await self.client.db.execute(QUERY, member.id, amount + currentcount)

    @checks.is_bav_or_mystic()
    @commands.command(name="gdm", brief="Reminds DV Grinders that the requirement has been checked.", description="Reminds DV Grinders that the requirement has been checked.")
    async def gdm(self, ctx):
        """
        Reminds DV Grinders that the requirement has been checked.
        """
        grinderrole = ctx.guild.get_role(grinder5mID)
        grinder3mrole = ctx.guild.get_role(grinder3mroleID)
        tgrinderrole = ctx.guild.get_role(grinderteamID)
        if grinderrole is None or tgrinderrole is None:
            return await ctx.send("One or more roles declared in this command are invalid, hence the command cannot proceed.")
        grinders = [member for member in ctx.guild.members if (grinderrole in member.roles or tgrinderrole in member.roles or grinder3mrole in member.roles)]  # gets all grinders if not grinders:
        if len(grinders) == 0:
            return await ctx.send("There are no grinders to be DMed.")
        confirmview = confirm(ctx, self.client, 15.0)
        grinders = [member for member in ctx.guild.members if self.is_5m_grinder(member) or self.is_3m_grinder(member) or self.is_trial_grinder(member)]
        embed = discord.Embed(title="DM Grinders?", description=f"I will be checking the grinder requirement for the {len(grinders)} grinders and trial grinders, and I'll send a summary to <#{logchannel}>. Afterwards, I'll DM them to update them about the grinder check. Are you sure?", color=self.client.embed_color)
        message = await ctx.send(embed=embed, view=confirmview)
        confirmview.response = message
        await confirmview.wait()
        if confirmview.returning_value is None:
            embed.description = "Action cancelled."
            embed.color = discord.Color.red()
            return await message.edit(content="You didn't click a button on time. Do you know how to click buttons?", embed=embed)
        if confirmview.returning_value == False:
            embed.description = "Action cancelled."
            embed.color = discord.Color.red()
            return await message.edit(content="Command stopped.", embed=embed)
        if confirmview.returning_value == True:
            msg = await ctx.send("""
<:DVB_start_incomplete:895172799981817938> <a:DVB_typing:955345484648710154> **Checking daily requirement** 
<:DVB_middle_incomplete:895172800430620742> Updating statistics 
<:DVB_end_incomplete:895172799923109919> Notifying grinders and sending a summary""")
            completed_req = []
            not_complete = []
            for grinder in grinders:
                result = await self.client.db.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", grinder.id)
                if result is None:
                    await self.client.db.fetchrow("INSERT INTO grinderdata(user_id, today, past_week, last_week, past_month, all_time, last_dono_time, last_dono_msg, advance_amt) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)", grinder.id, 0, 0, 0, 0, 0, 0, "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 0)
                    result = await self.client.db.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", grinder.id)
                today = result.get('today') or 0
                if self.is_5m_grinder(grinder):
                    if today < 35000000:
                        not_complete.append((grinder, today, result, 35000000, ""))
                    else:
                        completed_req.append((grinder, today, ""))
                elif self.is_3m_grinder(grinder):
                    if today < 21000000:
                        not_complete.append((grinder, today, result, 21000000, ""))
                    else:
                        completed_req.append((grinder, today, ""))
                elif self.is_trial_grinder(grinder):
                    if today < 21000000:
                        not_complete.append((grinder, today, result, 21000000, ""))
                    else:
                        completed_req.append((grinder, today, ""))
            if len(not_complete) > 0:
                copied_not_complete = not_complete.copy()
                for tup in copied_not_complete:
                    grinder, today, result, req, desc = tup
                    uncompleted = req - today
                    available_funds = result.get('advance_amt') or 0
                    if req == uncompleted:
                        if available_funds >= uncompleted:
                            remaining = await self.client.db.fetchval("UPDATE grinderdata SET advance_amt = advance_amt - $1 WHERE user_id = $2 RETURNING advance_amt", uncompleted, grinder.id, column='advance_amt')
                            not_complete.remove(tup)
                            completed_req.append((grinder, uncompleted, f"Deduct from advance funds, ⏣ {comma_number(remaining)} remaining"))
                        elif available_funds > 0:
                            remaining = await self.client.db.fetchval("UPDATE grinderdata SET advance_amt = 0 WHERE user_id = $1 RETURNING advance_amt", grinder.id, column='advance_amt')
                            still_uncompleted = req - available_funds
                            not_complete.remove(tup)
                            not_complete.append((grinder, still_uncompleted, result, req, f"Deduct from advance funds, ⏣ {comma_number(remaining)} remaining"))
                        else:
                            continue




            await msg.edit(content="""
<:DVB_start_complete:895172800627769447> Checking daily requirement 
<:DVB_middle_incomplete:895172800430620742> <a:DVB_typing:955345484648710154> **Updating statistics** 
<:DVB_end_incomplete:895172799923109919> Notifying grinders and sending a summary""")
            reset_week = True
            week_values = []
            all = await self.client.db.fetch("SELECT user_id, past_week FROM grinderdata")
            if all is not None:
                for a in all:
                    week_values.append((0, 0, a.get('past_week'), a.get('user_id')))
            await self.client.db.executemany("UPDATE grinderdata SET today = $1, past_week = $2, last_week = $3 WHERE user_id = $4", week_values)
            await msg.edit(content="""
<:DVB_start_complete:895172800627769447> Checking daily requirement 
<:DVB_middle_complete:895172800627769444> Updating statistics
<:DVB_end_incomplete:895172799923109919> <a:DVB_typing:955345484648710154> **Notifying grinders and sending a summary**""")
            now = discord.utils.utcnow()
            thursday = now + timedelta(days=3 - now.weekday())
            thursday = thursday.replace(hour=7, minute=0, second=0)
            if thursday < now:
                thursday += timedelta(weeks=1)
            timestamp = f"<t:{round(thursday.timestamp())}>"
            embed = discord.Embed(title="DV Grinders Team",
                                  description=f"<a:dv_pointArrowOwO:837656328482062336> The weekly grinder requirement has been checked.\n<a:dv_pointArrowOwO:837656328482062336> <#862574856846704661> is now unlocked and you may send the cash (21M/35M) or 1 Trophy to `{ctx.author}`.\n<a:dv_pointArrowOwO:837656328482062336> The next requirement check will take place at {timestamp}.",
                                  color=self.client.embed_color)
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/595457764935991326/a_58b91a8c9e75742d7b423411b0205b2b.gif")
            embed.set_footer(text="DM/Ping Ari#0005 if you have any queries.", icon_url=ctx.guild.icon.url)
            success = 0  # gets the grinder list again since the earlier one was popped
            faileddms = []
            for grinder in grinders:
                try:
                    await grinder.send(f"Hello {grinder.name}! I have a message for you:", embed=embed)  # hehe
                    success += 1
                except discord.Forbidden:
                    faileddms.append(grinder.mention)  # gets list of people who will be pinged later"""
            if faileddms:
                channel = self.client.get_channel(donochannel)
                await channel.send(''.join(faileddms), embed=embed)
            content = ''
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhook_url, session=session)
                reportchannel = self.client.get_channel(logchannel)
                await reportchannel.send(f"**__DV GRINDERS SUMMARY__** (for **{discord.utils.utcnow().strftime('%A, %d %B %Y')}**)")
                await webhook.send(f"**__DV GRINDERS SUMMARY__** (for **{discord.utils.utcnow().strftime('%A, %d %B %Y')}**)", username=self.client.user.name, avatar_url=ctx.me.display_avatar.url)

                def generate_tier_label(grinder_user):
                    return '5' if self.is_5m_grinder(grinder_user) else '3' if self.is_3m_grinder(grinder_user) else 'T' if self.is_trial_grinder(grinder_user) else 'U'

                def add_text_to_content(data_tuple):
                    initial_text = f"\n`{generate_tier_label(data_tuple[0])}` <:DVB_True:887589686808309791> **{dat[0]}** sent `⏣ {comma_number(data_tuple[1])}`"
                    if data_tuple[2] != "":
                        initial_text += f" ({data_tuple[2]})"
                    return initial_text

                for dat in completed_req:
                    if len(content) < 1800:
                        content += add_text_to_content(dat)
                    else:
                        await reportchannel.send(content)
                        await webhook.send(content, username=self.client.user.name, avatar_url=ctx.me.display_avatar.url)
                        content = add_text_to_content(dat)

                def add_text_to_content(data_tuple):
                    initial_text = f"\n`{generate_tier_label(data_tuple[0])}` <:DVB_False:887589731515392000> **{dat[0]}** sent `⏣ {comma_number(data_tuple[1])}`"
                    if data_tuple[4] != "":
                        initial_text += f" ({data_tuple[4]})"
                    return initial_text


                for dat in not_complete:
                    if len(content) < 1800:
                        content += add_text_to_content(dat)
                    else:
                        await reportchannel.send(content)
                        await webhook.send(content, username=self.client.user.name, avatar_url=ctx.me.display_avatar.url)
                        content = add_text_to_content(dat)
                        await reportchannel.send(content)
                await reportchannel.send(content)
                await webhook.send(content, username=self.client.user.name, avatar_url=ctx.me.display_avatar.url)
                await reportchannel.send(f"Total grinded today: {comma_number(sum([dat[1] for dat in completed_req] + [dat[1] for dat in not_complete]))}")
                await webhook.send(f"Total grinded today: {comma_number(sum([dat[1] for dat in completed_req] + [dat[1] for dat in not_complete]))}", username=self.client.user.name, avatar_url=ctx.me.display_avatar.url)
            await msg.edit(content=f"""
<:DVB_start_complete:895172800627769447> Checking daily requirement 
<:DVB_middle_complete:895172800627769444> Updating statistics
<:DVB_end_complete:895172800082509846> Notifying grinders and sending a summary
Done! Note: People who **did not** complete the req won't be told they didn't complete it. Otherwise, I would've told them that they had completed the req.\n{'Additionally, the weekly statistics has been reset.' if reset_week else ''}""")

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='grinderleaderboard', aliases=['glb', 'grinderlb'])
    async def grinderleaderboard(self, ctx, *, arg: str = None):
        """
        Shows the Grinder leaderboard for Dank Vibes.

        `dv.grinderleaderboard daily` for today's Grinder leaderboard.
        `dv.grinderleaderboard weekly` for this week's Grinder leaderboard.
        `dv.grinderleaderboard last week` for last week's Grinder leaderboard
        `dv.grinderleaderboard monthly` for this month's Grinder leaderboard.

        You can also specify how many grinders you want to show on the leaderboard.
        """
        async with ctx.typing():
            arg = "total 5" if arg is None else arg
            number = [int(i) for i in arg.split() if i.isdigit()]
            top = 5 if len(number) == 0 else number[0]
            if 'daily' in arg.lower() or 'today' in arg.lower():
                title = "Today's Grinder leaderboard"
                query = "SELECT user_id, today FROM grinderdata ORDER BY today DESC LIMIT $1"
            elif 'last week' in arg.lower():
                title = "Last week's Grinder leaderboard"
                query = "SELECT user_id, last_week FROM grinderdata ORDER BY last_week DESC LIMIT $1"
            elif 'weekly' in arg.lower() or 'week' in arg.lower():
                title = "This week's Grinder leaderboard"
                query = "SELECT user_id, past_week FROM grinderdata ORDER BY past_week DESC LIMIT $1"
            elif 'monthly' in arg.lower():
                title = "This Month's Grinder leaderboard"
                query = "SELECT user_id, past_month FROM grinderdata ORDER BY past_month DESC LIMIT $1"
            else:
                title = f"Grinder Leaderboard for {ctx.guild.name}"
                query = "SELECT user_id, all_time FROM grinderdata ORDER BY all_time DESC LIMIT $1"
            leaderboard = await self.get_leaderboard(ctx.guild, query, top)
            if isinstance(leaderboard, discord.Embed):
                leaderboard.title = title
                return await ctx.send(embed=leaderboard)
            else:
                pages = CustomMenu(source=GrinderLeaderboard(leaderboard, title), clear_reactions_after=True, timeout=60)
                return await pages.start(ctx)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='grinderpaymentinadvance', aliases=['gpia', 'pia'])
    async def grinderpaymentinadvance(self, ctx, member: discord.Member = None, *, amount: BetterInt = None):
        """
        Sets the payout for a user.
        """
        if member is None:
            return await ctx.send("Please specify a user.")
        if amount is None:
            return await ctx.send("Please specify an amount.")
        current = await self.client.db.fetchrow("SELECT advance_amt FROM grinderdata WHERE user_id = $1", member.id)
        if current is None:
            old_amt = 0
            amt = await self.client.db.fetchval("INSERT INTO grinderdata (user_id, advance_amt) VALUES ($1, $2) RETURNING advance_amt", member.id, amount, column='advance_amt')
            new_amt = amt
        else:
            old_amt = current.get('advance_amt') or 0
            new_amt = old_amt + amount
            await self.client.db.execute("UPDATE grinderdata SET advance_amt = $1 WHERE user_id = $2", new_amt, member.id)
        embed = discord.Embed(title=f"Summary for {proper_userf(member)}'s In Advance statistics", description=f"Old Amount: `⏣ {comma_number(old_amt)}`\nNew Amount: `⏣ {comma_number(new_amt)}` (+ ⏣ {comma_number(amount)})", color=discord.Color.green())
        await ctx.send(embed=embed)