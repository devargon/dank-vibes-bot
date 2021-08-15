import discord
import asyncio
from discord.ext import commands

class Fun(commands.Cog, name='fun'):
    """
    Fun commands
    """
    def __init__(self, client):
        self.client = client

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