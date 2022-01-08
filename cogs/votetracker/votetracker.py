import os
import time
import topgg
import discord
import random
from PIL import ImageFont, Image, ImageDraw
from discord.ext import commands, tasks
from utils.format import print_exception, ordinal, plural, short_time
from io import BytesIO
from utils.buttons import *
from utils import checks


class VoteSetting(discord.ui.Select):
    def __init__(self, client, context, response, currentsetting):
        self.client = client
        self.response = response
        self.context = context
        self.currentsetting = currentsetting
        labels = ["None", "DM", "Ping"]
        descriptions = [f"{self.client.user.name} will not remind you to vote for the server.", f"{self.client.user.name} will DM you after 12 hours to vote for the server.", f"{self.client.user.name} will ping you after 12 hours to vote for the server."]
        emojis = [discord.PartialEmoji.from_str("<:DVB_None:884743780027219989>"), discord.PartialEmoji.from_str("<:DVB_Letter:884743813166407701>"), discord.PartialEmoji.from_str("<:DVB_Ping:883744614295674950>")]
        options = []
        for index, label in enumerate(labels):
            options.append(discord.SelectOption(label=label, description=descriptions[labels.index(label)], emoji=emojis[labels.index(label)], default=True if index == self.currentsetting and label != "None" else False))
        super().__init__(placeholder='Choose your type of vote reminder...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "DM":
            await self.client.pool_pg.execute("UPDATE rmpreference SET rmtype = $1 WHERE member_id = $2", 1, self.context.author.id)
            await interaction.response.send_message("Your reminder settings have been changed. You will **now be DMed** to vote for Dank Vibes.", ephemeral=True)
        if self.values[0] == "Ping":
            await self.client.pool_pg.execute("UPDATE rmpreference SET rmtype = $1 WHERE member_id = $2", 2, self.context.author.id)
            await interaction.response.send_message("Your reminder settings have been changed. You will **now be pinged** to vote for Dank Vibes.", ephemeral=True)
        if self.values[0] == "None":
            await self.client.pool_pg.execute("UPDATE rmpreference SET rmtype = $1 WHERE member_id = $2", 0, self.context.author.id)
            await interaction.response.send_message("Your reminder settings have been changed. You will **not be reminded** to vote for Dank Vibes.\nYou will lose out on some vote perks if you don't vote regularly!", ephemeral=True)


class VoteSettingView(discord.ui.View):
    def __init__(self, client, ctx, timeout, currentsetting, timetovote):
        self.client = client
        self.timeout = timeout
        self.response = None
        self.context = ctx
        self.currentsetting = currentsetting
        super().__init__(timeout=timeout)
        self.add_item(VoteSetting(client=self.client, context=self.context, response=self.response, currentsetting=self.currentsetting))
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
channelid = 874897401729671189 if os.getenv('state') == '1' else 754725833540894750  # 874897401729671189


class VoteTracker(commands.Cog, name='votetracker'):
    """
    Vote tracker commands
    """
    def __init__(self, client):
        self.client = client
        self.description = "Vote tracker commands"
        self.reminders.start()
        self.leaderboardloop.start()
        self.client.topgg_webhook = topgg.WebhookManager(client).dsl_webhook("/webhook", "ABCDE")
        self.client.topgg_webhook.run(5000)

    def cog_unload(self):
        self.reminders.stop()
        self.leaderboardloop.stop()

    @tasks.loop(seconds=5.0)  # this is the looping task that will remind people to vote in 12 hours.
    async def reminders(self):
        try:
            await self.client.wait_until_ready()
            timenow = round(time.time())
            result = await self.client.pool_pg.fetch("SELECT * FROM roleremove WHERE rmtime < $1", timenow)
            first_time = False
            if len(result) == 0:
                return
            for row in result:  # iterate through the list of members who have reminders.
                memberid = row.get('member_id')
                await self.client.pool_pg.execute('UPDATE roleremove SET rmtime = $1 WHERE member_id = $2', 9223372036854775807, memberid)
                preferences = await self.client.pool_pg.fetchrow("SELECT rmtype FROM rmpreference WHERE member_id = $1", memberid)
                if preferences is None:  # somehow there is no preference for this user, so i'll create an entry to prevent it from breaking
                    await self.client.pool_pg.execute("INSERT INTO rmpreference(member_id, rmtype) VALUES($1, $2)", memberid, 1)
                    preferences = await self.client.pool_pg.fetchrow("SELECT rmtype FROM rmpreference WHERE member_id = $1", memberid)  # refetch the configuration for this user after it has been added
                    first_time = True
                member = self.client.get_user(memberid)
                channel = self.client.get_channel(channelid)

                class VoteLink(discord.ui.View):
                    def __init__(self):
                        super().__init__()
                        self.add_item(discord.ui.Button(label='Vote for Dank Vibes at Top.gg', url="https://top.gg/servers/595457764935991326/vote", emoji=discord.PartialEmoji.from_str('<a:dv_iconOwO:837943874973466664>')))
                if member is None:
                    return
                if preferences.get('rmtype') == 1:
                    message = "You can now vote for Dank Vibes again!"
                    if first_time:
                        message += " By voting for Dank Vibes **multiple times**, you can get **special perks**! Run `-voterperks` in a channel to find out more.\n\nTip: You can turn off reminders or be pinged for voting by selecting the respective option in `dv.myvotes`. Use this in a server channel though."
                    try:
                        await member.send(message, view=VoteLink())
                    except discord.Forbidden:
                        await channel.send(f"{member.mention} You can now vote for Dank Vibes again!", view=VoteLink(), delete_after=5.0)  # uses ping instead if the bot cannot DM this user
                elif preferences.get('rmtype') == 2:
                    await channel.send(f"{member.mention} You can now vote for Dank Vibes again!", view=VoteLink(), delete_after=5.0)  # self-explainable
                elif preferences.get('rmtype') not in [0, 1, 2]:  # somehow this guy doesn't have "dm" "ping or "none" in his setting so i'll update it to show that
                    await self.client.pool_pg.execute('UPDATE rmpreference set rmtype = $1 where member_id = $2', 0, memberid)  # changes his setting to none
                    return
        except Exception as error:
            traceback_error = print_exception(f'Ignoring exception in Reminder task', error)
            embed = discord.Embed(color=0xffcccb, description=f"Error encountered on a Reminder task.\n```py\n{traceback_error}```", timestamp=discord.utils.utcnow())
            await self.client.get_guild(871734809154707467).get_channel(871737028105109574).send(embed=embed)

    @tasks.loop(hours=24.0)
    async def leaderboardloop(self):
        await self.client.wait_until_ready()
        if await self.client.pool_pg.fetchval("SELECT enabled FROM serverconfig WHERE guild_id=$1 AND settings=$2", guildid, 'votelb'):
            votecount = await self.client.pool_pg.fetch("SELECT * FROM votecount ORDER BY count DESC LIMIT 10")  # gets top 10 voters
            leaderboard = []
            guild = self.client.get_guild(guildid)
            channel = guild.get_channel(channelid)
            if channel is None:
                return
            for voter in votecount:
                member = guild.get_member(voter.get('member_id'))
                name = member.display_name.replace("[AFK] ", "") if member is not None else str(voter.get('member_id'))  # shows user id if the user left the server
                name = (name[:12] + '...') if len(name) > 15 else name  # shortens the nickname if it's too long
                leaderboard.append((name, voter[1]))  # this is the final list of leaderboard people
            font_name = "assets/Gagalin.ttf"
            lbpositions = [(204, 240), (204, 390), (204, 550), (204, 710), (204, 870), (1150, 240), (1150, 390),
                        (1150, 550), (1150, 710),
                        (1150, 870)]  # these are the positions for the nicknames in the leaderboard
            countpositions = [(780, 240), (780, 390), (780, 550), (780, 710), (780, 870), (1730, 240), (1730, 390),
                            (1730, 550), (1730, 710), (1730, 870)]  # these are the positions for the number of votes
            font = ImageFont.truetype(font_name, 60)  # opens the font
            ima = Image.open("assets/lbbg.png")  # opens leaderboard background
            ima = ima.convert("RGB")  # Convert into RGB instead of RGBA so that it can be saved as a jpeg
            draw = ImageDraw.Draw(ima)  # starts the drawing process
            for voter in leaderboard:
                draw.text(lbpositions[leaderboard.index(voter)], voter[0], font=font, align="middle left")  # Adds a user's nickname
                draw.text(countpositions[leaderboard.index(voter)], str(voter[1]), font=font, align="right")  # adds a user's vote count
            b = BytesIO()
            b.seek(0)
            ima.save(b, format="jpeg", optimize=True, quality=50)  # saves the file under a temporary name
            b.seek(0)
            file = discord.File(fp=b, filename="leaderboard.jpg")
            try:
                await channel.send("This is the vote leaderboard for **Dank Vibes**!" if len(leaderboard) != 0 else "This is the vote leaderboard for **Dank Vibes**!\nThere's no one in the leaderboard, perhaps you could be the first on the leaderboard by voting at https://top.gg/servers/595457764935991326/vote !", file=file)
            except discord.Forbidden:
                await channel.send("I do not have permission to send the leaderboard here.")
            return

    @commands.Cog.listener()
    async def on_dsl_vote(self, data):
        timenow = round(time.time())
        timetoremove = timenow + 86400
        timetoremind = timenow + 43200
        userid = int(data['user'])
        guildid = int(data['guild'])
        if data['type'] != 'upvote':
            return
        votingchannel = self.client.get_channel(channelid)
        guild = self.client.get_guild(guildid)
        member = guild.get_member(userid)
        if member is None or votingchannel is None or guild is None:
            return f"Some variables not found:\nMember: {member}\nVoting Channel: {votingchannel}\nGuild: {guild}"
        vdankster = guild.get_role(vdanksterid)
        rolesummary = "\u200b"  # If no roles are added, this will be in the section where the roles added are displayed.
        result = await self.client.pool_pg.fetchrow("SELECT count FROM votecount WHERE member_id = $1", userid)
        votecount = 1 if result is None else result.get('count') + 1
        if result is None:
            await self.client.pool_pg.execute("INSERT INTO votecount VALUES($1, $2)", userid, votecount)
        else:
            await self.client.pool_pg.execute("UPDATE votecount SET count = $1 where member_id = $2", votecount, userid)
        try:
            await member.add_roles(vdankster, reason="Voted for the server")
            rolesummary = f"You've received the role {vdankster.mention} for 24 hours."
        except discord.Forbidden:
            pass
        existing_remind = await self.client.pool_pg.fetchrow("SELECT * from roleremove where member_id = $1", userid)
        if existing_remind is None:
            await self.client.pool_pg.execute("INSERT INTO roleremove VALUES($1, $2, $3)", userid, timetoremind, timetoremove)
        else:
            await self.client.pool_pg.execute("UPDATE roleremove SET rmtime = $1, roletime = $2 WHERE member_id = $3", timetoremind, timetoremove, userid)
        existing_remove = await self.client.pool_pg.fetchrow("SELECT * FROM autorole WHERE member_id = $1 and role_id = $2", userid, vdanksterid)
        if existing_remove is None:
            await self.client.pool_pg.execute("INSERT INTO autorole VALUES($1, $2, $3, $4)", userid, guildid, vdanksterid, timetoremove)
        else:
            await self.client.pool_pg.execute("UPDATE autorole SET time = $1 WHERE member_id = $2 and role_id = $3", timetoremove, userid, vdanksterid)
        milestones = await self.client.pool_pg.fetch("SELECT * FROM milestones")
        if len(milestones) != 0:
            for milestone in milestones:
                role = guild.get_role(milestone.get('roleid'))
                if (
                    role is not None
                    and votecount >= milestone.get('votecount')
                    and role not in member.roles
                ):
                    try:
                        await member.add_roles(role, reason=f"Milestone reached for user")
                        rolesummary += f"\n**You've also gotten the role {role.mention} for voting {milestone[0]} times!** 🥳"
                    except discord.Forbidden:
                        pass
        embed = discord.Embed(title=f"Thank you for voting for {guild.name}, {member.name}!", description=f"You've voted **{plural(votecount):time}** so far.\n[You can vote for Dank Vibes on top.gg here!](https://top.gg/servers/595457764935991326/vote)", timestamp=discord.utils.utcnow(), color=self.client.embed_color)
        embed.set_author(name=f"{member.name}#{member.discriminator} ({member.id})", icon_url=member.display_avatar.url)
        embed.set_footer(text=guild.name, icon_url=guild.icon.url)
        qbemojis = ["https://cdn.discordapp.com/emojis/869579459420913715.gif?v=1", "https://cdn.discordapp.com/emojis/869579448708653066.gif?v=1", "https://cdn.discordapp.com/emojis/869579493776457838.gif?v=1", "https://cdn.discordapp.com/emojis/869579480509841428.gif?v=1", "https://cdn.discordapp.com/emojis/873643650607894548.gif?v=1", "https://cdn.discordapp.com/emojis/871970548576559155.gif?v=1", "https://cdn.discordapp.com/emojis/872470665607909417.gif?v=1", "https://cdn.discordapp.com/emojis/830920902019514408.gif?v=1"]
        embed.set_thumbnail(url=random.choice(qbemojis))
        embed.add_field(name="\u200b", value=rolesummary)
        try:
            await votingchannel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.command(name="votereminder", aliases=["vrm"])
    @checks.not_in_gen()
    async def votereminder(self, ctx):
        """
        Manage your vote reminder here! This command will be deprecated in a later update.
        """
        return await ctx.send("This command's functions have been merged with `dv.myv`.")

    @commands.group(invoke_without_command=True, name="voteroles")
    @commands.has_guild_permissions(administrator=True)
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
    @commands.has_guild_permissions(administrator=True)
    async def rolelist(self, ctx):
        """
        Lists milestones for vote roles.
        """
        milestones = await self.client.pool_pg.fetch("SELECT * FROM milestones")
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
    @commands.has_guild_permissions(administrator=True)
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
        existing_milestones = await self.client.pool_pg.fetch("SELECT * FROM milestones WHERE votecount = $1", votecount)
        if len(existing_milestones) > 0:
            await ctx.send(f"You have already set a milestone for **{votecount} votes**. To set a new role, remove this milestone and add it again.")
            return
        await self.client.pool_pg.execute("INSERT INTO milestones VALUES($1, $2)", votecount, role.id)
        await ctx.send(f"**Done**\n**{role.name}** will be added to a member when they have voted **{votecount} time(s)**.")

    @voteroles.command(name="remove", aliases=["delete"])
    @commands.has_guild_permissions(administrator=True)
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
        existing_milestones = await self.client.pool_pg.fetch("SELECT * FROM milestones WHERE votecount = $1", votecount)
        if len(existing_milestones) == 0:
            return await ctx.send(
                f"You do not have a milestone set for {votecount} votes. Use `voteroles add [votecount] [role]` to add one.")
        await self.client.pool_pg.execute("DELETE FROM milestones WHERE votecount = $1", votecount)
        await ctx.send(f"**Done**\nThe milestone for having voted **{votecount} time(s)** has been removed.")

    @commands.command(name="votecountreset")
    @commands.has_guild_permissions(administrator=True)
    async def vcreset(self, ctx):
        """
        Reset the vote count database. **This action is irreversible.**
        """
        votecount = await self.client.pool_pg.fetch("SELECT * FROM votecount")
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
        elif confirmview.returning_value == False:
            embed.description, embed.color = "Command stopped.", discord.Color.red()
            return await message.edit(embed=embed)
        elif confirmview.returning_value == True:
            await self.client.pool_pg.execute("DELETE FROM votecount")
            return await message.edit(embed=discord.Embed(title="Database pending removal", description="All vote counts have been reset, and all entries in the database has been deleted.", color = discord.Color.green()))

    @commands.command(name="voteleaderboard", aliases = ["vlb", "votelb"])
    async def leaderboard(self, ctx):
        """
        Shows the leaderboard for the top 10 voters for Dank Vibes.
        You can also view your rank on the vote leaderboard.
        """
        with ctx.typing():
            votecount = await self.client.pool_pg.fetch("SELECT * FROM votecount ORDER BY count DESC")
            leaderboard = []
            for voter in votecount[:10]:
                member = ctx.guild.get_member(voter.get('member_id'))
                name = member.display_name.replace("[AFK] ", "") if member is not None else str(voter.get('member_id'))
                name = (name[:15] + '...') if len(name) > 18 else name
                leaderboard.append((name, voter[1]))
            font_name = "assets/Gagalin.ttf"
            lbpositions = [(204, 240), (204, 390), (204, 550), (204, 710), (204, 870), (1150, 240), (1150, 390), (1150, 550), (1150, 710), (1150, 870)]
            countpositions = [(780, 240), (780, 390), (780, 550), (780, 710), (780, 870), (1730, 240), (1730, 390), (1730, 550), (1730, 710), (1730, 870)]
            font = ImageFont.truetype(font_name, 60)
            ima = Image.open("assets/lbbg.png")
            ima = ima.convert("RGB")
            draw = ImageDraw.Draw(ima)
            for voter in leaderboard:
                draw.text(lbpositions[leaderboard.index(voter)], voter[0], font=font, align="middle left")
                draw.text(countpositions[leaderboard.index(voter)], str(voter[1]), font=font, align="right")
            b = BytesIO()
            b.seek(0)
            ima.save(b, format="jpeg", optimize=True, quality=50)
            b.seek(0)
            file = discord.File(fp=b, filename="leaderboard.jpg")
            uservotecount = await self.client.pool_pg.fetchrow("SELECT * FROM votecount where member_id = $1", ctx.author.id)
            if uservotecount is None:
                message = "You're not on the leaderboard yet. Vote for Dank Vibes for a chance to be on the leaderboard! <https://top.gg/servers/595457764935991326/vote>"
            else:
                position = ordinal(votecount.index(uservotecount)+1)
                message = f"You're ranked **{position}** out of {len(votecount)} members on the vote leaderboard. {'🏆' if votecount.index(uservotecount) < 10 else ''}"
        try:
            await ctx.send(f"This is the vote leaderboard for Dank Vibes! {message}" if len(leaderboard) != 0 else "This is the vote leaderboard for **Dank Vibes**!\nThere's no one in the leaderboard, perhaps you could be the first on the leaderboard by voting at https://top.gg/servers/595457764935991326/vote !", file=file)
        except discord.Forbidden:
            await ctx.send("I do not have permission to send the leaderboard here.")
        return

    @commands.command(name="vote", aliases=["upvote"])
    async def vote(self, ctx):
        """
        Shows you where to vote for Dank Vibes.
        """
        embed = discord.Embed(title="Show Your Support!", description="If you like what you're seeing from Dank Vibes, feel free to upvote the server [here](https://top.gg/servers/595457764935991326/vote). You can upvote the server every 12 hours! <a:dv_qbThumbsupOwO:837666232811257907>\n\n**__Voter Perks__** \n<a:dv_pointArrowOwO:837656328482062336> Obtain the <@&683884762997587998> role\n<a:dv_pointArrowOwO:837656328482062336> Access to <#753577021950656583> ~ **2x** multi \n<a:dv_pointArrowOwO:837656328482062336> Access to <#751740855269851236> ~ **2x** multi\n\n⭐ View the additional perks for voting by running `-voterperks`\n\n**TIP**: Set reminders to vote using `dv.votereminder`\n**NOTE**: Perks are limited to 1 day | Revote to obtain the perks again", timestamp=discord.utils.utcnow(), color=0xB8D5FF)
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
        count = await self.client.pool_pg.fetchval("SELECT count FROM votecount where member_id = $1", ctx.author.id) or 0
        result = await self.client.pool_pg.fetchrow("SELECT * FROM roleremove WHERE member_id = $1 and rmtime > $2", ctx.author.id, timenow)
        nextmilestone = await self.client.pool_pg.fetchval("SELECT votecount FROM milestones WHERE votecount > $1 LIMIT 1", count)
        if result is not None and result.get('rmtime') != 9223372036854775807:
            desc = f"You can vote <t:{result.get('rmtime')}:R>!"
        else:
            desc = f"You can vote now!"
        embed = discord.Embed(title=f"You have voted for Dank Vibes **__{plural(count):__**time}.", description=desc, timestamp=discord.utils.utcnow(), url="https://top.gg/servers/595457764935991326/vote")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        preferences = await self.client.pool_pg.fetchval("SELECT rmtype FROM rmpreference WHERE member_id = $1", ctx.author.id)
        if preferences is None:  # if it's the first time for the user to invoke the command, it will create an entry automatically with the default setting "none".
            preferences = await self.client.pool_pg.fetchval("INSERT INTO rmpreference VALUES($1, $2) RETURNING rmtype", ctx.author.id, 0, column='rmtype')  # fetches the new settings after the user's entry containing the 'none' setting has been created
        if preferences == 0:
            footer_msg = "You are currently not reminded to vote for Dank Vibes. You can be reminded to vote for Dank Vibes by choosing DMs or pings on the dropdown menu below!"
        elif preferences == 1:
            footer_msg = "You can change your reminder preference below!"
        elif preferences == 2:
            footer_msg = "You can change your reminder preference below!"
        else:
            footer_msg = None
        if nextmilestone is not None:
            count_to_next = nextmilestone - count
            embed.add_field(name="Milestones 🏁", value=f"You are **{plural(count_to_next):** vote} away from reaching **{nextmilestone} votes**!", inline=False)
        if footer_msg is not None:
            embed.set_footer(text=footer_msg)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        if result is None or result.get('rmtime') == 9223372036854775807:
            duration = 0
        else:
            duration = result.get('rmtime') - timenow
        view = VoteSettingView(client=self.client, ctx=ctx, timeout=30.0, currentsetting=preferences, timetovote=duration)
        message = await ctx.send(embed=embed, view=view)
        view.response = message
        await view.wait()
