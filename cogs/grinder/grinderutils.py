import asyncio
import os
import aiohttp
import discord
from typing import Optional
from utils.menus import CustomMenu
from discord import Webhook
from discord.ext import commands, menus
from utils import checks
import re
import time
from utils.format import comma_number, stringnum_toint
from utils.buttons import confirm
from datetime import datetime
guildid = 871734809154707467 if os.getenv('state') == '1' else 595457764935991326
tgrinderroleID = 896052592797417492 if os.getenv('state') == '1' else 827270880182009956
grinderroleID = 896052612284166204 if os.getenv('state') == '1' else 859494328422367273
argon = 650647680837484556
donochannel = 871737314831908974 if os.getenv('state') == '1' else 862574856846704661
logchannel = 871737332431216661 if os.getenv('state') == '1' else 896693789312319508
holder = 827080569501777942 if os.getenv('state') == '1' else 798238834340528149
grinderlogID = 896068443093229579 if os.getenv('state') == '1' else 862433139921911809
webhook_url = 'https://canary.discord.com/api/webhooks/896095030970818622/kI5DdgTRxbfkDS-xdoULPpDqan1nDpRexe6g8D4K5c-Dw5Rn-RLKyUBRCkesLhBwgO_p' if os.getenv('state') == '1' else 'https://discord.com/api/webhooks/922933444370104330/DxlVMQ7rxdk__R6Ej8SPWpaTXWprKcUVb606Hfo91PvFnA-5xXdMi3RuyQdIngZdU3Rf'

class MessageFlag(commands.FlagConverter, case_insensitive = True, delimiter = ' ', prefix='--'):
    msg : Optional[str]


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
        self.client = client
        self.waitlist = []
        #self.daily_owo_reset.start()

    def cog_unload(self):
        pass
        #self.daily_owo_reset.stop()

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
                embed.add_field(name=f"#{index} {position[0]}", value=f"**⏣ {comma_number(position[1])}**", inline=False)
            return embed
        ranks = []
        for index, position in enumerate(leaderboard, 1):
            ranks.append((f"#{index} {position[0]}", position[1]))
        return ranks

    @commands.command(name='grindercheck', usage='[member]', aliases=['gcheck', 'gc'])
    async def grindercheck(self, ctx, member: discord.Member = None):
        """
        Shows your or a member's grinder statistics.
        """
        if member is None:
            member = ctx.author
        if ctx.author.id not in [argon] and ctx.author.guild_permissions.manage_roles != True:
            member = ctx.author
        if not (ctx.author.id == argon or ctx.author.guild_permissions.manage_roles==True or discord.utils.get(ctx.author.roles, id=grinderroleID) or discord.utils.get(ctx.author.roles, id=tgrinderroleID) or ctx.author.id in [argon]):
            return await ctx.send("You need to be a **Grinder**/**Trial Grinder** to use this command.")
        result = await self.client.pool_pg.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", member.id)
        embed = discord.Embed(color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.add_field(name='Grinder contributions', value=f"Today: `⏣ {comma_number(result.get('today')) if result else 0}` \nThis Week: `⏣ {comma_number(result.get('past_week')) if result else 0}`\nLast Week: `⏣ {comma_number(result.get('last_week')) if result else 0}`\nThis Month: `⏣ {comma_number(result.get('past_month')) if result else 0}`\nAll Time: `⏣ {comma_number(result.get('all_time')) if result else 0}`", inline=True)
        embed.add_field(name='Last Logged', value=f"<t:{result.get('last_dono_time')}>\n[Jump to logged message]({result.get('last_dono_msg')})" if result else "[<t:0>](https://www.youtube.com/watch?v=dQw4w9WgXcQ)", inline=True)
        embed.add_field(name='Has fulfilled requirement?', value='<:DVB_True:887589686808309791> Yes' if (result and result.get('today') >= 5000000) else f"<:DVB_False:887589731515392000> No\nTo complete your requirement, you have to send `⏣ {comma_number(5000000-result.get('today') if result else 5000000)}` with tax to {self.client.get_user(holder)}.", inline=False)
        total = await self.client.pool_pg.fetchrow("SELECT SUM(all_time) FROM grinderdata")
        embed.set_footer(text=f"A total ⏣ {comma_number(int(total.get('sum')))} grinded so far! · {ctx.guild.name}")
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @checks.is_bav_or_mystic()
    @commands.command(name="gedit")
    async def grinder_edit(self, ctx, member: discord.Member = None, number: str = None):
        """
        Adds or removes a certain amount of coins from a grinder's data. To change it to a specific amount, use `g set` instead.
        """
        if member is None or number is None:
            return await ctx.send("The correct usage of this command is `gedit [member] [amount to add]`.")
        try:
            number = stringnum_toint(number)
        except Exception as e:
            return await ctx.send(e)
        if number is None:
            return await ctx.send("There was a problem converting your requested sum to a number. You might have input an incorrect number.")
        confirmview = confirm(ctx, self.client, 10.0)
        embed = discord.Embed(title="Action awaiting confirmation", description=f"Do you want this amount to be added to {member}'s daily, weekly and monthly stats? Otherwise, it will only be added in 'all time'.", color=self.client.embed_color)
        message = await ctx.send(embed=embed, view=confirmview)
        confirmview.response = message
        await confirmview.wait()
        if confirmview.returning_value is None:
            embed.color, embed.description = discord.Color.red(), "Action timeout. Nothing has been done."
            return await message.edit(embed=embed)
        result = await self.client.pool_pg.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", member.id)
        if confirmview.returning_value == False:
            embed.color, embed.description = discord.Color.green(), f"{member}'s grinder statistics has been updated for **all time**. "
            if result is None:
                await self.client.pool_pg.execute("INSERT INTO grinderdata VALUES($1, $2, $3, $4, $5, $6, $7, $8)", member.id, 0, 0, 0, 0, number, round(time.time()), ctx.message.jump_url)
            else:
                await self.client.pool_pg.execute("UPDATE grinderdata SET all_time = $1, last_dono_time = $2, last_dono_msg = $3 WHERE user_id = $4", result.get('all_time') + number, round(time.time()), ctx.message.jump_url, member.id)
            await message.edit(embed=embed)
        elif confirmview.returning_value == True:
            embed.color, embed.description = discord.Color.green(), f"All of {member}'s grinder statistics has been updated."
            if result is None:
                await self.client.pool_pg.execute("INSERT INTO grinderdata VALUES($1, $2, $3, $4, $5, $6, $7, $8)", member.id, number, number, 0, number, number, round(time.time()), ctx.message.jump_url)
            else:
                await self.client.pool_pg.execute("UPDATE grinderdata SET today = $1, past_week = $2, last_week = $3, past_month = $4, all_time = $5, last_dono_time = $6, last_dono_msg = $7 WHERE user_id = $8", result.get('today') + number, result.get('past_week') + number, result.get('last_week'), result.get('past_month') + number, result.get('all_time') + number, round(time.time()), ctx.message.jump_url, member.id)
            await message.edit(embed=embed)

    @checks.is_bav_or_mystic()
    @commands.command(name="gset")
    async def grinder_set(self, ctx, member: discord.Member = None, number: str = None):
        """
        Sets the coins a grinder has donated to a specific amount. To add or remove coins, use `g edit` instead.
        """
        if member is None or number is None:
            return await ctx.send("The correct usage of this command is `gset [member] [amount to add]`.")
        try:
            number = stringnum_toint(number)
        except Exception as e:
            return await ctx.send(e)
        if number is None:
            return await ctx.send("There was a problem converting your requested sum to a number. You might have input an incorrect number.")
        confirmview = confirm(ctx, self.client, 10.0)
        embed = discord.Embed(title="Action awaiting confirmation", description=f"Do you want {member}'s all time coins donated to be `⏣ {comma_number(number)}`? This will not change their daily, weekly and monthly statistics (to ensure consistency accross the data).", color=self.client.embed_color)
        message = await ctx.send(embed=embed, view=confirmview)
        confirmview.response = message
        await confirmview.wait()
        if confirmview.returning_value is None:
            embed.color, embed.description = discord.Color.red(), "Action timeout. Nothing has been done."
            return await message.edit(embed=embed)
        result = await self.client.pool_pg.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", member.id)
        if confirmview.returning_value == False:
            embed.color, embed.description = discord.Color.red(), f"Action cancelled."
            return await message.edit(embed=embed)
        elif confirmview.returning_value == True:
            embed.color, embed.description = discord.Color.green(), f"All of {member}'s grinder statistics has been updated."
            if result is None:
                await self.client.pool_pg.execute("INSERT INTO grinderdata VALUES($1, $2, $3, $4, $5, $6, $7, $8)", member.id, 0, 0, 0, 0, number, round(time.time()), ctx.message.jump_url)
            else:
                await self.client.pool_pg.execute("UPDATE grinderdata SET all_time = $1, last_dono_time = $2, last_dono_msg = $3 WHERE user_id = $4", number, round(time.time()), ctx.message.jump_url, member.id)
            await message.edit(embed=embed)


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        if message.author.id != 270904126974590976:
            #print('Author is not Dank Memer')
            return
        #if self.client.maintenance.get(self.qualified_name):
            #print('Cog is under maintenance')
            #return
        if not message.guild: # or message.guild.id != 595457764935991326:
            #print('Message is not from a guild')
            return
        if len(message.embeds) == 0:
            return
        if message.channel.id != donochannel:
            #print('not donor channel')
            return
        dankholder = message.guild.get_member(holder)
        msgembed = message.embeds[0]
        if len(msgembed.fields) < 0:
            return
        if not type(msgembed.fields[0].value) == str:
            return
        shared = msgembed.fields[0].value
        shared = shared[3:][:-1].replace(',', '')
        try:
            shared = int(shared)
        except Exception as e:
            return await message.channel.send(f"There was an error converting the shared amount to a number: ```py\n{e}\n```")
        else:
            amt = shared
            if len(message.mentions) > 0:
                member = message.mentions[0]
            else:
                return await message.channel.send("⚠️ **You need to have Reply Pings enabled!** Please inform **Ari#0005** to manually add your grinder statistics, as I was unable to detect who shared the coins.")
            if not (discord.utils.get(member.roles, id=tgrinderroleID) or discord.utils.get(member.roles, id=grinderroleID)):
                return await message.channel.send("You don't have the required roles or the roles declared are invalid.")
            result = await self.client.pool_pg.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", member.id)
            if result is None:
                await self.client.pool_pg.execute("INSERT INTO grinderdata VALUES($1, $2, $3, $4, $5, $6, $7, $8)", member.id, amt, amt, 0, amt, amt, round(time.time()), message.jump_url)
            else:
                await self.client.pool_pg.execute("UPDATE grinderdata SET today = $1, past_week = $2, past_month = $3, all_time = $4, last_dono_time = $5, last_dono_msg = $6 WHERE user_id = $7", result.get('today') + amt, result.get('past_week') + amt, result.get('past_month') + amt, result.get('all_time') + amt, round(time.time()), message.jump_url, member.id)
            total = await self.client.pool_pg.fetchrow("SELECT SUM(all_time) FROM grinderdata")
            logembed = discord.Embed(description=f"**Grinder**: {member.mention}\n**Amount**: `⏣ {comma_number(amt)}`\nClick [here]({message.jump_url}) to view.\n`⏣ {comma_number(int(total.get('sum')))}` total grinded by grinders!", color=self.client.embed_color, timestamp=discord.utils.utcnow())
            logembed.set_footer(text=f"{message.guild.name} Grinder Log", icon_url=message.guild.icon.url)
            await self.client.get_channel(grinderlogID).send(f"A grinder transaction by `{member} ({member.id})` has been logged.", embed=logembed)
            await message.channel.send(f"{member.mention}, I have logged your transfer of **⏣ {comma_number(amt)}** to {dankholder}.")
            if result is None:
                old = 0
            else:
                old = result.get('today')
            if old + amt >= 5000000:
                try:
                    await member.send("<:DVB_True:887589686808309791> You have completed your Grinder requirement for today! I will notify you when you can submit your next ⏣ 5,000,000 again.")
                except:
                    await message.channel.send(f"{member.mention} <:DVB_True:887589686808309791> You have completed your Grinder requirement for today! I will notify you when you can submit your next ⏣ 5,000,000 again.")

    @checks.is_bav_or_mystic()
    @commands.command(name="gdm", brief="Reminds DV Grinders that the requirement has been checked.", description="Reminds DV Grinders that the requirement has been checked.")
    async def gdm(self, ctx, *, flags:MessageFlag):
        """
        Reminds DV Grinders that the requirement has been checked.
        Optional flag:
        `--msg [message]` To add a message when DMing grinders.
        """
        if flags.msg is not None and len(flags.msg) > 2500:
            return await ctx.send("You might have included a message, but it's more than 2500 characters so I cannot send it.")
        grinderrole = ctx.guild.get_role(grinderroleID)
        tgrinderrole = ctx.guild.get_role(tgrinderroleID)
        if grinderrole is None or tgrinderrole is None:
            return await ctx.send("One or more roles declared in this command are invalid, hence the command cannot proceed.")
        grinders = [member for member in ctx.guild.members if grinderrole in member.roles or tgrinderrole in member.roles]  # gets all grinders
        if not grinders:
            return await ctx.send("There are no grinders to be DMed.")
        confirmview = confirm(ctx, self.client, 15.0)
        grinders = [member for member in ctx.guild.members if grinderrole in member.roles or tgrinderrole in member.roles]
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
<:DVB_start_incomplete:895172799981817938> <a:typing:839487089304141875> **Checking daily requirement** 
<:DVB_middle_incomplete:895172800430620742> Updating statistics 
<:DVB_end_incomplete:895172799923109919> Notifying grinders and sending a summary""")
            completed_req = []
            not_complete = []
            for grinder in grinders:
                result = await self.client.pool_pg.fetchrow("SELECT * FROM grinderdata WHERE user_id = $1", grinder.id)
                if result is None:
                    not_complete.append((grinder, 0))
                elif result.get('today') < 5000000:
                    not_complete.append((grinder, result.get('today')))
                else:
                    completed_req.append((grinder, result.get('today')))
            await msg.edit(content="""
<:DVB_start_complete:895172800627769447> Checking daily requirement 
<:DVB_middle_incomplete:895172800430620742> <a:typing:839487089304141875> **Updating statistics** 
<:DVB_end_incomplete:895172799923109919> Notifying grinders and sending a summary""")
            if discord.utils.utcnow().day == 1:
                await self.client.pool_pg.execute("UPDATE grinderdata SET past_month = $1", 0)
            if discord.utils.utcnow().weekday() == 3:
                reset_week = True
                week_values = []
                all = await self.client.pool_pg.fetch("SELECT user_id, past_week FROM grinderdata")
                if all is not None:
                    for a in all:
                        if ctx.guild.get_member(a.get('user_id')) in grinders:
                            week_values.append((0, 0, a.get('past_week'), a.get('user_id')))
                await self.client.pool_pg.executemany("UPDATE grinderdata SET today = $1, past_week = $2, last_week = $3 WHERE user_id = $4", week_values)
            else:
                reset_week = False
                await self.client.pool_pg.execute("UPDATE grinderdata SET today = $1", 0)
            await msg.edit(content="""
<:DVB_start_complete:895172800627769447> Checking daily requirement 
<:DVB_middle_complete:895172800627769444> Updating statistics
<:DVB_end_incomplete:895172799923109919> <a:typing:839487089304141875> **Notifying grinders and sending a summary**""")
            embed = discord.Embed(title="DV Grinders Team",
                                  description=f"<a:dv_pointArrowOwO:837656328482062336> The daily grinder requirement has been checked.\n<a:dv_pointArrowOwO:837656328482062336> <#862574856846704661> is now unlocked and you may send the cash to `Dank Vibes Holder#2553`\n<a:dv_pointArrowOwO:837656328482062336> The next requirement check will take place in about <t:{round(time.time()) + 86400}:R> ( i.e between 1:30PM and 3:30PM GMT)",
                                  color=self.client.embed_color)
            embed.set_thumbnail(url="https://cdn.discordapp.com/icons/595457764935991326/a_58b91a8c9e75742d7b423411b0205b2b.gif")
            embed.set_footer(text="DM/Ping Ari#0005 if you have any queries.", icon_url=ctx.guild.icon.url)
            if flags.msg is not None and len(flags.msg) != 0:
                embed.add_field(name=f"Additional Message from {ctx.author}", value=flags.msg, inline=False)
            success = 0  # gets the grinder list again since the earlier one was popped
            faileddms = []
            for grinder in grinders:
                try:
                    await grinder.send(f"Hello {grinder.name}! I have a message for you:", embed=embed)  # hehe
                    success += 1
                except discord.Forbidden:
                    faileddms.append(grinder.mention)  # gets list of people who will be pinged later
            if faileddms:
                channel = self.client.get_channel(donochannel)
                await channel.send(''.join(faileddms), embed=embed)
            content = ''
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhook_url, session=session)
                reportchannel = self.client.get_channel(logchannel)
                await reportchannel.send(f"**__DV GRINDERS SUMMARY__** (for **{discord.utils.utcnow().strftime('%A, %d %B %Y')}**)")
                await webhook.send(f"**__DV GRINDERS SUMMARY__** (for **{discord.utils.utcnow().strftime('%A, %d %B %Y')}**)", username=self.client.user.name, avatar_url=ctx.me.display_avatar.url)
                for dat in completed_req:
                    if len(content) < 1800:
                        content += f"\n<:DVB_True:887589686808309791> **{dat[0]}** sent `⏣ {comma_number(dat[1])}`"
                    else:
                        await reportchannel.send(content)
                        await webhook.send(content, username=self.client.user.name, avatar_url=ctx.me.display_avatar.url)
                        content = f"\n<:DVB_True:887589686808309791> **{dat[0]}** sent `⏣ {comma_number(dat[1])}`"
                for dat in not_complete:
                    if len(content) < 1800:
                        content += f"\n<:DVB_False:887589731515392000> **{dat[0]}** sent `⏣ {comma_number(dat[1])}`"
                    else:
                        await reportchannel.send(content)
                        await webhook.send(content, username=self.client.user.name, avatar_url=ctx.me.display_avatar.url)
                        content = f"\n<:DVB_False:887589731515392000> **{dat[0]}** sent `⏣ {comma_number(dat[1])}`"
                        await reportchannel.send(content)
                await reportchannel.send(content)
                await webhook.send(content, username=self.client.user.name, avatar_url=ctx.me.display_avatar.url)
                await reportchannel.send(f"Total grinded today: {sum([dat[1] for dat in completed_req] + [dat[1] for dat in not_complete])}")
                await webhook.send(f"Total grinded today: {sum([dat[1] for dat in completed_req] + [dat[1] for dat in not_complete])}", username=self.client.user.name, avatar_url=ctx.me.display_avatar.url)
            await msg.edit(content=f"""
<:DVB_start_complete:895172800627769447> Checking daily requirement 
<:DVB_middle_complete:895172800627769444> Updating statistics
<:DVB_end_complete:895172800082509846> Notifying grinders and sending a summary
Done! Note: People who **did not** complete the req won't be told they didn't complete it. Otherwise, I would've told them that they had completed the req.\n{'Additionally, the weekly statistics has been reset.' if reset_week else ''}""")


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