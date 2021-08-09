import os
import time
import topgg
import discord
import sqlite3
import asyncio
import random
import datetime
from PIL import ImageFont, Image, ImageDraw
from utils.time import humanize_timedelta
from discord.ext import commands, tasks
from utils.format import print_exception

vdanksterid = 683884762997587998 #Change this to the Vibing Dankster role ID.
channelid = 754725833540894750 #Change this to where all the bot messages are sent.

class VoteTracker(commands.Cog, name='votetracker'):
    """
    Vote tracker commands
    """
    def __init__(self, client):
        self.client = client
        self.description = "Vote tracker commands" #If you are using a custom help command, this
        self.votetracker = sqlite3.connect('databases/votetracker.db')
        self.vdankster.start()
        self.reminders.start()
        self.client.topgg_webhook = topgg.WebhookManager(client).dsl_webhook("/webhook", "ABCDE")
        self.client.topgg_webhook.run(5000)

    def cog_unload(self):
        self.vdankster.stop()
        self.reminders.stop()

    @tasks.loop(seconds=5.0) # this is the looping task that will remove the Vibing Dankster role from the person.
    async def vdankster(self):
        await self.client.wait_until_ready()
        timenow = round(time.time()) # Gets the time now
        cursor = self.votetracker.cursor()
        result = cursor.execute("SELECT * FROM roleremove WHERE roletime < ?", (timenow,)).fetchall() # Finds the users whose roletime has passed since 24 hours ago, which was added in the webhook event below
        if len(result) == 0:
            return # No one's roles need to be removed.
        for row in result: #individually iterates through the list of people who have voted for dv more than 12 hours ago
            print("hi")
            guild = self.client.get_guild(595457764935991326)
            member = guild.get_member(row[0])
            role = guild.get_role(vdanksterid)
            if guild is not None and member is not None and role is not None: #if a member leaves, it won't break this function
                try:
                    await member.remove_roles(role, reason="24 hours passed since voting") #removes the vibing dankster role
                except discord.Forbidden:
                    pass
            cursor.execute("DELETE FROM roleremove WHERE member_id = ? and rmtime = ? and roletime = ?",(row[0], row[1], row[2])) # Removes the member from the database, but it is not published yet so it will not be overwritten
        self.votetracker.commit() #saves the deleted state of those members
        cursor.close()

    @tasks.loop(seconds=5.0) # this is the looping task that will remind people to vote in 12 hours.
    async def reminders(self):
        try:
            await self.client.wait_until_ready()
            timenow = round(time.time())
            cursor = self.votetracker.cursor()
            result = cursor.execute("SELECT * FROM roleremove WHERE rmtime < ?", (timenow,)).fetchall() # just like the task above, finds users who have voted since 12 hours ago
            if len(result) == 0:
                return
            for row in result: # iterate through the list of members who have reminders.
                cursor.execute('UPDATE roleremove SET rmtime = ? WHERE member_id = ?',(9223372036854775807, row[0]))
                preferences = cursor.execute("SELECT rmtype FROM rmpreference WHERE member_id = ?", (row[0],)).fetchall()
                if len(preferences) == 0: # somehow there is no preference for this user, so i'll create an entry to prevent it from breaking
                    sql = 'INSERT into rmpreference(member_id, rmtype) VALUES(?, ?)'  # creats a new row for first time vote count if user isn't in database
                    val = (row[0], 'none')
                    cursor.execute(sql, val)
                    self.votetracker.commit()
                    preferences = cursor.execute("SELECT rmtype FROM rmpreference WHERE member_id = ?", (row[0],)).fetchall() # refetch the configuration for this user after it has been added
                member = self.client.get_user(row[0])
                channel = self.client.get_channel(channelid)
                if preferences[0][0] == "dm":
                    try:
                        dmembed = discord.Embed(
                            description="[Vote for Dank Vibes at top.gg](https://top.gg/servers/595457764935991326/vote)",
                            color=0x57f0f0)
                        await member.send("You can now vote for Dank Vibes again!", embed=dmembed) # tries to DM the user that it is time for him to vote again
                    except discord.Forbidden:
                        await channel.send(f"{member.mention} You can now vote for Dank Vibes again!", delete_after=5.0) # uses ping instead if the bot cannot DM this user
                elif preferences[0][0] == "ping":
                    await channel.send(f"{member.mention} You can now vote for Dank Vibes again!", delete_after=5.0) # self-explainable
                elif preferences[0][0] != "none": # somehow this guy doesn't have "dm" "ping or "none" in his setting so i'll update it to show that
                    cursor.execute('UPDATE rmpreference set rmtype = ? where member_id = ?', ('none', row[0],)) # changes his setting to none
                    self.votetracker.commit()
                    return
                self.votetracker.commit()
            cursor.close()
        except Exception as error:
            traceback_error = print_exception(f'Ignoring exception in Reminder task', error)
            embed = discord.Embed(color=0xffcccb, description=f"Error encountered on a Reminder task.\n**UserID:** {row[0]} \n**For the reminder:** {row[1]}\n**More details:**\n```py\n{traceback_error}```", timestamp=datetime.datetime.utcnow())
            await self.client.get_guild(871734809154707467).get_channel(871737028105109574).send(embed=embed)

    @tasks.loop(hours=24.0)
    async def leaderboardloop(self):
        await self.client.wait_until_ready()
        cursor = self.votetracker.cursor()
        votecount = cursor.execute(
            "SELECT * FROM votecount ORDER BY count DESC LIMIT 10").fetchall()  # gets top 10 voters
        leaderboard = []
        guild = self.client.get_guild(595457764935991326)
        channel = self.client.get_channel(channelid)
        for voter in votecount:
            member = guild.get_member(voter[0])
            name = member.display_name if member is not None else voter[0]  # shows user id if the user left the server
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
            draw.text(lbpositions[leaderboard.index(voter)], voter[0], font=font,
                    align="middle left")  # Adds a user's nickname
            draw.text(countpositions[leaderboard.index(voter)], str(voter[1]), font=font,
                    align="right")  # adds a user's vote count
        filename = f"temp/{random.randint(1, 9999999)}.jpg"
        ima.save(filename, optimize=True, quality=50)  # saves the file under a temporary name
        file = discord.File(filename)
        try:
            await channel.send("This is the vote leaderboard for **Dank Vibes**!" if len(leaderboard) != 0 else "This is the vote leaderboard for **Dank Vibes**!\nThere's no one in the leaderboard, perhaps you could be the first on the leaderboard by voting at https://top.gg/servers/595457764935991326/vote !",file=file)
        except discord.Forbidden:
            await channel.send("I do not have permission to send the leaderboard here.")
        os.remove(filename)  # deletes the temporary file
        cursor.close()
        return

    @commands.Cog.listener()
    async def on_ready(self):
        cursor = self.votetracker.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS rmpreference(member_id integer PRIMARY KEY, rmtype text)")  # first time setup, creates the database for saving configurations for reminder task
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS votecount(member_id integer PRIMARY KEY,count integer)") #first time setup, creates the database for vote count
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS roleremove(member_id integer PRIMARY KEY, rmtime integer, roletime integer)") #first time setup, creates the database for role removal, time is when the role is removed in epoch time
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS milestones(votecount integer, roleid integer)")  # first time setup, creates the database for milestones to be referred to
        print("Cogs \"VoteTracker\" has loaded")

    @commands.Cog.listener()
    async def on_dsl_vote(self, data):
        timenow = time.time()
        timetoremove = timenow + 86400 # epoch time that role will be removed
        timetoremind = timenow + 43200 # epoch time that member will be reminded
        userid = int(data['user'])
        guildid = int(data['guild'])
        if data['type'] != 'upvote': #ignores webhook messages such as test
            return
        votingchannel = self.client.get_channel(channelid)  # gets the channel to send messages in
        guild = self.client.get_guild(595457764935991326)
        member = guild.get_member(userid)
        if member is None:
            return
        vdankster = guild.get_role(vdanksterid)
        rolesummary = "\u200b"  # If no roles are added, this will be in the section where the roles added are displayed.
        cursor = self.votetracker.cursor()
        result = cursor.execute('SELECT count FROM votecount where member_id = ?',
                                (userid,)).fetchall()  # gets the vote count of the user
        votecount = 1 if len(result) == 0 else result[0][0] + 1
        sql = 'INSERT OR REPLACE INTO votecount(member_id, count) VALUES(?, ?)'  # creats a new row for first time vote count if user isn't in database
        val = (userid, votecount)
        cursor.execute(sql, val)
        self.votetracker.commit()  # Done with updating count
        try:
            await member.add_roles(vdankster, reason="Voted for the server")
            rolesummary = f"{member.name}#{member.discriminator} has received the role {vdankster.mention} for 24 hours."  # this is over here so that if the role is added properly, it will be shown in the embed
        except discord.Forbidden:
            pass # If it can't add the role, it won't be in the summary of roles added
        cursor.execute("INSERT OR REPLACE INTO roleremove VALUES (?, ?, ?)", (userid, timetoremind, timetoremove,))
        self.votetracker.commit()
        milestones = cursor.execute("SELECT * FROM milestones").fetchall() # fetches milestones for adding the milestone roles
        if len(milestones) != 0: # there are settings for milestones
            for milestone in milestones:
                role = guild.get_role(milestone[1]) # gets the milestone role
                if (
                    role is not None # successfully got the role
                    and votecount >= milestone[0] # the user has gotten the required (or more than required) number of votes
                    and role not in member.roles # the user doesn't have the role yet
                ):
                    try:
                        await member.add_roles(role, reason = f"Milestone reached for user") # adds the role
                        rolesummary += f"\n**In addition, {member.name}#{member.discriminator} has gotten the role {role.mention} for voting {milestone[0]} times!**" # adds on to the summary of roles added
                    except discord.Forbidden:
                        pass
        embed = discord.Embed(title=f"Thank you for voting for __{guild.name}__ on Top.gg, {member.name}!",
                              description=f"You have voted {guild.name} for **{votecount}** time(s).\n[You can vote for Dank Vibes here!](https://top.gg/servers/595457764935991326/vote)",
                              # It will look like this: https://i.ibb.co/g4PvRsQ/Discord-ha-R7-Hsdzo-E.png
                              timestamp=datetime.datetime.utcnow(), color=0x57f0f0)
        embed.set_author(name=f"{member.name}#{member.discriminator} ({member.id})", icon_url=member.avatar_url)
        embed.set_footer(text=f"{guild.name} • {self.client.user.name}", icon_url=guild.icon_url) # dory allowed me to credit myself c:
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/830920902019514408.gif?v=1")
        embed.add_field(name="\u200b", value=rolesummary)
        try:
            await votingchannel.send(embed=embed)
        except discord.Forbidden:
            pass
        cursor.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        pass

    @commands.command(name="votereminder",
                    brief="Manage your vote reminder here! Use this command without arguments to see how to use it.",
                    description="Manage your vote reminder here! Use this command without arguments to see how to use it.", aliases = ["vrm"])
    async def votereminder(self, ctx, argument=None):
        """
        Manage your vote reminder here! Use this command without arguments to see how to use it.
        """
        cursor = self.votetracker.cursor()
        preferences = cursor.execute("SELECT rmtype FROM rmpreference WHERE member_id = ?", (ctx.author.id,)).fetchall()
        if len(preferences) == 0:  # if it's the first time for the user to invoke the command, it will create an entry automatically with the default setting "none".
            sql = 'INSERT into rmpreference(member_id, rmtype) VALUES(?, ?)'
            val = (ctx.author.id, 'none')
            cursor.execute(sql, val)
            self.votetracker.commit()
            preferences = cursor.execute("SELECT rmtype FROM rmpreference WHERE member_id = ?",
                                         (ctx.author.id,)).fetchall() # fetches the new settings after the user's entry containing the 'none' setting has been created
        currentpreference = preferences[0][0]
        if argument is None:
            embed = discord.Embed(title=f"Dank Vibes vote reminder",
                                  description=f"Every 12 hours after you vote, you can be reminded to [vote for Dank Vibes on top.gg](https://top.gg/servers/595457764935991326/vote).", timestamp=datetime.datetime.utcnow(), color=0x57f0f0)
            embed.add_field(name="Your current reminder setting",
                            value="DM" if currentpreference == "dm" else "Ping" if currentpreference == "ping" else "No reminder" if currentpreference == "none" else "Unknown; Please try to choose a reminder setting!", inline=False) #shows current reminder setting
            embed.add_field(name = "How to configure the reminder?", value=f"`votereminder dm` will make {self.client.user.name} DM you to vote again.\n`votereminder ping/mention` will make {self.client.user.name} ping you in <#754725833540894750> to vote again.\n`votereminder none` will turn off reminders.", inline=False) # description on this command
            embed.set_footer(text=f"{ctx.guild.name} • {self.client.user.name}")
            embed.set_thumbnail(url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)
        if len(preferences) == 0:  # if it's the first time for the user to invoke the command, it will create an entry automatically.
            sql = 'INSERT into rmpreference(member_id, rmtype) VALUES(?, ?)'
            val = (ctx.author.id, 'none')
            cursor.execute(sql, val)
            self.votetracker.commit()
        if argument.lower() in ["dm"]:
            cursor.execute('UPDATE rmpreference SET rmtype = ? WHERE member_id = ?',("dm", ctx.author.id))  # changes the settings to dm
            self.votetracker.commit()
            await ctx.send("Your reminder settings have been changed. You will **now be DMed** to vote for Dank Vibes.")
        elif argument.lower() in ["ping", "mention", "@"]:
            cursor.execute('UPDATE rmpreference SET rmtype = ? WHERE member_id = ?', ("ping", ctx.author.id))  # changes the settings to ping
            self.votetracker.commit()
            await ctx.send("Your reminder settings have been changed. You will **now be pinged** to vote for Dank Vibes.")
        elif argument.lower() in ["no", "null", "none"]:
            cursor.execute('UPDATE rmpreference SET rmtype = ? WHERE member_id = ?', ("none", ctx.author.id))  # changes the settings to mention
            self.votetracker.commit()
            await ctx.send("Your reminder settings have been changed. You will **not be reminded** to vote for Dank Vibes.")
        else:
            await ctx.send("You provided an invalid option. You can change your reminder to `ping`, `dm` or `none`. Use this command without any arguments to see how to use it.") # the argument provided wasn't dm, mention or none
        cursor.close()

    @commands.group(invoke_without_command=True, name="voteroles", brief = "Configure the milestones for the roles.", description = "Configure the milestones for the roles.")
    @commands.has_guild_permissions(administrator=True)
    async def voteroles(self, ctx):
        """
        Configure the milestones for the roles.
        """
        embed = discord.Embed(title=f"Dank Vibes Vote Roles configuration",
                              description=f"",
                              timestamp=datetime.datetime.utcnow(), color=0x57f0f0)
        embed.add_field(name="How to configure the vote roles?",
                        value=f"`voteroles list` shows all milestones for vote roles.\n`votereminder add [votecount] [role]` adds a milestone for vote roles.\n`votereminder remove [votecount]` will remove the milestone for vote count.") # description on this command
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_footer(text="Roles can be stated via a name, mention or ID.")
        await ctx.send(embed=embed)

    @voteroles.command(name="list", brief = "Lists milestones for vote roles.", description = "Lists milestones for vote roles.", aliases = ["show"])
    async def rolelist(self, ctx):
        """
        Lists milestones for vote roles.
        """
        cursor = self.votetracker.cursor()
        milestones = cursor.execute("SELECT * FROM milestones").fetchall() # gets the milestones
        if len(milestones) == 0:
            embed = discord.Embed(title = "Vote count milestones", description = "There are no milestones set for now. Use `voteroles add [votecount] [role]` to add one.", color=0x57f0f0) # there are no milestones set
            return await ctx.send(embed=embed)
        output = ''
        for row in milestones:
            if len(output) >= 3780: # the limit for the descripptino is 4096 characters, so just to play safe.
                embed = discord.Embed(title="Vote count milestones",
                                      description=output,
                                      color=0x57f0f0)
                await ctx.send(embed=embed) # I was kinda lazy to paginate this, and it's unlikely that they will ever pass the limit of characters anyways
            role = ctx.guild.get_role(row[1]) # gets the milestone role
            rolemention = role.mention if role is not None else "unknown-or-deleted-role" # if the role was deleted, it will show as that, otherwise it will be the role mention
            output += f"**{row[0]} votes: **{rolemention}\n" # adds the milestone vote count and role to the descriptionn
        embed = discord.Embed(title="Vote count milestones",
                              description=output,
                              color=0x57f0f0, timestamp=datetime.datetime.utcnow()) # final embed send after iterating throgh
        embed.set_footer(text="To edit the milestones, use the subcommands `add` and `remove`.")
        await ctx.send(embed=embed)
        cursor.close()

    @voteroles.command(name="add", brief="Add milestones for vote roles.",
                       description="Adds milestones for vote roles.", aliases=["create"])
    @commands.has_guild_permissions(administrator=True)
    async def roleadd(self, ctx, votecount = None, role:discord.Role = None):
        """
        Adds milestones for vote roles.
        """
        if votecount is None or role is None: # missing arguments
            return await ctx.send("The correct usage of this command is `voteroles add [votecount] [role]`.")
        try:
            votecount = int(votecount)
        except ValueError:
            return await ctx.send("`votecount` is not a valid number.")
        cursor = self.votetracker.cursor()
        milestones = cursor.execute("SELECT * FROM milestones where votecount = ?", (votecount,)).fetchall()
        if len(milestones) > 0: # oh this milestone exists already!
            await ctx.send(f"You have already set a milestone for **{votecount} votes**. To set a new role, remove this milestone and add it again.")
            cursor.close()
            return
        try:
            sql = 'INSERT into milestones(votecount, roleid) VALUES(?, ?)'  # creates a milestone rule, with votecount and the roleid
            val = (votecount, role.id)
            cursor.execute(sql, val)
            self.votetracker.commit()
        except Exception as e:
            return await ctx.send(e)
        cursor.close()
        await ctx.send(f"**Done**\n**{role.name}** will be added to a member when they have voted **{votecount} time(s)**.")

    @voteroles.command(name="remove", brief="Removes milestones for vote roles.",
                       description="Removess milestones for vote roles.", aliases=["delete"])
    @commands.has_guild_permissions(administrator=True)
    async def roleremove(self, ctx, votecount=None):
        """
        Removes milestones for vote roles
        """
        if votecount is None:
            return await ctx.send("The correct usage of this command is `voteroles remove [votecount]`.")
        try:
            votecount = int(votecount)
        except ValueError:
            return await ctx.send(f"`{votecount}` as the votecount is not a valid number.")
        cursor = self.votetracker.cursor()
        milestones = cursor.execute("SELECT * FROM milestones where votecount = ?", (votecount,)).fetchall()
        if len(milestones) == 0:
            return await ctx.send(
                f"You do not have a milestone set for {votecount} votes. Use `voteroles add [votecount] [role]` to add one.")
        try:
            cursor.execute("DELETE FROM milestones WHERE votecount = ?",(votecount,)) # Removes the milestone rule
            self.votetracker.commit()
        except Exception as e:
            return await ctx.send(e)
        cursor.close()
        await ctx.send(
            f"**Done**\nThe milestone for having voted **{votecount} time(s)** has been removed.")

    @commands.command(name="votecountreset",
                      brief="Reset the vote count database. **This action is irreversible.**",
                      description="Reset the vote count database. **This action is irreversible.**")
    @commands.has_guild_permissions(administrator=True)
    async def vcreset(self, ctx):
        cursor = self.votetracker.cursor()
        votecount = cursor.execute("SELECT * FROM votecount").fetchall()
        if len(votecount) == 0:  # if there's nothing to be deleted
            await ctx.send("There's nothing in the database to be removed.")
            cursor.close()
            return
        totalvote = sum(voter[1] for voter in votecount)
        embed = discord.Embed(title="Database pending removal", description = f"There are **{len(votecount)}** entries (or users) currently in the database, amounting to a total of {totalvote} votes. \n Are you sure you want to remove them? **This action is irreversible**! This will not remove users' vote reminder settings.\nStrictly send a `yes` or `no` in the next 20 seconds.", color=0x57f0f0, timestamp = datetime.datetime.utcnow()) # summary of what's going to be removed
        await ctx.send(embed=embed)
        try:
            yn = await self.client.wait_for("message",
                                            check=lambda m: m.channel == ctx.channel and m.author == ctx.author,
                                            timeout=20.0) # waits for confirmation to ensure that whoever uses this command indeed wants to reset the votecount
        except asyncio.TimeoutError:
            return await ctx.send("Aborting this operation.")
        if yn.content.lower() == "yes":
            cursor.execute("DELETE FROM votecount") # DELETES ALL ENTRIES FROM THE DATABASE
            self.votetracker.commit()
            cursor.close()
            await ctx.send(f"All vote counts have been reset, and all entries in the database has been deleted.")
        else:
            await ctx.send("Aborting this operation.")

    @commands.command(name="leaderboard", brief="Shows the leaderboard for the top 10 voters for Dank Vibes.", description = "Shows the leaderboard for the top 10 voters for Dank Vibes.", aliases = ["lb"])
    async def leaderboard(self, ctx):
        with ctx.typing():
            cursor = self.votetracker.cursor()
            votecount = cursor.execute("SELECT * FROM votecount ORDER BY count DESC LIMIT 10").fetchall() # gets top 10 voters
            leaderboard = []
            for voter in votecount:
                member = ctx.guild.get_member(voter[0])
                name = member.display_name.replace("[AFK]", "") if member is not None else voter[0] # shows user id if the user left the server
                name = (name[:12] + '...') if len(name) > 15 else name # shortens the nickname if it's too long
                leaderboard.append((name, voter[1])) #this is the final list of leaderboard people
            font_name = "assets/Gagalin.ttf"
            lbpositions = [(204, 240), (204, 390), (204, 550), (204, 710), (204, 870), (1150, 240), (1150, 390), (1150, 550), (1150, 710), (1150, 870)] # these are the positions for the nicknames in the leaderboard
            countpositions = [(780, 240), (780, 390), (780, 550), (780, 710), (780, 870), (1730, 240), (1730, 390), (1730, 550), (1730, 710), (1730, 870)] # these are the positions for the number of votes
            font = ImageFont.truetype(font_name, 60) # opens the font
            ima = Image.open("assets/lbbg.png") # opens leaderboard background
            ima = ima.convert("RGB") # Convert into RGB instead of RGBA so that it can be saved as a jpeg
            draw = ImageDraw.Draw(ima) # starts the drawing process
            for voter in leaderboard:
                draw.text(lbpositions[leaderboard.index(voter)], voter[0], font=font, align="middle left") # Adds a user's nickname
                draw.text(countpositions[leaderboard.index(voter)], str(voter[1]), font=font, align="right") # adds a user's vote count
            filename = f"temp/{random.randint(1, 9999999)}.jpg"
            ima.save(filename, optimize=True, quality=50) # saves the file under a temporary name
            file = discord.File(filename)
        try:
            await ctx.send("This is the vote leaderboard for **Dank Vibes**!" if len(leaderboard) != 0 else "This is the vote leaderboard for **Dank Vibes**!\nThere's no one in the leaderboard, perhaps you could be the first on the leaderboard by voting at https://top.gg/servers/595457764935991326/vote !", file=file)
        except discord.Forbidden:
            await ctx.send("I do not have permission to send the leaderboard here.")
        os.remove(filename) # deletes the temporary file
        cursor.close()
        return

    @commands.command(name="myvotes", brief="Shows the number of times you have voted for Dank Vibes.",
                      description="Shows the number of times you have voted for Dank Vibes.", aliases=["myv", "myvote", "votes"])
    async def myvotes(self, ctx, member = None): # member variable is not used actually
        timenow = round(time.time())
        if member is not None and "<@" in ctx.message.content: # you can delete this if you want, I just added it to tease them hehe
            await ctx.send("Nice try, but you can't view other users' votecount.")
        cursor = self.votetracker.cursor()
        votecount = cursor.execute("SELECT * FROM votecount where member_id = ? LIMIT 1", (ctx.author.id,)).fetchall()
        count = 0 if len(votecount) == 0 else votecount[0][1] # number of times user has voted
        result = cursor.execute("SELECT * FROM roleremove WHERE member_id = ? and rmtime > ? LIMIT 1", (ctx.author.id, timenow)).fetchall()
        if len(result) != 0 and result[0][1] != 9223372036854775807:
            desc = f"You can [vote for Dank Vibes](https://top.gg/servers/595457764935991326/vote) in another {humanize_timedelta(seconds=(result[0][1] - timenow))}." #if the user has voted recently
        else:
            desc = f"You can now [vote for Dank Vibes](https://top.gg/servers/595457764935991326/vote) again!" # self explanatory
        embed = discord.Embed(title=f"You have voted for Dank Vibes **__{count}__** times.",
                              description=desc, color=0x57f0f0, timestamp = datetime.datetime.utcnow())
        embed.set_author(name=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url)
        embed.add_field(name="Want to be reminded to vote for Dank Vibes?", value="Use `dv.votereminder dm/ping` to be reminded 12 hours after you vote for Dank Vibes.")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)
        cursor.close()

    @commands.guild_only()
    @commands.command(name="dailyleaderboard", brief = "Enables or disables sending the leaderboard daily.", description = "Enables or disables sending the leaderboard daily.", aliases = ["dailylb", "dlb", "leaderboardloop"])
    @commands.has_guild_permissions(administrator=True)
    async def dlb(self, ctx, option=None):
        """
        Enables or disables sending the leaderboard daily.
        """
        if option is None: # explanation of command
            embed = discord.Embed(title="Daily Leaderboard Loop", description = "Every 24 hours, I will send the leaderboard to the specified channel. It is enabled by default when the bot is started.", color=0x57f0f0, timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Usage", value="`dlb start/enable` starts.\n`dlb stop/disable` stops this feature.")
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            await ctx.send(embed=embed)
            return
        if option.lower() in ["start", "enable"]:
            try:
                self.leaderboardloop.start() # starts the task of sending leaderboard running
            except RuntimeError:
                await ctx.send("The daily leaderboard feature is already running!")
                return
            else:
                await ctx.send("Got it. I will start sending the leaderboard in the specified channel every 24 hours.")
                return
        elif option.lower() in ["stop", "disable"]:
            self.leaderboardloop.stop() # if the task is stopped already, no error will appear
            await ctx.send("I will no longer send the leaderboard every 24 hours.")
        else:
            await ctx.send("You did not provide a proper option. Use `dv.dlb` to see how to use this command.")