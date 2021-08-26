import asyncio
import discord
from datetime import datetime
from discord.ext import commands
from utils import checks
import random
emojis = ["<:checkmark:841187106654519296>", "<:crossmark:841186660662247444>"]
class betting(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.fighters = {}


    @commands.group(name="bet", invoke_without_command=True)
    async def bet(self, ctx, member: discord.Member = None):
        """
        Bet on someone you think is going to win the competition!
        """
        for fighter in self.fighters:
            if fighter not in ctx.guild:
                self.fighters.pop(fighter)
        if len(self.fighters) == 0:
            return await ctx.send("It appears that there is no ongoing bets.")
        if not member:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to mention a member to send a message!")
        if member not in self.fighters:
            return await ctx.send("You can only vote for people who are chosen to fight against each other!")
        for fighter in self.fighters:
            if ctx.author in self.fighters[fighter]:
                return await ctx.send("You have already placed a bet on someone. Unfortunately, this action is irreversible.")
        argon = ctx.guild.get_member(321892489470410763)
        confirmation = await ctx.send(embed=discord.Embed(title="Placing a bet...", description=f"Are you sure you want to place a bet on **{member.name}**? You cannot change your bet after you have sent the entry fee for your bet.", color=self.client.embed_color))
        for emoji in emojis:
            await confirmation.add_reaction(emoji)
        def check(payload):
            return payload.message_id == confirmation.id and payload.member == ctx.author and str(payload.emoji) in emojis
        try:
            response = await self.client.wait_for('raw_reaction_add', timeout=15, check=check)
        except asyncio.TimeoutError:
            await confirmation.clear_reactions()
            return await confirmation.edit(embed=discord.Embed(title="Bet cancelled.", description=f"Are you sure you want to place a bet on **{member.name}**? You cannot change your bet after you have sent the entry fee for your bet."))
        if str(response.emoji) == emojis[0]:
            await confirmation.edit(embed=discord.Embed(title="Placing a bet...", description=f"Please send **exactly** `⏣ 500`to `{argon}` within the next 60 seconds to place your bet for **{member.name}**."))
        elif str(response.emoji) == emojis[1]:
            await confirmation.clear_reactions()
            return await confirmation.edit(embed=discord.Embed(title="Bet cancelled.", color=discord.Color.red()))
        await ctx.send(f"Please send `⏣ 500` to `{argon}` within the next 60 seconds to place your bet.")
        def check(payload):
            return payload.author.id == 270904126974590976 and payload.content.startswith(f"{ctx.author.mention} You gave {argon.name} **⏣ 500**")
        try:
            await self.client.wait_for("message", check=check, timeout = 60)
        except asyncio.TimeoutError:
            return await ctx.reply("I could not detect your donation. Please try again!")
        else:
            lst = self.fighters[member]
            lst.append(ctx.author)
            self.fighters[member] = lst
            await ctx.send(f"Your entry has been added! You are now betting `⏣ 500` on {member}.")

    @checks.has_permissions_or_role(administrator=True)
    @bet.command(name="check")
    async def bet_check(self, ctx, member:discord.Member=None):
        """
        Check the statistics for betting. To check the people who bet for a specific role, you can mention someone in the command.
        """
        if member is None or member not in self.fighters:
            string = ""
            for item in self.fighters:
                string += f"{item}: `{len(self.fighters[item])}`\n"
            await ctx.send(embed=discord.Embed(title="Bet statistics", description=string or "It appears there is no betting statistics at all. Perhaps you have not started a betting session with `dv.bet start`.", color=self.client.embed_color, timestamp=datetime.utcnow()))
        else:
            string = ""
            for item in self.fighters[member]:
                string += f"• {item.mention}"
            await ctx.send(embed=discord.Embed(title=f"People who have betted on {member}", description=string or f"How tragic, no one betted for {member.name}.", color=self.client.embed_color, timestamp=datetime.utcnow()))

    @checks.has_permissions_or_role(administrator=True)
    @bet.command(name="start")
    async def bet_start(self, ctx):
        """
        Starts a betting session by adding all members who have a role. The role is specified in the code. Rerunning this command will cause the previous betting session to reset.
        """
        mod_id = 879625711915241532
        mod_role = ctx.guild.get_role(mod_id)
        self.fighters.clear()
        joined_members = []
        members_with_role = []
        for member in ctx.guild.members:
            if member.id in [602066975866355752, 650647680837484556, 321892489470410763]:
                joined_members.append(f"**{member}**")
                self.fighters[member] = []
            elif mod_role in member.roles:
                members_with_role.append(member)
        if len(members_with_role) + len(joined_members) > 7:
            while len(joined_members) < 7:
                chosen_member = random.choice(members_with_role)
                self.fighters[chosen_member] = []
                members_with_role.remove(chosen_member)
                joined_members.append(f"**{chosen_member}**")

        await ctx.send(embed=discord.Embed(title="A new fighting match has started!", description=f"The fighting list has been cleared. You can now vote for these people: {', '.join(joined_members)}", color = self.client.embed_color, timestamp=datetime.utcnow()))


