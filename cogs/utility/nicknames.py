import asyncio
import discord
from datetime import datetime
from discord.ext import commands
emojis = ["<:DVB_checkmark:955345523139805214>", "<:DVB_crossmark:955345521151737896>"]
from utils import checks
from utils.errors import NicknameIsManaged

class NicknamePersistentView(discord.ui.View):
    def __init__(self, client):
        self.client = client
        super().__init__(timeout=None)

    @discord.ui.button(label='Approve', emoji=discord.PartialEmoji.from_str("<:DVB_checkmark:955345523139805214>"), style=discord.ButtonStyle.green, custom_id="button:approve_nickname") #, custom_id='persistent_view:approve')
    async def green(self, button: discord.ui.Button, interaction: discord.Interaction):
        config = await self.client.pool_pg.fetchrow("SELECT nicknamechannel_id FROM channelconfigs WHERE guild_id = $1", interaction.guild_id)
        if config is None or config.get('nicknamechannel_id') != interaction.channel_id:
            return
        nickname_request = await self.client.pool_pg.fetchrow("SELECT * FROM nicknames WHERE messageid = $1", interaction.message.id)
        if nickname_request is None:
            return
        nicktarget = self.client.get_guild(interaction.guild_id).get_member(nickname_request.get('member_id'))
        if nicktarget is None:
            authordetails = nickname_request.get('member_id')
        else:
            authordetails = f"{nicktarget} ({nicktarget.id})"
        ID, nickname, approver = nickname_request.get('id'), nickname_request.get('nickname'), interaction.guild.get_member(interaction.user.id)
        if nicktarget is None:
            output = (1, "Failed: Member has left the server",)
        else:
            try:
                await nicktarget.edit(nick=nickname, reason=f"Nickname Change approved by {approver}")
            except discord.Forbidden:
                output = (1, "Failed: Missing Permissions",)
            else:
                output = (2, "Approved and Changed",)
        await self.client.pool_pg.execute("DELETE from nicknames WHERE id = $1", ID)
        embed = interaction.message.embeds[0]
        embed.set_field_at(-1, name="Status", value=output[1], inline=False)
        embed.color = discord.Color.green() if output[0] == 2 else discord.Color.red()
        embed.set_footer(text=f"This message will be deleted in 10 seconds.")
        for b in self.children:
            b.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
        if output[0] == 1 and output[1] == "Failed: Member has left the server" or output[0] not in [1, 2, 0]:
            msgcontent = None
        elif output[0] == 1:
            msgcontent = f"Your requested nickname could not be approved as {self.client.user.name} is missing permissions to edit your name. Try requesting for a nickname after my permissions are fixed."
        elif output[0] == 2:
            msgcontent = f"Your nickname was successfully changed to {nickname}!"
        else:
            msgcontent = "error"
        if msgcontent is not None:
            try:
                await nicktarget.send(msgcontent)
            except discord.Forbidden:
                pass
        await asyncio.sleep(10)
        await interaction.delete_original_message()

    @discord.ui.button(label='Deny', emoji=discord.PartialEmoji.from_str("<:DVB_crossmark:955345521151737896>"), style=discord.ButtonStyle.red, custom_id="button:deny_nickname") #c, custom_id='persistent_view:red')
    async def red(self, button: discord.ui.Button, interaction: discord.Interaction):
        config = await self.client.pool_pg.fetchrow("SELECT nicknamechannel_id FROM channelconfigs WHERE guild_id = $1", interaction.guild_id)
        if config is None or config.get('nicknamechannel_id') != interaction.channel_id:
            return
        nickname_request = await self.client.pool_pg.fetchrow("SELECT * FROM nicknames WHERE messageid = $1", interaction.message.id)
        if nickname_request is None:
            return
        nicktarget = self.client.get_guild(interaction.guild_id).get_member(nickname_request.get('member_id'))
        if nicktarget is None:
            authordetails = nickname_request.get('member_id')
        else:
            authordetails = f"{nicktarget} ({nicktarget.id})"
        ID = nickname_request.get('id')
        approver = interaction.guild.get_member(interaction.user.id)
        if nicktarget is None:
            output = (1, "Failed: Member has left the server",)
        else:
            output = (0, "Denied",)
        await self.client.pool_pg.execute("DELETE from nicknames WHERE id = $1", ID)
        embed = interaction.message.embeds[0]
        embed.set_field_at(-1, name="Status", value=output[1], inline=False)
        embed.color = discord.Color.red()
        embed.set_footer(text=f"This message will be deleted in 10 seconds.")
        for b in self.children:
            b.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
        msgcontent = "Your requested nickname was denied."
        if msgcontent is not None and output[0] == 0:
            try:
                await nicktarget.send(msgcontent)
            except discord.Forbidden:
                pass
        await asyncio.sleep(10)
        await interaction.delete_original_message()


class nicknames(commands.Cog):
    def __init__(self, client):
        self.client = client

    #In polls.py
    """@commands.Cog.listener()
    async def on_ready(self):
        existing_requests = await self.client.pool_pg.fetch("SELECT messageid FROM nicknames")
        if not self.persistent_views_added:
            if len(existing_requests) == 0:
                return
            for entry in existing_requests:
                if entry.get('messageid'):
                    self.client.add_view(NicknamePersistentView(self.client), message_id=entry.get('messageid'))
            self.persistent_views_added = True"""

    @checks.is_not_blacklisted()
    @commands.cooldown(60, 1, commands.BucketType.user)
    @commands.command(name="nick", aliases = ["requestnick", "setnick"])
    @checks.not_in_gen()
    async def setnick(self, ctx, *, nickname = None):
        """
        Request a nickname here!
        """
        if nickname is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("What do you want your nickname to be? `dv.nick <nickname>`")
        if nickname == ctx.author.display_name:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You already have that nickname!")
        if await self.client.pool_pg.fetchval("SELECT user_id FROM freezenick WHERE user_id = $1", ctx.author.id):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Your nickname is currently frozen (probably due to a nick bet), even using `dv.nick` wouldn't change anything LOL.")
        if len(nickname) > 32:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"Your nickname is currently {len(nickname)} characters long. It can only be 32 characters long.")
        if not (config := self.nickconfig.get(ctx.guild.id)):
            config = await self.client.pool_pg.fetchrow("SELECT nicknamechannel_id FROM channelconfigs where guild_id = $1", ctx.guild.id)
            if config is None or config.get('nicknamechannel_id') is None:
                return await ctx.send('This server has not set a channel for nickname requests to be directed to. Have someone with the `Administrator` Permission to add a nickname request channel with `dv.setrequest <channel>`.')
            config = self.nickconfig.setdefault(ctx.guild.id, config.get('nicknamechannel_id'))
        request_channel = ctx.guild.get_channel(config)
        if request_channel is None:
            await self.client.pool_pg.execute("DELETE FROM channelconfigs WHERE guild_id = $1", ctx.guild.id)
            return await ctx.send("I could not find the channel to send nickname requests to. Please contact an admin about this!")
        pastnickname = await self.client.pool_pg.fetchrow("SELECT * FROM nicknames where member_id = $1", ctx.author.id)
        approveview = NicknamePersistentView(self.client)
        if pastnickname is not None:
            ID = pastnickname.get('id')
            await self.client.pool_pg.execute("UPDATE nicknames set nickname = $1 where id = $2", nickname, ID)
            requestembed = discord.Embed(title="Nickname Change Request", color=self.client.embed_color, timestamp=discord.utils.utcnow())
            if ctx.author.name == ctx.author.display_name:
                requestembed.set_author(name=f"{ctx.author} ({ctx.author.id})")
            else:
                requestembed.set_author(name=f"{ctx.author.display_name} ({ctx.author}, {ctx.author.id})")
            requestembed.add_field(name="Nickname", value=nickname, inline=True)
            requestembed.add_field(name="Requested where", value=f"[Jump to message]({ctx.message.jump_url})", inline=True)
            requestembed.add_field(name="Status", value="Awaiting Approval", inline=False)
            requestembed.set_thumbnail(url=ctx.author.display_avatar.url)
            requestembed.set_footer(text=f"Request ID: {pastnickname.get('id')}", icon_url=ctx.guild.icon.url)
            try:
                request_message = await request_channel.fetch_message(pastnickname.get('messageid'))
            except discord.NotFound:
                request_message = await request_channel.send(embed=requestembed)
                await self.client.pool_pg.execute("UPDATE nicknames set messageid = $1 where id = $2", request_message.id, ID)
            else:
                await request_message.edit(embed=requestembed)

        else:
            await self.client.pool_pg.execute("INSERT INTO nicknames(member_id, nickname) values($1, $2)", ctx.author.id, nickname)
            ID = (await self.client.pool_pg.fetchrow("SELECT id FROM nicknames where member_id = $1 and nickname = $2", ctx.author.id, nickname)).get('id')
            embed = discord.Embed(title="Nickname Change Request", color=self.client.embed_color, timestamp=discord.utils.utcnow())
            embed.set_author(name=f"{ctx.author} ({ctx.author.id})")
            embed.add_field(name="Nickname", value=nickname, inline=True)
            embed.add_field(name="Requested where", value=f"[Jump to message]({ctx.message.jump_url})", inline=True)
            embed.add_field(name="Status", value="Awaiting Approval", inline=False)
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            embed.set_footer(text=f"Request ID: {ID}", icon_url=ctx.guild.icon.url)
            new_message = await request_channel.send(embed=embed, view=approveview)
            await self.client.pool_pg.execute("UPDATE nicknames set messageid = $1 where id = $2", new_message.id, ID)
        authorembed = discord.Embed(title="Your nickname request has been submitted!", description="It will be manually approved/denied by the mods. I will DM you on the status of your nickname request.", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        authorembed.set_author(icon_url=ctx.guild.icon.url, name=ctx.guild.name)
        authorembed.add_field(name="Nickname", value=nickname, inline=True)
        authorembed.add_field(name="Request ID", value=str(ID), inline=True)
        authorembed.set_footer(text="Your nickname will be denied if it is blatantly inappropriate and/or unmentionable.")
        try:
            await ctx.reply(embed=authorembed)
        except Exception as e:
            await ctx.send(embed=authorembed)