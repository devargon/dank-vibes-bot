import discord
from discord import Webhook
from discord.commands import Option
from discord.ext import commands

import os
import time
import random
import aiohttp
import asyncio
import operator
import alexflipnote
from typing import Union, Optional
import matplotlib.pyplot as plt
from itertools import islice

from utils import checks
from utils.time import humanize_timedelta
from utils.errors import ArgumentBaseError, NicknameIsManaged
from utils.format import generate_loadbar

from .dm import dm
from .snipe import snipe
from .itemgames import ItemGames
from .games import games
from .color import color

alexflipnoteAPI = os.getenv('alexflipnoteAPI')
tenorAPI = os.getenv('tenorAPI')

class Fun(color, games, ItemGames, snipe, dm, commands.Cog, name='fun'):
    """
    Fun commands
    """
    def __init__(self, client):
        self.client = client
        self.dmconfig = {}
        self.mutedusers = {}
        self.scrambledusers = []
        self.persistent_views_added = False
        self.gen_is_muted = False
        self.chatchart_is_running = False
        self.deleted_messages = {}
        self.edited_messages = {}
        self.removed_reactions = {}
        self.karutaconfig = ''
        self.karutaevent_isrunning = False
        self.planning_numberevent = []
        self.numberevent_channels = []
        self.nickbets = []
        self.alex_api = alexflipnote.Client()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.command is None:
            return
        if ctx.command.name == 'chatchart':
            self.chatchart_is_running = False
        elif ctx.command.name == 'lockgen':
            self.gen_is_muted = False
        elif ctx.command.name == "nickbet":
            self.nickbets = []
    def lowered_cooldown(message: discord.Message):
        if discord.utils.get(message.author.roles, id=874833402052878396): # Contributor 24T
            return commands.Cooldown(1, 900)
        elif discord.utils.get(message.author.roles, id=931174008970444800): # weekly top grinder
            return commands.Cooldown(1, 900)
        elif discord.utils.get(message.author.roles, name="Vibing Investor"):
            return commands.Cooldown(1, 1800)
        else:
            return commands.Cooldown(1, 3600)

    async def cog_check(self, ctx):
        if ctx.author.id == 650647680837484556 or ctx.author.guild_permissions.administrator == True:
            return True
        else:
            if discord.utils.get(ctx.author.roles, name="No Tags"):
                raise ArgumentBaseError(message="You have the **No Tags** role and can't use any commands in the **Fun** cantegory. <:dv_pepeHahaUSuckOwO:837653798313918475>")
        return True

    @checks.requires_roles()
    @commands.dynamic_cooldown(lowered_cooldown, commands.BucketType.user)
    @commands.group(name="dumbfight", aliases = ["df"], invoke_without_command=True)
    async def dumbfight(self, ctx, member: discord.Member = None):
        """
        Mute people for a random duration between 30 to 120 seconds.
        """
        if self.gen_is_muted and ctx.channel.id == 608498967474601995:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Wait until the lockdown from `dv.lockgen` is over.")
        if member is None:
            if len(ctx.message.mentions) > 0:
                member = ctx.message.mentions[0]
            else:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send(f"Here we have a human AKA {ctx.author.mention} showing you that they are able to dumbfight you, although they could've just done it already. <:dv_pepeHahaUSuckOwO:837653798313918475>")
        if ctx.channel.id in self.mutedusers and member.id in self.mutedusers[ctx.channel.id]:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"**{member.name}** is currently muted in a dumbfight. Wait a few moments before using this command.")
        if member.bot:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Back off my kind. Don't dumbfight bots.")
        if member == ctx.me:
            ctx.command.reset_cooldown(ctx)
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
            if wonlossratio == 0 or wonlossratio >= 0.7 and wonlossratio <= 1.5:
                doesauthorwin = random.choice([True, False])
            elif wonlossratio < 0.7:
                doesauthorwin = True
            else:
                doesauthorwin = False
        if ctx.author.id == 650647680837484556 and ctx.message.content.lower().endswith('win'):
            doesauthorwin = True
        if ctx.author.id == 650647680837484556 and ctx.message.content.lower().endswith('lose'):
            doesauthorwin = False
        channel = ctx.channel
        if isinstance(channel, discord.Thread):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Dumbfight is not supported in threads yet. Sorry >.<")
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
        if ctx.channel.id in self.mutedusers:
            self.mutedusers[ctx.channel.id] = self.mutedusers[ctx.channel.id] + [muted.id]
        else:
            self.mutedusers[ctx.channel.id] = [muted.id]
        selfmute = random.choice(['punched themselves in the face', 'kicked themselves in the knee', 'stepped on their own feet', 'punched themselves in the stomach', 'tickled themselves until they couldn\'t take it'])
        embed = discord.Embed(title="Get muted!", description = f"{ctx.author.mention} fought {member.mention} {str} them.\n{muted.mention} is now muted for {duration} seconds." if ctx.author != member else f"{ctx.author.mention} {selfmute}.\n{muted.mention} is now muted for {duration} seconds.", colour=color)
        if member.id in [650647680837484556, 321892489470410763] and muted != ctx.author:
            embed.set_footer(text="why did you dumbfight the developer :c", icon_url="https://cdn.discordapp.com/emojis/796407682764505180.png?v=1")
        await ctx.send(embed=embed)
        await asyncio.sleep(duration)
        await channel.set_permissions(muted, overwrite=originaloverwrite)
        if muted.id in self.mutedusers[ctx.channel.id]:
            if len(self.mutedusers[ctx.channel.id]) == 1:
                del self.mutedusers[ctx.channel.id]
            else:
                lst = self.mutedusers[ctx.channel.id]
                lst.remove(muted.id)
                self.mutedusers[ctx.channel.id] = lst

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

    @checks.requires_roles()
    @commands.command(name="hideping", aliases = ["hp", "secretping"], hidden=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def hideping(self, ctx, channel: Optional[discord.TextChannel] = None, member: discord.Member=None, *, message=None):
        """
        Secretly ping someone with this command!
        """
        if channel is None:
            channel = ctx.channel
        if not (channel.permissions_for(ctx.author).send_messages and channel.permissions_for(ctx.author).view_channel):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You are not authorized to view/send messages in that channel.")
        if member is None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("You need to provide a member or message link.\n**Usage**: `hideping <channel> [member] [message]`")
            return
        if message is not None and len(message) > 180:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Your accompanying message can only be at most 180 characters.")
        try:
            await ctx.message.delete() # hides the ping so it has to delete the message that was sent to ping user
        except (discord.HTTPException, discord.Forbidden):
            ctx.command.reset_cooldown(ctx)
            await ctx.send("I could not complete this command as I could not delete your message.")
            return
        if message is None:
            message = ''
        if await self.client.check_blacklisted_content(message):
            message = ''
        content = f"{message or ''} ‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍ <@{member.id}>" # ik this looks sketchy, but you can paste it in discord and send it to see how this looks like :MochaLaugh:
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name=self.client.user.name)
        if webhook is None:
            try:
                webhook = await channel.create_webhook(name=self.client.user.name)
            except discord.Forbidden:
                try:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send("I am unable to create a webhook to send the hideping message.")
                except (discord.HTTPException, discord.Forbidden):
                    ctx.command.reset_cooldown(ctx)
                    return
                return
        await webhook.send(content, username="You were hidepinged", avatar_url="https://cdn.discordapp.com/attachments/871737314831908974/895639630429433906/incognito.png")
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url('https://canary.discord.com/api/webhooks/883563427455438858/GsF8ZPIemw6D-x6TIp7wO88ySQizKePKCS5zRA-EBtNfHRC15e9koti7-02GKBuoZ_Yi', session=session)
            embed=discord.Embed(title=f"Hideping command invoked with {ctx.me}", color=discord.Color.green())
            embed.add_field(name="Author", value=f"**{ctx.author}** ({ctx.author.id})", inline=True)
            embed.add_field(name="Target", value=f"**{member}** ({member.id})", inline=True)
            embed.add_field(name="Message", value=message or "No message", inline=True)
            await webhook.send(embed=embed, username=f"{self.client.user.name} Logs")

    @checks.requires_roles()
    @commands.slash_command(name="hideping", description="Secretly ping someone with this command!")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def hideping_slash(self, ctx,
                             target: Option(discord.Member, "Who you want to ping"),
                             channel: Option(discord.TextChannel, "If you want to ping someone in another channel") = None,
                             message: Option(str, "An optional message") = None
                             ):
        """
        Secretly ping someone with this command!
        """
        if channel is None:
            channel = ctx.channel
        if not (channel.permissions_for(ctx.author).send_messages and channel.permissions_for(ctx.author).view_channel):
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond("You are not authorized to view/send messages in that channel.", ephemeral=True)
        if message is not None and len(message) > 180:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Your accompanying message can only be at most 180 characters.")
        if message is None:
            message = ''
        if await self.client.check_blacklisted_content(message):
            message = ''
        content = f"{message or ''} ‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍ <@{target.id}>"  # ik this looks sketchy, but you can paste it in discord and send it to see how this looks like :MochaLaugh:
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name=self.client.user.name)
        if webhook is None:
            try:
                webhook = await channel.create_webhook(name=self.client.user.name)
            except discord.Forbidden:
                try:
                    ctx.command.reset_cooldown(ctx)
                    await ctx.send("I am unable to create a webhook to send the hideping message.")
                except (discord.HTTPException, discord.Forbidden):
                    ctx.command.reset_cooldown(ctx)
                    return
                return
        await webhook.send(content, username="You were hidepinged",
                           avatar_url="https://cdn.discordapp.com/attachments/871737314831908974/895639630429433906/incognito.png")
        await ctx.respond(f"**{target}** has been secretly pinged in {channel.mention}! <:qbgiggle:718020317632790548>", ephemeral=True)
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(
                'https://canary.discord.com/api/webhooks/883563427455438858/GsF8ZPIemw6D-x6TIp7wO88ySQizKePKCS5zRA-EBtNfHRC15e9koti7-02GKBuoZ_Yi',
                session=session)
            embed = discord.Embed(title=f"Hideping command invoked with {ctx.me}", color=discord.Color.green())
            embed.add_field(name="Author", value=f"**{ctx.author}** ({ctx.author.id})", inline=True)
            embed.add_field(name="Target", value=f"**{target}** ({target.id})", inline=True)
            embed.add_field(name="Message", value=message or "No message", inline=True)
            await webhook.send(embed=embed, username=f"{self.client.user.name} Logs")

    @checks.requires_roles()
    @commands.command(name="lockgen", brief = "Locks specified channel for 5 seconds", description = "Locks specified channel for 5 seconds", aliases = ["lg"])
    @commands.cooldown(1, 120, commands.BucketType.guild)
    async def lockgen(self, ctx):
        """
        Locks specified channel for 5 seconds
        """
        genchatid = 608498967474601995 # DV's genchat: 608498967474601995
        genchat = self.client.get_channel(genchatid)
        if genchat is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"Could not find a channel with the ID {genchatid}.")
        if ctx.channel != genchat:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"This command can only be used in {genchat.mention}!")
        timenow = round(time.time())
        cooldown = await self.client.pool_pg.fetchrow("SELECT * FROM cooldowns WHERE command_name = $1 and member_id = $2 and time > $3", ctx.command.name, ctx.author.id, timenow)
        if cooldown is not None:
            return await ctx.send(f"You're on cooldown. try again in {humanize_timedelta(seconds=(cooldown.get('time') - timenow))}.", delete_after=10.0)
        cooldown = await self.client.pool_pg.fetchrow(
            "SELECT * FROM cooldowns WHERE command_name = $1 and member_id = $2 and time < $3", ctx.command.name, ctx.author.id, timenow)
        if cooldown:
            await self.client.pool_pg.execute("DELETE FROM cooldowns WHERE command_name = $1 and member_id = $2 and time = $3", cooldown.get('command_name'), cooldown.get('member_id'), cooldown.get('time'))
        originaloverwrite = genchat.overwrites_for(ctx.guild.default_role) # this is the overwrite that will be restored to gen chat when the lockdown is over
        newoverwrite = genchat.overwrites_for(ctx.guild.default_role) # this is the overwrite that i will edit to lockdown the channel
        authornewoverwrite = genchat.overwrites_for(ctx.author) # this is the overwrite that I will edit to allow the invoker to continue talking
        authornewoverwrite.send_messages=True # this edits the author's overwrite
        newoverwrite.send_messages = False # this edits the @everyone overwrite
        authororiginaloverwrite = None if ctx.author not in genchat.overwrites else genchat.overwrites_for(ctx.author) # this is the BEFORE overwrite for an individual member, if the author already had an overwrite (such as no react) it will use that to restore, otherwise None since it won't have any overwrites in the first place
        self.gen_is_muted = True
        await self.client.pool_pg.execute("INSERT INTO cooldowns VALUES($1, $2, $3)", ctx.command.name, ctx.author.id, timenow + 10800)
        try:
            await genchat.set_permissions(ctx.author, overwrite=authornewoverwrite, reason=f"{ctx.author} invoked a lockdown with the lockgen command") # allows author to talk
            await genchat.set_permissions(ctx.guild.default_role, overwrite = newoverwrite, reason = f"5 second lockdown initiated by {ctx.author.name}#{ctx.author.discriminator}") # does not allow anyone else to talk
        except discord.Forbidden:
            ctx.command.reset_cooldown(ctx)
            self.gen_is_muted = False
            return await ctx.send(f"I do not have the required permission to lock down **{genchat.name}**.")
        message = await ctx.send(f"✅ Locked down **{genchat.name}** for 5 seconds.")
        await asyncio.sleep(5)
        try:
            await genchat.set_permissions(ctx.guild.default_role, overwrite = originaloverwrite, reason = "Lockdown over uwu") # restores
            await genchat.set_permissions(ctx.author, overwrite = authororiginaloverwrite, reason = "Overwrite no longer required") # restores
        except discord.Forbidden:
            self.gen_is_muted = False
            return await ctx.send(f"I do not have the required permission to remove the lockdown for **{genchat.name}**.")
        else:
            try:
                await message.add_reaction("🔓")
            except:
                pass
        self.gen_is_muted = False

    @checks.requires_roles()
    @commands.command(name="scramble", aliases=["shuffle"])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def scramble(self, ctx, member: discord.Member=None):
        """
        Scrambles your target's nickname for 3 minutes, effectively freezing it until the 3 minutes are up.
        """
        if member is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You have to tell me whose name you want to scramble, man. `dv.scramble [member]`")
        if member.bot:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("I ain't bullying bots.")
        if await self.client.pool_pg.fetchval("SELECT user_id FROM freezenick WHERE user_id = $1", member.id):
            raise NicknameIsManaged()
        if member == ctx.author:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Why change your own nickname when you can scramble others' nicknames?")
        member_name = member.display_name
        if len(member_name) == 1:
            if len(member.name) != 1:
                member_name = member.name
            else:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("Their name only has one character, it's not worth it.")
        async def scramble_nickname():
            tries = 0
            while True:
                if tries < 10:
                    lst_member_name = list(member_name)
                    random.shuffle(lst_member_name)
                    new_name = ''.join(lst_member_name)
                    if await self.client.check_blacklisted_content(new_name) or new_name == member.display_name:
                        tries += 1
                    else:
                        return new_name
                else:
                    return None
        new_name = await scramble_nickname()
        if new_name is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"I can't scramble **{member.name}**'s name as their scrambled name will still be the same/the resulting name is blacklisted.")
        try:
            await member.edit(nick=new_name, reason=f"Nickname scrambled by {ctx.author}")
        except discord.Forbidden:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Sorry! I am unable to change that user's name, probably due to role hierachy or missing permissions.")
        await self.client.pool_pg.execute("INSERT INTO freezenick(user_id, guild_id, nickname, old_nickname, time, reason, responsible_moderator) VALUES($1, $2, $3, $4, $5, $6, $7)", member.id, ctx.guild.id, new_name, member_name, round(time.time()) + 180, f"[Scrambled nickname]({ctx.message.jump_url})", ctx.author.id)
        await ctx.send(f"{member}'s name is now {new_name}!\n{member.mention}, your nickname/username has been scrambled by **{ctx.author.name}** and it is frozen for 3 minutes. It will automatically revert to your previous nickname/username after. ")

    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="firstmessage", aliases=['fm'])
    async def firstmessage(self, ctx, channel: discord.TextChannel = None):
        """
        Shows the first message of the specified channel.
        """
        if channel is None:
            channel = ctx.channel
        try:
            message: discord.Message = (await channel.history(limit=1, oldest_first=True).flatten())[0]
        except (discord.Forbidden, discord.HTTPException):
            return await ctx.send("I was unable to read message history for {}.".format(channel.mention))
        em = discord.Embed(description=f"[First Message in **{channel.name}**]({message.jump_url})\n>>> {message.content[:100] if len(message.content) > 100 else message.content}", color=self.client.embed_color, timestamp=message.created_at)
        em.set_footer(text="Sent on:")
        em.set_author(name=f"Sent by: {message.author.display_name}", icon_url=message.author.display_avatar.url)
        await ctx.send(embed=em)

    @checks.requires_roles()
    @commands.cooldown(1200, 1, commands.BucketType.user)
    @commands.command(name="chatchart", aliases=['cc'])
    async def chatchart(self, ctx, channel: Union[discord.TextChannel, str] = None):
        """
        Shows the percentage of messages sent by various members.
        Add the --bots flag to include bots in the chatchart.
        """
        if self.chatchart_is_running == True:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("This command is being run by another user at the moment. To prevent API spam, please try again later.")
        data = {}
        if channel is None or type(channel) is str:
            channel = ctx.channel
        embed=discord.Embed(title=f"Shuffling through #{channel}'s message history...", description=f"Fetching messages from Discord's API...", color=self.client.embed_color)
        statusmessage = await ctx.send(embed=embed)
        messagecount = 0
        self.chatchart_is_running = True
        async for message in channel.history(limit=5000):
            if isinstance(message.author, discord.Member):
                if discord.utils.get(message.author.roles, name="No Tags"):
                    pass
                else:
                    authorid = message.author.id
                    if message.author.bot:
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
            if messagecount %500 == 0:
                embed=discord.Embed(title=f"Shuffling through #{channel}'s message history...", description=f"**{messagecount}** of the last **5000** messages scanned.\n\n{generate_loadbar(messagecount/5000, 10)}", color=self.client.embed_color)
                try:
                    await statusmessage.edit(embed=embed)
                except:
                    statusmessage = await ctx.send(embed=embed)
        counted = sorted(data.items(), key=operator.itemgetter(1), reverse=True)
        """
        This removes the extra authors from the earlier dictionary so it's only 19 authors and 1 others
        """
        if len(counted) > 20:
            others_element = ("Others", 0)
            counted.append(others_element)
            while len(counted) > 20:
                counted.pop(19)
                counted.remove(others_element)
                others_element = ("Others", others_element[1] + 1)
                counted.append(others_element)
        labels = []
        sizes = []
        for entry in counted:
            if entry[0] == "Others":
                labels.append("Others")
            else:
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
        plt.title(f"Messages in #{channel.name}", color='w')
        colors = ['#3d405b', '#005f73', '#0a9396', '#94d2bd', '#e9d8a6', '#ee9b00', '#ca6702', '#bb3e03', '#ae2012', '#9b2226', '#3d405b', '#005f73', '#0a9396', '#94d2bd', '#e9d8a6', '#ee9b00', '#ca6702', '#bb3e03', '#ae2012', 'grey']
        plt.pie(sizes, colors=colors)
        plt.legend(bbox_to_anchor=(1, 0.5), loc='center left', labels=newlabels, facecolor="gray", edgecolor="white")
        filename = f"temp/{random.randint(0,9999999)}.png"
        plt.savefig(filename, bbox_inches="tight", pad_inches=0.1, transparent=True)
        embed = discord.Embed(title=f"Sending chatchart for #{channel}...", color=self.client.embed_color)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/871737314831908974/880374020267212830/discord_loading.gif")
        await statusmessage.edit(embed=embed)
        file = discord.File(filename)
        await ctx.send(file=file)
        self.chatchart_is_running = False
        await statusmessage.delete()
        os.remove(filename)

        if ctx.author.id in [650647680837484556, 321892489470410763]:
            ctx.command.reset_cooldown(ctx)

    @commands.command(name="covidvbot", aliases=["covid", "infect"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def covidbot(self, ctx):
        """
        Fetches information about CoviDVBot.
        """
        class description(discord.ui.View):
            def __init__(self, embed1, embed2, author):
                self.embed1 = embed1
                self.embed2 = embed2
                self.response = None
                self.author = author
                super().__init__(timeout=None)

            @discord.ui.button(label="Description of CoviDVBot", style=discord.ButtonStyle.green)
            async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
                await self.response.edit(embed=self.embed1)

            @discord.ui.button(label="CoviDVBot Statistics", style=discord.ButtonStyle.red)
            async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
                await self.response.edit(embed=self.embed2)

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user.id != self.author.id:
                    await interaction.response.send_message("These buttons aren't for you!", ephemeral=True)
                    return False
                return True

            async def on_timeout(self) -> None:
                self.returning_value = None
                for b in self.children:
                    b.disabled = True
                await self.response.edit(view=self)



        covidinfectors = await self.client.pool_pg.fetch("SELECT * FROM infections ORDER BY infectioncase DESC")
        um = f"CoviDVBot, also known as **Co**rona**vi**rus **D**isease of Dank Vibes **Bot**, is a coronavirus that emerged in January 2022. CoviDVBot is not known to cause any side effects to a user. It first originated from a bot called {self.client.user}, before evolving and being able to infect humans. (Patient Zero is Argon#0002)\nCoviDVBot is spread through interacting with other humans, especially via mentioning someone.\nThere is no known cure for CoviDVBot, hence once infected, the disease will stay with the user for eternity."
        embed1 = discord.Embed(title="CoviDVBot At a Glance", description=um, color=self.client.embed_color)
        nooo = {}
        for covidinfector in covidinfectors:
            userid = covidinfector.get('infector')
            if userid not in nooo:
                nooo[userid] = 1
            else:
                nooo[userid] = nooo[userid] + 1
        top_infectors = dict(sorted(nooo.items(), key=lambda x: x[1], reverse=True))
        final = dict(islice(top_infectors.items(), 3))
        superspreaders = []
        for spreader in final:
            member = self.client.get_user(spreader)
            if member is None:
                superspreaders.append(f"{spreader} - {final[spreader]}")
            else:
                name = f"{member} - {final[spreader]}"
                superspreaders.append(name)
        most_recent_infections = covidinfectors[:3]
        user_ids = [covid.get('member_id') for covid in covidinfectors]
        if ctx.author.id in user_ids:
            is_infected = True
        else:
            is_infected = False
        if is_infected:
            govmessage = "😷 **You have been diagnosed with CoviDVBot.**\nPlease head to the nearest quarantine facility to facilitate your recovery."
            users_infected_byauthor = [covid.get('member_id') for covid in covidinfectors if covid.get('infector') == ctx.author.id]
            if len(users_infected_byauthor) > 0:
                if len(users_infected_byauthor) <= 3:
                    infector_list = [str(self.client.get_user(user)) for user in users_infected_byauthor if self.client.get_user(user) is not None]
                    infector_list = ", ".join(infector_list)
                else:
                    infector_list = [str(self.client.get_user(user)) for user in users_infected_byauthor[:3] if self.client.get_user(user) is not None]
                    infector_list = ", ".join(infector_list) + f"and {len(users_infected_byauthor) - 3} others"
                embed1.add_field(name=f"People you infected ({len(users_infected_byauthor)})", value=f"{infector_list}", inline=True)
            else:
                embed1.add_field(name="People you infected", value="No one (yet)", inline=True)
            embed1.add_field(name="Your Status", value=govmessage, inline=False)
        else:
            govmessage = "<:DVB_True:887589686808309791> **You do not have CoviDVBot.**\nPlease stay safe."
            embed1.add_field(name="Your Status", value=govmessage, inline=False)
        embed2 = discord.Embed(title="CoviDVBot At a Glance", color=self.client.embed_color)
        if is_infected:
            govmessage = "😷 **You have been diagnosed with CoviDVBot.**\nPlease head to the nearest quarantine facility to facilitate your recovery."
            users_infected_byauthor = [covid.get('member_id') for covid in covidinfectors if covid.get('infector') == ctx.author.id]
            if len(users_infected_byauthor) > 0:
                if len(users_infected_byauthor) <= 3:
                    infector_list = [str(self.client.get_user(user)) for user in users_infected_byauthor if self.client.get_user(user) is not None]
                    infector_list = "**" + ", ".join(infector_list) + "**"
                else:
                    infector_list = [str(self.client.get_user(user)) for user in users_infected_byauthor[:3] if self.client.get_user(user) is not None]
                    infector_list = "**" + ", ".join(infector_list) + f"** and {len(users_infected_byauthor) - 3} others"
                embed2.add_field(name=f"People you infected ({len(users_infected_byauthor)})", value=f"{infector_list}", inline=True)
            else:
                embed2.add_field(name="People you infected", value="No one (yet)", inline=True)
            infectiontrack = []
            def get_infector(infected):
                for covid in covidinfectors:
                    if covid.get('infector') == self.client.user.id:
                        return None
                    elif covid.get('member_id') == infected:
                        return covid.get('infector')
                return None
            infectiontrack.append(f"**{ctx.author}**")
            infector = get_infector(ctx.author.id)
            if infector is not None:
                user = self.client.get_user(infector)
                if user is not None:
                    user = str(user)
                else:
                    user = str(infector)
                infectiontrack.append(user)
            while infector is not None:
                infector = get_infector(infector)
                if infector is not None:
                    user = self.client.get_user(infector)
                    if user is not None:
                        infectiontrack.append(str(user))
                    else:
                        infectiontrack.append(f"{infector}")
            if len(infectiontrack) > 0:
                infector_list = " <- ".join(infectiontrack)
                embed2.add_field(name="How you were infected", value=f"{infector_list}", inline=True)
            embed2.add_field(name="Your Status", value=govmessage, inline=False)
        else:
            govmessage = "<:DVB_True:887589686808309791> **You do not have CoviDVBot.**\nPlease stay safe."
            embed2.add_field(name="Your Status", value=govmessage, inline=False)
        embed2.add_field(name="Infected", value=f"{len(covidinfectors)}", inline=True)
        embed2.add_field(name="Superspreaders", value='\n'.join(superspreaders), inline=True)
        embed2.add_field(name="Deaths", value="0", inline=True)
        embed2.add_field(name="Recovered", value="0", inline=True)
        most_recent_infections_lst = []
        for recent_infection in most_recent_infections:
            member_id = recent_infection.get('member_id')
            member = self.client.get_user(member_id)
            #infector = self.client.get_user(recent_infection.get('infector')) or "Unknown"
            if member is None:
                member = f"{member_id} - <t:{recent_infection.get('timeinfected')}:R>"
            else:
                member = f"{member} - <t:{recent_infection.get('timeinfected')}:R>"
            most_recent_infections_lst.append(member)
        embed2.add_field(name="Most recent infections", value='\n'.join(most_recent_infections_lst), inline=True)
        view = description(embed1, embed2, ctx.author)
        view.response = await ctx.send(embed=embed1, view=view)
        await view.wait()

    @checks.in_beta()
    @commands.cooldown(1, 10800, commands.BucketType.user)
    @commands.command(name="sus")
    async def sus(self, ctx):
        """
        Undefined
        """
        choice = random.randint(1, 2)
        if choice == 1:
            name = ctx.author.display_name
            name = name + " ඞ"
            if len(name) > 32:
                choice = random.randint(1, 2)
            else:
                try:
                    await ctx.author.edit(nick=name)
                except discord.Forbidden:
                    choice = random.randint(1, 2)
                else:
                    await ctx.send(f"{ctx.author.mention} ඞ")
                    return
        if choice == 2:
            async with aiohttp.ClientSession() as session:
                url=f"https://g.tenor.com/v1/search?q=among+us&key={tenorAPI}&limit=100"
                async with session.get(url) as resp:
                    data = await resp.json()
                    gif = random.choice(data.get('results'))
                    gif = gif.get('media')[0].get('gif').get('url')
                    await ctx.send(gif)
        else:
            print('nooo')