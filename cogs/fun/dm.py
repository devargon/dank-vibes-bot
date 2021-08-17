import asyncio

import discord
from datetime import datetime
from discord.ext import commands
emojis = ["<:checkmark:841187106654519296>", "<:crossmark:841186660662247444>"]
class dm(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        if str(payload.emoji) not in emojis:
            return
        config = await self.client.pool_pg.fetchrow("SELECT dmchannel_id FROM channelconfigs WHERE guild_id = $1", payload.guild_id)
        if config is None or config.get('dmchannel_id') != payload.channel_id:
            return
        dm_request = await self.client.pool_pg.fetchrow("SELECT * FROM dmrequests WHERE messageid = $1", payload.message_id)
        if dm_request is None:
            return
        dmrequester = self.client.get_guild(payload.guild_id).get_member(dm_request.get('member_id'))
        if dmrequester is None:
            authordetails = dm_request.get('member_id')
        else:
            authordetails = f"{dmrequester} ({dmrequester.id})"
        dmtarget = self.client.get_guild(payload.guild_id).get_member(dm_request.get('target_id'))
        print("HOWIE")
        ID = dm_request.get('id')
        dmcontent = dm_request.get('dmcontent')
        approver = self.client.get_guild(payload.guild_id).get_member(payload.user_id)
        requestmessage = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if not approver.guild_permissions.manage_roles:
            return await requestmessage.remove_reaction(payload.emoji, approver)

        if str(payload.emoji) == "<:checkmark:841187106654519296>":
            if dmrequester is None:
                output = (1, "Failed: User who requested the DM has left the server",)
            if dmtarget is None:
                output = (1, "Failed: Targetted user to DM has left the server",)
            else:
                try:
                    await dmtarget.send(embed=discord.Embed(title="You have received an anonymous message!", description=dmcontent, color=self.client.embed_color))
                except discord.Forbidden:
                    output = (1, "Failed: Unable to DM user",)
                else:
                    output = (2, "Approved DM sent",)
        else:
            output = (0, "Denied")
        await self.client.pool_pg.execute("DELETE from dmrequests WHERE id = $1", ID)
        embed = discord.Embed(title="DM Request", description = dmcontent, color=discord.Color.green() if output[0] == 2 else discord.Color.red(), timestamp=datetime.utcnow())
        embed.set_author(name=authordetails)
        dmtargetdetails = f"{dmtarget} {dmtarget.mention}" if dmtarget is not None else dmtarget
        embed.add_field(name="DM Target", value=f"{dmtargetdetails}")
        embed.add_field(name="Status", value=output[1], inline=True)
        if dmrequester is not None:
            embed.set_thumbnail(url=dmrequester.avatar_url)
        embed.set_footer(text=f"This message will be deleted in 10 seconds.")
        await requestmessage.clear_reactions()
        await requestmessage.edit(embed=embed)
        if output[0] == 1:
            if output[1] == "Failed: Member has left the server" or output[0] not in [1, 2, 0]:
                msgcontent = None
            elif output[1] == "Failed: Targetted user to DM has left the server":
                msgcontent = "The user who you attempted to send an anonymous DM has left the server. Sorry about that!"
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
        await requestmessage.delete(delay=10)

    @commands.command(name="dm")
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def dmrequest(self, ctx, member: discord.Member = None, *, message: str = None):
        """
        Acting like a messenger, Dank Vibes Bot anonymously will DM the user on your behalf.
        """
        if not member:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Member is a required argument.")
        if not message:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Message is a required argument.")
        if len(message) > 4096:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"Your message has {len(message)} characters. It can only have a maximum of 4096 characters.")
        if not (config := self.dmconfig.get(ctx.guild.id)):
            config = await self.client.pool_pg.fetchrow("SELECT dmchannel_id FROM channelconfigs where guild_id = $1", ctx.guild.id)
            if config is None or config.get('dmchannel_id') is None:
                return await ctx.send(f"This server has not set a channel for DM requests to be directed to. Have someone with the `Administrator` Permission to add a DM request channel with `dv.setdmchannel <channel>`.")
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

        embed = discord.Embed(title="DM Request", description = message, color=0x57F0F0, timestamp=datetime.utcnow())
        embed.set_author(name=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(name="DM Target", value=f"{member} {member.mention}")
        embed.add_field(name="Status", value="Not approved", inline=True)
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(text=f"Request ID: {ID}", icon_url=ctx.guild.icon_url)
        new_message = await request_channel.send(embed=embed)

        await self.client.pool_pg.execute("UPDATE dmrequests set messageid = $1 where id = $2", new_message.id, ID)
        for emoji in emojis:
            if emoji not in new_message.reactions:
                await new_message.add_reaction(emoji)

        authorembed = discord.Embed(title="Your DM request has been submitted!", description="I will notify you on the status of your DM request.", color=0x57F0F0, timestamp=datetime.utcnow())
        authorembed.set_author(icon_url=ctx.guild.icon_url, name=ctx.guild.name)
        authorembed.add_field(name="Message", value=(message[:1020] + '...') if len(message) > 1024 else message, inline=False)
        embed.add_field(name="DM Target", value=f"{member} {member.mention}", inline=True)
        authorembed.add_field(name="Request ID", value=str(ID), inline=True)
        authorembed.set_footer(text="Your DM request will be denied if it breaks server rules. To hide/delete this message, react to the cross.")
        authormessage = await ctx.reply(embed=authorembed)

        await authormessage.add_reaction("<:crossmark:841186660662247444>")
        def check(payload):
            return str(payload.emoji) == "<:crossmark:841186660662247444>" and payload.message_id == authormessage.id and not payload.member.bot and payload.member == ctx.author
        try:
            response = await self.client.wait_for('raw_reaction_add', timeout=15, check=check)
        except asyncio.TimeoutError:
            await authormessage.clear_reactions()
        else:
            await ctx.message.delete()
            await authormessage.delete()
