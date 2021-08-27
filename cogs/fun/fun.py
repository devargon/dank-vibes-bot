import discord
import time
import asyncio
from discord.ext import commands
import random
from utils.time import humanize_timedelta
from .dm import dm
from utils import checks
import operator
from typing import Union
import matplotlib.pyplot as plt
import os
from PIL import Image, ImageFilter
import urllib.request
from io import BytesIO

class Fun(dm, commands.Cog, name='fun'):
    """
    Fun commands
    """
    def __init__(self, client):
        self.client = client
        self.dmconfig = {}
        self.mutedusers = []
        self.scrambledusers = []

    @checks.has_permissions_or_role(administrator=True)
    @commands.group(name="dumbfight", aliases = ["df"], invoke_without_command=True)
    async def dumbfight(self, ctx, member: discord.Member = None):
        """
        Mute people for a random duration between 30 to 120 seconds.
        """
        timenow = round(time.time())
        cooldown = await self.client.pool_pg.fetchrow("SELECT * FROM cooldowns WHERE command_name = $1 and member_id = $2 and time > $3", ctx.command.name, ctx.author.id, timenow)
        if cooldown is not None:
            return await ctx.send(f"You're on cooldown. try again in {humanize_timedelta(seconds=(cooldown.get('time') - timenow))}.", delete_after = 10.0)
        cooldown = await self.client.pool_pg.fetchrow("SELECT * FROM cooldowns WHERE command_name = $1 and member_id = $2 and time < $3", ctx.command.name, ctx.author.id, timenow)
        if cooldown:
            await self.client.pool_pg.execute("DELETE FROM cooldowns WHERE command_name = $1 and member_id = $2 and time = $3", cooldown.get('command_name'), cooldown.get('member_id'), cooldown.get('time'))
        if member is None:
            return await ctx.send("You need to tell me who you want to dumbfight.")
        if member.id in self.mutedusers:
            return await ctx.send(f"**{member.display_name}** is currently muted in a dumbfight. Wait a few moments before using this command.")
        if member.bot:
            return await ctx.send("Back off my kind. Don't dumbfight bots.")
        if member == ctx.me:
            return await ctx.send("How do you expect me to mute myself?")
        duration = random.randint(30, 120)
        won_dumbfights = await self.client.pool_pg.fetch(
            "SELECT * FROM dumbfightlog where did_win = $1 and invoker_id = $2", 1, ctx.author.id)
        lost_dumbfights = await self.client.pool_pg.fetch(
            "SELECT * FROM dumbfightlog where did_win = $1 and invoker_id = $2", 0, ctx.author.id)
        try:
            wonlossratio = len(won_dumbfights) / len(lost_dumbfights)
        except ZeroDivisionError:
            doesauthorwin = random.choice([True, False])
        else:
            if wonlossratio == 0:
                doesauthorwin = random.choice([True, False])
            elif wonlossratio < 0.7:
                doesauthorwin = True
            elif wonlossratio > 1.5:
                doesauthorwin = False
            else:
                doesauthorwin = random.choice([True, False])
        channel = ctx.channel
        if doesauthorwin:
            muted = member
            color = 0x00ff00
            str = "and won against"
        else:
            muted = ctx.author
            color = 0xff0000
            str = "and lost against"
        await self.client.pool_pg.execute("INSERT INTO dumbfightlog values($1, $2, $3)", ctx.author.id, member.id, 1 if doesauthorwin is True else 0)
        originaloverwrite = channel.overwrites_for(muted) if muted in channel.overwrites else None
        tempoverwrite = channel.overwrites_for(muted) if muted in channel.overwrites else discord.PermissionOverwrite()
        tempoverwrite.send_messages = False
        await channel.set_permissions(muted, overwrite=tempoverwrite)
        self.mutedusers.append(muted.id)
        selfmute = random.choice(['punched themselves in the face', 'kicked themselves in the knee', 'stepped on their own feet', 'punched themselves in the stomach', 'tickled themselves until they couldn\'t take it'])
        embed = discord.Embed(title="Get muted!", description = f"{ctx.author.mention} fought {member.mention} {str} them.\n{muted.mention} is now muted for {duration} seconds." if ctx.author != member else f"{ctx.author.mention} {selfmute}.\n{muted.mention} is now muted for {duration} seconds.", colour=color)
        if member.id in [650647680837484556, 321892489470410763] and muted != ctx.author:
            embed.set_footer(text="why did you dumbfight the developer :c", icon_url="https://cdn.discordapp.com/emojis/796407682764505180.png?v=1")
        await ctx.send(embed=embed)
        specialrole = ctx.guild.get_role(876767313263734805) # 874931276329656370
        cooldowntime = 1800 if specialrole in ctx.author.roles else 3600
        await self.client.pool_pg.execute("INSERT INTO cooldowns VALUES($1, $2, $3)", ctx.command.name, ctx.author.id, timenow + cooldowntime)
        await asyncio.sleep(duration)
        await channel.set_permissions(muted, overwrite=originaloverwrite)
        if muted.id in self.mutedusers:
            self.mutedusers.remove(muted.id)

    @checks.dev()
    @dumbfight.command(name="statistics", aliases = ["stats"])
    async def dfstatistics(self, ctx, member:discord.Member=None):
        if member is None:
            won_dumbfights = await self.client.pool_pg.fetch("SELECT * FROM dumbfightlog where did_win = $1", 1)
            lost_dumbfights = await self.client.pool_pg.fetch("SELECT * FROM dumbfightlog where did_win = $1", 0)
            top3_won = {}
            top3_lost = {}
            for entry in won_dumbfights:
                if entry.get('invoker_id') not in top3_won:
                    top3_won[entry.get('invoker_id')] = 1
                else:
                    top3_won[entry.get('invoker_id')] += 1
            for entry in lost_dumbfights:
                if entry.get('invoker_id') not in top3_lost:
                    top3_lost[entry.get('invoker_id')] = 1
                else:
                    top3_lost[entry.get('invoker_id')] += 1
            won_users = sorted(top3_won.items(), key=operator.itemgetter(1), reverse=True)  # sorts dict by descending
            lost_users = sorted(top3_lost.items(), key=operator.itemgetter(1), reverse=True)  # sorts dict by descending
            embed=discord.Embed(title="Dumbfight statistics", description = f"Number of dumbfights won: {len(won_dumbfights)}\nNumber of dumbfights lost: {len(lost_dumbfights)}", color = 0x1E90FF if ctx.author.id == 650647680837484556 else 0xffcccb)
            top3won = [f"<@{user[0]}>: {user[1]}" for user in won_users[:3]]
            top3won = "\n".join(top3won)
            top3lost = [f"<@{user[0]}>: {user[1]}" for user in lost_users[:3]]
            top3lost = "\n".join(top3lost)
            embed.add_field(name="Top 3 wiwnners", value = top3won)
            embed.add_field(name="Top 3 lost dumbfighters", value=top3lost)
            await ctx.send(embed=embed)
        else:
            won_dumbfights = await self.client.pool_pg.fetch("SELECT * FROM dumbfightlog where did_win = $1 and invoker_id = $2", 1, member.id)
            lost_dumbfights = await self.client.pool_pg.fetch("SELECT * FROM dumbfightlog where did_win = $1 and invoker_id = $2", 0, member.id)
            non_invoked_losses = await self.client.pool_pg.fetch("SELECT * FROM dumbfightlog where did_win = $1 and target_id = $2", 1, member.id)
            non_invoked_wins = await self.client.pool_pg.fetch("SELECT * FROM dumbfightlog where did_win = $1 and target_id = $2", 0, member.id)
            non_invoked_wins.reverse()
            non_invoked_losses.reverse()
            text = ""
            for entry in won_dumbfights[:3]:
                text += f"{member.mention} invoked a dumbfight and **won** to <@{entry.get('target_id')}>.\n"
            for entry in lost_dumbfights[:3]:
                text += f"{member.mention} invoked a dumbfight and **lost** to <@{entry.get('target_id')}>.\n"
            for entry in non_invoked_wins[:3]:
                text += f"{member.mention} was dumbfoughted by <@{entry.get('invoker_id')}> and lost to them.\n"
            for entry in non_invoked_losses[:3]:
                text += f"{member.mention} was dumbfoughted by <@{entry.get('invoker_id')}> and won to them.\n"
            embed=discord.Embed(title=f"Dumbfight statistics for {member}", description=f"Number of dumbfights won: {len(won_dumbfights)}\nNumber of dumbfights lost: {len(lost_dumbfights)}\n\nNumber of wins from non-self-invoked dumbfights: {len(non_invoked_wins)}\nNumber of losses from non-self-invoked dumbfights: {len(non_invoked_losses)}\n\n**Total** number of **wins**: {len(won_dumbfights) + len(non_invoked_wins)}\n**Total** number of **losses**: {len(lost_dumbfights) + len(non_invoked_losses)}",color = 0x1E90FF if ctx.author.id == 650647680837484556 else 0xffcccb)
            message = await ctx.send(f"React with 🥺 to view more information about **{member}**'s dumbfight statistics.", embed=embed)
            await message.add_reaction("🥺")
            def check(payload):
                return str(payload.emoji == "🥺") and payload.user_id == ctx.author.id  and payload.message_id == message.id
            try:
                await self.client.wait_for('raw_reaction_add', check=check, timeout = 20.0)
            except asyncio.TimeoutError:
                await message.clear_reactions()
            else:
                await message.clear_reactions()
                embed.add_field(name=f"Last few wins and losses for {member}", value=text)
                await message.edit(content="🥺", embed=embed)


    @commands.command(name="hideping", brief="hides ping", description= "hides ping", aliases = ["hp", "secretping", "sp"], hidden=True)
    @commands.cooldown(1,5, commands.BucketType.user)
    async def hideping(self, ctx, member: discord.Member=None, *, message=None):
        """
        hides ping
        """
        perm_role = ctx.guild.get_role(865534172403597312)
        if perm_role is not None and perm_role not in ctx.author.roles:
            raise commands.CheckFailure()
        if member is None:
            await ctx.send("You missed out `member` for this command.\n**Usage**: `hideping [member] [message]`")
            return
        message = "" if message is None else message
        try:
            await ctx.message.delete() # hides the ping so it has to delete the message that was sent to ping user
        except discord.Forbidden:
            embed = discord.Embed(title="Command failed", description = "I could not complete this command as I am missing the permissions to delete your message.", color = 0xB00B13)
            embed.set_footer(text=self.client.user.name, icon_url=self.client.user.avatar_url)
            await ctx.send("I could not complete this command as I am missing the permissions to delete your message.")
            return
        content = f"‍{message}||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍ <@{member.id}>" # ik this looks sketchy, but you can paste it in discord and send it to see how this looks like :MochaLaugh:
        await ctx.send(content)

    @commands.command(name="lockgen", brief = "Locks specified channel for 5 seconds", description = "Locks specified channel for 5 seconds", aliases = ["lg"])
    @commands.cooldown(1, 10800, commands.BucketType.user)
    async def lockgen(self, ctx):
        """
        Locks specified channel for 5 seconds
        """
        roleid = 865534338471690280 # DV's Voted 150x: 865534338471690280
        genchatid = 608498967474601995 # DV's genchat: 608498967474601995
        genchat = self.client.get_channel(genchatid)
        role = ctx.guild.get_role(roleid)
        if role not in ctx.author.roles:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"You do not have the required role (`{role}`) to use this command.")
        if genchat is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"Could not find a channel with the ID {genchatid}.")
        if ctx.channel != genchat:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"This command can only be used in {genchat.mention}!")
        if role is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"Could not find a role with the ID {roleid}.")
        originaloverwrite = genchat.overwrites_for(ctx.guild.default_role) # this is the overwrite that will be restored to gen chat when the lockdown is over
        newoverwrite = genchat.overwrites_for(ctx.guild.default_role) # this is the overwrite that i will edit to lockdown the channel
        authornewoverwrite = genchat.overwrites_for(ctx.author) # this is the overwrite that I will edit to allow the invoker to continue talking
        authornewoverwrite.send_messages=True # this edits the author's overwrite
        newoverwrite.send_messages = False # this edits the @everyone overwrite
        authororiginaloverwrite = None if ctx.author not in genchat.overwrites else genchat.overwrites_for(ctx.author) # this is the BEFORE overwrite for an individual member, if the author already had an overwrite (such as no react) it will use that to restore, otherwise None since it won't have any overwrites in the first place
        try:
            await genchat.set_permissions(ctx.author, overwrite=authornewoverwrite, reason=f"Lockdown invoker gets to talk c:") # allows author to talk
            await genchat.set_permissions(ctx.guild.default_role, overwrite = newoverwrite, reason = f"5 second lockdown initiated by {ctx.author.name}#{ctx.author.discriminator} with the {role.name} perk") # does not allow anyone else to talk
        except discord.Forbidden:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"I do not have the required permission to lock down **{genchat.name}**.")
        message = await ctx.send(f"✅ Locked down **{genchat.name}** for 5 seconds.")
        await asyncio.sleep(5)
        try:
            await genchat.set_permissions(ctx.guild.default_role, overwrite = originaloverwrite, reason = "Lockdown over uwu") # restores
            await genchat.set_permissions(ctx.author, overwrite = authororiginaloverwrite, reason = "Overwrite no longer required") # restores
        except discord.Forbidden:
            return await ctx.send(f"I do not have the required permission to remove the lockdown for **{genchat.name}**.")
        else:
            try:
                await message.add_reaction("🔓")
            except discord.Forbidden:
                pass

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="scramble", aliases=["shuffle"])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def scramble(self, ctx, member: discord.Member=None):
        """
        Scrambles your target's nickname for 3 minutes, effectively freezing it until the 3 minutes are up.
        In this testing server, the duration is just 20 seconds.
        """
        if member is None:
            return await ctx.send("You have to tell me whose name you want to scramble, man. `dv.scramble [member]`")
        if member.bot:
            return await ctx.send("I ain't bullying bots.")
        if member == ctx.author:
            return await ctx.send("Why change your own nickname when you can scramble others' nicknames?")
        if member in self.scrambledusers:
            return await ctx.send(f"**{member.name}**'s nickname is currently scrambled. Use this command when their nickname has returned to normal.")
        member_name = member.display_name
        lst_member_name = list(member_name)
        random.shuffle(lst_member_name)
        new_name = ''.join(lst_member_name)
        try:
            await member.edit(nick=new_name)
            self.scrambledusers.append(member)
        except discord.Forbidden:
            return await ctx.send("Sorry! I am unable to change that user's name, probably due to role hierachy or missing permissions.")
        await ctx.send(f"{member}'s name is now {new_name}!\n{member.mention}, your nickname has been jumbled up by **{ctx.author.name}**. It will automatically revert to your previous nickname after 3 minutes. If you try to change your nickname, I will jumble it again.")
        def check(payload_before, payload_after):
            return payload_before == member and payload_before.display_name == new_name and payload_after.display_name != new_name
        active = True
        has_warned = False
        while active:
            try:
                member_edit = await self.client.wait_for("member_update", check = check, timeout=180)
            except asyncio.TimeoutError:
                await member.edit(nick=member_name)
                active = False
                self.scrambledusers.remove(member)
            else:
                await member.edit(nick=new_name)
                if has_warned == False:
                    await ctx.send(f"{member.mention} how bad! You changed your nickname before the three minutes were up. Your scrambled nickname will still remain on you until 3 minutes are up. I will only tell you this once.")
                    has_warned = True
        return await ctx.send(f"{member.mention} good boy! I have restored your original nickname. :)")

    @checks.dev()
    @commands.command(name="chatchart")
    async def chatchart(self, ctx, channel: Union[discord.TextChannel, str] = None):
        """
        Shows the percentage of messages sent by various members. Use `chatchart <channel> --nobots` to filter out bots.
        """
        data = {}
        if channel is None or type(channel) is str:
            channel = ctx.channel
        embed=discord.Embed(title=f"Shuffling through #{channel}'s message history...", description=f"Fetching messages from Discord's API...", color=self.client.embed_color)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/871737314831908974/880374020267212830/discord_loading.gif")
        statusmessage = await ctx.send(embed=embed)
        messagecount = 0
        async for message in channel.history(limit=5000):
            if message.webhook_id is None:
                authorid = message.author.id
                if len(data) > 19 and authorid not in data:
                    if "Others" not in data:
                        data["Others"] = 1
                    else:
                        data["Others"] += 1
                elif message.author.bot:
                    if ctx.message.content.endswith("--bots"):
                        if authorid not in data:
                            data[authorid] = 1
                        else:
                            data[authorid] += 1
                else:
                    if authorid not in data:
                        data[authorid] = 1
                    else:
                        data[authorid] += 1
            messagecount += 1
            if messagecount %200 == 0:
                embed=discord.Embed(title=f"Shuffling through #{channel}'s message history...", description=f"Scanned {messagecount} of the last **5000** messages sent here.", color=self.client.embed_color)
                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/871737314831908974/880374020267212830/discord_loading.gif")
                await statusmessage.edit(embed=embed)
        counted = sorted(data.items(), key=operator.itemgetter(1), reverse=True)
        for entry in counted:
            if entry[0] == "Others":
                counted.pop(counted.index(entry))
                counted.append((entry[0], entry[1],))
        labels = []
        sizes = []
        for entry in counted:
            if entry[0] == "Others":
                labels.append("Others")
            else:
                print(entry[0])
                member = self.client.get_user(entry[0])
                if member is None:
                    pass
                else:
                    if len(member.name) > 15:
                        name = f"{member.name[0:15]}...#{member.discriminator}"
                    else:
                        name = f"{member.name}#{member.discriminator}"
                    labels.append(name)
            sizes.append(entry[1])
        count = counted
        if len(labels) == 0:
            await statusmessage.delete()
            await ctx.send("There were no entries to display in chatchart. This can happen as: \n    • No one had talked in the channel.\n    • `--nobots` was used but there're only bots talking.\n    • I do not have `Read Message History` permissions.")
            return
        plt.figure(figsize=plt.figaspect(1))
        newlabels = []
        for l, s in zip(labels, sizes):
            s = s / sum(sizes) * 100
            s = round(s, 1)
            newlabels.append(f"{l}, {s}%")
        title = plt.title(f"Messages in #{channel.name}", color='w')
        colors = ['#3d405b', '#005f73', '#0a9396', '#94d2bd', '#e9d8a6', '#ee9b00', '#ca6702', '#bb3e03', '#ae2012', '#9b2226', '#3d405b', '#005f73', '#0a9396', '#94d2bd', '#e9d8a6', '#ee9b00', '#ca6702', '#bb3e03', '#ae2012', 'grey']
        plt.pie(sizes, colors=colors)
        plt.legend(bbox_to_anchor=(1, 0.5), loc='center left', labels=newlabels, facecolor="gray",
                   edgecolor="white")
        filename = f"temp/{random.randint(0,9999999)}.png"
        plt.savefig(filename, bbox_inches="tight", pad_inches=0.1, transparent=True)
        embed = discord.Embed(title=f"Shuffling through #{channel}'s message history...",
                              description=f"Sending chatchart...",
                              color=self.client.embed_color)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/871737314831908974/880374020267212830/discord_loading.gif")
        await statusmessage.edit(embed=embed)
        file = discord.File(filename)
        await ctx.send(file=file)
        await statusmessage.delete()
        os.remove(filename)

    @checks.dev()
    @commands.command(name="goeatpoop")
    async def goeatpoop(self, ctx, member:discord.Member = None):
        """
        Get someone to eat poop
        """
        if member is None:
            return await ctx.send("mention someone lol")
        memberfilename = f"temp/{random.randint(1, 9999999)}.png"
        main = Image.open("assets/poop.png")
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(str(ctx.author.avatar_url).replace('webp', 'png'), memberfilename)
        ima = Image.open(memberfilename).convert('RGBA')
        ima = ima.resize((220,220))
        backg = main.copy()
        backg.paste(ima, (107, 218), ima)
        urllib.request.urlretrieve(str(member.avatar_url).replace('webp', 'png'), memberfilename)
        ima2 = Image.open(memberfilename).convert('RGBA')
        ima2 = ima2.resize((227,227))
        backg.paste(ima2, (555,112), ima2)
        b = BytesIO()
        backg.save(b, format="png", optimize=True, quality=50)
        b.seek(0)
        file = discord.File(fp=b, filename="goeatpoop.jpg")
        await ctx.send("If you don't understand the reference: <https://www.youtube.com/watch?v=M-PvB0NdO2g>", file=file)
        os.remove(memberfilename)