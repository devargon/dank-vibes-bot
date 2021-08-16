import time
import asyncio
import discord
import operator
from utils import checks
from datetime import datetime
from discord.ext import commands, tasks

class DankMemer(commands.Cog, name='dankmemer'):
    """
    Dank Memer utilities
    """
    def __init__(self, client):
        self.client = client
        self.dankmemerreminders.start()

    def cog_unload(self):
        self.dankmemerreminders.stop()

    @tasks.loop(seconds=5)
    async def dankmemerreminders(self):
        await self.client.wait_until_ready()
        results = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where time < $1", round(time.time())) # all reminders that are due for reminding
        if len(results) == 0:
            return
        for result in results:
            config = await self.client.pool_pg.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", result.get('member_id')) # get the user's configuration
            if config is None: # no config means user doesn't even use this reminder system lol
                pass
            elif result.get('remindertype') not in [2, 3, 4, 6 , 7, 8, 9]: # since 2 3 4 5 corresponds to the respective reminders, if somehow an invalid number is inserted it skips straight to deleting
                pass
            elif config[result.get('remindertype')] == 0: # activity specific reminder check
                pass
            elif config.get('method') == 0: # chose not to be reminded
                pass
            elif config.get('method') in [1, 2]: # DMs or Mentions
                def message(reminderaction):
                    if reminderaction == 2:
                        return "**claim your daily.** <:DVB_calendar:873107952159059991>"
                    elif reminderaction == 3:
                        return "**enter the lottery.** <:DVB_lotteryticket:873110581085880321>"
                    elif reminderaction == 4:
                        return "**work again.** <:DVB_workbadge:873110507605872650>"
                    elif reminderaction == 5:
                        return "**use a lifesaver.** <:DVB_lifesaver:873110547854405722>"
                    elif reminderaction == 6:
                        return "**use an apple.** <:DVB_apple:876627457275469867>"
                    elif reminderaction == 7:
                        return "**redeem your Patreon perks.** <:DVB_patreon:876628017194082395>"
                    elif reminderaction == 8:
                        return "**claim your weekly.** <:DVB_week:876711052669247528> "
                    elif reminderaction == 9:
                        return "**claim your monthly**. <:DVB_month:876711072030150707> "
                try:
                    member = self.client.get_guild(result.get('guild_id')).get_member(result.get('member_id'))
                    channel = self.client.get_channel(result.get('channel_id'))
                except AttributeError: # member is none or channel is none
                    pass
                else:
                    if config.get('method') == 1:  # DMs or is lottery/daily reminder
                        try:
                            await member.send(f"You can now {message(result.get('remindertype'))}") # DM
                        except discord.Forbidden:
                            await channel.send(f"{member.mention} {self.client.user.name} is unable to DM you.\nTo receive Dank Memer reminders properly, open your DMs or switch to ping reminders via `dv.drm ping`. Your reminders have been disabled for now.")
                            await self.client.pool_pg.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 0, result.get('member_id')) # change reminder settings to None
                    elif config.get('method') == 2: # Mention
                            await channel.send(f"{member.mention} you can now {message(result.get('remindertype'))}")
                await self.client.pool_pg.execute("INSERT into stats(member_id, remindertype, time) VALUES($1, $2, $3)", result.get('member_id'), result.get('remindertype'), result.get('time'))
            await self.client.pool_pg.execute("DELETE from dankreminders WHERE member_id = $1 and remindertype = $2 and channel_id = $3 and guild_id = $4 and time = $5", result.get('member_id'), result.get('remindertype'), result.get('channel_id'), result.get('guild_id'), result.get('time'))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot and message.author.id != 235148962103951360:
            return
        if message.guild.id != 871734809154707467:
            return
        if not message.guild:
            return
        """
        Refer to https://discord.com/channels/871734809154707467/871737332431216661/873142587001827379 to all message events here
        """
        if message.content.lower() in ["pls daily", "pls 24hr"]:
            if not message.author.bot:
                def check_daily(payload):
                    if len(payload.embeds) == 0 or payload.author.id == message.author.id or not payload.author.bot or message.channel != payload.channel or payload.author.id != 235148962103951360:
                        return False
                    else:
                        return payload.embeds[0].title == f"Here are yer daily coins, {message.author.name}" or payload.embeds[0].title == f"Here are your daily coins, {message.author.name}"
                try:
                    botresponse = await self.client.wait_for("message", check=check_daily, timeout=10)
                except asyncio.TimeoutError:
                    await message.add_reaction("<:crossmark:841186660662247444>")
                else:
                    member = message.author
                    nextdailytime = round(time.time())
                    while nextdailytime % 86400 != 0:
                        nextdailytime += 1
                    existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 2)
                    if len(existing) > 0:
                        await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextdailytime, member.id, 2)
                    else:
                        await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 2, message.channel.id, message.guild.id, nextdailytime)
                    await botresponse.add_reaction("⏰")
            else:
                pass

        if "pls weekly" in message.content.lower():
            if not message.author.bot:
                def check_weekly(payload):
                    if len(payload.embeds) == 0 or payload.author.id == message.author.id or not payload.author.bot or message.channel != payload.channel or payload.author.id != 235148962103951360:
                        return False
                    else:
                        return payload.embeds[0].title == f"Here are yer weekly coins, {message.author.name}" or payload.embeds[0].title == f"Here are your weekly coins, {message.author.name}"
                try:
                    botresponse = await self.client.wait_for("message", check=check_weekly, timeout=10)
                except asyncio.TimeoutError:
                    await message.add_reaction("<:crossmark:841186660662247444>")
                else:
                    member = message.author
                    nextweeklytime = round(time.time()) + 604800
                    existing = await self.client.pool_pg.fetch(
                        "SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 8)
                    if len(existing) > 0:
                        await self.client.pool_pg.execute(
                            "UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextweeklytime,
                            member.id, 8)
                    else:
                        await self.client.pool_pg.execute(
                            "INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)",
                            member.id, 8, message.channel.id, message.guild.id, nextweeklytime)
                    await botresponse.add_reaction("⏰")
            else:
                pass

        if "pls monthly" in message.content.lower():
            if not message.author.bot:
                def check_monthly(payload):
                    if len(payload.embeds) == 0 or payload.author.id == message.author.id or not payload.author.bot or message.channel != payload.channel or payload.author.id != 235148962103951360:
                        return False
                    else:
                        return payload.embeds[0].title == f"Here are yer monthly coins, {message.author.name}" or payload.embeds[0].title == f"Here are your monthly coins, {message.author.name}"
                try:
                    botresponse = await self.client.wait_for("message", check=check_monthly, timeout=10)
                except asyncio.TimeoutError:
                    await message.add_reaction("<:crossmark:841186660662247444>")
                else:
                    member = message.author
                    nextmonthlytime = round(time.time()) + 2592000
                    existing = await self.client.pool_pg.fetch(
                        "SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 9)
                    if len(existing) > 0:
                        await self.client.pool_pg.execute(
                            "UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3",
                            nextmonthlytime,
                            member.id, 9)
                    else:
                        await self.client.pool_pg.execute(
                            "INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)",
                            member.id, 9, message.channel.id, message.guild.id, nextmonthlytime)
                    await botresponse.add_reaction("⏰")
            else:
                pass

        if len(message.embeds) > 0 and len(message.mentions) > 0 and message.embeds[0].title == "Pending Confirmation" and "tryna buy a lottery ticket" in message.embeds[0].description:
            member = message.mentions[0]
            def check_lottery(payload_before, payload_after):
                return payload_before.author == message.author and payload_after.author == message.author and payload_before.id == message.id and payload_after.id == message.id and len(message.embeds) > 0
            try:
                newedit = await self.client.wait_for("message_edit", check=check_lottery, timeout=20)
            except asyncio.TimeoutError:
                return await message.add_reaction("<:crossmark:841186660662247444>")
            else:
                if message.embeds[0].title == "Action Canceled" or message.embeds[0].title == "Action Canceled":
                    return await message.add_reaction("<:crossmark:841186660662247444>")
                if message.embeds[0].title == "Action Confirmed":
                    print(f"{member} Completed the lottery")
                    nextlotterytime = round(time.time())
                    while nextlotterytime % 3600 != 0:
                        nextlotterytime += 1
                    existing = await self.client.pool_pg.fetch(
                        "SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 3)
                    if len(existing) > 0:
                        await self.client.pool_pg.execute(
                            "UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3",
                            nextlotterytime, member.id, 3)
                    else:
                        await self.client.pool_pg.execute(
                            "INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)",
                            member.id, 3, message.channel.id, message.guild.id, nextlotterytime)
                    await message.add_reaction("⏰")

        if "pls redeem" in message.content.lower():
            print("checking redeen")
            def check_redeem(payload):
                return payload.author.bot and len(payload.embeds) > 0
            try:
                redeemresponse = await self.client.wait_for("message", check=check_redeem, timeout = 15)
            except asyncio.TimeoutError:
                return await message.add_reaction("<:crossmark:841186660662247444>")
            else:
                if f"{message.author.name} has redeemed their" in redeemresponse.embeds[0].title:
                    member = message.author
                    nextredeemtime = round(time.time()) + 259200
                    existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 7)
                    if len(existing) > 0:
                        await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextredeemtime, member.id, 7)
                    else:
                        await self.client.pool_pg.execute(
                            "INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)",
                            member.id, 7, message.channel.id, message.guild.id, nextredeemtime)
                    await message.add_reaction("⏰")

        if message.content.lower() in ["pls work", "pls job"] and not message.author.bot:
            argument = message.content.split()
            if len(argument) > 2:
                if argument[2].lower() in ["info", "resign", "list", "view"]:
                    return
            def check_work(payload):
                if len(payload.embeds) == 0 or payload.author.id == message.author.id or not payload.author.bot or message.channel != payload.channel:
                    return False
                else:
                    if len(payload.mentions) != 0 and payload.mentions[0] == message.author and payload.author.id == 235148962103951360:
                        return True if payload.embeds[0].description.startswith("**TERRIBLE work!**") or payload.embeds[0].description.startswith("**Great work!**") else False
            try:
                botresponse = await self.client.wait_for("message", check=check_work, timeout=60)
            except asyncio.TimeoutError:
                await message.add_reaction("<:crossmark:841186660662247444>")
            else:
                member = botresponse.mentions[0]
                nextdailytime = round(time.time()) + 3600
                existing = await self.client.pool_pg.fetch(
                    "SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 4)
                if len(existing) > 0:
                    await self.client.pool_pg.execute(
                        "UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextdailytime,
                        member.id, 4)
                else:
                    await self.client.pool_pg.execute(
                        "INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)",
                        member.id, 4, message.channel.id, message.guild.id, nextdailytime)
                await botresponse.add_reaction("⏰")

        if len(message.mentions) > 0 and "You've eaten an apple!" in message.content and message.author.bot:
            member = message.mentions[0]
            nextappletime = round(time.time()) + 86400
            existing = await self.client.pool_pg.fetch("SELECT * FROM dankreminders where member_id = $1 and remindertype = $2", member.id, 6)
            if len(existing) > 0:
                await self.client.pool_pg.execute("UPDATE dankreminders set time = $1 WHERE member_id = $2 and remindertype = $3", nextappletime, member.id, 6)
            else:
                await self.client.pool_pg.execute("INSERT INTO dankreminders(member_id, remindertype, channel_id, guild_id, time) VALUES($1, $2, $3, $4, $5)", member.id, 6, message.channel.id, message.guild.id, nextappletime)
            await message.add_reaction("⏰")

    @checks.dev()
    @commands.command(name="drmstats", aliases = ["dankreminderstats, statistics"])
    async def statistics(self, ctx, argument = None):
        """
        Shows dev-only statistics for Dank Memer reminders.
        """
        if argument and argument.lower() == "reset":
            alltime = await self.client.pool_pg.fetch("SELECT * from stats")
            embed = discord.Embed(title="Reset Dank reminder database?", description=f"{len(alltime)} entries will be deleted. Are you sure?", color=discord.Color.red())
            message = await ctx.send(embed=embed)
            reactions = ["<:checkmark:841187106654519296>", "<:crossmark:841186660662247444>"] # request to confirm
            for reaction in reactions:
                await message.add_reaction(reaction)
            def check(payload):
                return payload.user_id == ctx.message.author.id and payload.channel_id == ctx.channel.id and payload.message_id == message.id and str(
                    payload.emoji) in reactions
            try:
                response = await self.client.wait_for('raw_reaction_add', timeout=15, check=check)
                if not str(response.emoji) == '<:checkmark:841187106654519296>':
                    return await message.edit(content="Command stopped.")
            except asyncio.TimeoutError:
                ctx.command.reset_cooldown(ctx)
                return await message.edit(content="You didn't react on time.")
            else:
                await message.clear_reactions()
                async with ctx.typing():
                    await self.client.pool_pg.execute("DELETE FROM stats") # delete statistics database
                    embed = discord.Embed(title="Reset Dank reminder database?", description=f"Database has been reset.", color=discord.Color.green())
                    await message.edit(embed=embed)
                    return await message.delete(delay=10)
        def remindertype(num):
            if num == 2:
                return "Daily"
            if num == 3:
                return "Lottery"
            if num == 4:
                return "Work"
            if num == 5:
                return "Lifesaver"
            if num == 6:
                return "Apple"
            if num == 7:
                return "Patreon"
            if num == 8:
                return "Weekly"
            if num == 9:
                return "Monthly"
            else:
                return "None"
        """
        Shows statistics for Dank Memer reminders for this bot.
        """
        timecounter = time.perf_counter()
        timenow = round(time.time())
        alltime = await self.client.pool_pg.fetch("SELECT * from stats") # gets all entries from all time
        twentyfourhour = await self.client.pool_pg.fetch("SELECT * from stats WHERE time > $1", timenow - 86400) # gets all entries from the last 24 hours
        week = await self.client.pool_pg.fetch("SELECT * from stats WHERE time > $1",timenow - 604800) # gets all entries from the past week
        users = {} # result will be something like {321892489470410763: 123, 650647680837484556: 456}
        reminders = {} # result will be something like {Lottery: 123, Work: 45, Lifesaver: 67, Daily: 89}
        for entry in alltime:
            if entry.get('member_id') not in users:
                users[entry.get('member_id')] = 1
            else:
                users[entry.get('member_id')] += 1
            if remindertype(entry.get('remindertype')) not in reminders:
                reminders[remindertype(entry.get('remindertype'))] = 1
            else:
                reminders[remindertype(entry.get('remindertype'))] += 1
        sortusers = sorted(users.items(), key=operator.itemgetter(1), reverse=True) # sorts dict by descending
        listof = [f"<@{user[0]}>: {user[1]}" for user in sortusers[:3]] # makes it into a list that is readable
        listof = "\n".join(listof) # makes top 3 users into string
        sortreminders = sorted(reminders.items(), key=operator.itemgetter(1), reverse=True) # sorts dict by descending
        listofreminders = [f"{reminder[0]}: {reminder[1]}" for reminder in sortreminders[:3]]
        listofreminders = "\n".join(listofreminders) # makes top 3 reminder types into string
        daily = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 2)) # number of daily reminders served
        lottery = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 3)) # number of lottery reminders served
        work = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 4)) # number of work reminders served
        apple = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 6)) # number of lifesavers reminders served
        redeem = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 7))
        weekly = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 8))
        monthly = len(await self.client.pool_pg.fetch("SELECT * from stats WHERE remindertype = $1", 9))

        onhold = len(await self.client.pool_pg.fetch("SELECT * FROM dankreminders"))
        embed = discord.Embed(title="Dank Memer Reminder Statistics", description=f"Fetched in {round(time.perf_counter() - timecounter, 3)} seconds.", color = 0x57F0F0, timestamp= datetime.utcnow())
        embed.add_field(name="Top 3 reminder types:", value=listof or "None", inline=True)
        embed.add_field(name="Top 3 reminder users:", value=listofreminders or "None", inline=True)
        embed.add_field(name="Number of activated settings", value=str(len(await self.client.pool_pg.fetch("SELECT * FROM remindersettings"))), inline=False)
        embed.add_field(name="History statistics", value=f"Since dawn of time: `{len(alltime)}`\nPast 24 hours: `{len(twentyfourhour)}`\nPast week: `{len(week)}`\nOn hold:`{onhold}`", inline=True)
        embed.add_field(name="History statistics",value=f"Daily: `{daily}`\nLottery: `{lottery}`\nWork: `{work}`\nApple:`{apple}`\nPatreon: `{redeem}`\nWeekly: `{weekly}`\nMonthly: `{monthly}`", inline=True)
        await ctx.send(embed=embed)



    @commands.command(name="dankreminders", aliases = ["dankrm", "drm"])
    async def dankreminders(self, ctx, argument=None):
        """
        Shows your reminders for Dank Memer and allows you to enable/disable them, without any arguments.
        Change your type of reminder with `dv.dankreminders dm`,  `dv.dankreminders ping/mention` or `dv.dankreminders none`.
        """
        result = await self.client.pool_pg.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id) # gets the configuration for user to check if they have used dank reminder before
        if result is None:
            await self.client.pool_pg.execute("INSERT into remindersettings VALUES ($1, $2, $3, $4, $5, $6)", ctx.author.id, 1, 0, 0, 0, 0) # creates new entry for settings
        def numberswitcher(no):
            if no == 1:
                return 0
            elif no == 0:
                return 1
            else:
                return 0
        def emojioutput(truefalse): # shows the enabled or disabled emoji for 0 or 1 values
            if truefalse == 0:
                return "<:DVB_disabled:872003709096321024>"
            elif truefalse == 1:
                return "<:DVB_enabled:872003679895560193>"
            else:
                return "error"
        if argument is not None and argument.lower() in ["dm", "ping", "mention", "none", "off", "false", "disable"]:
            if argument.lower() in ["none", "off", "false", "disable"]:
                await self.client.pool_pg.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 0, ctx.author.id) # disables dank reminders
                return await ctx.send("Got it. You will not be reminded for any Dank Memer reminders.")
            elif argument.lower() == "dm":
                await self.client.pool_pg.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 1, ctx.author.id) # sets to DMs
                return await ctx.send("Got it. You will **now be DMed** for your enabled Dank Memer reminders.")
            elif argument.lower() in ["ping", "mention"]:
                await self.client.pool_pg.execute("UPDATE remindersettings SET method = $1 WHERE member_id = $2", 2, ctx.author.id) # sets to mentions
                return await ctx.send(f"Got it. You will **now pinged in the channel where you used the command** for your enabled Dank Memer reminders.\n{'<a:DVB_Exclamation:873635993427779635> **Daily** and **lottery** reminders will still be sent in your DMs.' if (await self.client.pool_pg.fetchrow('SELECT truefalse from dankmemersetting')).get('truefalse') == 0 else ''}")
        reminders = await self.client.pool_pg.fetch("SELECT * FROM dankreminders WHERE member_id = $1 and guild_id = $2", ctx.author.id, ctx.guild.id) # gets user's reminders
        dailytime, lotterytime, worktime, appletime, redeemtime, weeklytime, monthlytime = None, None, None, None, None, None, None
        for reminder in reminders:
            if reminder.get('remindertype') == 2:
                dailytime = f"<t:{reminder.get('time')}:R>" # time in discord time format
            if reminder.get('remindertype') == 3:
                lotterytime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 4:
                worktime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 6:
                appletime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 7:
                redeemtime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 8:
                weeklytime = f"<t:{reminder.get('time')}:R>"
            if reminder.get('remindertype') == 9:
                monthlytime = f"<t:{reminder.get('time')}:R>"
        result = await self.client.pool_pg.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id)
        embed = discord.Embed(title="Your Dank Memer reminders", description="**React with the emoji that corresponds to the reminder to enable/disable it.**\nChange how you want to be reminded with `dv.dankreminders dm`,  `dv.dankreminders ping/mention` or `dv.dankreminders none`.", color=0x57f0f0, timestamp=datetime.utcnow())
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.add_field(name=f"{emojioutput(result.get('daily'))} Claim daily <:DVB_calendar:873107952159059991>", value=dailytime or "Ready!", inline=True)
        embed.add_field(name=f"{emojioutput(result.get('weekly'))} Claim weekly <:DVB_week:876711052669247528> ", value=weeklytime or "Ready!", inline=True) #8
        embed.add_field(name=f"{emojioutput(result.get('monthly'))} Claim monthly <:DVB_month:876711072030150707> ", value=monthlytime or "Ready!", inline=True) #9
        embed.add_field(name=f"{emojioutput(result.get('lottery'))} Enter the lottery <:DVB_lotteryticket:873110581085880321>", value=lotterytime or "Ready!", inline=True)
        embed.add_field(name=f"{emojioutput(result.get('work'))} Work <:DVB_workbadge:873110507605872650>", value=worktime or "Ready!", inline=True)
        embed.add_field(name=f"{emojioutput(result.get('apple'))} Use an apple <:DVB_apple:876627457275469867>", value=appletime or "Ready!", inline=True)
        embed.add_field(name=f"{emojioutput(result.get('redeem'))} Redeem donor rewards <:DVB_patreon:876628017194082395>", value=redeemtime or "Ready!", inline=True)
        if ctx.author.id == 650647680837484556:
            embed.add_field(name=f"<:DVB_enabled:872003679895560193> Slap Frenzy <a:DVB_pandaslap:876631217750048798>", value="Always enabled", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Reminder preference", value=f"{'DM' if result.get('method') == 1 else 'Ping' if result.get('method') == 2 else None}", inline=False)
        embed.set_footer(text="For reminders to work, your reply pings needs to be enabled in Dank Memer's settings.", icon_url=ctx.guild.icon_url)
        message = await ctx.send(embed=embed)
        reminderemojis = ["<:DVB_calendar:873107952159059991>", "<:DVB_week:876711052669247528>", "<:DVB_month:876711072030150707>", "<:DVB_lotteryticket:873110581085880321>", "<:DVB_workbadge:873110507605872650>", "<:DVB_apple:876627457275469867>", "<:DVB_patreon:876628017194082395>"]
        for emoji in reminderemojis:
            await message.add_reaction(emoji)
        active = True
        while active:
            def check(payload):
                return payload.user_id == ctx.author.id and payload.channel_id == ctx.channel.id and payload.message_id == message.id and str(payload.emoji) in reminderemojis
            try:
                response = await self.client.wait_for('raw_reaction_add', timeout=15, check=check)
            except asyncio.TimeoutError:
                active = False
            else:
                if str(response.emoji) == "<:DVB_calendar:873107952159059991>":
                    await self.client.pool_pg.execute("UPDATE remindersettings SET daily = $1 WHERE member_id = $2", numberswitcher(result.get('daily')), ctx.author.id) # switches to enabled/disabled reminder
                elif str(response.emoji) == "<:DVB_lotteryticket:873110581085880321>":
                    await self.client.pool_pg.execute("UPDATE remindersettings SET lottery = $1 WHERE member_id = $2", numberswitcher(result.get('lottery')), ctx.author.id)
                elif str(response.emoji) == "<:DVB_workbadge:873110507605872650>":
                    await self.client.pool_pg.execute("UPDATE remindersettings SET work = $1 WHERE member_id = $2", numberswitcher(result.get('work')), ctx.author.id)
                elif str(response.emoji) == "<:DVB_week:876711052669247528> ":
                    await self.client.pool_pg.execute("UPDATE remindersettings SET weekly = $1 WHERE member_id = $2", numberswitcher(result.get('weekly')), ctx.author.id)
                elif str(response.emoji) == "<:DVB_month:876711072030150707> ":
                    await self.client.pool_pg.execute("UPDATE remindersettings SET monthly = $1 WHERE member_id = $2", numberswitcher(result.get('monthly')), ctx.author.id)
                elif str(response.emoji) == "<:DVB_apple:876627457275469867>":
                    await self.client.pool_pg.execute("UPDATE remindersettings SET apple = $1 WHERE member_id = $2", numberswitcher(result.get('apple')), ctx.author.id)
                elif str(response.emoji) == "<:DVB_patreon:876628017194082395>":
                    await self.client.pool_pg.execute("UPDATE remindersettings SET redeem = $1 WHERE member_id = $2", numberswitcher(result.get('redeem')), ctx.author.id)
                '''elif str(response.emoji) == "<:DVB_lifesaver:873110547854405722>":
                    await self.client.pool_pg.execute("UPDATE remindersettings SET lifesaver = $1 WHERE member_id = $2", numberswitcher(result.get('lifesaver')), ctx.author.id)'''
                await message.remove_reaction(response.emoji, ctx.author)
                result = await self.client.pool_pg.fetchrow("SELECT * FROM remindersettings WHERE member_id = $1", ctx.author.id)
                embed = discord.Embed(title="Your Dank Memer reminders",  description="**React with the emoji that corresponds to the reminder to enable/disable it.**\nChange how you want to be reminded with `dv.dankreminders dm`,  `dv.dankreminders ping/mention` or `dv.dankreminders none`.", color=0x57f0f0, timestamp=datetime.utcnow())
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
                embed.add_field(name=f"{emojioutput(result.get('daily'))} Claim daily <:DVB_calendar:873107952159059991>", value=dailytime or "Ready!", inline=True)
                embed.add_field(name=f"{emojioutput(result.get('weekly'))} Claim weekly <:DVB_week:876711052669247528> ", value=weeklytime or "Ready!", inline=True)  # 8
                embed.add_field(name=f"{emojioutput(result.get('monthly'))} Claim monthly <:DVB_month:876711072030150707> ", value=monthlytime or "Ready!", inline=True)  # 9
                embed.add_field(name=f"{emojioutput(result.get('lottery'))} Enter the lottery <:DVB_lotteryticket:873110581085880321>", value=lotterytime or "Ready!", inline=True)
                embed.add_field(name=f"{emojioutput(result.get('work'))} Work <:DVB_workbadge:873110507605872650>", value=worktime or "Ready!", inline=True)
                embed.add_field(name=f"{emojioutput(result.get('apple'))} Use an apple <:DVB_apple:876627457275469867>", value=appletime or "Ready!", inline=True)
                embed.add_field(name=f"{emojioutput(result.get('redeem'))} Redeem donor rewards <:DVB_patreon:876628017194082395>", value=redeemtime or "Ready!", inline=True)
                if ctx.author.id == 650647680837484556:
                    embed.add_field(name=f"<:DVB_enabled:872003679895560193> Slap Frenzy <a:DVB_pandaslap:876631217750048798>", value="Always ready", inline=True)
                embed.add_field(name="\u200b", value="\u200b", inline=False)
                embed.add_field(name="Reminder preference", value=f"{'DM' if result.get('method') == 1 else 'Ping' if result.get('method') == 2 else None}", inline=False)
                embed.set_footer(text="For reminders to work, your reply pings needs to be enabled in Dank Memer's settings.", icon_url=ctx.guild.icon_url)
                await message.edit(embed=embed)
        await message.clear_reactions()
