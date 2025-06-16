import random
from typing import Union

import discord
from discord.ext import commands
from discord.ext.commands import MemberNotFound, MissingRequiredArgument

from utils import checks
import asyncio
import aiohttp
from main import dvvt
from utils.context import DVVTcontext
from dataclasses import dataclass

from utils.errors import ArgumentBaseError

# warm pastel colors for friendly actions (hug, cuddle, kiss, pat, feed, tickle)
warm_colors = [
    0xFFB3BA, # pastel pink
    0xFFDFBA, # peach
    0xFFFFBA, # pale yellow
    0xBAFFC9, # mint green
    0xBAE1FF, # baby blue
    0xE3BAFF  # lavender
]

# accent colors for more intense or emotive actions
action_colors = {
    "slap":  0xFF6B6B, # coral red
    "punch": 0xC0392B, # dark red
    "kick":  0xE67E22, # carrot orange
    "yeet":  0x9B59B6, # amethyst purple
    "laugh": 0xF1C40F, # bright yellow
    "cry":   0x3498DB, # sky blue
    "bite":  0x2ECC71   # emerald green
}

async def confirm_target(ctx: DVVTcontext, target: Union[discord.Member, None]):
    if target is None:
        viewable_members = get_members_that_can_view_this_channel(ctx)
        if not viewable_members:
            raise commands.BadArgument("You need to specify a member.")
        await ctx.reply(
            "Why run this command without mentioning somebody... when you can do it with many members here!",
            mention_author=False)
        target = random.choice(viewable_members)
    return target

@dataclass
class ImageResult:
    url: str
    source: str


class MemberOrRandomUser(commands.Converter):
    async def convert(self, ctx, argument: str):
        print('converting')
        argument = argument.strip() if argument else ""
        resulting_member = None

        # If no argument provided or it's just whitespace
        if not argument:
            viewable_members = [
                member for member in ctx.guild.members
                if ctx.channel.permissions_for(member).read_messages
                   and member.id != ctx.author.id
                   and not member.bot
            ]
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")

            await ctx.send(
                "Why run this command without mentioning somebody... when you can do it with many members here!",
                mention_author=False)
            resulting_member = random.choice(viewable_members)

        else:
            try:
                resulting_member = await commands.MemberConverter().convert(ctx, argument)
            except MemberNotFound:
                viewable_members = [
                    member for member in ctx.guild.members
                    if ctx.channel.permissions_for(member).read_messages
                       and member.id != ctx.author.id
                       and not member.bot
                ]
                if not viewable_members:
                    raise commands.MemberNotFound(argument)
                await ctx.send(
                    "I could not find the member you are looking for. Instead, I found someone else for you!",
                    mention_author=False)
                resulting_member = random.choice(viewable_members)

        return resulting_member

class NekosBestAPIWrapper:
    def __init__(self):
        self.endpoint = "https://nekos.best/api/v2"
        self.format = "gif"

    async def fetch(self, action: str) -> ImageResult:
        url = f"{self.endpoint}/{action}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    session.raise_for_status()
                data = await response.json()

        try:
            result = data["results"][0]
            return ImageResult(url=result.get("url"), source=result["anime_name"])
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected response format: {data}") from e

    async def fetch_hug(self) -> ImageResult:
        return await self.fetch("hug")

    async def fetch_kiss(self) -> ImageResult:
        return await self.fetch("kiss")

strings = {
    "hug": {
        "title": "warm hug incoming",
        "description": [
            "{invocator} gives {target} a big cozy hug 🤗",
            "soft hug incoming from {invocator} to {target} <a:dv_nyaHugOwO:1318037829678268426>",
            "{target}, you’ve been hugged by {invocator} 💞",
            "{invocator} wraps {target} in a gentle embrace <a:dv_pandaHugOwO:1326371157502591027>",
            "all the snug hugs for {target} from {invocator} <a:dv_pandaHugOwO:1326371157502591027>",
            "{invocator} squeezes {target} just right 🤍",
            "here’s a warm bear hug from {invocator} 🐻"
        ]
    },
    "cuddle": {
        "title": "snuggle time",
        "description": [
            "{invocator} snuggles up with {target} ☁️",
            "feel the warmth—{invocator} cuddles {target} <:dv_bunbunHugOwO:1317980510428991558>",
            "time to nestle: {invocator} and {target} 😊",
            "fluffy cuddle hug from {invocator} <:dv_hugOwO:1317966802898391122>",
            "{target}, {invocator} is ready for snuggles <:dv_nyaHugOwO:1317966811047788586>",
            "cozy blanket snuggle by {invocator} 🛋️"
        ]
    },
    "kiss": {
        "title": "sweet smooch",
        "description": [
            "{invocator} plants a sweet kiss on {target} 💋",
            "{target}, you just got kissed by {invocator} <a:panda_spamkiss:929302788775739412>",
            "pucker up for {invocator}’s kiss to {target} <:dv_pepeBlushKissOwO:1317542694641336361>",
            "soft kiss from {invocator} <a:dv_aKissesOwO:1318037701882282065>",
            "{invocator} sends a gentle smooch 💗",
            "sweet peck incoming from {invocator} <a:panda_spamkiss:929302788775739412>",
            "tiny peck delivered: {invocator} → {target} <a:panda_spamkiss:929302788775739412>",
            "{invocator} leans in and kisses {target} 💕"
        ]
    },
    "pat": {
        "title": "gentle pat",
        "description": [
            "{invocator} pats {target} <a:dv_pepePatOwO:1318081846793211934>",
            "gentle pat from {invocator} to {target} <a:dv_patpat:1383734060349788260>",
            "{target}, here’s a friendly pat from {invocator} <:dv_nekoPatOwO:1317966809764335616>",
            "soft pat on the back by {invocator} <:dv_aPatOwO:1317966771180802089>",
            "{invocator} gives {target} a reassuring pat 🫶",
            "tiny pat delivered by {invocator} <:dv_kittyPatOwO:1317966805272236172>",
            "{target} pat-pats {invocator} gently <a:dv_aSitchPatOwO:1318063280089993226>"
        ]
    },
    "feed": {
        "title": "snack time",
        "description": [
            "{invocator} offers a tasty snack to {target} 🍪",
            "here’s a bite for {target} from {invocator} 🍎",
            "feeding time: {invocator} → {target}",
            "nom-nom: {invocator} feeds {target} 🍫",
            "{invocator} shares a treat with {target}",
            "snack delivery by {invocator} 🥨",
            "a little tasty bite from {invocator} 🍩"
        ]
    },
    "tickle": {
        "title": "tickle attack",
        "description": [
            "tickle attack! {invocator} → {target} 😛",
            "{target}, prepare to giggle—{invocator} is here 😂",
            "soft tickles incoming from {invocator}",
            "{invocator} pokes {target} with tickles 🤣",
            "tickle time: {invocator} + {target}",
            "feather-light tickle by {invocator} 🪶",
            "tiny tickles from {invocator} 😝"
        ]
    },
    "highfive": {
        "title": "high-five!",
        "description": [
            "*clap* {invocator} high-fives {target} 🙌",
            "up top! {invocator} ↔ {target}",
            "high-five exchange: {invocator} + {target}",
            "hand-slap fun by {invocator} ✋",
            "solid five from {invocator} to {target}",
            "{invocator} slaps five with {target}"
        ]
    },
    "dance": {
        "title": "dance party",
        "description": [
            "{invocator} spins and grooves 💃",
            "dance party starting: {invocator} 🎉",
            "bust a move! {invocator} is on the floor",
            "rhythm time: {invocator} shows off those moves 🎶",
            "boogie alert for {invocator}",
            "{invocator} hits the dance floor 🕺",
            "shake it out with {invocator}"
        ]
    },
    "slap": {
        "title": "watch your cheek",
        "description": [
            "whap! {invocator} slaps {target} 🤚",
            "{target}, that slap from {invocator} stung, huh? 😬",
            "playful smack delivered by {invocator}",
            "{invocator} smacks {target}—watch out 💥",
            "light slap by {invocator}",
            "{invocator} gives {target} a quick slap",
            "snap-slap from {invocator}",
            "{invocator} slaps {target} across the face! the audacity 😡"
        ]
    },
    "punch": {
        "title": "direct hit",
        "description": [
            "pow! {invocator} punches {target} 💥",
            "{invocator} lands a solid punch on {target}",
            "boom—{target} got hit by {invocator} 😵",
            "heavy punch thrown by {invocator}",
            "{invocator} delivers a strong punch",
            "smashing punch from {invocator}",
            "{target}, feel that hit from {invocator}"
        ]
    },
    "kick": {
        "title": "firm boot",
        "description": [
            "boop! {invocator} kicks {target}",
            "{invocator} lands a swift kick on {target}",
            "hard kick delivered by {invocator}",
            "{target}, watch that kick from {invocator} 👢",
            "power kick by {invocator}",
            "{invocator} gives {target} a firm boot",
            "smack-kick from {invocator}"
        ]
    },
    "yeet": {
        "title": "getting yeeted",
        "description": [
            "yeet! {invocator} launches {target} 🚀",
            "whoosh—{invocator} yeets {target} 💨",
            "sending {target} flying by {invocator}",
            "power yeet from {invocator}",
            "strong toss by {invocator}",
            "{invocator} hurls {target} away",
            "{target} gets yeeted by {invocator}"
        ]
    },
    "laugh": {
        "title": "burst of laughter",
        "description": [
            "{invocator} bursts into laughter <a:dv_kekKittyLaughOwO:1328568623652012053>",
            "can’t stop laughing—{invocator} <a:dv_mJerryLaughOwO:1328569103971258398>",
            "{invocator} cracks up hard <a:dv_kekKittyLaughOwO:1328568623652012053>",
            "laughter erupts from {invocator} <a:dv_mJerryLaughOwO:1328569103971258398>",
            "{invocator} howls with laughter <a:dv_mJerryLaughOwO:1328569103971258398>",
            "giggle flood by {invocator} <a:dv_kekKittyLaughOwO:1328568623652012053>",
            "roaring laugh from {invocator} <a:dv_mJerryLaughOwO:1328569103971258398>"
        ]
    },
    "cry": {
        "title": "tears incoming",
        "description": [
            "{invocator} starts to tear up 😢💧",
            "soft sobs from {invocator} 🥺",
            "{invocator} is crying :c",
            "{invocator} can’t hold back the tears 💔",
            "quiet tears by {invocator} 😿",
            "sniffle session: {invocator} 😥",
            "heartache from {invocator} 😭💔"
        ]
    },
    "bite": {
        "title": "playful bite",
        "description": [
            "{invocator} chomps on {target} like a snack. yum~"
            "chomp! {invocator} bites {target}",
            "{invocator} nibbles on {target}",
            "playful bite from {invocator}",
            "{target}, watch out for {invocator}’s bite",
            "sharp little bite by {invocator}",
            "hungry bite delivered by {invocator}",
            "{invocator} takes a friendly bite of {target}"
        ]
    },
    "poke": {
        "title": "poke time",
        "description": [
            "boop! {invocator} pokes {target} to get attention 🤏",
            "{invocator} gives {target} a little nudge with a poke",
            "{target}, {invocator} just poked you! ☝️",
            "{invocator} prods {target} gently",
            "tap tap—{invocator} pokes {target}",
            "{invocator} can't resist a quick poke on {target} 🥺",
            "{invocator} pokes {target} playfully 👈"
        ]
    },
}

def get_members_that_can_view_this_channel(ctx: DVVTcontext):
    """Get members that can view the current channel."""
    return [
        member for member in ctx.guild.members
        if ctx.channel.permissions_for(member).read_messages and member.id != ctx.author.id and not member.bot
    ]


class Actions(commands.Cog, name='actions'):
    def __init__(self, client):
        self.client: dvvt = client
        self.nekosbest = NekosBestAPIWrapper()

    async def create_action_record_and_return_count(self, guild_id: int, channel_id: int, message_id: int, user_id: int, action: str, target_id: int = None):
        await self.create_action_record(guild_id, channel_id, message_id, user_id, action, target_id)
        if target_id is not None:
            sql_query = "SELECT COUNT(*) AS action_count FROM actions WHERE action = $1 AND ((user_id = $2 AND target_user_id = $3) OR (user_id = $3 AND target_user_id = $2))"
            return await self.client.db.fetchval(sql_query, action, user_id, target_id)
        else:
            sql_query = "SELECT COUNT(*) AS action_count FROM actions WHERE action = $1 AND user_id = $2"
            return await self.client.db.fetchval(sql_query, action, user_id)

    async def create_action_record(self, guild_id: int, channel_id: int, message_id: int, user_id: int, action: str, target_id: int = None):
        """Create a record of the action performed by the user."""
        await self.client.db.execute("""
        INSERT INTO actions(guild_id, channel_id, message_id, user_id, action, target_user_id) VALUES($1, $2, $3, $4, $5, $6)""",
                                     guild_id, channel_id, message_id, user_id, action, target_id)


    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="hug")
    async def action_hug(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Playfully bite someone to tease them.
        """
        target = await confirm_target(ctx, target)
        hug_result = await self.nekosbest.fetch("hug")
        chosen_string = random.choice(strings.get("hug").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = random.choice(warm_colors)
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "hug", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("hug").get("title"), description=chosen_string, color=color).set_image(url=hug_result.url)
        embed.set_footer(text=f"You and {target.display_name} have hugged {n_times_display}!", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="cuddle")
    async def action_cuddle(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Cuddle someone with a warm cozy embrace.
        """
        target = await confirm_target(ctx, target)
        cuddle_result = await self.nekosbest.fetch("cuddle")
        chosen_string = random.choice(strings.get("cuddle").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = random.choice(warm_colors)
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "cuddle", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("cuddle").get("title"), description=chosen_string, color=color).set_image(url=cuddle_result.url)
        embed.set_footer(text=f"You and {target.display_name} have cuddled {n_times_display}!", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="kiss")
    async def action_kiss(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Plant a sweet kiss on someone to show affection.
        """
        if target is None:
            viewable_members = get_members_that_can_view_this_channel(ctx)
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")
            await ctx.reply("Why run this command without mentioning somebody... when you can do it with many members here!", mention_author=False)
            target = random.choice(viewable_members)
        kiss_result = await self.nekosbest.fetch(random.choice(["kiss", "peck"]))
        chosen_string = random.choice(strings.get("kiss").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = random.choice(warm_colors)
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "kiss", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("kiss").get("title"), description=chosen_string, color=color).set_image(url=kiss_result.url)
        embed.set_footer(text=f"You and {target.display_name} have kissd {n_times_display}!", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="pat")
    async def action_pat(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Give someone a gentle pat to reassure them.
        """
        if target is None:
            viewable_members = get_members_that_can_view_this_channel(ctx)
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")
            await ctx.reply("Why run this command without mentioning somebody... when you can do it with many members here!", mention_author=False)
            target = random.choice(viewable_members)
        pat_result = await self.nekosbest.fetch("pat")
        chosen_string = random.choice(strings.get("pat").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = random.choice(warm_colors)
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "pat", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("pat").get("title"), description=chosen_string, color=color).set_image(url=pat_result.url)
        embed.set_footer(text=f"You and {target.display_name} have patted each other {n_times_display}!", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="feed")
    async def action_feed(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Feed someone food to show you care.
        """
        if target is None:
            viewable_members = get_members_that_can_view_this_channel(ctx)
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")
            await ctx.reply("Why run this command without mentioning somebody... when you can do it with many members here!", mention_author=False)
            target = random.choice(viewable_members)
        feed_result = await self.nekosbest.fetch("feed")
        chosen_string = random.choice(strings.get("feed").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = random.choice(warm_colors)
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "feed", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("feed").get("title"), description=chosen_string, color=color).set_image(url=feed_result.url)
        embed.set_footer(text=f"You and {target.display_name} have fed each other {n_times_display}!", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="tickle")
    async def action_tickle(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Tickle someone until they can't help but laugh.
        """
        if target is None:
            viewable_members = get_members_that_can_view_this_channel(ctx)
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")
            await ctx.reply("Why run this command without mentioning somebody... when you can do it with many members here!", mention_author=False)
            target = random.choice(viewable_members)
        tickle_result = await self.nekosbest.fetch("tickle")
        chosen_string = random.choice(strings.get("tickle").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = random.choice(warm_colors)
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "tickle", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("tickle").get("title"), description=chosen_string, color=color).set_image(url=tickle_result.url)
        embed.set_footer(text=f"You and {target.display_name} have tickled each other {n_times_display}!", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="highfive")
    async def action_highfive(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Share a celebratory high-five to celebrate together.
        """
        if target is None:
            viewable_members = get_members_that_can_view_this_channel(ctx)
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")
            await ctx.reply("Why run this command without mentioning somebody... when you can do it with many members here!", mention_author=False)
            target = random.choice(viewable_members)
        highfive_result = await self.nekosbest.fetch("highfive")
        chosen_string = random.choice(strings.get("highfive").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = random.choice(warm_colors)
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "highfive", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("highfive").get("title"), description=chosen_string, color=color).set_image(url=highfive_result.url)
        embed.set_footer(text=f"You and {target.display_name} have high-fived {n_times_display}!", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="dance")
    async def action_dance(self, ctx: DVVTcontext):
        """
        Break into a dance party!
        """
        dance_result = await self.nekosbest.fetch("dance")
        chosen_string = random.choice(strings.get("dance").get("description")).format(invocator=ctx.author.mention)
        color = random.choice(warm_colors)
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "dance", None)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("dance").get("title"), description=chosen_string, color=color).set_image(url=dance_result.url)
        embed.set_footer(text=f"You have danced {n_times_display}!", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="slap")
    async def action_slap(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Slap someone to tease them.
        """
        if target is None:
            viewable_members = get_members_that_can_view_this_channel(ctx)
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")
            await ctx.reply("Why run this command without mentioning somebody... when you can do it with many members here!", mention_author=False)
            target = random.choice(viewable_members)
        slap_result = await self.nekosbest.fetch("slap")
        chosen_string = random.choice(strings.get("slap").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = action_colors.get("slap")
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "slap", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("slap").get("title"), description=chosen_string, color=color).set_image(url=slap_result.url)
        embed.set_footer(text=f"You and {target.display_name} have slapped each other {n_times_display}... 😟", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="punch")
    async def action_punch(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Deliver a powerful punch to spar with someone.
        """
        if target is None:
            viewable_members = get_members_that_can_view_this_channel(ctx)
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")
            await ctx.reply("Why run this command without mentioning somebody... when you can do it with many members here!", mention_author=False)
            target = random.choice(viewable_members)
        punch_result = await self.nekosbest.fetch("punch")
        chosen_string = random.choice(strings.get("punch").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = action_colors.get("punch")
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "punch", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("punch").get("title"), description=chosen_string, color=color).set_image(url=punch_result.url)
        embed.set_footer(text=f"You and {target.display_name} have punched each other {n_times_display}... 😟", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="kick")
    async def action_kick(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Give someone a swift kick for some playful banter.
        """
        if target is None:
            viewable_members = get_members_that_can_view_this_channel(ctx)
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")
            await ctx.reply("Why run this command without mentioning somebody... when you can do it with many members here!", mention_author=False)
            target = random.choice(viewable_members)
        kick_result = await self.nekosbest.fetch("kick")
        chosen_string = random.choice(strings.get("kick").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = action_colors.get("kick")
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "kick", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("kick").get("title"), description=chosen_string, color=color).set_image(url=kick_result.url)
        embed.set_footer(text=f"You and {target.display_name} have kicked each other {n_times_display}... 😟", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="yeet")
    async def action_yeet(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Yeet someone across the screen for dramatic effect.
        """
        if target is None:
            viewable_members = get_members_that_can_view_this_channel(ctx)
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")
            await ctx.reply("Why run this command without mentioning somebody... when you can do it with many members here!", mention_author=False)
            target = random.choice(viewable_members)
        yeet_result = await self.nekosbest.fetch("yeet")
        chosen_string = random.choice(strings.get("yeet").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = action_colors.get("yeet")
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "yeet", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("yeet").get("title"), description=chosen_string, color=color).set_image(url=yeet_result.url)
        embed.set_footer(text=f"You and {target.display_name} have yeeted each other {n_times_display}...", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="laugh")
    async def action_laugh(self, ctx: DVVTcontext):
        """
        Let your laughter loose.
        """
        laugh_result = await self.nekosbest.fetch("laugh")
        chosen_string = random.choice(strings.get("laugh").get("description")).format(invocator=ctx.author.mention)
        color = action_colors.get("laugh")
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "laugh", None)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("laugh").get("title"), description=chosen_string, color=color).set_image(url=laugh_result.url)
        embed.set_footer(text=f"You have laughed {n_times_display}! 😂", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="cry")
    async def action_cry(self, ctx: DVVTcontext):
        """
        Tear up and share a crying reaction when you need comfort.
        """
        cry_result = await self.nekosbest.fetch("cry")
        chosen_string = random.choice(strings.get("cry").get("description")).format(invocator=ctx.author.mention)
        color = action_colors.get("cry")
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "cry", None)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("cry").get("title"), description=chosen_string, color=color).set_image(url=cry_result.url)
        embed.set_footer(text=f"You have cried {n_times_display} 😢", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="bite", aliases=["nom"])
    async def action_bite(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        nom nom nom
        """
        if target is None:
            viewable_members = get_members_that_can_view_this_channel(ctx)
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")
            await ctx.reply("Why run this command without mentioning somebody... when you can do it with many members here!", mention_author=False)
            target = random.choice(viewable_members)
        bite_result = await self.nekosbest.fetch("bite")
        chosen_string = random.choice(strings.get("bite").get("description")).format(invocator=ctx.author.mention, target=target.mention)
        color = action_colors.get("bite")
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id, ctx.author.id, "bite", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("bite").get("title"), description=chosen_string, color=color).set_image(url=bite_result.url)
        embed.set_footer(text=f"You and {target.display_name} have bit each other {n_times_display}!", icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="poke", aliases=["boop"])
    async def action_poke(self, ctx: DVVTcontext, target: discord.Member = None):
        """
        Prod someone to get their attention.
        """
        if target is None:
            viewable_members = get_members_that_can_view_this_channel(ctx)
            if not viewable_members:
                raise commands.BadArgument("You need to specify a member.")
            await ctx.reply(
                "Why run this command without mentioning somebody... when you can do it with many members here!",
                mention_author=False)
            target = random.choice(viewable_members)
        poke_result = await self.nekosbest.fetch("poke")
        chosen_string = random.choice(strings.get("poke").get("description")).format(invocator=ctx.author.mention,
                                                                                     target=target.mention)
        color = action_colors.get("poke")
        new_count = await self.create_action_record_and_return_count(ctx.guild.id, ctx.channel.id, ctx.message.id,
                                                                     ctx.author.id, "poke", target.id)
        n_times_display = "once" if new_count == 1 else f"{new_count} times"
        embed = discord.Embed(title=strings.get("poke").get("title"), description=chosen_string, color=color).set_image(
            url=poke_result.url)
        embed.set_footer(text=f"You and {target.display_name} have poked each other {n_times_display}!",
                         icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)
