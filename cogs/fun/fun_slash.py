import asyncio
import json
import random
import time

import discord
from discord import Webhook, Option
from discord.ext import commands
import aiohttp
from utils import checks


def lowered_cooldown(message: discord.Message):
    if discord.utils.get(message.author.roles, id=874833402052878396):  # Contributor 24T
        return commands.Cooldown(1, 900)
    elif discord.utils.get(message.author.roles, id=931174008970444800):  # weekly top grinder
        return commands.Cooldown(1, 900)
    elif discord.utils.get(message.author.roles, name="Vibing Investor"):
        return commands.Cooldown(1, 1800)
    else:
        return commands.Cooldown(1, 3600)

class DMPersistentView(discord.ui.View):
    def __init__(self, client):
        self.client = client
        super().__init__(timeout=None)

    @discord.ui.button(label='Approve', emoji=discord.PartialEmoji.from_str("<:DVB_checkmark:955345523139805214>"), style=discord.ButtonStyle.green, custom_id="button:approve_dm") #, custom_id='persistent_view:approve')
    async def green(self, button: discord.ui.Button, interaction: discord.Interaction):
        dm_request = await self.client.db.fetchrow("SELECT * FROM dmrequests WHERE messageid = $1", interaction.message.id)
        if dm_request is None:
            return
        dmrequester = interaction.guild.get_member(dm_request.get('member_id'))
        if dmrequester is None:
            authordetails = dm_request.get('member_id')
        else:
            authordetails = f"{dmrequester} ({dmrequester.id})"
        dmtarget = interaction.guild.get_member(dm_request.get('target_id'))
        ID = dm_request.get('id')
        dmcontent = dm_request.get('dmcontent')
        approver = interaction.guild.get_member(interaction.user.id)
        if not approver.guild_permissions.manage_roles:
            return await interaction.response.send_message("You don't have the required permissions to approve this request.", ephemeral=True)
        if dmrequester is None:
            output = (1, "Failed: User who requested the DM has left the server",)
        elif dmtarget is None:
            output = (1, "Failed: Targetted user to DM has left the server",)
        else:
            try:
                await dmtarget.send(embed=discord.Embed(title="You have received an anonymous message!", description=dmcontent, color=self.client.embed_color))
            except discord.Forbidden:
                output = (1, "Failed: Unable to DM user",)
            else:
                output = (2, "Approved DM sent",)
        await self.client.db.execute("DELETE from dmrequests WHERE id = $1", ID)
        await self.client.db.execute("INSERT INTO dmrequestslog values($1, $2, $3, $4, $5, $6)", ID, dmrequester.id if dmrequester else dm_request.get('member_id'), dmtarget.id if dmtarget else dm_request.get('target_id'), interaction.user.id, dmcontent, output[0]) # 0 : Denied, 1: Failed, 2 : Approved
        embed = discord.Embed(title="DM Request", description = dmcontent, color=discord.Color.green() if output[0] == 2 else discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.set_author(name=authordetails)
        dmtargetdetails = f"{dmtarget} {dmtarget.mention}" if dmtarget is not None else dmtarget
        embed.add_field(name="DM Target", value=f"{dmtargetdetails}")
        embed.add_field(name="Status", value=output[1], inline=True)
        if dmrequester is not None:
            embed.set_thumbnail(url=dmrequester.display_avatar.url)
        embed.set_footer(text=f"This message will be deleted in 10 seconds.")
        for b in self.children:
            b.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        if output[0] == 1:
            if output[1] == "Failed: Member has left the server" or output[0] not in [1, 2, 0]:
                msgcontent = None
            elif output[1] == "Failed: Targetted user to DM has left the server":
                msgcontent = "The user who you attempted to send an anonymous DM has left the server. Sorry about that!"
            elif output[1] == "Failed: Unable to DM user":
                msgcontent = f"I am unable to DM {dmtarget}. Sorry about that!"
            else:
                msgcontent = None
        elif output[0] == 2:
            msgcontent = f"Your message was successfully sent to {dmtarget}!"
        else:
            msgcontent = f"Your DM request was denied."
        if msgcontent is not None and dmrequester is not None:
            try:
                await dmrequester.send(msgcontent)
            except discord.Forbidden:
                pass
        await asyncio.sleep(10)
        await interaction.delete_original_message()

    @discord.ui.button(label='Deny', emoji=discord.PartialEmoji.from_str("<:DVB_crossmark:955345521151737896>"), style=discord.ButtonStyle.red, custom_id="button:deny_dm") #c, custom_id='persistent_view:red')
    async def red(self, button: discord.ui.Button, interaction: discord.Interaction):
        dm_request = await self.client.db.fetchrow("SELECT * FROM dmrequests WHERE messageid = $1", interaction.message.id)
        if dm_request is None:
            return
        dmrequester = interaction.guild.get_member(dm_request.get('member_id'))
        if dmrequester is None:
            authordetails = dm_request.get('member_id')
        else:
            authordetails = f"{dmrequester} ({dmrequester.id})"
        dmtarget = interaction.guild.get_member(dm_request.get('target_id'))
        ID = dm_request.get('id')
        dmcontent = dm_request.get('dmcontent')
        approver = interaction.guild.get_member(interaction.user.id)
        if not approver.guild_permissions.manage_roles:
            return await interaction.response.send_message("You don't have the required permissions to approve this request.", ephemeral=True)
        if dmrequester is None:
            output = (1, "Failed: User who requested the DM has left the server",)
        else:
            output = (0, "Denied")
        await self.client.db.execute("DELETE from dmrequests WHERE id = $1", ID)
        await self.client.db.execute("INSERT INTO dmrequestslog values($1, $2, $3, $4, $5, $6)", ID, dmrequester.id if dmrequester else dm_request.get('member_id'), dmtarget.id if dmtarget else dm_request.get('target_id'), interaction.user.id, dmcontent, output[0]) # 0 : Denied, 1: Failed, 2 : Approved
        embed = discord.Embed(title="DM Request", description = dmcontent, color=discord.Color.green() if output[0] == 2 else discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.set_author(name=authordetails)
        dmtargetdetails = f"{dmtarget} {dmtarget.mention}" if dmtarget is not None else dmtarget
        embed.add_field(name="DM Target", value=f"{dmtargetdetails}")
        embed.add_field(name="Status", value=output[1], inline=True)
        if dmrequester is not None:
            embed.set_thumbnail(url=dmrequester.display_avatar.url)
        embed.set_footer(text=f"This message will be deleted in 10 seconds.")
        for b in self.children:
            b.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        if output[0] == 1:
            msgcontent = None
        else:
            msgcontent = f"Your DM request was denied."
        if msgcontent is not None and dmrequester is not None:
            try:
                await dmrequester.send(msgcontent)
            except discord.Forbidden:
                pass
        await asyncio.sleep(10)
        await interaction.delete_original_message()

class FunSlash(commands.Cog):
    def __init__(self, client):
        self.client = client
        with open('assets/localization/dumbfight_statements.json', 'r') as f:
            self.dumbfight_statements = json.load(f)

    @checks.perm_insensitive_roles()
    @commands.slash_command(name="hideping", description="Secretly ping someone with this command!")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def hideping_slash(self, ctx,
                             target: Option(discord.Member, "Who you want to ping"),
                             channel: Option(discord.TextChannel, "If you want to ping someone in another channel") = None,
                             message: Option(str, "An optional message") = None
                             ):
        if channel is None:
            channel = ctx.channel
        channel = ctx.guild.get_channel(channel.id)
        if not (channel.permissions_for(ctx.author).send_messages and channel.permissions_for(ctx.author).view_channel):
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond("You are not authorized to view/send messages in that channel.", ephemeral=True)
        if message is not None and len(message) > 180:
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond(f"Your accompanying message is currently {len(message)} characters long; it can only be at most 180 characters.", ephemeral=True)
        if message is None:
            message = ''
        if await self.client.check_blacklisted_content(message):
            message = ''
        content = f"{message or ''} ‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍||‍ <@{target.id}>"  # ik this looks sketchy, but you can paste it in discord and send it to see how this looks like :MochaLaugh:
        webhook = await self.client.get_webhook(channel)
        await webhook.send(content, username="You were hidepinged",
                           avatar_url="https://cdn.discordapp.com/attachments/871737314831908974/895639630429433906/incognito.png")
        await ctx.respond(f"**{target}** has been secretly pinged in {channel.mention}! <:qbgiggle:718020317632790548>",
                          ephemeral=True)
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(
                'https://canary.discord.com/api/webhooks/883563427455438858/GsF8ZPIemw6D-x6TIp7wO88ySQizKePKCS5zRA-EBtNfHRC15e9koti7-02GKBuoZ_Yi',
                session=session)
            embed = discord.Embed(title=f"Hideping command invoked with {ctx.me}", color=discord.Color.green())
            embed.add_field(name="Author", value=f"**{ctx.author}** ({ctx.author.id})", inline=True)
            embed.add_field(name="Target", value=f"**{target}** ({target.id})", inline=True)
            embed.add_field(name="Message", value=message or "No message", inline=True)
            await webhook.send(embed=embed, username=f"{self.client.user.name} Logs")

    @commands.slash_command(name="dm", description="Acting like a messenger, Dank Vibes Bot anonymously will DM the user on your behalf.")
    @checks.perm_insensitive_roles()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def dm_slash(self, ctx: discord.ApplicationContext,
                       member: discord.Option(discord.Member, "The user you want to send a message to"),
                       message: discord.Option(str, "What to DM to the user")
                       ):
        if member.id == self.client.user.id:
            return await ctx.respond("Just DM me already... Do you not know how to DM me??\nhttps://cdn.nogra.me/core/how_to_dm_a_bot.gif", ephemeral=True)
        if member.bot:
            return await ctx.respond(f"🤖 **{member}**: `Do not speak to me, you inferior human being.`", ephemeral=True)
        if len(message) > 4000:
            ctx.command.reset_cooldown(ctx)
            return await ctx.respond(f"Your message has {len(message)} characters. It can only have a maximum of 4000 characters.", ephemeral=True)
        if await self.client.check_blacklisted_content(message):
            return await ctx.respond("You cannot send content with blacklisted words via the bot.", ephemeral=True)
        if not (config := self.dmconfig.get(ctx.guild.id)):
            config = await self.client.db.fetchrow("SELECT dmchannel_id FROM channelconfigs where guild_id = $1", ctx.guild.id)
            if config is None or config.get('dmchannel_id') is None:
                return await ctx.respond('This server has not set a channel for DM requests to be directed to. Have someone with the `Administrator` Permission to add a DM request channel with `dv.setdmchannel <channel>`.', ephemeral=True)
            config = self.dmconfig.setdefault(ctx.guild.id, config.get('dmchannel_id'))
        request_channel = ctx.guild.get_channel(config)
        if request_channel is None:
            await self.client.db.execute("DELETE FROM channelconfigs WHERE guild_id = $1", ctx.guild.id, ephemeral=True)
            return await ctx.respond("I could not find the channel to send DM requests to. Please contact an admin about this!", ephemeral=True)
        existing = await self.client.db.fetch("SELECT * FROM dmrequests WHERE member_id = $1 and target_id = $2 and dmcontent = $3", ctx.author.id, member.id, message)
        if len(existing) > 0:
            return await ctx.respond("I already have an existing DM request that matches your new request.", ephemeral=True)
        await self.client.db.execute("INSERT INTO dmrequests(member_id, target_id, dmcontent) values($1, $2, $3)", ctx.author.id, member.id, message)
        ID = (await self.client.db.fetchrow("SELECT id FROM dmrequests where member_id = $1 and dmcontent = $2", ctx.author.id, message)).get('id')
        embed = discord.Embed(title="DM Request", description=message, color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(name="DM Target", value=f"{member} {member.mention}")
        embed.add_field(name="Status", value="Not approved", inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Request ID: {ID}", icon_url=ctx.guild.icon.url)
        view = DMPersistentView(self.client)
        new_message = await request_channel.send(embed=embed, view=view)
        await self.client.db.execute("UPDATE dmrequests set messageid = $1 where id = $2", new_message.id, ID)
        authorembed = discord.Embed(title="Your DM request has been submitted!", description="I will notify you on the status of your DM request.", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        authorembed.set_author(icon_url=ctx.guild.icon.url, name=ctx.guild.name)
        authorembed.add_field(name="Message", value=(message[:1020] + '...') if len(message) > 1024 else message, inline=False)
        authorembed.add_field(name="DM Target", value=f"{member} {member.mention}", inline=True)
        authorembed.add_field(name="Request ID", value=str(ID), inline=True)
        authorembed.set_footer(text="Your DM request will be denied if it breaks server rules.")
        try:
            await ctx.author.send(embed=authorembed)
        except discord.Forbidden:
            await ctx.respond("Your DM request has been submitted!", embed=authorembed, ephemeral=True)
        else:
            await ctx.respond("Your DM request has been submitted, check your DMs!", ephemeral=True)