from datetime import datetime
from typing import Union
import discord
from discord.ext import commands
emojis = ["<:checkmark:841187106654519296>", "<:crossmark:841186660662247444>"]
class nicknames(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        if str(payload.emoji) not in emojis:
            return
        config = await self.client.pool_pg.fetchrow("SELECT channel_id FROM nicknameconfig WHERE guild_id = $1", payload.guild_id)
        if config is None or config.get('channel_id') != payload.channel_id:
            return
        nickname_request = await self.client.pool_pg.fetchrow("SELECT * FROM nicknames WHERE messageid = $1", payload.message_id)
        if nickname_request is None:
            return
        nicktarget = self.client.get_guild(payload.guild_id).get_member(nickname_request.get('member_id'))
        if nicktarget is None:
            authordetails = nickname_request.get('member_id')
        else:
            authordetails = f"{nicktarget} ({nicktarget.id}"
        ID = nickname_request.get('id')
        nickname = nickname_request.get('nickname')
        approver = self.client.get_guild(payload.guild_id).get_member(payload.user_id)
        requestmessage = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if not approver.guild_permissions.manage_roles:
            return await requestmessage.remove_reaction(payload.emoji, approver)

        if str(payload.emoji) == "<:checkmark:841187106654519296>":
            if nicktarget is None:
                output = (1, "Failed: Member has left the server")
            else:
                try:
                    await nicktarget.edit(nick=nickname, reason=f"Nickname Change approved by {approver}")
                except discord.Forbidden:
                    output = (1, "Failed: Missing Permissions")
                else:
                    output = (2, "Approved and Changed")
        else:
            output = (0, "Denied")
        await self.client.pool_pg.execute("DELETE from nicknames WHERE id = $1", nickname_request.get('id'))
        embed = discord.Embed(title="Nickname Change Request", color=discord.Color.green() if output[0] == 2 else discord.Color.red(), timestamp=datetime.utcnow())
        embed.set_author(name=authordetails)
        embed.add_field(name="Nickname", value=nickname, inline=True)
        embed.add_field(name="Status", value=output[1], inline=True)
        if nicktarget is not None:
            embed.set_thumbnail(url=nicktarget.avatar_url)
        embed.set_footer(text=f"This message will be deleted in 10 seconds. | wicked is very nice !!")
        await requestmessage.clear_reactions()
        await requestmessage.edit(embed=embed)
        if output[0] == 1 and output[1] == "Failed: Member has left the server" or output[0] not in [1, 2, 0]:
            msgcontent = None
        elif output[0] == 1:
            msgcontent = f"Your requested nickname could not be approved as {self.client.user.name} is missing permissions to edit your name. Try requesting for a nickname after my permissions are fixed."
        elif output[0] == 2:
            msgcontent = f"Your nickname was successfully changed to {nickname}!"
        else:
            msgcontent = f"Your requested nickname was denied."
        if msgcontent is not None:
            try:
                await nicktarget.send(msgcontent)
            except discord.Forbidden:
                pass
        await requestmessage.delete(delay=10)

    @commands.command(name="nick", aliases = ["requestnick", "setnick"])
    async def setnick(self, ctx, *, nickname = None):
        """
        Request a nickname here!
        """
        if nickname is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Nickname is a required argument.")
        if len(nickname) > 32:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"Your nickname is currently {len(nickname)} characters long. It can only be 32 characters long.")
        config = await self.client.pool_pg.fetchrow("SELECT channel_id FROM nicknameconfig where guild_id = $1", ctx.guild.id)
        if config is None:
            return await ctx.send(f"This server has not set a channel for nickname requests to be directed to. Have someone with the `Administrator` Permission to add a nickname request channel with `dv.setrequest <channel>`.")
        request_channel = ctx.guild.get_channel(config.get('channel_id'))
        if request_channel is None:
            await self.client.pool_pg.execute("DELETE FROM nicknameconfig WHERE guild_id = $1", ctx.guild.id)
            return await ctx.send("I could not find the channel to send nickname requests to. Please contact an admin about this!")
        pastnickname = await self.client.pool_pg.fetchrow("SELECT * FROM nicknames where member_id = $1", ctx.author.id)

        if pastnickname is not None:
            ID = pastnickname.get('id')
            await self.client.pool_pg.execute("UPDATE nicknames set nickname = $1 where id = $2", nickname, ID)
            embed = discord.Embed(title="Nickname Change Request", color=0x57F0F0, timestamp=datetime.utcnow())
            embed.set_author(name=f"{ctx.author} ({ctx.author.id})")
            embed.add_field(name="Nickname", value=nickname, inline=True)
            embed.add_field(name="Status", value="Not approved", inline=True)
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.set_footer(text=f"Request ID: {pastnickname.get('id')} | wicked is very nice !!", icon_url=ctx.guild.icon_url) # DONT REMOVE IT PLEASDSWD
            try:
                request_message = await request_channel.fetch_message(pastnickname.get('messageid'))
            except discord.NotFound:
                request_message = await request_channel.send(embed=embed)
                await self.client.pool_pg.execute("UPDATE nicknames set messageid = $1 where id = $2", request_message.id, ID)
            else:
                await request_message.edit(embed=embed)
            for emoji in emojis:
                if emoji not in request_message.reactions:
                    await request_message.add_reaction(emoji)

        else:
            await self.client.pool_pg.execute("INSERT INTO nicknames(member_id, nickname) values($1, $2)", ctx.author.id, nickname)
            ID = (await self.client.pool_pg.fetchrow("SELECT id FROM nicknames where member_id = $1 and nickname = $2", ctx.author.id, nickname)).get('id')
            embed = discord.Embed(title="Nickname Change Request", color=0x57F0F0, timestamp=datetime.utcnow())
            embed.set_author(name=f"{ctx.author} ({ctx.author.id})")
            embed.add_field(name="Nickname", value=nickname, inline=True)
            embed.add_field(name="Status", value="Not approved", inline=True)
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.set_footer(text=f"Request ID: {ID} | wicked is very nice !!", icon_url=ctx.guild.icon_url)
            new_message = await request_channel.send(embed=embed)
            await self.client.pool_pg.execute("UPDATE nicknames set messageid = $1 where id = $2", new_message.id, ID)
            for emoji in emojis:
                if emoji not in new_message.reactions:
                    await new_message.add_reaction(emoji)
        embed = discord.Embed(title="Your nickname request has been submitted!", description="I will DM you on the status of your nickname request.", color=0x57F0F0, timestamp=datetime.utcnow())
        embed.set_author(icon_url=ctx.guild.icon_url, name=ctx.guild.name)
        embed.add_field(name="Nickname", value=nickname, inline=True)
        embed.add_field(name="Request ID", value=str(ID), inline=True)
        await ctx.reply(embed=embed)

    @commands.command(name="setnickchannel", aliases = ["nickchannel"])
    @commands.has_guild_permissions(administrator=True)
    async def setchannel(self, ctx, channel:discord.TextChannel=None):
        """
        Set the channel for nickname requests to be sent to.
        """
        result = await self.client.pool_pg.fetch("SELECT * FROM nicknameconfig where guild_id = $1", ctx.guild.id)
        if len(result) == 0:
            await self.client.pool_pg.execute("INSERT INTO nicknameconfig VALUES($1, $2)", ctx.guild.id, channel.id)
            return await ctx.send(f"I will now send nickname requests to {channel.mention}.")
        else:
            await self.client.pool_pg.execute("UPDATE nicknameconfig SET channel_id = $1 where guild_id = $2", channel.id, ctx.guild.id)
            await self.client.pool_pg.execute("DELETE FROM nicknames")
            return await ctx.send(f"I will now send nickname requests to {channel.mention}.\nAll nickname requests sent in the previous channel have been forfeited.")
