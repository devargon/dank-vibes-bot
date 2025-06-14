import random

import discord
from discord.ext import commands
from utils import checks
import asyncio
import aiohttp
from main import dvvt
from utils.context import DVVTcontext
from dataclasses import dataclass

@dataclass
class ImageResult:
    url: str
    source: str


class NekosBestAPIWrapper:
    def __init__(self):
        self.endpoint = "https://nekos.best/api/v2"
        self.format = "gif"

    async def _fetch(self, action: str) -> ImageResult:
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
        return await self._fetch("hug")

    async def fetch_kiss(self) -> ImageResult:
        return await self._fetch("kiss")

strings = {
    "hug": [
        "{invocator} gives {target} a big cozy hug 🤗",
        "soft hug incoming from {invocator} to {target} 🥰",
        "{target}, you’ve been hugged by {invocator} 💞",
        "{invocator} wraps {target} in a gentle embrace",
        "all the snug hugs for {target} from {invocator}",
        "{invocator} squeezes {target} just right 🤍",
        "here’s a warm bear hug from {invocator} 🐻"
    ],
    "cuddle": [
        "{invocator} snuggles up with {target} ☁️",
        "cuddle session starting: {invocator} + {target} 🥺",
        "feel the warmth—{invocator} cuddles {target}",
        "time to nestle: {invocator} and {target} 😊",
        "fluffy cuddle hug from {invocator}",
        "{target}, {invocator} is ready for snuggles",
    ],
    "kiss": [
        "{invocator} plants a sweet kiss on {target} 💋",
        "{target}, you just got kissed by {invocator} 😘",
        "pucker up for {invocator}’s kiss to {target}",
        "soft kiss from {invocator} ❤️",
        "{invocator} sends a gentle smooch 💗",
        "sweet peck incoming from {invocator} 💕"
    ],
    "pat": [
        "{invocator} pats {target} 👋",
        "gentle pat from {invocator} to {target}",
        "{target}, here’s a friendly pat from {invocator}",
        "soft pat on the back by {invocator} 🤚",
        "{invocator} gives {target} a reassuring pat 🫶",
        "tiny pat delivered by {invocator}",
        "pat of approval from {invocator} 👍"
    ],
    "feed": [
        "{invocator} offers a tasty snack to {target} 🍪",
        "here’s a bite for {target} from {invocator} 🍎",
        "feeding time: {invocator} → {target}",
        "nom-nom: {invocator} feeds {target} 🍫",
        "{invocator} shares a treat with {target}",
        "snack delivery by {invocator} 🥨",
        "a little tasty bite from {invocator} 🍩"
    ],
    "tickle": [
        "tickle attack! {invocator} → {target} 😛",
        "{target}, prepare to giggle—{invocator} is here 😂",
        "soft tickles incoming from {invocator}",
        "{invocator} pokes {target} with tickles 🤣",
        "tickle time: {invocator} + {target}",
        "feather-light tickle by {invocator} 🪶",
        "tiny tickles from {invocator} 😝"
    ],
    "highfive": [
        "*clap* {invocator} high-fives {target} 🙌",
        "up top! {invocator} ↔ {target}",
        "high-five exchange: {invocator} + {target}",
        "hand-slap fun by {invocator} ✋",
        "solid five from {invocator} to {target}",
        "tap five: {invocator} → {target}",
        "{invocator} slaps five with {target}"
    ],
    "dance": [
        "{invocator} spins and grooves with {target} 💃",
        "dance party starting: {invocator} + {target} 🎉",
        "bust a move! {invocator} invites {target}",
        "rhythm time: {invocator} dances for {target} 🎶",
        "boogie alert from {invocator}",
        "{invocator} and {target} hit the dance floor 🕺",
        "shake it out with {invocator}"
    ],
    "slap": [
        "whap! {invocator} slaps {target} 🤚",
        "{target}, that slap from {invocator} stung, huh? 😬",
        "playful smack delivered by {invocator}",
        "{invocator} smacks {target}—watch out 💥",
        "light slap by {invocator}",
        "{invocator} gives {target} a quick slap",
        "snap-slap from {invocator}"
    ],
    "punch": [
        "pow! {invocator} punches {target} 💥",
        "{invocator} lands a solid punch on {target}",
        "boom—{target} got hit by {invocator} 😵",
        "heavy punch thrown by {invocator}",
        "{invocator} delivers a strong punch",
        "smashing punch from {invocator}",
        "{target}, feel that hit from {invocator}"
    ],
    "kick": [
        "boop! {invocator} kicks {target} 🦶",
        "{invocator} lands a swift kick on {target}",
        "hard kick delivered by {invocator}",
        "{target}, watch that kick from {invocator} 👢",
        "power kick by {invocator}",
        "{invocator} gives {target} a firm boot",
        "smack-kick from {invocator}"
    ],
    "yeet": [
        "yeet! {invocator} launches {target} 🚀",
        "whoosh—{invocator} yeets {target} 💨",
        "sending {target} flying by {invocator}",
        "power yeet from {invocator}",
        "strong toss by {invocator}",
        "{invocator} hurls {target} away",
        "{target} gets yeeted by {invocator}"
    ],
    "laugh": [
        "{invocator} bursts into laughter 😂",
        "can’t stop laughing—{invocator} 🤣",
        "{invocator} cracks up hard",
        "laughter erupts from {invocator}",
        "{invocator} howls with laughter",
        "giggle flood by {invocator}",
        "roaring laugh from {invocator}"
    ],
    "cry": [
        "{invocator} starts to tear up 😢",
        "soft sobs from {invocator}",
        "teary moment for {invocator}",
        "{invocator} can’t hold back the tears",
        "quiet tears by {invocator}",
        "sniffle session: {invocator}",
        "heartache from {invocator} 😭"
    ],
    "bite": [
        "chomp! {invocator} bites {target}",
        "{invocator} nibbles on {target}",
        "playful bite from {invocator}",
        "{target}, watch out for {invocator}’s bite",
        "sharp little bite by {invocator}",
        "hungry bite delivered by {invocator}",
        "{invocator} takes a friendly bite of {target}"
    ]
}



class Actions(commands.Cog, name='actions'):
    def __init__(self, client):
        self.client: dvvt = client
        self.nekosbest = NekosBestAPIWrapper()


    @checks.perm_insensitive_roles()
    @commands.command(name="hug")
    async def action_hug(self, ctx: DVVTcontext):
        hug_result = await self.nekosbest._fetch("hug")
        chosen_string = random.choice(strings.get("hug"))
        embed = discord.Embed(title=chosen_string).set_image(url=hug_result.url).set_footer(text=hug_result.source)
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.command(name="cuddle")
    async def action_cuddle(self, ctx: DVVTcontext):
        cuddle_result = await self.nekosbest._fetch("cuddle")
    @checks.perm_insensitive_roles()
    @commands.command(name="kiss")
    async def action_kiss(self, ctx: DVVTcontext):
        kiss_result = await self.nekosbest._fetch("kiss")
    @checks.perm_insensitive_roles()
    @commands.command(name="pat")
    async def action_pat(self, ctx: DVVTcontext):
        pat_result = await self.nekosbest._fetch("pat")
    @checks.perm_insensitive_roles()
    @commands.command(name="feed")
    async def action_feed(self, ctx: DVVTcontext):
        feed_result = await self.nekosbest._fetch("feed")
    @checks.perm_insensitive_roles()
    @commands.command(name="tickle")
    async def action_tickle(self, ctx: DVVTcontext):
        tickle_result = await self.nekosbest._fetch("tickle")
    @checks.perm_insensitive_roles()
    @commands.command(name="highfive")
    async def action_highfive(self, ctx: DVVTcontext):
        highfive_result = await self.nekosbest._fetch("highfive")
    @checks.perm_insensitive_roles()
    @commands.command(name="dance")
    async def action_dance(self, ctx: DVVTcontext):
        dance_result = await self.nekosbest._fetch("dance")
    @checks.perm_insensitive_roles()
    @commands.command(name="slap")
    async def action_slap(self, ctx: DVVTcontext):
        slap_result = await self.nekosbest._fetch("slap")
    @checks.perm_insensitive_roles()
    @commands.command(name="punch")
    async def action_punch(self, ctx: DVVTcontext):
        punch_result = await self.nekosbest._fetch("punch")
    @checks.perm_insensitive_roles()
    @commands.command(name="kick")
    async def action_kick(self, ctx: DVVTcontext):
        kick_result = await self.nekosbest._fetch("kick")
    @checks.perm_insensitive_roles()
    @commands.command(name="yeet")
    async def action_yeet(self, ctx: DVVTcontext):
        yeet_result = await self.nekosbest._fetch("yeet")
    @checks.perm_insensitive_roles()
    @commands.command(name="laugh")
    async def action_laugh(self, ctx: DVVTcontext):
        laugh_result = await self.nekosbest._fetch("laugh")
    @checks.perm_insensitive_roles()
    @commands.command(name="cry")
    async def action_cry(self, ctx: DVVTcontext):
        cry_result = await self.nekosbest._fetch("cry")
    @checks.perm_insensitive_roles()
    @commands.command(name="bite", aliases=["nom"])
    async def action_bite(self, ctx: DVVTcontext):
        bite_result = await self.nekosbest._fetch("bite")
