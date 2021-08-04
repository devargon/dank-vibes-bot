import asyncio
import discord
import sqlite3
import contextlib
from typing import Optional
from dateutil import relativedelta
from datetime import datetime, timedelta
from discord.ext import commands, tasks

owo50_id = 847877497634553856
owo100_id = 847881186314289243
owo_player_id = 837594929974870047

class OwO(commands.Cog, name='owo'):
    """
    OwO related commands
    """
    def __init__(self, client):
        self.client = client
        self.waitlist = []
        self.active = True
        self.con = sqlite3.connect('databases/owo.db', timeout=5.0)
        self.daily_owo_reset.start()
        self.weekly_owo_reset.start()

    @commands.Cog.listener()
    async def on_ready(self):
        cursor = self.con.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS current(member_id integer PRIMARY KEY, daily_count integer, weekly_count integer, total integer)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS past(member_id integer PRIMARY KEY, yesterday integer, last_week integer)")

    def cog_unload(self):
        self.con.close()
        self.daily_owo_reset.stop()
        self.weekly_owo_reset.stop()

    @tasks.loop(hours=24)
    async def daily_owo_reset(self):
        guild = self.client.get_guild(595457764935991326)
        owo50 = guild.get_role(owo50_id)
        owo100 = guild.get_role(owo100_id)
        self.active = False
        cur = self.con.cursor()
        daily_res = cur.execute("SELECT member_id, daily_count FROM current").fetchall()
        daily_query = []
        update_query = []
        reset_query = []
        for res in daily_res:
            reset_query.append((0, res[0]))
            daily_query.append((res[0], 0, 0))
            update_query.append((res[1], res[0]))
        cur.executemany("UPDATE current SET daily_count=? WHERE member_id=?", reset_query)
        cur.executemany("INSERT OR IGNORE INTO past(member_id, yesterday, last_week) VALUES (?, ?, ?)", daily_query)
        cur.executemany("UPDATE past SET yesterday=? WHERE member_id=?", update_query)
        self.con.commit()
        cur.close()
        self.active = True
        if owo50 is not None:
            for member in owo50.members:
                with contextlib.suppress(discord.Forbidden):
                    await member.remove_roles(owo50, reason="OwO count has been reset.")
                    await asyncio.sleep(0.2)
        if owo100 is not None:
            for member in owo100.members:
                with contextlib.suppress(discord.Forbidden):
                    await member.remove_roles(owo100, reason="OwO count has been reset.")
                    await asyncio.sleep(0.2)

    @daily_owo_reset.before_loop
    async def wait_until_7am(self):
        await self.client.wait_until_ready()
        now = datetime.utcnow()
        next_run = now.replace(hour=5, minute=58, second=0)
        if next_run < now:
            next_run += timedelta(days=1)
        await discord.utils.sleep_until(next_run)

    @tasks.loop(hours=168)
    async def weekly_owo_reset(self):
        self.active = False
        cur = self.con.cursor()
        weekly_res = cur.execute("SELECT member_id, weekly_count FROM current").fetchall()
        reset_query = []
        weekly_query = []
        update_query = []
        for res in weekly_res:
            reset_query.append((0, res[0]))
            weekly_query.append((res[0], 0, 0))
            update_query.append((res[1], res[0]))
        cur.executemany("UPDATE current SET weekly_count=? WHERE member_id=?", reset_query)
        cur.executemany("INSERT OR IGNORE INTO past(member_id, yesterday, last_week) VALUES (?, ?, ?)", weekly_query)
        cur.executemany('UPDATE past SET last_week=? WHERE member_id=?', update_query)
        self.con.commit()
        cur.close()
        self.active = True

    @weekly_owo_reset.before_loop
    async def wait_until_sunday(self):
        await self.client.wait_until_ready()
        now = datetime.utcnow()
        today = now.replace(hour=7, minute=1, second=0)
        sunday = today + timedelta ((6 - today.weekday()) % 7)
        if sunday < now:
            delta = relativedelta.relativedelta(days=1, weekday=relativedelta.SU)
            sunday = today + delta
        await discord.utils.sleep_until(sunday)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.active:
            return
        if message.author.bot:
            return
        if message.guild.id != 595457764935991326:
            return
        if message.author.id in self.waitlist:
            return
        if not self.check_content(message):
            return
        cur = self.con.cursor()
        result = cur.execute("SELECT daily_count, weekly_count, total FROM current WHERE member_id=?", (message.author.id,)).fetchall()
        if len(result) == 0:
            dailycount = 0
            param = (message.author.id, 0, 0, 0,)
        else:
            count = result[0]
            dailycount = count[0]
            param = (message.author.id, count[0]+1, count[1]+1, count[2]+1,)
        cur.execute("INSERT OR REPLACE INTO current (member_id, daily_count, weekly_count, total) VALUES (?, ?, ?, ?)", param)
        self.con.commit()
        cur.close()
        if dailycount >= 50:
            owoplayer = message.guild.get_role(owo_player_id)
            if owoplayer is not None and owoplayer in message.author.roles:    
                owo50 = message.guild.get_role(owo50_id)
                owo100 = message.guild.get_role(owo100_id)
                if owo50 is not None and owo50 not in message.author.roles:
                    with contextlib.suppress(discord.Forbidden):
                        await message.author.add_roles(owo50, reason="50 OwO count reached.")
                if dailycount >= 100 and owo100 is not None and owo100 not in message.author.roles:
                    with contextlib.suppress(discord.Forbidden):
                        await message.author.add_roles(owo100, reason="100 OwO count reached.")
        self.waitlist.append(message.author.id)
        await asyncio.sleep(10)
        self.waitlist.remove(message.author.id)

    def check_content(self, message):
        msg = message.content.lower()
        if msg.startswith('owo') or 'owo' in msg:
            msg = msg.strip('owo').split()
            if len(msg) != 0 and msg[0] in self.owo_commands:
                return False
            return True
        if 'uwu' in msg:
            return True
        if msg.startswith('p'):
            msg = msg[1:].split()
            if len(msg) != 0 and msg[0] in self.owo_commands:
                return False
            return True

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
        cur = self.con.cursor()
        counts = cur.execute("SELECT daily_count, weekly_count, total FROM current WHERE member_id=?", (member.id,)).fetchall()
        past_count = cur.execute("SELECT yesterday, last_week FROM past WHERE member_id=?", (member.id,)).fetchall()
        cur.close()
        embed = discord.Embed(color=self.client.embed_color, timestamp=datetime.utcnow())
        embed.add_field(name='Current Stats', value=f"Today's OwO count: `{counts[0][0] if len(counts) != 0 else 0}`\nThis week's OwO count: `{counts[0][1] if len(counts) !=0 else 0}`\nTotal OwO count: `{counts[0][2] if len(counts) !=0 else 0}`")
        embed.add_field(name='Past Stats', value=f"Yesterday's OwO count: `{past_count[0][0] if len(past_count) != 0 else 0}`\nLast week's OwO count: `{past_count[0][1] if len(past_count) !=0 else 0}`")
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(name='owoleaderboard', aliases=['owolb'])
    async def owoleaderboard(self, ctx, *, arg: str = None):
        """
        Shows the OwO leaderboard for Dank Vibes.

        `dv.owoleaderboard daily` for today's OwO leaderboard.
        `dv.owoleaderboard weekly` for this week's OwO leaderboard.
        `dv.owoleaderboard yesterday` for yesterday's OwO leaderboard.
        `dv.owoleaderboard last week` for last week's OwO leaderboard.
        """
        async with ctx.typing():
            cur = self.con.cursor()
            embed = discord.Embed(color=self.client.embed_color, timestamp=datetime.utcnow())
            arg = "total" if arg is None else arg
            if arg.lower() == 'weekly' or arg.lower() == 'week':
                embed.title = "This week's OwO leaderboard"
                counts = cur.execute("SELECT member_id, weekly_count FROM current ORDER BY weekly_count DESC LIMIT 10").fetchall()
            elif arg.lower() == 'daily' or arg.lower() == 'today':
                embed.title = "Today's OwO leaderboard"
                counts = cur.execute("SELECT member_id, daily_count FROM current ORDER BY daily_count DESC LIMIT 10").fetchall()
            elif arg.lower() == 'yesterday':
                embed.title = "Yesterday's OwO leaderboard"
                counts = cur.execute("SELECT member_id, yesterday FROM past ORDER BY yesterday DESC LIMIT 10").fetchall()
            elif arg.lower() == 'last week':
                embed.title = "Last week's OwO leaderboard"
                counts = cur.execute("SELECT member_id, last_week FROM past ORDER BY last_week DESC LIMIT 10")
            else:
                embed.title = f"OwO leaderboard for {ctx.guild.name}"
                counts = cur.execute("SELECT member_id, total FROM current ORDER BY total DESC LIMIT 10").fetchall()
            leaderboard = []
            cur.close()
            for count in counts:
                member = ctx.guild.get_member(count[0])
                name = member.name if member is not None else count[0]
                leaderboard.append((name, count[1]))
            for index, position in enumerate(leaderboard):
                embed.add_field(name=f'#{index + 1} {position[0]}', value=f"**{position[1]}** OwOs", inline=False)
        await ctx.send(embed=embed)