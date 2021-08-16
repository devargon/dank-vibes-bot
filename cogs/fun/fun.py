import discord
import time
import asyncio
from discord.ext import commands
import random
from utils.time import humanize_timedelta
from utils import checks


class Fun(commands.Cog, name='fun'):
    """
    Fun commands
    """
    def __init__(self, client):
        self.client = client

    @commands.command(name="dumbfight", aliases = ["df"])
    async def dumbfight(self, ctx, member: discord.Member = None):
        """
        Mute people for a random duration between 20 to 120 seconds.
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
        if member.bot:
            return await ctx.send("Back off my kind.")
        if member == ctx.me:
            return await ctx.send("How do you expect me to mute myself?")
        duration = random.randint(30, 120)
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
        originaloverwrite = channel.overwrites_for(muted) if muted in channel.overwrites else None
        tempoverwrite = channel.overwrites_for(muted) if muted in channel.overwrites else discord.PermissionOverwrite()
        tempoverwrite.send_messages = False
        await channel.set_permissions(muted, overwrite=tempoverwrite)
        embed = discord.Embed(title="Get muted!", description = f"{ctx.author.mention} fought {member.mention} {str} them.\n{muted.mention} is now muted for {duration} seconds.", colour=color)
        await ctx.send(embed=embed)
        specialrole = ctx.guild.get_role(876767313263734805) # 874931276329656370
        cooldowntime = 1800 if specialrole in ctx.author.roles else 3600
        await self.client.pool_pg.execute("INSERT INTO cooldowns VALUES($1, $2, $3)", ctx.command.name, ctx.author.id, timenow + cooldowntime)
        await asyncio.sleep(duration)
        await channel.set_permissions(muted, overwrite=originaloverwrite)

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