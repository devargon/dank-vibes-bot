import datetime
import os
import time
import topgg
import discord
import random
from PIL import ImageFont, Image, ImageDraw
from discord.ext import commands, tasks
from typing import List

from cogs.votetracker.votedb import VoteDB, Voter
from main import dvvt
from utils.format import print_exception, ordinal, plural, short_time, proper_userf
from io import BytesIO
from utils.buttons import *
from utils import checks


class VoteSetting(discord.ui.Select):
    def __init__(self, client, cog, context, response, voter):
        self.client = client
        self.cog = cog
        self.response = response
        self.context = context
        self.voter = voter
        options = [
            discord.SelectOption(label="None", description="You might miss out on reward if you don't vote!", emoji=discord.PartialEmoji.from_str("<:DVB_None:884743780027219989>")),
            discord.SelectOption(label="Direct Message (DM)", description="I'll DM you after 12 hours to vote for Dank Vibes.", emoji=discord.PartialEmoji.from_str("<:DVB_Letter:884743813166407701>")),
            discord.SelectOption(label="Ping in this server", description="I'll ping you in our voting channel!", emoji=discord.PartialEmoji.from_str("<:DVB_Ping:883744614295674950>"))
        ]
        options[voter.rmtype].default = True
        super().__init__(placeholder='Choose your type of vote reminder...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        now = ""
        if self.values[0] == "DM":
            self.voter.rmtype, now = 1, "You will **now be DMed** to vote for Dank Vibes."
        if self.values[0] == "Ping":
            self.voter.rmtype, now = 2, "You will **now be pinged** to vote for Dank Vibes."
        if self.values[0] == "None":
            self.voter.rmtype, now = 0, "You will **not be reminded** to vote for Dank Vibes.\nYou will lose out on some vote perks if you don't vote regularly!"
        await self.cog.votedb.update_voter(self.voter)
        await interaction.response.send_message(f"Updated successfully; {now}")


class VoteSettingView(discord.ui.View):
    def __init__(self, client, cog, ctx, timeout, voter, timetovote):
        self.client = client
        self.timeout = timeout
        self.response = None
        self.cog = cog
        self.context = ctx
        self.voter = voter
        super().__init__(timeout=timeout)
        self.add_item(VoteSetting(client=self.client, cog=self.cog, context=self.context, response=self.response, voter=self.voter))
        if timetovote > 0:
            label = f"Vote at top.gg - {short_time(timetovote)}"
        else:
            label = f"Vote at top.gg"
        self.add_item(discord.ui.Button(label=label, url="https://top.gg/servers/595457764935991326/vote", emoji=discord.PartialEmoji.from_str('<a:dv_iconOwO:837943874973466664>'), disabled=True if timetovote > 0 else False))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        ctx = self.context
        author = ctx.author
        if interaction.user != author:
            await interaction.response.send_message("These are not your vote reminders. You can choose to be reminded for voting for the server by sending `dv.votereminder` yourself!", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        for b in self.children:
            b.disabled = True
        await self.response.edit(view=self)


guildid = 871734809154707467 if os.getenv('state') == '1' else 595457764935991326  # testing server: 871734809154707467
vdanksterid = 874897331252760586 if os.getenv('state') == '1' else 683884762997587998  # testing server role: 874897331252760586
channelid = 977043022082613320 if os.getenv('state') == '1' else 754725833540894750  # 874897401729671189
level_10_role = 905980110954455070 if os.getenv('state') == '1' else 758172014439301150


async def generate_leaderboard(voters: List[Voter], guild, channel):
    leaderboard = []
    for voter in voters[:10]:
        member = guild.get_member(voter.member_id)
        name = member.display_name.replace("[AFK] ", "") if member is not None else str(voter.member_id)
        name = (name[:12] + '...') if len(name) > 15 else name  # shortens the nickname if it's too long
        leaderboard.append((name, voter.count))  # this is the final list of leaderboard people
    font_name = "assets/fonts/Fredoka-Medium.ttf"

    cover1to5 = Image.open("assets/1to5votecover.png").convert("RGBA")
    cover6to10 = Image.open("assets/6to10votecover.png").convert("RGBA")

    lbpositions = [(204, 240), (204, 390), (204, 550), (204, 710), (204, 870), (1150, 240), (1150, 390),
                   (1150, 550), (1150, 710),
                   (1150, 870)]  # these are the positions for the nicknames in the leaderboard
    countpositions = [(780, 240), (780, 390), (780, 550), (780, 710), (780, 870), (1730, 240), (1730, 390),
                      (1730, 550), (1730, 710), (1730, 870)]  # these are the positions for the number of votes
    font = ImageFont.truetype(font_name, 60)  # opens the font
    ima = Image.open("assets/lbbg.png")  # opens leaderboard background
    ima = ima.convert("RGB")  # Convert into RGB instead of RGBA so that it can be saved as a jpeg
    draw = ImageDraw.Draw(ima)  # starts the drawing process
    # Draw the names and vote counts for all
    for voter in leaderboard[:5]:
        draw.text(lbpositions[leaderboard.index(voter)], voter[0], font=font, fill=(255, 255, 255))  # White color for text

    ima.paste(cover1to5, (0, 0), cover1to5)

    if len(leaderboard) > 5:
        for voter in leaderboard[5:]:
            draw.text(lbpositions[leaderboard.index(voter)], voter[0], font=font,
                      fill=(255, 255, 255))  # White color for text
        ima.paste(cover6to10, (0, 0), cover6to10)


    # Redraw the vote counts to ensure they are on top of the overlays
    draw = ImageDraw.Draw(ima)  # Refresh the drawing context
    for voter in leaderboard:
        draw.text(countpositions[leaderboard.index(voter)], str(voter[1]), font=font, fill=(255, 255, 255))  # White color for text
    b = BytesIO()
    b.seek(0)
    ima.save(b, format="jpeg", optimize=True, quality=50)  # saves the file under a temporary name
    b.seek(0)
    return len(voters), discord.File(fp=b, filename="leaderboard.jpg")


class VoteTracker(commands.Cog, name='votetracker'):
    """
    Vote tracker commands
    """
    def __init__(self, client):
        self.client: dvvt = client
        self.description = "Vote tracker commands"
        self.reminders.start()
        self.leaderboardloop.start()
        self.client.topgg_webhook = topgg.WebhookManager(client).dsl_webhook("/webhook", "ABCDE")
        self.client.topgg_webhook.run(5000)
        print(f"{datetime.datetime.utcnow().strftime(self.client.logstrf)} | Topgg Webhook loaded")
        self.client.topgg_webhook = topgg.WebhookManager(client).dsl_webhook("/webhook", "Basic KPmcFTMadfHBHo3hWm5MqzxDTArZHYeC")
        self.client.topgg_webhook.run(5001)
        self.votedb = None
        print(f"{datetime.datetime.utcnow().strftime(self.client.logstrf)} | Disurl Webhook loaded")

    async def prepare_votedb(self):
        if self.votedb is None:
            self.votedb = VoteDB(self.client.db)
    async def add_item_count(self, item, user, amount):
        does_inventory_exist = await self.client.db.fetchrow("SELECT * FROM inventories WHERE user_id = $1",
                                                                  user.id)
        useritem_query = "SELECT {} FROM inventories WHERE user_id = $1".format(item)
        useritem = await self.client.db.fetchval(useritem_query, user.id)
        if does_inventory_exist:
            if useritem is None:
                useritem_query = "UPDATE inventories SET {} = $2 WHERE user_id = $1 RETURNING {}".format(item, item)
            else:
                useritem_query = "UPDATE inventories SET {} = {} + $2 WHERE user_id = $1 RETURNING {}".format(item, item, item)
        else:
            useritem_query = "INSERT INTO inventories (user_id, {}) VALUES ($1, $2) RETURNING {}".format(item, item)
        return await self.client.db.fetchval(useritem_query, user.id, amount, column=item)

    def cog_unload(self):
        self.reminders.stop()
        self.leaderboardloop.stop()
        self.client.topgg_webhook.close()
        self.client.disurl_webhook.close()

    @tasks.loop(seconds=5.0)  # this is the looping task that will remind people to vote in 12 hours.
    async def reminders(self):
        try:
            await self.client.wait_until_ready()
            await self.prepare_votedb()
            result = await self.votedb.get_voters(True)
            if len(result) == 0:
                return
            for row in result:  # iterate through the list of members who have reminders.
                row: Voter = row
                memberid = row.member_id
                member = self.client.get_user(memberid)
                remindertime = row.rmtime
                row.rmtime = None
                await self.votedb.update_voter(row)
                channel = self.client.get_channel(channelid)

                class VoteLink(discord.ui.View):
                    def __init__(self):
                        super().__init__()
                        self.add_item(discord.ui.Button(label='Vote for Dank Vibes at Top.gg', url="https://top.gg/servers/595457764935991326/vote", emoji=discord.PartialEmoji.from_str('<a:dv_iconOwO:837943874973466664>')))
                if member is None:
                    return
                if row.rmtype == 1: # DM
                    message = "You can now vote for Dank Vibes again!"
                    if row.count < 1:
                        message += "\nYou can get **special perks** by voting multiple times for Dank Vibes! Run `-voterperks` in a channel to find out more.\n\n*If you do not wish to receive reminders, run `dv.myvotes` in a channel in Dank Vibes.*"
                    try:
                        await member.send(message, view=VoteLink())
                    except discord.Forbidden:
                        await channel.send(f"{member.mention} You can now vote for Dank Vibes again!", view=VoteLink(), delete_after=5.0)  # uses ping instead if the bot cannot DM this user
                elif row.rmtype == 2:
                    await channel.send(f"{member.mention} You can now vote for Dank Vibes again!", view=VoteLink(), delete_after=5.0)  # self-explainable
                elif row.rmtype not in [0, 1, 2]:  # somehow this guy doesn't have "dm" "ping or "none" in his setting so i'll update it to show that
                    row.rmtype = 0
                    await self.votedb.update_voter(row)
                    return
        except Exception as error:
            traceback_error = print_exception(f'Ignoring exception in Reminder task', error)
            embed = discord.Embed(color=0xffcccb, description=f"Error encountered on a Reminder task.\n```py\n{traceback_error}```", timestamp=discord.utils.utcnow())
            if len(embed) < 6000:
                await self.client.get_guild(871734809154707467).get_channel(871737028105109574).send(embed=embed)
            else:
                await self.client.get_guild(871734809154707467).get_channel(871737028105109574).send("There was en error with vote reminders, check the log for more info.")

    @tasks.loop(hours=24.0)
    async def leaderboardloop(self):
        await self.client.wait_until_ready()
        if (await self.client.get_guild_settings(guildid)).votelb is True:
            voters = await self.votedb.get_voters(expiring=False, limit=10)
            guild = self.client.get_guild(guildid)
            channel = guild.get_channel(channelid)
            if channel is None:
                return
            leaderboard_len, file = await generate_leaderboard(voters, guild, channel)
            try:
                await channel.send("This is the vote leaderboard for **Dank Vibes**!" if leaderboard_len != 0 else "This is the vote leaderboard for **Dank Vibes**!\nThere's no one in the leaderboard, perhaps you could be the first on the leaderboard by voting at https://top.gg/servers/595457764935991326/vote !", file=file)
            except discord.Forbidden:
                await channel.send("I do not have permission to send the leaderboard here.")
            return

    @commands.Cog.listener()
    async def on_dsl_vote(self, data):
        await self.client.wait_until_ready()
        await self.prepare_votedb()
        print(f"raw vote data detected {data}")
        try:
            timenow = round(time.time())
            timetoremove = timenow + 86400
            timetoremind = timenow + 43200
            userid = int(data.get('user', None) or data.get('userId', None) or data.get('user_id', None))
            guildid = int(data.get('guild', None) or data.get('guildId', None) or data.get('guild_id', None))
            votingchannel = self.client.get_channel(channelid)
            guild = self.client.get_guild(guildid)
            member = guild.get_member(userid)
            if member is None or votingchannel is None or guild is None:
                print(
                    f"Some variables not found:\nMember: {member}\nVoting Channel: {votingchannel}\nGuild: {guild}")
                return
            vdankster = guild.get_role(vdanksterid)
            rolesummary = "\u200b"  # If no roles are added, this will be in the section where the roles added are displayed.

            embed = discord.Embed(title=f"Thank you for voting for {guild.name}, {member.name}!",
                                  description=f"This was a test vote. \n[You can vote for Dank Vibes on top.gg here!](https://top.gg/servers/595457764935991326/vote)",
                                  timestamp=discord.utils.utcnow(), color=self.client.embed_color) # In case it is a test upvote

            if data.get('type', None) in ['upvote', 'vote']:
                rolesummary = ""
                try:
                    votecount = await self.votedb.add_one_votecount(member)
                    if votecount is False:
                        rolesummary += "⚠️ An error occred and I could not add this vote count.\n"

                except Exception as e:
                    print_exception("Error while updating votecount", e)
                    await self.client.get_channel(871737028105109574).send(str(e))
                else:
                    try:
                        await member.add_roles(vdankster, reason=f"Voted for {guild.name}")
                        rolesummary = f"You've received {vdankster.mention} for 24 hours."
                    except discord.Forbidden:
                        pass
                    existing_reminder = await self.votedb.get_voter(member)
                    existing_reminder.rmtime = timetoremind
                    await self.votedb.update_voter(existing_reminder)
                    await self.client.db.execute("INSERT INTO autorole (member_id, guild_id, role_id, time) VALUES ($1, $2, $3, $4) ON CONFLICT (member_id, role_id) DO UPDATE SET time = EXCLUDED.time", userid, guildid, vdanksterid, timetoremove)

                    milestones = await self.client.db.fetch("SELECT * FROM milestones")
                    if len(milestones) != 0:
                        for milestone in milestones:
                            role = guild.get_role(milestone.get('roleid'))
                            if (
                                    role is not None
                                    and votecount.count >= milestone.get('votecount')
                                    and role not in member.roles
                            ):
                                try:
                                    await member.add_roles(role, reason=f"Vote Milestone reached for user")
                                    rolesummary += f"\n**You've also received {role.mention} for voting {milestone[0]} times!** 🥳"
                                except discord.Forbidden:
                                    pass
                    if discord.utils.get(member.roles, id=level_10_role) is not None and votecount.count % 2 == 0:
                        await self.add_item_count('snipepill', member, 1)
                        rolesummary += f"\nYou've received **1 <:DVB_SnipePill:983244179213783050> Snipe Pill** for every 2 votes!"
                    embed.description = f"You've voted **{plural(votecount.count):time}** so far.\n[Vote for Dank Vibes on top.gg here!](https://top.gg/servers/595457764935991326/vote)"
            embed.set_author(name=f"{proper_userf(member)} ({member.id})", icon_url=member.display_avatar.url)
            embed.set_footer(text=guild.name, icon_url=guild.icon.url)
            qbemojis = ["https://cdn.discordapp.com/emojis/869579459420913715.gif?v=1",
                        "https://cdn.discordapp.com/emojis/869579448708653066.gif?v=1",
                        "https://cdn.discordapp.com/emojis/869579493776457838.gif?v=1",
                        "https://cdn.discordapp.com/emojis/869579480509841428.gif?v=1",
                        "https://cdn.discordapp.com/emojis/873643650607894548.gif?v=1",
                        "https://cdn.discordapp.com/emojis/871970548576559155.gif?v=1",
                        "https://cdn.discordapp.com/emojis/872470665607909417.gif?v=1",
                        "https://cdn.discordapp.com/emojis/830920902019514408.gif?v=1"]
            embed.set_thumbnail(url=random.choice(qbemojis))
            embed.add_field(name="\u200b", value=rolesummary)
            try:
                await votingchannel.send(embed=embed)
            except discord.Forbidden:
                pass
        except Exception as e:
            await self.client.get_user(650647680837484556).send(
                f"Error in DSL Vote: ```py\n{e}\n```\nData: ```json\n{data}\n```")
            print_exception("Error in Vote", e)
            raise(e)

    @commands.group(invoke_without_command=True, name="voteroles")
    @commands.has_guild_permissions(manage_roles=True)
    async def voteroles(self, ctx):
        """
        Configure the milestones for the roles.
        """
        embed = discord.Embed(title=f"Dank Vibes Vote Roles configuration", description=f"",
                              timestamp=discord.utils.utcnow(), color=self.client.embed_color)
        embed.add_field(name="How to configure the vote roles?",
                        value=f"`voteroles list` shows all milestones for vote roles.\n`votereminder add [votecount] [role]` adds a milestone for vote roles.\n`votereminder remove [votecount]` will remove the milestone for vote count.")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="Roles can be stated via a name, mention or ID.")
        await ctx.send(embed=embed)

    @voteroles.command(name="list", aliases=["show"])
    @commands.has_guild_permissions(manage_roles=True)
    async def rolelist(self, ctx):
        """
        Lists milestones for vote roles.
        """
        milestones = await self.client.db.fetch("SELECT * FROM milestones")
        if len(milestones) == 0:
            embed = discord.Embed(title="Vote count milestones", description="There are no milestones set for now. Use `voteroles add [votecount] [role]` to add one.", color=self.client.embed_color)
            return await ctx.send(embed=embed)
        output = ''
        for row in milestones:
            if len(output) >= 3780:
                embed = discord.Embed(title="Vote count milestones",
                                      description=output,
                                      color=self.client.embed_color)
                await ctx.send(embed=embed)
            role = ctx.guild.get_role(row.get('roleid'))
            rolemention = role.mention if role is not None else "unknown-or-deleted-role"
            output += f"**{row.get('votecount')} votes: **{rolemention}\n"
        embed = discord.Embed(title="Vote count milestones",
                              description=output,
                              color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_footer(text="To edit the milestones, use the subcommands `add` and `remove`.")
        await ctx.send(embed=embed)

    @voteroles.command(name="add", aliases=["create"])
    @commands.has_guild_permissions(manage_roles=True)
    async def roleadd(self, ctx, votecount=None, role: discord.Role = None):
        """
        Adds milestones for vote roles.
        """
        if votecount is None or role is None:
            return await ctx.send("The correct usage of this command is `voteroles add [votecount] [role]`.")
        try:
            votecount = int(votecount)
        except ValueError:
            return await ctx.send("`votecount` is not a valid number.")
        existing_milestones = await self.client.db.fetch("SELECT * FROM milestones WHERE votecount = $1", votecount)
        if len(existing_milestones) > 0:
            await ctx.send(f"You have already set a milestone for **{votecount} votes**. To set a new role, remove this milestone and add it again.")
            return
        await self.client.db.execute("INSERT INTO milestones VALUES($1, $2)", votecount, role.id)
        await ctx.send(f"**Done**\n**{role.name}** will be added to a member when they have voted **{votecount} time(s)**.")

    @voteroles.command(name="remove", aliases=["delete"])
    @commands.has_guild_permissions(manage_roles=True)
    async def roleremove(self, ctx, votecount=None):
        """
        Removes milestones for vote roles.
        """
        if votecount is None:
            return await ctx.send("The correct usage of this command is `voteroles remove [votecount]`.")
        try:
            votecount = int(votecount)
        except ValueError:
            return await ctx.send(f"`{votecount}` as the votecount is not a valid number.")
        existing_milestones = await self.client.db.fetch("SELECT * FROM milestones WHERE votecount = $1", votecount)
        if len(existing_milestones) == 0:
            return await ctx.send(
                f"You do not have a milestone set for {votecount} votes. Use `voteroles add [votecount] [role]` to add one.")
        await self.client.db.execute("DELETE FROM milestones WHERE votecount = $1", votecount)
        await ctx.send(f"**Done**\nThe milestone for having voted **{votecount} time(s)** has been removed.")

    @commands.command(name="votecountreset")
    @commands.has_guild_permissions(manage_roles=True)
    async def vcreset(self, ctx):
        """
        Reset the vote count database. **This action is irreversible.**
        """
        votecount = await self.client.db.fetch("SELECT * FROM votecount")
        if len(votecount) == 0:  # if there's nothing to be deleted
            return await ctx.send("There's nothing in the database to be removed.")
        totalvote = sum(voter.get('count') for voter in votecount)
        embed = discord.Embed(title="Database pending removal", description=f"There are **{len(votecount)}** entries (or users) currently in the database, amounting to a total of {totalvote} votes. \n Are you sure you want to remove them? **This action is irreversible**! This will not remove users' vote reminder settings.", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        confirmview = confirm(ctx, self.client, 15.0)
        message = await ctx.send(embed=embed, view=confirmview)
        confirmview.response = message
        await confirmview.wait()
        if confirmview.returning_value is None:
            embed.description, embed.color = "No response.", discord.Color.red()
            return await message.edit(embed=embed)
        elif not confirmview.returning_value:
            embed.description, embed.color = "Command stopped.", discord.Color.red()
            return await message.edit(embed=embed)
        elif confirmview.returning_value:
            await self.client.db.execute("UPDATE voters SET count = 0 WHERE count > 0")
            return await message.edit(embed=discord.Embed(title="Database pending removal", description="All vote counts have been reset, and all entries in the database has been deleted.", color = discord.Color.green()))

    @commands.command(name="voteleaderboard", aliases = ["vlb", "votelb"])
    async def leaderboard(self, ctx):
        """
        Shows the leaderboard for the top 10 voters for Dank Vibes.
        You can also view your rank on the vote leaderboard.
        """
        with ctx.typing():
            # votecount =
            voters = await self.votedb.get_voters(expiring=False, limit=None)
            guild = self.client.get_guild(guildid)
            channel = guild.get_channel(channelid)
            if channel is None:
                return
            leaderboard_len, file = await generate_leaderboard(voters, guild, channel)
            voter = await self.votedb.get_voter(ctx.author)
            position = await self.client.db.fetchval("SELECT COUNT(*) + 1 AS rank FROM voters WHERE count > (SELECT count FROM voters WHERE member_id = $1)", ctx.author.id)
            if voter.count < 1:
                message = "You're not on the leaderboard yet. Vote for Dank Vibes for a chance to be on it! <https://top.gg/servers/595457764935991326/vote>"
            else:
                message = f"You're ranked **{position}** out of {leaderboard_len} members on the vote leaderboard. {'🏆' if position < 11 else ''}"
        try:
            await ctx.send(f"This is the vote leaderboard for Dank Vibes! {message}" if leaderboard_len != 0 else "This is the vote leaderboard for **Dank Vibes**!\nThere's no one in the leaderboard, perhaps you could be the first on the leaderboard by voting at https://top.gg/servers/595457764935991326/vote !", file=file)
        except discord.Forbidden:
            await ctx.send("I do not have permission to send the leaderboard here.")
        return

    @commands.command(name="vote", aliases=["upvote", "v"])
    async def vote(self, ctx):
        """
        Shows you where to vote for Dank Vibes.
        """
        embed = discord.Embed(title="Show Your Support!", description="If you like what you're seeing from Dank Vibes, feel free to upvote the server [here](https://top.gg/servers/595457764935991326/vote). You can upvote the server every 12 hours! <a:dv_qbThumbsupOwO:837666232811257907>\n\n**__Voter Perks__** \n<a:dv_wpointArrowOwO:837656328482062336> Obtain the <@&683884762997587998> role\n<a:dv_wpointArrowOwO:837656328482062336> Access to <#753577021950656583> ~ **2x** multi \n<a:dv_wpointArrowOwO:837656328482062336> Access to <#751740855269851236> ~ **2x** multi\n\n⭐ View the additional perks for voting by running `-voterperks`\n\n**TIP**: Set reminders to vote using `dv.votereminder`\n**NOTE**: Perks are limited to 1 day | Revote to obtain the perks again", timestamp=discord.utils.utcnow(), color=0xB8D5FF)
        embed.set_thumbnail(url="https://i.imgur.com/kLVa5dD.gif")
        embed.set_footer(text="Dank Vibes | Thank you for all your support ♡", icon_url="https://cdn.discordapp.com/icons/595457764935991326/a_58b91a8c9e75742d7b423411b0205b2b.png?size=1024")

        class Vote(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.add_item(discord.ui.Button(label='Vote for Dank Vibes', url="https://top.gg/servers/595457764935991326/vote", emoji=discord.PartialEmoji.from_str('<a:dv_iconOwO:837943874973466664>')))

        await ctx.send(embed=embed, view=Vote())

    @commands.command(name="myvotes", aliases=["myv", "myvote", "votes"])
    @checks.not_in_gen()
    async def myvotes(self, ctx):
        """
        See how many times you have voted for Dank Vibes.
        """
        timenow = round(time.time())
        user_voter = await self.votedb.get_voter(ctx.author)
        # count = await self.client.db.fetchval("SELECT count FROM votecount where member_id = $1", ctx.author.id) or 0
        # result = await self.client.db.fetchrow("SELECT * FROM roleremove WHERE member_id = $1 and rmtime > $2", ctx.author.id, timenow)
        nextmilestone = await self.client.db.fetchval("SELECT votecount FROM milestones WHERE votecount > $1 LIMIT 1", user_voter.count)
        if user_voter.rmtime is not None:
            desc = f"Vote again in <t:{user_voter.rmtime}:R>!"
        else:
            desc = f"You can vote now!"
        embed = discord.Embed(title=f"You've voted for Dank Vibes **__{plural(user_voter.count):__**time}.", description=desc, url="https://top.gg/servers/595457764935991326/vote")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        if user_voter.rmtype == 0:
            footer_msg = "You're currently not reminded to vote. Choose how you'd like to be reminded below (DMs or Pings)!"
        elif user_voter.rmtype == 1:
            footer_msg = None
        elif user_voter.rmtype == 2:
            footer_msg = None
        else:
            footer_msg = None
        if nextmilestone is not None:
            count_to_next = nextmilestone - user_voter.count
            embed.add_field(name="Milestones 🎯 ", value=f"**{plural(count_to_next):** vote} votes away from **{nextmilestone} votes**!", inline=False)
        if footer_msg is not None:
            embed.set_footer(text=footer_msg)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        if user_voter.rmtime is None:
            duration = 0
        else:
            duration = user_voter.rmtime - timenow
        view = VoteSettingView(client=self.client, cog=self, ctx=ctx, timeout=30.0, voter=user_voter, timetovote=duration)
        message = await ctx.send(embed=embed, view=view)
        view.response = message
        await view.wait()
