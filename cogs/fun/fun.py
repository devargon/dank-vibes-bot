from datetime import datetime
from textwrap import dedent

import discord
from discord import Webhook
from discord.commands import Option
from discord.ext import commands

from main import dvvt
from utils.context import DVVTcontext

import os
import json
import time
import random
import aiohttp
import asyncio
import operator
import alexflipnote
from typing import Union, Optional
import matplotlib.pyplot as plt
from palettable.tableau import Tableau_20
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
from itertools import islice

from utils import checks
from utils.time import humanize_timedelta
from utils.errors import ArgumentBaseError, NicknameIsManaged
from utils.format import generate_loadbar, proper_userf, truncate_text
from .apple_shortcuts import AppleShortcuts

from .dm import dm
from .snipe import snipe
from .itemgames import ItemGames
from .games import games
from .color import color
from .fun_slash import FunSlash
from .bigmoji import Bigmoji

CALSANSUI_GEOBOLD = "assets/fonts/CalSansUI-GeoBold.otf"
CALSANSUI_UISEMIBOLD = "assets/fonts/CalSansUI-UISemiBold.otf"

TITLE_FONT = FontProperties(fname=CALSANSUI_GEOBOLD)
LEGEND_FONT = FontProperties(fname=CALSANSUI_UISEMIBOLD)

alexflipnoteAPI = os.getenv('alexflipnoteAPI')
tenorAPI = os.getenv('tenorAPI')

RandomColorID = 943530953110880327 if os.getenv('state') == '1' else 1317873362994987018

_DUMBFIGHT_ACTIONS = [
    "{winmen} reported the impostor {losemen}.",
    "{winmen} fought {losemen}.",
    "{winmen} farted on {losemen}.",
    "{winmen} rickrolled {losemen}.",
    "{winmen} took a huge dump on {losemen}.",
    "{winmen} landed a soft punch on {losemen}.",
    "{winmen} kicked {losemen} in *that* area.",
    "{winmen} didn't need to do anything; {losemen} saw the simps in this server and fainted.",
    "{winmen} used the 6 Infinity Stones to fight {losemen}.",
    "{winmen} was a coward and got Thanos to fight {losemen}.",
    "{losemen} cheated on {winmen} and lost the court case.",
    "{winmen} freeze-rayed {losemen}.",
    "{winmen} won a game of Fortnite against {losemen}.",
    "{losemen} lagged and took the W.",
    "{losemen} saw {winmen} vent and die.",
    "{winmen} did {losemen}'s mom.",
    "{losemen} slipped on {winmen}'s banana.",
    "{winmen} caught {losemen} in 4K while fighting. 😳",
    "{winmen} turned hacks on.",
    "{winmen} fed {losemen} foot lettuce and {losemen} died.",
    "{winmen} made {losemen} look at the mirror.",
    "{winmen} told {losemen} that their dad went out to get milk.",
    "{winmen} exposed {losemen}'s speedrun.",
    "{losemen} tried to ratio {winmen}.",
    "{winmen} told {losemen} that their Discord kitten doesn't love them.",
    "{winmen} touched grass and became a god.",
    "{winmen} said {losemen}'s memes suck.",
    "{winmen} scammed {losemen} out of their life insurance.",
    "{losemen} got head-shot by {winmen}.",
    "{losemen} looked at {winmen}'s search history.",
    "{losemen} tried insulting {winmen}'s grandma.",
    "> {winmen}: We don't talk about {losemen}, no, no, no!",
    "{winmen} forced {losemen} to sleep.",
    "{losemen} got stuck in the backrooms.",
    "{losemen} ate a fishbone and died.",
    "{losemen} tried making out with {winmen}'s wife.",
    "{losemen} took a shower after 3 years.",
    "{losemen} thought they were cool and tried hitting on {winmen}.",
    "{losemen} put milk before cereal in front of {winmen}.",
    "{winmen} EMOTIONALLY DAMAGED {losemen}.",
    "{losemen} raged over a game because {winmen} tilted them so bad.",
    "{losemen} tried listening to to {winmen}'s instructions and breathe but died.",
    "{losemen} became a Discord Mod.",
    "{losemen} raged over video games while playing with {winmen}.",
    "{losemen} sent sus images to {winmen}. 🤨",
    "{losemen} leaned too much on the chair.",
    "{losemen} missed the ender pearl shot because {winmen} distracted them.",
    "{losemen} put their socks in water in front of {winmen}.",
    "{losemen} mined straight into the desert temple as they were distracted by {winmen}.",
    "{winmen} told {losemen} to mine straight down in Minecraft.",
    "{losemen} tried to crack 90s in front of {winmen} and died.",
]

_DUMBFIGHT_SELF_ACTIONS = [
    'punched themselves in the face',
    'kicked themselves in the knee',
    'stepped on their own feet',
    'punched themselves in the stomach',
    "tickled themselves until they couldn't take it",
]

class Fun(Bigmoji, FunSlash, color, games, ItemGames, snipe, dm, AppleShortcuts, commands.Cog, name='fun'):
    """
    Fun commands
    """
    def __init__(self, client: dvvt):
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
        self.rcdata = ""
        self.alex_api = alexflipnote.Client()
        self.rantimes = {}
        self.session = None
        self.server = client.server
        with open('assets/localization/dumbfight_statements.json', 'r') as f:
            self.dumbfight_statements = json.load(f)

    def format_help_for_context(self, ctx: commands.Context):
        """
        Thanks Sinbad!
        """
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nCog Version: {self.__version__}"

    async def cap_change(self, message: str) -> str:
        result = ""
        for char in message:
            value = random.choice([True, False])
            if value:
                result += char.upper()
            else:
                result += char.lower()
        return result



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
            return commands.Cooldown(1, 450)
        elif discord.utils.get(message.author.roles, id=931174008970444800): # weekly top grinder
            return commands.Cooldown(1, 450)
        elif discord.utils.get(message.author.roles, name="Server Booster"): # previously investor
            return commands.Cooldown(1, 1200)
        else:
            return commands.Cooldown(1, 1800)

    async def cog_check(self, ctx):
        if ctx.author.id == 312876934755385344 or ctx.author.guild_permissions.administrator == True:
            return True
        else:
            if discord.utils.get(ctx.author.roles, name="No Tags"):
                raise ArgumentBaseError(message="You have the **No Tags** role and can't use any commands in the **Fun** category. <:dv_pepeHahaUSuckOwO:837653798313918475>")
        return True

    def _determine_base_winner(self, won_count: int, lost_count: int) -> bool:
        if lost_count == 0:
            return random.choice([True, False])
        ratio = won_count / lost_count
        if ratio == 0 or 0.7 <= ratio <= 1.5:
            return random.choice([True, False])
        return ratio < 0.7  # losing a lot → give author a win; winning a lot → give author a loss

    async def _get_active_potion(self, user_id: int):
        row = await self.client.db.fetchrow(
            "SELECT dumbfight_result, dumbfight_rig_duration FROM userconfig WHERE user_id = $1", user_id
        )
        if (row is not None
                and row.get('dumbfight_rig_duration') is not None
                and row.get('dumbfight_rig_duration') > round(time.time())):
            return row.get('dumbfight_result')
        return None

    def _resolve_potion_outcome(self, doesauthorwin: bool, author_potion, target_potion, author, member):
        extra_info = None
        if author_potion is not None:
            if target_potion is not None:
                if author_potion == target_potion:
                    doesauthorwin = random.choice([True, False])
                    extra_info = (f"Both {proper_userf(author)} and {proper_userf(member)} have drank a "
                                  f"dumbfight shield potion, so the result was randomly decided.")
                else:
                    if target_potion is True:
                        doesauthorwin = False
                        extra_info = f"{proper_userf(member)} has drank a dumbfight shield potion to make them win."
                    elif author_potion is False:
                        doesauthorwin = False
                        extra_info = f"{proper_userf(author)} has drank a dumbfight shield potion to make them lose."
                    elif target_potion is False:
                        doesauthorwin = True
                        extra_info = f"{proper_userf(member)} has drank a dumbfight shield potion to make them lose."
                    elif author_potion is True:
                        doesauthorwin = True
                        extra_info = f"{proper_userf(author)} has drank a dumbfight shield potion to make them win."
            else:
                doesauthorwin = author_potion is True
                action = "win" if author_potion is True else "lose"
                extra_info = f"{proper_userf(author)} has drank a dumbfight shield potion to make them {action}."
        elif target_potion is not None:
            doesauthorwin = target_potion is False
            action = "win" if target_potion is True else "lose"
            extra_info = f"{proper_userf(member)} has drank a dumbfight shield potion to make them {action}."
        return doesauthorwin, extra_info

    @checks.perm_insensitive_roles()
    @commands.dynamic_cooldown(lowered_cooldown, commands.BucketType.user)
    @commands.group(name="dumbfight", aliases = ["df"], invoke_without_command=True)
    async def dumbfight(self, ctx, member: discord.Member = None):
        """
        Mute people for a random duration between 30 to 120 seconds.
        """
        if self.gen_is_muted and ctx.channel.id == 1288032530569625663:
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
            return await ctx.send("This is a **dumb**fight. Use it on dumb people and back off the bots.")
        if member == ctx.me:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("How do you expect me to mute myself?")
        if ctx.channel.id in [748758938836795653, 735477033949462578] or "mafia" in ctx.channel.name:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You cannot use dumbfights in events or mafia channels.")
        if isinstance(ctx.channel, discord.Thread):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Dumbfight is not supported in threads yet. Sorry >.<")

        duration = random.randint(30, 120)

        won_dumbfights = await self.client.db.fetch(
            "SELECT * FROM dumbfightlog where did_win = $1 and invoker_id = $2", 1, ctx.author.id)
        lost_dumbfights = await self.client.db.fetch(
            "SELECT * FROM dumbfightlog where did_win = $1 and invoker_id = $2", 0, ctx.author.id)
        doesauthorwin = self._determine_base_winner(len(won_dumbfights), len(lost_dumbfights))

        author_potion = await self._get_active_potion(ctx.author.id)
        target_potion = await self._get_active_potion(member.id)
        doesauthorwin, extra_info = self._resolve_potion_outcome(
            doesauthorwin, author_potion, target_potion, ctx.author, member)

        if author_potion is None and ctx.author.id == 312876934755385344:
            content_lower = ctx.message.content.lower()
            if content_lower.endswith('win'):
                doesauthorwin = True
            elif content_lower.endswith('lose'):
                doesauthorwin = False

        if doesauthorwin:
            muted, winner, loser = member, ctx.author.mention, member.mention
            embed_color = 0x00ff00
        else:
            muted, winner, loser = ctx.author, member.mention, ctx.author.mention
            embed_color = 0xff0000

        if ctx.author == member:
            description = (f"{muted.mention} {random.choice(_DUMBFIGHT_SELF_ACTIONS)}.\n"
                           f"{muted.mention} is now muted for {duration} seconds.")
        else:
            action = random.choice(_DUMBFIGHT_ACTIONS).format(winmen=winner, losemen=loser)
            description = f"{action}\n{muted.mention} lost and is now muted for {duration} seconds."

        if extra_info is None:
            await self.client.db.execute(
                "INSERT INTO dumbfightlog values($1, $2, $3)", ctx.author.id, member.id, 1 if doesauthorwin else 0)

        channel = ctx.channel
        original_overwrite = channel.overwrites_for(muted) if muted in channel.overwrites else None
        temp_overwrite = channel.overwrites_for(muted) if muted in channel.overwrites else discord.PermissionOverwrite()
        temp_overwrite.send_messages = False
        await channel.set_permissions(muted, overwrite=temp_overwrite)

        if ctx.channel.id in self.mutedusers:
            self.mutedusers[ctx.channel.id].append(muted.id)
        else:
            self.mutedusers[ctx.channel.id] = [muted.id]

        embed = discord.Embed(title="Get muted!", description=description, colour=embed_color)
        if extra_info is not None:
            embed.set_footer(text=extra_info, icon_url="https://cdn.discordapp.com/emojis/944226900988026890.webp?size=96&quality=lossless")
        await ctx.send(embed=embed)

        await asyncio.sleep(duration)
        await channel.set_permissions(muted, overwrite=original_overwrite)
        if muted.id in self.mutedusers.get(ctx.channel.id, []):
            channel_muted = self.mutedusers[ctx.channel.id]
            if len(channel_muted) == 1:
                del self.mutedusers[ctx.channel.id]
            else:
                channel_muted.remove(muted.id)


    @checks.perm_insensitive_roles()
    @dumbfight.command(name="statistics", aliases = ["stats"])
    async def dfstatistics(self, ctx, member:discord.Member=None):
        if member is None:
            won_dumbfights = await self.client.db.fetch("SELECT * FROM dumbfightlog where did_win = $1", 1)
            lost_dumbfights = await self.client.db.fetch("SELECT * FROM dumbfightlog where did_win = $1", 0)
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
            embed=discord.Embed(title="Dumbfight statistics", description = f"Number of dumbfights won: {len(won_dumbfights)}\nNumber of dumbfights lost: {len(lost_dumbfights)}", color = 0x1E90FF if ctx.author.id == 312876934755385344 else 0xffcccb)
            top3won = [f"<@{user[0]}>: {user[1]}" for user in won_users[:3]]
            top3won = "\n".join(top3won)
            top3lost = [f"<@{user[0]}>: {user[1]}" for user in lost_users[:3]]
            top3lost = "\n".join(top3lost)
            embed.add_field(name="Top 3 wiwnners", value = top3won)
            embed.add_field(name="Top 3 lost dumbfighters", value=top3lost)
            await ctx.send(embed=embed)
        else:
            won_dumbfights = await self.client.db.fetch("SELECT * FROM dumbfightlog where did_win = $1 and invoker_id = $2", 1, member.id)
            lost_dumbfights = await self.client.db.fetch("SELECT * FROM dumbfightlog where did_win = $1 and invoker_id = $2", 0, member.id)
            non_invoked_losses = await self.client.db.fetch("SELECT * FROM dumbfightlog where did_win = $1 and target_id = $2", 1, member.id)
            non_invoked_wins = await self.client.db.fetch("SELECT * FROM dumbfightlog where did_win = $1 and target_id = $2", 0, member.id)
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
            embed=discord.Embed(title=f"Dumbfight statistics for {proper_userf(member)}", description=f"Number of dumbfights won: {len(won_dumbfights)}\nNumber of dumbfights lost: {len(lost_dumbfights)}\n\nNumber of wins from non-self-invoked dumbfights: {len(non_invoked_wins)}\nNumber of losses from non-self-invoked dumbfights: {len(non_invoked_losses)}\n\n**Total** number of **wins**: {len(won_dumbfights) + len(non_invoked_wins)}\n**Total** number of **losses**: {len(lost_dumbfights) + len(non_invoked_losses)}",color = 0x1E90FF if ctx.author.id == 312876934755385344 else 0xffcccb)
            message = await ctx.send(f"React with 🥺 to view more information about **{proper_userf(member)}**'s dumbfight statistics.", embed=embed)
            await message.add_reaction("🥺")
            def check(payload):
                return str(payload.emoji == "🥺") and payload.user_id == ctx.author.id  and payload.message_id == message.id
            try:
                await self.client.wait_for('raw_reaction_add', check=check, timeout = 20.0)
            except asyncio.TimeoutError:
                await message.clear_reactions()
            else:
                await message.clear_reactions()
                embed.add_field(name=f"Last few wins and losses for {proper_userf(member)}", value=text)
                await message.edit(content="🥺", embed=embed)

    @checks.perm_insensitive_roles()
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
            return await ctx.send(f"Your accompanying message is currently {len(message)} characters long; it can only be at most 180 characters.")
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
        webhook = await self.client.get_webhook(channel)
        await webhook.send(content, username="You were hidepinged", avatar_url="https://cdn.discordapp.com/attachments/871737314831908974/895639630429433906/incognito.png")
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url('https://canary.discord.com/api/webhooks/883563427455438858/GsF8ZPIemw6D-x6TIp7wO88ySQizKePKCS5zRA-EBtNfHRC15e9koti7-02GKBuoZ_Yi', session=session)
            embed=discord.Embed(title=f"Hideping command invoked with {ctx.me}", color=discord.Color.green())
            embed.add_field(name="Author", value=f"**{ctx.author}** ({ctx.author.id})", inline=True)
            embed.add_field(name="Target", value=f"**{proper_userf(member)}** ({member.id})", inline=True)
            embed.add_field(name="Message", value=message or "No message", inline=True)
            await webhook.send(embed=embed, username=f"{self.client.user.name} Logs")



    @checks.perm_insensitive_roles()
    @commands.command(name="lockgen", aliases = ["lg"])
    @commands.cooldown(1, 120, commands.BucketType.guild)
    async def lockgen(self, ctx):
        """
        Locks specified channel for 5 seconds
        """
        genchatid = 1288032530569625663 # DV's genchat: 1288032530569625663
        genchat = self.client.get_channel(genchatid)
        if genchat is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"Could not find a channel with the ID {genchatid}.")
        if ctx.channel != genchat:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"This command can only be used in {genchat.mention}!")
        timenow = round(time.time())
        cooldown = await self.client.db.fetchrow("SELECT * FROM cooldowns WHERE command_name = $1 and member_id = $2 and time > $3", ctx.command.name, ctx.author.id, timenow)
        if cooldown is not None:
            return await ctx.send(f"You're on cooldown. try again in {humanize_timedelta(seconds=(cooldown.get('time') - timenow))}.", delete_after=10.0)
        cooldown = await self.client.db.fetchrow(
            "SELECT * FROM cooldowns WHERE command_name = $1 and member_id = $2 and time < $3", ctx.command.name, ctx.author.id, timenow)
        if cooldown:
            await self.client.db.execute("DELETE FROM cooldowns WHERE command_name = $1 and member_id = $2 and time = $3", cooldown.get('command_name'), cooldown.get('member_id'), cooldown.get('time'))
        originaloverwrite = genchat.overwrites_for(ctx.guild.default_role) # this is the overwrite that will be restored to gen chat when the lockdown is over
        newoverwrite = genchat.overwrites_for(ctx.guild.default_role) # this is the overwrite that i will edit to lockdown the channel
        authornewoverwrite = genchat.overwrites_for(ctx.author) # this is the overwrite that I will edit to allow the invoker to continue talking
        authornewoverwrite.send_messages=True # this edits the author's overwrite
        newoverwrite.send_messages = False # this edits the @everyone overwrite
        authororiginaloverwrite = None if ctx.author not in genchat.overwrites else genchat.overwrites_for(ctx.author) # this is the BEFORE overwrite for an individual member, if the author already had an overwrite (such as no react) it will use that to restore, otherwise None since it won't have any overwrites in the first place
        self.gen_is_muted = True
        await self.client.db.execute("INSERT INTO cooldowns VALUES($1, $2, $3)", ctx.command.name, ctx.author.id, timenow + 10800)
        try:
            await genchat.set_permissions(ctx.author, overwrite=authornewoverwrite, reason=f"{ctx.author} invoked a lockdown with the lockgen command") # allows author to talk
            await genchat.set_permissions(ctx.guild.default_role, overwrite = newoverwrite, reason = f"5 second lockdown initiated by {proper_userf(ctx.author)}") # does not allow anyone else to talk
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

    @checks.perm_insensitive_roles()
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
        if await self.client.db.fetchval("SELECT user_id FROM freezenick WHERE user_id = $1", member.id):
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
        await self.client.db.execute("INSERT INTO freezenick(user_id, guild_id, nickname, old_nickname, time, reason, responsible_moderator) VALUES($1, $2, $3, $4, $5, $6, $7)", member.id, ctx.guild.id, new_name, member_name, round(time.time()) + 180, f"[Scrambled nickname]({ctx.message.jump_url})", ctx.author.id)
        await ctx.send(f"{proper_userf(member)}'s name is now {new_name}!\n{member.mention}, your nickname/username has been scrambled by **{ctx.author.name}** and it is frozen for 3 minutes. It will automatically revert to your previous nickname/username after. ")

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

    @checks.perm_insensitive_roles()
    @commands.cooldown(1200, 1, commands.BucketType.user)
    @commands.command(name="chatchart", aliases=['cc'])
    async def chatchart(self, ctx: DVVTcontext, channel: Union[discord.TextChannel, str] = None):
        """
        Shows the percentage of messages sent by various members.
        Add the --bots flag to include bots in the chatchart.
        """
        MAX_ENTRIES_TO_SHOW = 20
        LABEL_MAX_LENGTH = 35
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
            messagecount += 1
            if messagecount %500 == 0:
                embed.description=f"**{messagecount}** of the last **5000** messages scanned.\n\n{generate_loadbar(messagecount/5000, 10)}"
                try:
                    await statusmessage.edit(embed=embed)
                except:
                    statusmessage = await ctx.send(embed=embed)
            if isinstance(message.author, discord.Member):
                if discord.utils.get(message.author.roles, name="No Tags"):
                    continue
                else:
                    authorid = message.author.id
                    if message.author.bot and not ctx.message.content.endswith("--bots"):
                        continue
                    if authorid not in data:
                        data[authorid] = 1
                    else:
                        data[authorid] += 1
        counted = sorted(data.items(), key=operator.itemgetter(1), reverse=True)
        # This removes the extra authors from the earlier dictionary so it's only 19 authors and 1 others
        if len(counted) > MAX_ENTRIES_TO_SHOW:
            first_n = MAX_ENTRIES_TO_SHOW - 1
            top = counted[:first_n]
            others_total = sum(count for _, count in counted[first_n:])
            counted = top + [("Others", others_total)]
        labels = []
        sizes = []
        for user_id_or_label, count in counted:
            if user_id_or_label == "Others":
                labels.append("Others")
            else:
                server_user = None
                server_member = ctx.guild.get_member(user_id_or_label)
                if server_member is None:
                    server_user = self.client.get_user(user_id_or_label)
                if server_member:
                    labels.append(truncate_text(server_member.display_name, LABEL_MAX_LENGTH))
                elif server_user:
                    labels.append(truncate_text(server_user.display_name, LABEL_MAX_LENGTH))
                else:
                    labels.append("Unknown user")
            sizes.append(count)
        if len(labels) == 0:
            await statusmessage.delete()
            await ctx.send("There were no entries to display in chatchart. This can happen as: \n    • No one had talked in the channel.\n    • `--nobots` was used but there're only bots talking.\n    • I do not have `Read Message History` permissions.")
            return

        fig, ax = plt.subplots(figsize=plt.figaspect(1), facecolor="#323339")
        ax.set_facecolor("#323339")
        newlabels = []
        for place, (l, s) in enumerate(zip(labels, sizes), start=1):
            front_emoji = f"{place}. "
            if len(front_emoji) == 3:
                front_emoji = "\u2009" + front_emoji
            p = s / sum(sizes) * 100
            print(p, s, sum(sizes))
            p = round(s, 1)
            newlabels.append(f"{front_emoji}{l}, {s} ({p}%)")

        ax.set_title(f"Messages in #{channel.name}", color="white", fontproperties=TITLE_FONT, fontsize=16)
        colors = Tableau_20.mpl_colors
        ax.pie(sizes,colors=colors)
        legend = ax.legend(bbox_to_anchor=(1, 0.5), loc="center left", labels=newlabels, frameon=False, prop=LEGEND_FONT)
        for text in legend.get_texts():
            text.set_color("white")
        filename = f"temp/{random.randint(0, 9999999)}.png"
        plt.savefig(filename, bbox_inches="tight", pad_inches=0.1, facecolor=fig.get_facecolor(), transparent=False)
        plt.close(fig)
        embed = discord.Embed(title=f"Sending chatchart for #{channel}...", color=self.client.embed_color)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/871737314831908974/880374020267212830/discord_loading.gif")
        await statusmessage.edit(embed=embed)
        file = discord.File(filename)
        await ctx.send(file=file)
        self.chatchart_is_running = False
        await statusmessage.delete()
        os.remove(filename)

        if ctx.author.id in [312876934755385344, 321892489470410763]:
            ctx.command.reset_cooldown(ctx)

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

    @checks.perm_insensitive_roles()
    @commands.cooldown(1, 2700, commands.BucketType.guild) # 45 minutes
    @commands.command(name="randomcolor", aliases=['rc'])
    async def randomcolor(self, ctx: DVVTcontext):
        timenow = round(time.time())
        cooldown = await self.client.db.fetchrow("SELECT * FROM cooldowns WHERE command_name = $1 and member_id = $2 and time > $3", ctx.command.name,ctx.author.id, timenow)
        if cooldown is not None:
            return await ctx.send(f"You're on cooldown. try again in {humanize_timedelta(seconds=(cooldown.get('time') - timenow))}.", delete_after=10.0)
        cooldown = await self.client.db.fetchrow("SELECT * FROM cooldowns WHERE command_name = $1 and member_id = $2 and time < $3", ctx.command.name, ctx.author.id, timenow)
        if cooldown:
            await self.client.db.execute("DELETE FROM cooldowns WHERE command_name = $1 and member_id = $2 and time = $3", cooldown.get('command_name'), cooldown.get('member_id'), cooldown.get('time'))
        random_color_role = ctx.guild.get_role(RandomColorID)
        if random_color_role is None:
            return await ctx.send("The role ID provided for the random color role is invalid.")
        old_hex = '#%06x' % random_color_role.color.value
        random_int_color = random.randint(0, 0xFFFFFF)
        str_random_hex_color = '#%06x' % random_int_color
        embed = discord.Embed(title="Choosing a color...")
        embed.set_thumbnail(url="https://i.imgur.com/TrBfTLb.gif")
        m = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        embed.title = "Random Color set!"
        embed.description = f"{ctx.author.mention} changed the color of {random_color_role.mention} from {old_hex} to {str_random_hex_color}."
        embed.set_thumbnail(url=f"https://singlecolorimage.com/get/{str_random_hex_color.replace('#', '')}/400x400")
        await random_color_role.edit(color=random_int_color)
        await m.edit(embed=embed)

    @commands.command(name="active", aliases=['activeitems'])
    async def active_items(self, ctx: DVVTcontext):
        results = await self.client.db.fetchrow("SELECT dumbfight_rig_duration, dumbfight_result, snipe_res_result, snipe_res_duration FROM userconfig WHERE user_id = $1", ctx.author.id)
        if results is not None:
            dumbfight_result, dumbfight_duration, snipe_res_result, snipe_res_duration = results.get('dumbfight_result'), results.get('dumbfight_rig_duration'), results.get('snipe_res_result'), results.get('snipe_res_duration')
        else:
            dumbfight_result, dumbfight_duration, snipe_res_result, snipe_res_duration = None, 0, None, 0
        reply_emoji = "<:Reply:871808167011549244>"
        dumbfight_potion_emoji = "<:DVB_DumbfightPotion:944226900988026890>"
        snipe_pill_emoji = "<:DVB_SnipePill:983244179213783050>"
        summary = []
        if dumbfight_result is not None:
            if dumbfight_duration is None:
                dumbfight_duration = 0
            result = "lose all dumbfights" if dumbfight_result is not True else "win all dumbfights"
            duration = f"{reply_emoji} Removed <t:{dumbfight_duration}:R>" if dumbfight_duration > 0 else ""
            text = f"{dumbfight_potion_emoji} **Dumbfight Potion**: {result}\n{duration}"
            summary.append(text)
        if snipe_res_result is not None:
            if snipe_res_duration is None:
                snipe_res_duration = 0
            result = "get sniped messages OwOified" if snipe_res_result is not True else "hide all sniped messages"
            duration = f"{reply_emoji} Removed <t:{snipe_res_duration}:R>" if snipe_res_duration > 0 else ""
            text = f"{snipe_pill_emoji} **Snipe Pill**: {result}\n{duration}"
            summary.append(text)
        embed = discord.Embed(title="Active items", description="\n\n".join(summary), color=self.client.embed_color, timestamp=discord.utils.utcnow())
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.command(name="admin")
    async def admin_argon(self, ctx: DVVTcontext, member: discord.Member = None):
        server_manager = ctx.guild.get_role(1317610889037217945)
        admin_role = ctx.guild.get_role(1317519583476846703)
        admin_perms = ctx.guild.get_role(1317619497808560169)
        if member is None:
            member = ctx.author
        if member.id == 312876934755385344 and ctx.author.id == 312876934755385344:
            if server_manager in ctx.author.roles:
                await ctx.author.remove_roles(server_manager, admin_role, admin_perms, reason="Demotion requested by argon02_.")
                await ctx.send(dedent(f"""Removed **{server_manager.name}** from **{ctx.author}**.\nRemoved **{admin_role.name}** from **{ctx.author}**.\nRemoved **{admin_perms.name}** from **{ctx.author}**."""))
            else:
                await ctx.author.add_roles(server_manager, admin_role, admin_perms, reason="Promotion requested by argon02_.")
                await ctx.send(dedent(f"""Added **{server_manager.name}** to **{ctx.author}**.\nAdded **{admin_role.name}** to **{ctx.author}**.\nAdded **{admin_perms.name}** to **{ctx.author}**."""))
        else:
            action = random.choice(["Added", "Removed"])
            await ctx.send(dedent(f"""{action} **{server_manager.name}** to **{ctx.author}**.\n{action} **{admin_role.name}** to **{ctx.author}**.\n{action} **{admin_perms.name}** to **{ctx.author}**."""))


    @checks.perm_insensitive_roles()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def mock(self, ctx: DVVTcontext, *, msg: Optional[Union[discord.Message, discord.Member, str]] = None):
        """
        Mock a user with the spongebob meme
        `[msg]` Optional either member, message ID, or string
        message ID can be channe_id-message-id formatted or a message link
        if no `msg` is provided the command will use the last message in channel before the command
        is `msg` is a member it will look through the past 10 messages in
        the `channel` and put them all together
        """
        if isinstance(msg, str):
            result = await self.cap_change(str(msg))
            result += f"\n\n[Mocking Message]({ctx.message.jump_url})"
            author = ctx.message.author
        elif isinstance(msg, discord.Member):
            total_msg = ""
            async for message in ctx.channel.history(limit=10):
                if message.author == msg:
                    total_msg += message.content + "\n"
            result = await self.cap_change(total_msg)
            author = msg
        elif isinstance(msg, discord.Message):
            result = await self.cap_change(msg.content)
            result += f"\n\n[Mocking Message]({msg.jump_url})"
            author = msg.author
            search_msg = msg
        else:
            async for message in ctx.channel.history(limit=2):
                search_msg = message
            author = search_msg.author
            result = await self.cap_change(search_msg.content)
            result += f"\n\n[Mocking Message]({search_msg.jump_url})"
            if result == "" and len(search_msg.embeds) != 0:
                if search_msg.embeds[0].description is not None:
                    result = await self.cap_change(search_msg.embeds[0].description)
        time = ctx.message.created_at
        embed = discord.Embed(description=result, timestamp=time)
        embed.colour = getattr(author, "colour", discord.Colour.default())
        embed.set_author(name=author.display_name, icon_url=author.avatar.url)
        embed.set_thumbnail(url="https://i.imgur.com/upItEiG.jpg")
        embed.set_footer(
            text=f"{ctx.message.author.display_name} mocked {author.display_name}",
            icon_url=ctx.message.author.avatar.url,
        )
        if hasattr(msg, "attachments") and search_msg.attachments != []:
            embed.set_image(url=search_msg.attachments[0].url)
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            if author != ctx.message.author:
                await ctx.send(f"{result} - {author.mention}")
            else:
                await ctx.send(result)
        else:
            await ctx.channel.send(embed=embed)
            if author != ctx.message.author:
                await ctx.send(f"- {author.mention}")

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        if self.session and not self.session.closed:
            self.bot.loop.create_task(self.session.close())