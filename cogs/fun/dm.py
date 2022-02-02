import asyncio
import discord
from datetime import datetime
from discord.ext import commands
from utils import checks
emojis = ["<:checkmark:841187106654519296>", "<:crossmark:841186660662247444>"]

class DMPersistentView(discord.ui.View):
    def __init__(self, client):
        self.client = client
        super().__init__(timeout=None)

    @discord.ui.button(label='Approve', emoji=discord.PartialEmoji.from_str("<:checkmark:841187106654519296>"), style=discord.ButtonStyle.green, custom_id="button:approve_dm") #, custom_id='persistent_view:approve')
    async def green(self, button: discord.ui.Button, interaction: discord.Interaction):
        dm_request = await self.client.pool_pg.fetchrow("SELECT * FROM dmrequests WHERE messageid = $1", interaction.message.id)
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
        await self.client.pool_pg.execute("DELETE from dmrequests WHERE id = $1", ID)
        await self.client.pool_pg.execute("INSERT INTO dmrequestslog values($1, $2, $3, $4, $5, $6)", ID, dmrequester.id if dmrequester else dm_request.get('member_id'), dmtarget.id if dmtarget else dm_request.get('target_id'), interaction.user.id, dmcontent, output[0]) # 0 : Denied, 1: Failed, 2 : Approved
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

    @discord.ui.button(label='Deny', emoji=discord.PartialEmoji.from_str("<:crossmark:841186660662247444>"), style=discord.ButtonStyle.red, custom_id="button:deny_dm") #c, custom_id='persistent_view:red')
    async def red(self, button: discord.ui.Button, interaction: discord.Interaction):
        dm_request = await self.client.pool_pg.fetchrow("SELECT * FROM dmrequests WHERE messageid = $1", interaction.message.id)
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
        await self.client.pool_pg.execute("DELETE from dmrequests WHERE id = $1", ID)
        await self.client.pool_pg.execute("INSERT INTO dmrequestslog values($1, $2, $3, $4, $5, $6)", ID, dmrequester.id if dmrequester else dm_request.get('member_id'), dmtarget.id if dmtarget else dm_request.get('target_id'), interaction.user.id, dmcontent, output[0]) # 0 : Denied, 1: Failed, 2 : Approved
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

class dm(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        existing_requests = await self.client.pool_pg.fetch("SELECT messageid FROM dmrequests")
        if not self.persistent_views_added:
            if len(existing_requests) == 0:
                return
            for entry in existing_requests:
                if entry.get('messageid'):
                    self.client.add_view(DMPersistentView(self.client), message_id=entry.get('messageid'))
            self.persistent_views_added = True

    @commands.command(name="dm")
    @checks.requires_roles()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def dmrequest(self, ctx, member: discord.Member = None, *, message: str = None):
        """
        Acting like a messenger, Dank Vibes Bot anonymously will DM the user on your behalf.
        """
        if not member:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to mention a member to send a message!")
        if member == ctx.me:
            return await ctx.send("Just DM me already... Do you not know how to DM me??\nhttps://cdn.nogra.me/core/how_to_dm_a_bot.gif")
        if member.bot:
            return await ctx.send(f"🤖 **{member}**: `Do not speak to me, you inferior human being.`")
        if not message:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("I'm not sending a blank message, write something meaningful and try again.")
        if len(message) > 4000:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"Your message has {len(message)} characters. It can only have a maximum of 4000 characters.")
        if await self.client.check_blacklisted_content(message):
            return await ctx.send("You cannot send content with blacklisted words via the bot.")
        if not (config := self.dmconfig.get(ctx.guild.id)):
            config = await self.client.pool_pg.fetchrow("SELECT dmchannel_id FROM channelconfigs where guild_id = $1", ctx.guild.id)
            if config is None or config.get('dmchannel_id') is None:
                return await ctx.send('This server has not set a channel for DM requests to be directed to. Have someone with the `Administrator` Permission to add a DM request channel with `dv.setdmchannel <channel>`.')

            config = self.dmconfig.setdefault(ctx.guild.id, config.get('dmchannel_id'))
        request_channel = ctx.guild.get_channel(config)
        if request_channel is None:
            await self.client.pool_pg.execute("DELETE FROM channelconfigs WHERE guild_id = $1", ctx.guild.id)
            return await ctx.send("I could not find the channel to send DM requests to. Please contact an admin about this!")
        existing = await self.client.pool_pg.fetch("SELECT * FROM dmrequests WHERE member_id = $1 and target_id = $2 and dmcontent = $3", ctx.author.id, member.id, message)
        if len(existing) > 0:
            return await ctx.send("I already have an existing DM request that matches your new request.")
        await self.client.pool_pg.execute("INSERT INTO dmrequests(member_id, target_id, dmcontent) values($1, $2, $3)", ctx.author.id, member.id, message)
        ID = (await self.client.pool_pg.fetchrow("SELECT id FROM dmrequests where member_id = $1 and dmcontent = $2", ctx.author.id, message)).get('id')

        embed = discord.Embed(title="DM Request", description = message, color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(name="DM Target", value=f"{member} {member.mention}")
        embed.add_field(name="Status", value="Not approved", inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Request ID: {ID}", icon_url=ctx.guild.icon.url)
        view = DMPersistentView(self.client)
        new_message = await request_channel.send(embed=embed, view=view)
        await self.client.pool_pg.execute("UPDATE dmrequests set messageid = $1 where id = $2", new_message.id, ID)
        authorembed = discord.Embed(title="Your DM request has been submitted!", description="I will notify you on the status of your DM request.", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        authorembed.set_author(icon_url=ctx.guild.icon.url, name=ctx.guild.name)
        authorembed.add_field(name="Message", value=(message[:1020] + '...') if len(message) > 1024 else message, inline=False)
        authorembed.add_field(name="DM Target", value=f"{member} {member.mention}", inline=True)
        authorembed.add_field(name="Request ID", value=str(ID), inline=True)
        authorembed.set_footer(text="Your DM request will be denied if it breaks server rules.")
        await ctx.message.delete()
        try:
            await ctx.author.send(embed=authorembed)
        except discord.Forbidden:
            pass

    @commands.slash_command(name="dm")
    @checks.requires_roles()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def dm_slash(self, ctx: discord.ApplicationContext, member: discord.Member, *, message: str):
        """
        Acting like a messenger, Dank Vibes Bot anonymously will DM the user on your behalf.
        """
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
            config = await self.client.pool_pg.fetchrow("SELECT dmchannel_id FROM channelconfigs where guild_id = $1", ctx.guild.id)
            if config is None or config.get('dmchannel_id') is None:
                return await ctx.send('This server has not set a channel for DM requests to be directed to. Have someone with the `Administrator` Permission to add a DM request channel with `dv.setdmchannel <channel>`.')
            config = self.dmconfig.setdefault(ctx.guild.id, config.get('dmchannel_id'))
        request_channel = ctx.guild.get_channel(config)
        if request_channel is None:
            await self.client.pool_pg.execute("DELETE FROM channelconfigs WHERE guild_id = $1", ctx.guild.id)
            return await ctx.send("I could not find the channel to send DM requests to. Please contact an admin about this!")
        existing = await self.client.pool_pg.fetch("SELECT * FROM dmrequests WHERE member_id = $1 and target_id = $2 and dmcontent = $3", ctx.author.id, member.id, message)
        if len(existing) > 0:
            return await ctx.send("I already have an existing DM request that matches your new request.")
        await self.client.pool_pg.execute("INSERT INTO dmrequests(member_id, target_id, dmcontent) values($1, $2, $3)", ctx.author.id, member.id, message)
        ID = (await self.client.pool_pg.fetchrow("SELECT id FROM dmrequests where member_id = $1 and dmcontent = $2", ctx.author.id, message)).get('id')
        embed = discord.Embed(title="DM Request", description=message, color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_author(name=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(name="DM Target", value=f"{member} {member.mention}")
        embed.add_field(name="Status", value="Not approved", inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Request ID: {ID}", icon_url=ctx.guild.icon.url)
        view = DMPersistentView(self.client)
        new_message = await request_channel.send(embed=embed, view=view)
        await self.client.pool_pg.execute("UPDATE dmrequests set messageid = $1 where id = $2", new_message.id, ID)
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