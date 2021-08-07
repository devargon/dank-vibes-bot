import asyncio
import time

import discord
import sqlite3
import contextlib
from dateutil import relativedelta
from datetime import datetime, timedelta
from discord.ext import commands, tasks

class DankMemer(commands.Cog, name='Dank Memer'):
    """
    Dank Memer utilities
    """
    def __init__(self, client):
        self.client = client
        self.active = True
        self.con = sqlite3.connect('databases/dankmemer.db', timeout=5.0)
        self.dankmemerreminders.start()

    @commands.Cog.listener()
    async def on_ready(self):
        cursor = self.con.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS reminders(member_id integer, remindertype integer, time integer)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS remindersettings(member_id integer PRIMARY KEY, work integer, daily integer, lottery integer, lifesaver integer)")

    def cog_unload(self):
        self.con.close()
        self.dankmemerreminders.stop()

    @tasks.loop(seconds=5)
    async def dankmemerreminders(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.active:
            return
        #if message.author.bot and message.author.id != 270904126974590976:
        #    return
        #if message.guild.id != 595457764935991326:
#            return
        if message.content.lower() in ["pls daily", "pls 24hr"]:# and not message.author.bot:
            if not message.author.bot:
                def check_daily(payload):
                    if len(payload.embeds) == 0 or payload.author.id == message.author.id or not payload.author.bot:
                        return False
                    else:
                        return payload.embeds[0].title == f"Here are yer daily coins, {message.author.name}" or payload.embeds[0].title == f"Here are your daily coins, {message.author.name}"
                try:
                    print("Checking for daily message")
                    botresponse = await self.client.wait_for("message", check=check_daily, timeout=10)
                except asyncio.TimeoutError:
                    await message.add_reaction("<:crossmark:841186660662247444>")
                else:
                    await botresponse.add_reaction("⏰")
                    # get member via message mentions and do db stuff here
            else:
                pass

        if message.content.lower() in ["pls work", "pls job"]: # and not message.author.bot:
            argument = message.content.split()
            if len(argument) > 2:
                if argument[2].lower() in ["info", "resign", "list", "view"]:
                    return

            def check_daily(payload):
                if len(payload.embeds) == 0 or payload.author.id == message.author.id or not payload.author.bot:
                    return False
                else:
                    if payload.mentions[0] == message.author:
                        return True if payload.embeds[0].description.startswith("**TERRIBLE work!**") or payload.embeds[0].description.startswith("**Great work!**") else False
            try:
                print("Checking for work message")
                botresponse = await self.client.wait_for("message", check=check_daily, timeout=60)
            except asyncio.TimeoutError:
                await message.add_reaction("<:crossmark:841186660662247444>")
            else:
                await botresponse.add_reaction("⏰")
                # get member via payload mentions
            print("Trigger fufilled")

        if "You equipped a lifesaver. For the next 10 hours if you die, you won't lose any items or coins. You will get a notification once this item expires." in message.content:# and message.author.bot: # and message.author.id == 270904126974590976
            if len(message.mentions) == 0:
                pass
            else:
                print(message.mentions[0])
                # get member via message mentions and do db stuff here
                await message.add_reaction("⏰")

        if "You tryna buy a lottery ticket for ⏣ 5000?" in message.content and message.author.bot: # and message.author.id == 270904126974590976
            if len(message.mentions) == 0:
                pass
            else:
                def check_lottery(payload):
                    return payload.author == message.mentions[0]
                try:
                    print("Checking for lottery message")
                    lotteryresponse = await self.client.wait_for("message", check=check_lottery, timeout=30)
                except asyncio.TimeoutError:
                    await message.add_reaction("<:crossmark:841186660662247444>")
                else:
                    if not "yes" in lotteryresponse.content.lower():
                        pass
                    else:
                        #get member via message mentions and do db stuff here
                        await lotteryresponse.add_reaction("⏰")

    @commands.command(name="dankreminders", aliases = ["dankrm", "drm"])
    async def dankreminders(self, ctx, argument=None):
        """
        Shows your reminders for Dank Memer, without any arguments.

        Change your type of reminder with `dv.dankreminders dm` or `dv.dankreminders ping/mention`.
        """
        timenow = time.time()
        embed = discord.Embed(title="Your Dank Memer reminders", description="For reminders to work, your reply pings needs to be enabled in Dank Memer's settings.", color=0x57f0f0)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.add_field(name="<:enabled:872003679895560193> Claim daily <:calendar:873107952159059991>", value=f"<t:{round(timenow)}:R>", inline=True)
        embed.add_field(name="<:disabled:872003709096321024> Enter the lottery <:lotteryticket:873110581085880321>", value=f"<t:{round(timenow)}:R> ", inline=True)
        embed.add_field(name="<:disabled:872003709096321024> Work <:workbadge:873110507605872650>", value=f"<t:{round(timenow)}:R>", inline=True)
        embed.add_field(name="<:enabled:872003679895560193> Use a lifesaver <:lifesaver:873110547854405722>", value=f"<t:{round(timenow)}:R>", inline=True)
        embed.add_field(name="Reminder preference", value=f"Ping\n(Regardless of your preference, lottery and daily reminders will always be sent in your DMs.", inline=False)
        message = await ctx.send(embed=embed)
        reminderemojis = ["<:calendar:873107952159059991>", "<:lotteryticket:873110581085880321>", "<:workbadge:873110507605872650>", "<:lifesaver:873110547854405722>"]
        for emoji in reminderemojis:
            await message.add_reaction(emoji)
        active = True
        while active == True:
            def check(payload):
                return payload.user_id == ctx.author.id and payload.channel_id == ctx.channel.id and payload.message_id == message.id and str(payload.emoji) in reminderemojis
            try:
                response = await self.client.wait_for('raw_reaction_add', timeout=15, check=check)
            except asyncio.TimeoutError:
                active = False
            else:
                if str(response.emoji) == "<:calendar:873107952159059991>":
                    await ctx.send("Change settings for Daily")
                    await message.remove_reaction(response.emoji, ctx.author)
                elif str(response.emoji) == "<:lotteryticket:873110581085880321>":
                    await ctx.send("Change settings for Lottery")
                    await message.remove_reaction(response.emoji, ctx.author)
                elif str(response.emoji) == "<:workbadge:873110507605872650>":
                    await ctx.send("Change settings for Work")
                    await message.remove_reaction(response.emoji, ctx.author)
                elif str(response.emoji) == "<:lifesaver:873110547854405722>":
                    await ctx.send("Change settings for Lifesaver")
                    await message.remove_reaction(response.emoji, ctx.author)
        await message.clear_reactions()
