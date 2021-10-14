import asyncio
import discord
from abc import ABC
from datetime import datetime
from discord.ext import commands
from .serverrule import ServerRule
from .sticky import Sticky
from .joining import Joining
from utils import checks
from utils.buttons import *

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    pass
class Admin(Joining, Sticky, ServerRule, commands.Cog, name='admin', metaclass=CompositeMetaClass):
    """
    Server Commands
    """
    def __init__(self, client):
        self.client = client
        self.queue = []

    async def handle_toggle(self, guild, settings) -> bool:
        if (result := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", guild.id, settings)) is not None:
            result = result.get('enabled')
        else:
            await self.client.pool_pg.execute("INSERT INTO serverconfig VALUES ($1, $2, $3)", guild.id, settings, False)
            result = False
        if result:
            result = False
        else:
            result = True
        await self.client.pool_pg.execute("UPDATE serverconfig SET enabled=$1 WHERE guild_id=$2 AND settings=$3", result, guild.id, settings)
        return result

    @commands.command(name='leaderboards')
    @commands.has_guild_permissions(administrator=True)
    async def leaderboards(self, ctx):
        """
        Shows guild's leaderboard settings and also allows you to allow/disable them.
        """
        def get_emoji(enabled):
            if enabled:
                return "<:DVB_enabled:872003679895560193>"
            return "<:DVB_disabled:872003709096321024>"
        embed = discord.Embed(title=f"Leaderboard Settings For {ctx.guild.name}", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        if (owodaily := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", ctx.guild.id, "owodailylb")) is not None:
            owodaily = owodaily.get('enabled')
        if (owoweekly := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", ctx.guild.id, "owoweeklylb")) is not None:
            owoweekly = owoweekly.get('enabled')
        if (votelb := await self.client.pool_pg.fetchrow("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", ctx.guild.id, "votelb")) is not None:
            votelb = votelb.get('enabled')
        embed.add_field(name=f"{get_emoji(owodaily)} OwO Daily Leaderboard", value=f"{'Enabled' if owodaily else 'Disabled'}", inline=False)
        embed.add_field(name=f"{get_emoji(owoweekly)} OwO Weekly Leaderboard", value=f"{'Enabled' if owoweekly else 'Disabled'}", inline=False)
        embed.add_field(name=f"{get_emoji(votelb)} Vote Leaderboard", value=f"{'Enabled' if votelb else 'Disabled'}", inline=False)
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon.url)
        message = await ctx.send(embed=embed)
        emojis = ['1⃣', '2⃣', '3⃣', 'ℹ']
        for emoji in emojis:
            await message.add_reaction(emoji)
        def check(payload):
                return payload.user_id == ctx.message.author.id and payload.channel_id == ctx.channel.id and payload.message_id == message.id and str(payload.emoji) in emojis
        while True:
            try:
                response = await self.client.wait_for('raw_reaction_add', timeout=15, check=check)
            except asyncio.TimeoutError:
                return await message.clear_reactions()
            if str(response.emoji) == emojis[0]:
                owodaily = await self.handle_toggle(ctx.guild, "owodailylb")
                embed.set_field_at(index=0, name=f"{get_emoji(owodaily)} OwO Daily Leaderboard", value=f"{'Enabled' if owodaily else 'Disabled'}", inline=False)
                await message.edit(embed=embed)
            elif str(response.emoji) == emojis[1]:
                owoweekly = await self.handle_toggle(ctx.guild, 'owoweeklylb')
                embed.set_field_at(index=1, name=f"{get_emoji(owoweekly)} OwO Weekly Leaderboard", value=f"{'Enabled' if owoweekly else 'Disabled'}", inline=False)
                await message.edit(embed=embed)
            elif str(response.emoji) == emojis[2]:
                votelb = await self.handle_toggle(ctx.guild, 'votelb')
                embed.set_field_at(index=2, name=f"{get_emoji(votelb)} Vote Leaderboard", value=f"{'Enabled' if votelb else 'Disabled'}", inline=False)
                await message.edit(embed=embed)
            elif str(response.emoji) == emojis[3]:
                tempembed = discord.Embed(title='Information', color=self.client.embed_color, description="React with the emojis to toggle leaderboards")
                tempembed.add_field(name='Reactions' ,value=f"{emojis[0]} Toggles OwO daily leaderboard\n{emojis[1]} Toggles OwO weekly leaderboard\n{emojis[2]} Toggles vote leaderboard\n{emojis[3]} Shows this infomation message.")
                await message.edit(embed=tempembed)
            await message.remove_reaction(response.emoji, ctx.author)
        
    @commands.command(name="setnickchannel", aliases = ["nickchannel"])
    @commands.has_guild_permissions(administrator=True)
    async def setchannel(self, ctx, channel:discord.TextChannel=None):
        """
        Set the channel for nickname requests to be sent to.
        """
        result = await self.client.pool_pg.fetch("SELECT * FROM channelconfigs where guild_id = $1", ctx.guild.id)
        if len(result) == 0:
            await self.client.pool_pg.execute("INSERT INTO channelconfigs(guild_id, nicknamechannel_id) VALUES($1, $2)", ctx.guild.id, channel.id)
            return await ctx.send(f"I will now send nickname requests to {channel.mention}.")
        else:
            await self.client.pool_pg.execute("UPDATE channelconfigs SET nicknamechannel_id = $1 where guild_id = $2", channel.id, ctx.guild.id)
            await self.client.pool_pg.execute("DELETE FROM nicknames")
            return await ctx.send(f"I will now send nickname requests to {channel.mention}.\nAll nickname requests sent in a previous channel have been forfeited.")

    @commands.command(name="setdmchannel", aliases = ["dmchannel"])
    @commands.has_guild_permissions(administrator=True)
    async def setdmchannel(self, ctx, channel:discord.TextChannel=None):
        """
        Set the channel for dmname requests to be sent to.
        """
        result = await self.client.pool_pg.fetch("SELECT * FROM channelconfigs where guild_id = $1", ctx.guild.id)
        if len(result) == 0:
            await self.client.pool_pg.execute("INSERT INTO channelconfigs(guild_id, dmchannel_id) VALUES($1, $2)", ctx.guild.id, channel.id)
            return await ctx.send(f"I will now send DM requests to {channel.mention}.")
        else:
            await self.client.pool_pg.execute("UPDATE channelconfigs SET dmchannel_id = $1 where guild_id = $2", channel.id, ctx.guild.id)
            await self.client.pool_pg.execute("DELETE FROM dmrequests")
            return await ctx.send(f"I will now send DM requests to {channel.mention}.\nAll DM requests sent in a previous channel have been forfeited.")

    @commands.command(name="viewconfig")
    @commands.has_guild_permissions(administrator=True)
    async def viewconfig(self, ctx, channel: discord.TextChannel = None):
        """
        Show configurations for nickname and DM requests.
        """
        result = await self.client.pool_pg.fetchrow("SELECT * FROM channelconfigs where guild_id = $1", ctx.guild.id)
        if len(result) == 0:
            return await ctx.send(f"No configuration for DM and nickname requests have been set yet. ")
        else:
            await ctx.send(embed=discord.Embed(title=f"Configurations for {ctx.guild.name}", description = f"Nickname requests: {ctx.guild.get_channel(result.get('nicknamechannel_id'))}\nDM requests: {ctx.guild.get_channel(result.get('dmchannel_id'))}", color = self.client.embed_color))

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="messagereset", aliases=["mreset"], invoke_without_command=True)
    async def messagelog(self, ctx):
        """
        Resets the database for counting messages sent.
        """
        confirm_view = confirm(ctx, self.client, 30.0)
        messagecount = await self.client.pool_pg.fetch("SELECT * FROM messagelog")
        if len(messagecount) == 0:  # if there's nothing to be deleted
            return await ctx.send("There's no message count to be removed.")
        totalvote = sum(userentry.get('messagecount') for userentry in messagecount)
        embed = discord.Embed(title="Action awaiting confirmation", description=f"There are {len(messagecount)} people who have chatted, amounting to a total of {totalvote} messages. Are you sure you want to reset the message count?", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        msg = await ctx.reply(embed=embed, view=confirm_view)
        confirm_view.response = msg
        await confirm_view.wait()
        if confirm_view.returning_value is None:
            embed.color, embed.description = discord.Color.red(), "You didn't respond."
            return await msg.edit(embed=embed)
        if confirm_view.returning_value == False:
            embed.color, embed.description = discord.Color.red(), "Action cancelled."
            return await msg.edit(embed=embed)
        if confirm_view.returning_value == True:
            await self.client.pool_pg.execute("DELETE FROM messagelog")
            embed.color, embed.description = discord.Color.green(), "The message count has been cleared."
            await msg.edit(embed=embed)

    @commands.group(invoke_without_command=True, name="messageroles")
    @commands.has_guild_permissions(administrator=True)
    async def messageroles(self, ctx):
        """
        Configure the milestones for the roles.
        """
        embed = discord.Embed(title=f"Dank Vibes Message Count Autorole configuration", description=f"", timestamp=discord.utils.utcnow(), color=self.client.embed_color)
        embed.add_field(name="How to configure the message count roles?",
                        value=f"`messageroles list` shows all milestones for message count roles.\n`messageroles add [messagecount] [role]` adds a milestone for message count roles.\n`messageroles remove [messagecount]` will remove the milestone for the specified message count.")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="Roles can be stated via a name, mention or ID.")
        await ctx.send(embed=embed)

    @messageroles.command(name="list", aliases = ["show"])
    @commands.has_guild_permissions(administrator=True)
    async def mrolelist(self, ctx):
        """
        Lists milestones for message count roles.
        """
        messagemilestones = await self.client.pool_pg.fetch("SELECT * FROM messagemilestones")
        if len(messagemilestones) == 0:
            embed = discord.Embed(title = "Message count milestones", description = "There are no milestones set for now. Use `messageroles add [messagecount] [role]` to add one.", color=self.client.embed_color) # there are no milestones set
            return await ctx.send(embed=embed)
        output = ''
        for row in messagemilestones:
            if len(output) >= 3780:
                embed = discord.Embed(title="Message count milestones", description=output, color=self.client.embed_color)
                await ctx.send(embed=embed)
            role = ctx.guild.get_role(row.get('roleid'))
            rolemention = role.mention if role is not None else "unknown-or-deleted-role"
            output += f"**{row.get('messagecount')} messagess: **{rolemention}\n"
        embed = discord.Embed(title="Message count milestones", description=output, color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_footer(text="To edit the milestones, use the subcommands `add` and `remove`.")
        await ctx.send(embed=embed)

    @messageroles.command(name="add", aliases=["create"])
    @commands.has_guild_permissions(administrator=True)
    async def roleadd(self, ctx, messagecount = None, role:discord.Role = None):
        """
        Adds milestones for message roles.
        """
        if messagecount is None or role is None: # missing arguments
            return await ctx.send("The correct usage of this command is `messageroles add [messagecount] [role]`.")
        try:
            messagecount = int(messagecount)
        except ValueError:
            return await ctx.send("`messagecount` is not a valid number.")
        existing_milestones = await self.client.pool_pg.fetch("SELECT * FROM messagemilestones WHERE messagecount = $1", messagecount)
        if len(existing_milestones) > 0:
            await ctx.send(f"You have already set a milestone for **{messagecount} messages**. To set a new role, remove this milestone and add it again.")
            return
        await self.client.pool_pg.execute("INSERT INTO messagemilestones VALUES($1, $2)", messagecount, role.id)
        await ctx.send(f"**Done**\n**{role.name}** will be added to a member when they have sent a message **{messagecount} time(s)**.")

    @messageroles.command(name="remove", aliases=["delete"])
    @commands.has_guild_permissions(administrator=True)
    async def roleremove(self, ctx, messagecount=None):
        """
        Removes milestones for nessage count roles.
        """
        if messagecount is None:
            return await ctx.send("The correct usage of this command is `messageroles remove [messagecount]`.")
        try:
            messagecount = int(messagecount)
        except ValueError:
            return await ctx.send(f"`{messagecount}` as the messagecount is not a valid number.")
        existing_milestones = await self.client.pool_pg.fetch("SELECT * FROM messagemilestones WHERE messagecount = $1", messagecount)
        if len(existing_milestones) == 0:
            return await ctx.send(
                f"You do not have a milestone set for {messagecount} messages. Use `messageroles add [messagecount] [role]` to add one.")
        await self.client.pool_pg.execute("DELETE FROM messagemilestones WHERE messagecount = $1", messagecount) # Removes the milestone rule
        await ctx.send(f"**Done**\nThe milestone for having sent a message **{messagecount} time(s)** has been removed.")

    @checks.has_permissions_or_role(administrator=True)
    @commands.cooldown(1, 15, commands.BucketType.guild)
    @commands.command(name='demote', aliases = ['suggestion49', 'suggest49'])
    async def demote(self, ctx, member: discord.Member=None):
        """
        The infamous suggestion 49.
        """
        selfdemote = False
        if member is None:
            return await ctx.send("You need to tell me who to demote, otherwise I'm demoting **you**.")
        if ctx.author.guild_permissions.administrator != True and ctx.guild.get_role(684591962094829569) not in member.roles:
            await ctx.send("You have not met the requirements to demote someone else, hence you're being self-demoted.")
            selfdemote = True
            member = ctx.author
        staffroleids = [758172293133762591, 837595970464120842, 837595945616277504, 837595910661603330, 843756047964831765,
         758172863580209203, 758173099752423435, 758173535029559376, 735417263968223234, 627284965222121482,
         892266027495350333, 756667326623121568, 644711739618885652, 709107981568180327, 697314852162502698,
         758175645393223680, 608495204399448066, 870850266868633640, 674774385894096896, 795914641191600129,
         722871699325845626, 608503892002603029, 684591962094829569, 663502776952815626,
         735015819771379712, 895341539549659136]
        #staffroleids = [896052612284166204, 896052592797417492, 895815832465190933, 895815799812521994, 895815773208051763, 895815588289581096, 895815546292035625]
        staffroles = [ctx.guild.get_role(id) for id in staffroleids]
        for i in staffroles:
            if i is None:
                staffroles.remove(i)
        if not staffroles:
            return await ctx.send("I can't find any roles to remove.")
        removable = [role for role in staffroles if role in member.roles]
        tupremove = tuple(removable)
        if not tupremove:
            return await ctx.send(f"There are no roles that I can remove from {member} to demote them.")
        msg = await ctx.send(f"**Demoting {member.mention}...**")
        async with ctx.typing():
            try:
                await member.remove_roles(*tupremove, reason=f"Demoted by {ctx.author}")
            except Exception as e:
                return await msg.edit(content=f"There was an issue with removing roles. I've temporarily stopped demoting {member}. More details: {e}")
        try:
            await msg.edit(content=f"{member.mention} has been demoted for 30 seconds. Their removed roles are: **{', '.join(role.name for role in tupremove)}**")
        except discord.NotFound:
            await ctx.send(f"{member.mention} has been demoted for 30 seconds. Their removed roles are: **{', '.join(role.name for role in tupremove)}**")
        try:
            message = f"Alas! Due to you misbehaving, you have been demoted by **{ctx.author}**." if not selfdemote else "You have just self demoted yourself."
            await member.send(f"{message} You no longer have the roles: **{', '.join(role.name for role in tupremove)}**. \nYour roles might be readded afterwards. Or will they? <:dv_bShrugOwO:837687264263798814>")
        except:
            pass
        await asyncio.sleep(30.0)
        try:
            await member.add_roles(*tupremove, reason='Demotion reversed automatically')
        except Exception as e:
            return await ctx.send(f"There was an issue with adding roles. I've temporarily stopped promoting {member}. More details: {e}")
        return await ctx.send(f"{member.mention} congratulations on your promotion to:  **{', '.join(role.name for role in tupremove)}**!")