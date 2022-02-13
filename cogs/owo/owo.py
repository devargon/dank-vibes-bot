import asyncio
import discord
import contextlib
from typing import Optional
from datetime import datetime, timedelta
from utils.menus import CustomMenu
from discord.ext import commands, menus, tasks
from utils import checks

owo50_id = 847877497634553856
owo100_id = 847881186314289243
owo_player_id = 837594929974870047
owo_announcement = 837781619057885184

class Leaderboard(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=10)
    
    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=menu.ctx.bot.embed_color, timestamp=discord.utils.utcnow())
        for entry in entries:
            embed.add_field(name=f"{entry[0]}", value=f"**{entry[1]}** OwOs", inline=False)
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed

class OwO(commands.Cog, name='owo'):
    """
    OwO related commands
    """
    def __init__(self, client):
        self.client = client
        self.waitlist = []
        self.active = True
        self.daily_owo_reset.start()

    def cog_unload(self):
        self.daily_owo_reset.stop()

    def check_content(self, message):
        msg = message.content.lower()
        if msg.startswith('owo') or 'owo' in msg:
            msg = msg.strip('owo').split()
            if len(msg) != 0 and msg[0] in self.owo_commands:
                return False
            return True
        if 'uwu' in msg:
            return True
        return False

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
                embed.add_field(name=f"#{index} {position[0]}", value=f"**{position[1]}** OwOs", inline=False)
            return embed
        ranks = []
        for index, position in enumerate(leaderboard, 1):
            ranks.append((f"#{index} {position[0]}", position[1]))
        return ranks

    owo_commands = {"ab", "acceptbattle",
    "cowoncy", "money", "currency", "cash", "credit", "balance",
    "wallpaper", "wp", "wallpapers", "background", "backgrounds",
    "battle", "b", "fight", "battlesetting", "bs", "battlesettings",
    "crate", "weaponcrate", "wc", "db", "declinebattle", "pets", "pet",
    "bully", "pika", "pikapika", "alastor", "army", "gauntlet", "piku",
    "propose", "marry", "marriage", "wife", "husband", "avatar", "user",
    "rename", "team", "squad", "teams", "setteam", "squads", "useteams",
    "covid", "cv", "covid19", "coronavirus", "math", "calc", "calculate",
    "announce", "changelog", "announcement", "announcements", "disable", "enable",
    "pizza", "poutine", "rose", "bouquet", "rum", "sharingan", "slime", "teddy", "yy",
    "weapon", "w", "weapons", "wep", "weaponshard", "ws", "weaponshards", "dismantle",
    "claim", "reward", "compensation", "daily", "give", "send", "quest", "gif", "pic",
    "feedback", "question", "report", "suggest", "guildlink", "help", "invite", "link",
    "communism", "communismcat", "distractedbf", "distracted", "drake", "eject", "amongus",
    "my", "me", "guild", "top", "rank", "ranking", "buy", "describe", "desc", "equip", "use",
    "handholding", "tickle", "kill", "hold", "pats", "wave", "boop", "snuggle", "fuck", "sex",
    "merch", "patreon", "donate", "ping", "pong", "prefix", "rule", "rules", "shards", "shard",
    "censor", "checklist", "task", "tasks", "cl", "color", "randcolor", "colour", "randcolour",
    "owo", "owoify", "ify", "pray", "curse", "profile", "ship", "combine", "translate", "listlang",
    "bunny", "cake", "java", "crown", "cpc", "dish", "donut", "icecream", "lollipop", "meshi", "milk",
    "coinflip", "cf", "coin", "flip", "drop", "pickup", "lottery", "bet", "lotto", "slots", "slot", "s",
    "owodex", "od", "dex", "d", "sacrifice", "essence", "butcher", "sac", "sc", "sell", "upgrade", "upg",
    "inventory", "inv", "shop", "market", "acceptmarriage", "am", "cookie", "rep", "declinemarriage", "dm",
    "blush", "cry", "dance", "lewd", "pout", "shrug", "sleepy", "smile", "smug", "thumbsup", "wag", "thinking",
    "triggered", "teehee", "deredere", "thonking", "scoff", "happy", "thumbs", "grin", "blackjack", "bj", "21",
    "emergency", "emergencymeeting", "headpat", "isthisa", "slapcar", "slaproof", "spongebobchicken", "schicken",
    "cuddle", "hug", "kiss", "lick", "nom", "pat", "poke", "slap", "stare", "highfive", "bite", "greet", "punch",
    "coffee", "cupachicake", "yinyang", "tarot", "bell", "strengthtest", "roll", "d20", "choose", "pick", "decide",
    "stats", "stat", "info", "uncensor", "vote", "autohunt", "huntbot", "hb", "hunt", "h", "catch", "lootbox", "lb",
    "define", "divorce", "eightball", "8b", "ask", "8ball", "emoji", "enlarge", "jumbo", "level", "lvl", "levels", "xp",
    "zoo"}

    @commands.command(name='owocount', usage='[member]', aliases=['mycount', 'myc', 'owoc', 'stat'])
    async def owocount(self, ctx, member: Optional[discord.Member] = None):
        """
        Shows your or a member's daily OwO count for this server.
        """
        member = member if member is not None else ctx.author
        count = await self.client.pool_pg.fetchrow("SELECT daily_count, weekly_count, total_count, yesterday, last_week FROM owocount WHERE member_id=$1", member.id)
        embed = discord.Embed(color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.add_field(name='Current Stats', value=f"Today's OwO count: `{count.get('daily_count') if count else 0}`\nThis week's OwO count: `{count.get('weekly_count') if count else 0}`\nTotal OwO count: `{count.get('total_count') if count else 0}`")
        embed.add_field(name='Past Stats', value=f"Yesterday's OwO count: `{count.get('yesterday') if count else 0}`\nLast week's OwO count: `{count.get('last_week') if count else 0}`")
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @commands.command(name='owoleaderboard', aliases=['owolb'])
    @checks.not_in_gen()
    async def owoleaderboard(self, ctx, *, arg: str = None):
        """
        Shows the OwO leaderboard for Dank Vibes.

        `dv.owoleaderboard daily` for today's OwO leaderboard.
        `dv.owoleaderboard weekly` for this week's OwO leaderboard.
        `dv.owoleaderboard yesterday` for yesterday's OwO leaderboard.
        `dv.owoleaderboard last week` for last week's OwO leaderboard.
        """
        async with ctx.typing():
            arg = "total 5" if arg is None else arg
            number = [int(i) for i in arg.split() if i.isdigit()]
            top = 5 if len(number) == 0 else number[0]
            if 'daily' in arg.lower() or 'today' in arg.lower():
                title = "Today's OwO leaderboard"
                query = "SELECT member_id, daily_count FROM owocount ORDER BY daily_count DESC LIMIT $1"
            elif 'last week' in arg.lower():
                title = "Last week's OwO leaderboard"
                query = "SELECT member_id, last_week FROM owocount ORDER BY last_week DESC LIMIT $1"
            elif 'weekly' in arg.lower() or 'week' in arg.lower():
                title = "This week's OwO leaderboard"
                query = "SELECT member_id, weekly_count FROM owocount ORDER BY weekly_count DESC LIMIT $1"
            elif 'yesterday' in arg.lower():
                title = "Yesterday's OwO leaderboard"
                query = "SELECT member_id, yesterday FROM owocount ORDER BY yesterday DESC LIMIT $1"
            else:
                title = f"OwO leaderboard for {ctx.guild.name}"
                query = "SELECT member_id, total_count FROM owocount ORDER BY total_count DESC LIMIT $1"
            leaderboard = await self.get_leaderboard(ctx.guild, query, top)
            if isinstance(leaderboard, discord.Embed):
                leaderboard.title = title                
                return await ctx.send(embed=leaderboard)
            else:
                pages = CustomMenu(source=Leaderboard(leaderboard, title), clear_reactions_after=True, timeout=60)
                return await pages.start(ctx)

    @tasks.loop(hours=24)
    async def daily_owo_reset(self):
        guild = self.client.get_guild(595457764935991326)
        channel = guild.get_channel(owo_announcement)
        owo50 = guild.get_role(owo50_id)
        owo100 = guild.get_role(owo100_id)
        self.active = False
        if discord.utils.utcnow().weekday() == 6:
            if await self.client.pool_pg.fetchval("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", guild.id, "owoweeklylb"): # check if the weekly owo lb is enabled or not
                query = "SELECT member_id, weekly_count FROM owocount ORDER BY weekly_count DESC LIMIT $1"
                embed = await self.get_leaderboard(guild, query, top=5)
                embed.title = "This week's OwO leaderboard"
                if channel is not None:
                    with contextlib.suppress(discord.HTTPException):
                        await channel.send(embed=embed)
            weekly_res = await self.client.pool_pg.fetch("SELECT member_id, weekly_count FROM owocount")
            reset_values = []
            for res in weekly_res:
                reset_values.append((0, res.get('weekly_count'), res.get('member_id')))
            await self.client.pool_pg.executemany("UPDATE owocount SET weekly_count=$1, last_week=$2 WHERE member_id=$3", reset_values)
        if await self.client.pool_pg.fetchval("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", guild.id, "owodailylb"): # check if the daily owo lb is enabled or not
            query = "SELECT member_id, daily_count FROM owocount ORDER BY daily_count DESC LIMIT $1"
            embed = await self.get_leaderboard(guild, query, top=5)
            embed.title = "Today's OwO leaderboard"
            if channel is not None:
                with contextlib.suppress(discord.HTTPException):
                    await channel.send(embed=embed)
        daily_res = await self.client.pool_pg.fetch("SELECT member_id, daily_count FROM owocount")
        reset_values = []
        for res in daily_res:
            reset_values.append((0, res.get('daily_count'), res.get('member_id')))
        await self.client.pool_pg.executemany("UPDATE owocount SET daily_count=$1, yesterday=$2 WHERE member_id=$3", reset_values)
        self.active = True
        if owo50 is not None:
            for member in owo50.members:
                with contextlib.suppress(discord.Forbidden):
                    await member.remove_roles(owo50, reason="OwO count has been reset.")
                    await asyncio.sleep(0.1)
        if owo100 is not None:
            for member in owo100.members:
                with contextlib.suppress(discord.Forbidden):
                    await member.remove_roles(owo100, reason="OwO count has been reset.")
                    await asyncio.sleep(0.1)

    @daily_owo_reset.before_loop
    async def wait_until_8am(self):
        await self.client.wait_until_ready()
        now = discord.utils.utcnow()
        next_run = now.replace(hour=8, minute=0, second=0)
        if next_run < now:
            next_run += timedelta(days=1)
        await discord.utils.sleep_until(next_run)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.active:
            return
        if message.author.bot:
            return
        if self.client.maintenance.get(self.qualified_name):
            return
        if not message.guild or message.guild.id != 595457764935991326:
            return
        if message.author.id in self.waitlist:
            return
        if not self.check_content(message):
            return
        query = "SELECT daily_count, weekly_count, total_count FROM owocount WHERE member_id=$1"
        values = message.author.id
        result = await self.client.pool_pg.fetchrow(query, values)
        if result is None:
            dailycount = 1
            values = (message.author.id, dailycount, 1, 1, 0, 0)
            query = "INSERT INTO owocount VALUES ($1, $2, $3, $4, $5, $6)"
        else:
            dailycount = result.get('daily_count') + 1
            values = (dailycount, result.get('weekly_count') +1, result.get('total_count') +1, message.author.id)
            query = "UPDATE owocount SET daily_count=$1, weekly_count=$2, total_count=$3 WHERE member_id=$4"
        await self.client.pool_pg.execute(query, *values)
        if dailycount >= 50:
            owoplayer = message.guild.get_role(owo_player_id)
            if owoplayer is not None and owoplayer in message.author.roles:    
                owo50 = message.guild.get_role(owo50_id)
                owo100 = message.guild.get_role(owo100_id)
                if owo50 is not None and owo50 not in message.author.roles:
                    with contextlib.suppress(discord.Forbidden):
                        await message.author.add_roles(owo50, reason="50 OwO count reached.")
                        await message.reply(f"You've gotten the role **{owo50.name}**!")
                if dailycount >= 100 and owo100 is not None and owo100 not in message.author.roles:
                    with contextlib.suppress(discord.Forbidden):
                        await message.author.add_roles(owo100, reason="100 OwO count reached.")
                        await message.reply(f"You've gotten the role **{owo100.name}**!")
        self.waitlist.append(message.author.id)
        await asyncio.sleep(10.0)
        self.waitlist.remove(message.author.id)

    @checks.dev()
    @commands.command(name="tempowocmd")
    async def tepowocmd(self, ctx):
        guild = self.client.get_guild(595457764935991326)
        channel = guild.get_channel(owo_announcement)
        query = "SELECT member_id, weekly_count FROM owocount ORDER BY weekly_count DESC LIMIT $1"
        embed = await self.get_leaderboard(guild, query, top=5)
        embed.title = "This week's OwO leaderboard"
        if channel is not None:
            with contextlib.suppress(discord.HTTPException):
                await channel.send(embed=embed)
        weekly_res = await self.client.pool_pg.fetch("SELECT member_id, weekly_count FROM owocount")
        reset_values = []
        for res in weekly_res:
            reset_values.append((0, res.get('weekly_count'), res.get('member_id')))
        await self.client.pool_pg.executemany("UPDATE owocount SET weekly_count=$1, last_week=$2 WHERE member_id=$3", reset_values)
        daily_res = await self.client.pool_pg.fetch("SELECT member_id, daily_count FROM owocount")
        reset_values = []
        for res in daily_res:
            reset_values.append((0, res.get('daily_count'), res.get('member_id')))
        await self.client.pool_pg.executemany("UPDATE owocount SET daily_count=$1, yesterday=$2 WHERE member_id=$3", reset_values)