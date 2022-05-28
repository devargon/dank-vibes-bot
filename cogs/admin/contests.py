import os
import time
import contextlib
from collections import Counter
from typing import Union

import discord
from discord.ext import commands

from main import dvvt
from utils import checks
from utils.buttons import confirm
from utils.context import DVVTcontext
from utils.format import plural
from utils.specialobjects import Contest, ContestSubmission

media_events_id = 978493758427512853 if os.getenv('state') == '1' else 685237146415792128

approving_channel_id = 978563862896967681 if os.getenv('state') == '1' else 690455600068427836

class DenyWithReason(discord.ui.Modal):
    def __init__(self):
        self.reason = None
        self.interaction = None
        super().__init__(title="Notify user for Denied Submission")

        self.add_item(
            discord.ui.InputText(
                label="Reason for denying",
                required=False,
                style=discord.InputTextStyle.long,
                placeholder="i just hate it tbh"
            )
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.children[0].value
        if type(value) == str:
            self.reason = value.strip()
        else:
            self.reason = ""
        self.interaction = interaction
        self.stop()

class HowToSubmit2(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="I'm on Desktop", emoji="💻")
    async def desktop(self, button: discord.ui.Button, interaction: discord.Interaction):
        for b in self.children:
            if b == button:
                b.style = discord.ButtonStyle.green
            else:
                b.style = discord.ButtonStyle.grey
        await interaction.response.edit_message(content="Here's a video on how to submit your entry via Desktop: https://cdn.discordapp.com/attachments/871737314831908974/979760235415732304/Desktop_Final_V1.mp4", view=self)


    @discord.ui.button(label="I'm on Mobile", emoji="📱")
    async def mobile(self, button: discord.ui.Button, interaction: discord.Interaction):
        for b in self.children:
            if b == button:
                b.style = discord.ButtonStyle.green
            else:
                b.style = discord.ButtonStyle.grey
        await interaction.response.edit_message(content="Here's a video on how to submit your entry via Mobile: https://cdn.discordapp.com/attachments/871737314831908974/979760236019724348/Mobile_Final_V1.mp4", view=self)


class HowToSubmit1(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="How to submit?", style=discord.ButtonStyle.green, custom_id='howtosubmit')
    async def how_to_submit(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Select the device that you're currently on.", ephemeral=True, view=HowToSubmit2())


class interactionconfirm(discord.ui.View):
    def __init__(self, author: Union[discord.User, discord.Member], client, timeout):
        self.timeout = timeout
        self.author = author
        self.response = None
        self.client = client
        self.returning_value = None
        super().__init__(timeout=30.0)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.returning_value = True
        for b in self.children:
            if b != button:
                b.style = discord.ButtonStyle.grey
            b.disabled = True
        if isinstance(self.response, discord.Message) or isinstance(self.response, discord.WebhookMessage):
            await self.response.edit(view=self)
        elif isinstance(self.response, discord.Interaction):
            await self.response.edit_original_message(view=self)
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.returning_value = False
        for b in self.children:
            if b != button:
                b.style = discord.ButtonStyle.grey
            b.disabled = True
        if isinstance(self.response, discord.Message) or isinstance(self.response, discord.WebhookMessage):
            await self.response.edit(view=self)
        elif isinstance(self.response, discord.Interaction):
            await self.response.edit_original_message(view=self)
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        author = self.author
        if interaction.user != author:
            await interaction.response.send_message("These buttons aren't for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        self.returning_value = None
        for b in self.children:
            b.disabled = True
        if isinstance(self.response, discord.Message) or isinstance(self.response, discord.WebhookMessage):
            await self.response.edit(view=self)
        elif isinstance(self.response, discord.Interaction):
            await self.response.edit_original_message(view=self)

class VoteView(discord.ui.View):
    def __init__(self, client, disabled):
        self.client: dvvt = client
        self.disabled: bool = disabled
        super().__init__(timeout=None)

        class Vote(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                submission = await self.view.client.db.fetchrow("SELECT * FROM contest_submissions WHERE msg_id = $1", interaction.message.id)
                if submission is None:
                    return await interaction.followup.send("There doesn't seem to be a valid submission associated with this post.", ephemeral=True)
                submission = ContestSubmission(submission)
                contest = await self.view.client.db.fetchrow("SELECT * FROM contests WHERE contest_id = $1", submission.contest_id)
                if contest is None:
                    return await interaction.followup.send("There doesn't seem to be a valid contest associated with this post.", ephemeral=True)
                contest = Contest(contest)
                print(contest)
                if contest.voting is not True:
                    if contest.active is not True:
                        return await interaction.followup.send("This contest is over. Thank you for voting for your favorite entries!", ephemeral=True)
                    else:
                        return await interaction.followup.send(f"This contest is still in the **submission stage**. Voting will start after Submission of entries are over.", ephemeral=True)
                successembed = discord.Embed(
                    title=f"<:DVB_True:887589686808309791> You have voted for Submission #{submission.entry_id}!",
                    description="The results of voting will be out when the contest is over.",
                    color=self.view.client.embed_color)
                if (vote := await self.view.client.db.fetchrow("SELECT * FROM contest_votes WHERE contest_id = $1 AND user_id = $2", submission.contest_id, interaction.user.id)) is not None:
                    if vote.get('entry_id') == submission.entry_id:
                        successembed.title = f"<:DVB_True:887589686808309791> You already voted for Submission #{submission.entry_id}."
                        return await interaction.followup.send(embed=successembed, ephemeral=True)
                    confirmview = interactionconfirm(interaction.user, self.view.client, 30.0)
                    confirmview.response = await interaction.followup.send(f"You have previously voted for [this entry](https://discord.com/channels/{interaction.guild.id}/{contest.contest_channel_id}/{submission.msg_id}).\nAre you sure you want to change your vote?", view=confirmview, wait=True)
                    await confirmview.wait()
                    if confirmview.returning_value is not True:
                        return
                    await self.view.client.db.execute("DELETE FROM contest_votes WHERE contest_id = $1 AND user_id = $2", submission.contest_id, interaction.user.id)
                await self.view.client.db.execute("INSERT INTO contest_votes(contest_id, entry_id, user_id) VALUES($1, $2, $3)", contest.contest_id, submission.entry_id, interaction.user.id)
                successembed = discord.Embed(title=f"<:DVB_True:887589686808309791> You have voted for Submission #{submission.entry_id}!", description="The results of voting will be out when the contest is over.", color=self.view.client.embed_color)
                await interaction.followup.send(embed=successembed, ephemeral=True)

        self.add_item(Vote(style=discord.ButtonStyle.green, emoji=discord.PartialEmoji.from_str("<:DVB_Upvote:977772469945499709>"), custom_id='contestvote', disabled=self.disabled))



class SubmissionApproval(discord.ui.View):
    def __init__(self, client, contest_id: int, entry_id: int, submitter_id: int):
        self.client = client
        self.submission_handled = False
        super().__init__(timeout=None)



        class Approve(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                if self.view.submission_handled is True:
                    return await interaction.response.send_message("This submission has been handled by another user.", ephemeral=True)
                derived_contest_id, derived_entry_id, derived_submitter_id, buttoncommand = self.custom_id.split(':')
                derived_contest_id, derived_entry_id, derived_submitter_id = int(derived_contest_id), int(derived_entry_id), int(derived_submitter_id)
                contest_channel_id = await self.view.client.db.fetchval("SELECT contest_channel_id FROM contests WHERE contest_id = $1", contest_id)
                if contest_channel_id is None:
                    return await interaction.response.send_message(f"I could not find a channel ID for this contest.", ephemeral=True)
                contest_channel = interaction.guild.get_channel(contest_channel_id)
                if contest_channel is None:
                    return await interaction.response.send_message(f"I could not find a channel with ID {contest_channel_id}for this contest.", ephemeral=True)
                contest_submission = await self.view.client.db.fetchrow("SELECT * FROM contest_submissions WHERE entry_id = $1", derived_entry_id)
                submission = ContestSubmission(contest_submission)
                entry_embed = discord.Embed(title=f"Submission #{derived_entry_id}", color=self.view.client.embed_color, timestamp=discord.utils.utcnow())
                entry_embed.set_footer(text="Submitted at")
                entry_embed.set_image(url=submission.second_media_link or submission.media_link)
                if submission.msg_id is not None:
                    try:
                        submission_msg = await contest_channel.fetch_message(submission.msg_id)
                    except Exception as e:
                        result_message = await contest_channel.send(embed=entry_embed, view=VoteView(self.view.client, True))
                    else:
                        await submission_msg.edit(embed=entry_embed, view=VoteView(self.view.client, True))
                        result_message = submission_msg
                else:
                    result_message = await contest_channel.send(embed=entry_embed, view=VoteView(self.view.client, True))
                if submission.second_media_link is not None:
                    await self.view.client.db.execute("UPDATE contest_submissions SET msg_id = $1, media_link = second_media_link, approve_id = NULL, approved = TRUE WHERE entry_id = $2 AND contest_id = $3", result_message.id, derived_entry_id, derived_contest_id)
                    await self.view.client.db.execute("UPDATE contest_submissions SET second_media_link = NULL WHERE entry_id = $1 AND contest_id = $2", derived_entry_id, derived_contest_id)
                else:
                    await self.view.client.db.execute("UPDATE contest_submissions SET msg_id = $1, approve_id = NULL, approved = TRUE WHERE entry_id = $2 AND contest_id = $3", result_message.id, derived_entry_id, derived_contest_id)
                embed = interaction.message.embeds[0]
                embed.color = discord.Color.green()
                embed.set_footer(text="Approved")
                for b in self.view.children:
                    b.disabled = True
                self.view.submission_handled = True
                await interaction.message.edit(embed=embed, view=self.view, delete_after=10.0)

                interaction.guild.get_member(derived_submitter_id)
                with contextlib.suppress(discord.Forbidden):
                    if (user := self.view.client.get_user(derived_submitter_id)) is not None:
                        approve_embed = discord.Embed(title="Submission Approved", description=f"Your submission for contest #{derived_contest_id} has been approved. Check it out [here]({result_message.jump_url})!", color=discord.Color.green()).set_image(url=submission.second_media_link or submission.media_link)
                        await user.send(embed=approve_embed)

        class Deny(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                if self.view.submission_handled is True:
                    return await interaction.response.send_message("This submission has been handled by another user.", ephemeral=True)
                derived_contest_id, derived_entry_id, derived_submitter_id, buttoncommand = self.custom_id.split(':')
                derived_contest_id, derived_entry_id, derived_submitter_id = int(derived_contest_id), int(derived_entry_id), int(derived_submitter_id)
                submission = await self.view.client.db.fetchrow("SELECT * FROM contest_submissions WHERE contest_id = $1 AND submitter_id = $2 AND entry_id = $3", derived_contest_id, derived_submitter_id, derived_entry_id)
                submission = ContestSubmission(submission)
                get_reason_modal = DenyWithReason()
                print('sending_modal')
                await interaction.response.send_modal(get_reason_modal)
                print('sussi')
                await get_reason_modal.wait()
                print('test')
                if self.view.submission_handled is True:
                    return await interaction.response.send_message("This submission has been handled by another user.", ephemeral=True)
                if get_reason_modal.reason is not None:
                    reason = get_reason_modal.reason
                    self.view.submission_handled = True
                    embed_to_dm = discord.Embed(title="Submission denied", color=discord.Color.red()).set_image(url=submission.second_media_link or submission.media_link)
                    if len(reason) == 0:
                        embed_to_dm.description = "Your submission was denied for the following reason:\n\n> No reason provided\n\nYou can try again and resubmit using the slash command `/submit <attachment>`."
                    else:
                        embed_to_dm.description = f"Your submission was denied for the following reason:\n\n> {reason}\n\nYou can try again and resubmit using the slash command `/submit <attachment>`."
                    if (submitter := self.view.client.get_user(derived_submitter_id)) is not None:
                        try:
                            await submitter.send(embed=embed_to_dm)
                            dm_successful = True
                        except discord.Forbidden:
                            dm_successful = False
                    else:
                        dm_successful = False
                    if submission.msg_id is not None:
                        await self.view.client.db.execute("UPDATE contest_submissions SET second_media_link = NULL, approve_id = NULL, approved = TRUE WHERE entry_id = $1 AND contest_id = $2", derived_entry_id, derived_contest_id)
                    else:
                        await self.view.client.db.execute("DELETE FROM contest_submissions WHERE entry_id = $1 AND contest_id = $2", derived_entry_id, derived_contest_id)
                    embed = interaction.message.embeds[0]
                    embed.color = discord.Color.red()
                    embed.set_footer(text="Denied")
                    for b in self.view.children:
                        b.disabled = True
                    self.view.submission_handled = True
                    await interaction.edit_original_message(embed=embed, view=self.view, delete_after=10.0)
                    await get_reason_modal.interaction.response.send_message(f"You have disqualified the entry for {submission.second_media_link or submission.media_link}. {'The submitter has been notified.' if dm_successful else 'I was unable to DM the submitter.'}", ephemeral=True)
                else:
                    return await interaction.response.send_message('umm', ephemeral=True)

        self.add_item(item=Approve(custom_id=f"{contest_id}:{entry_id}:{submitter_id}:approve", emoji=discord.PartialEmoji.from_str("<:DVB_checkmark:955345523139805214>"), style=discord.ButtonStyle.green))
        self.add_item(item=Deny(custom_id=f"{contest_id}:{entry_id}:{submitter_id}:deny", emoji=discord.PartialEmoji.from_str("<:DVB_crossmark:955345521151737896>"), style=discord.ButtonStyle.red))


class GetMediaEventsPing(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Get Media Events Ping!", style=discord.ButtonStyle.green)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not discord.utils.get(interaction.user.roles, name="Heist Ping"):
            await interaction.user.add_roles(interaction.guild.get_role(media_events_id))
            await interaction.response.send_message(f"<:DVB_True:887589686808309791> The <@&{media_events_id}> role has been added to you!", ephemeral=True)
        else:
            await interaction.response.send_message(f"<:DVB_True:887589686808309791> You already have the <@&{media_events_id}> role.", ephemeral=True)

class Contests(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name='contest', aliases=['contests'], invoke_without_command=True)
    async def contest(self, ctx: DVVTcontext):
        """
        Contest Management
        """
        return await ctx.help()

    @contest.command(name='list')
    async def contest_list(self, ctx: DVVTcontext):
        """
        Lists the active contest, and the last 5 contests.
        """
        active_contest = await self.client.db.fetchrow("SELECT * FROM contests WHERE guild_id = $1 AND (active = TRUE OR voting = TRUE) LIMIT 1", ctx.guild.id)
        past_contests = await self.client.db.fetch("SELECT * FROM contests WHERE guild_id = $1 AND active = FALSE AND voting = FALSE ORDER BY contest_id DESC LIMIT 5", ctx.guild.id)
        embed_contest_list = discord.Embed(title=f"{ctx.guild.name} Contests", color=self.client.embed_color)
        if active_contest is None:
            active_contest = "No ongoing contests."
        else:
            submissions = await self.client.db.fetch("SELECT * FROM contest_submissions WHERE contest_id = $1", active_contest.get('contest_id'))
            submissions_sorted = Counter([submission.get('approved') for submission in submissions])
            if ctx.author.guild_permissions.manage_roles is True:
                submission_str = f"{sum(submissions_sorted.values())} Submissions ({submissions_sorted[True]} Approved, {submissions_sorted[False]} Pending Approval)"
            else:
                submission_str = f"{submissions_sorted[True]} Approved Submissions"
            channel_str = f"Channel: <#{active_contest.get('contest_channel_id')}>"
            active_contest = f"**Contest #{active_contest.get('contest_id')}: {active_contest.get('name')}**\n{channel_str}\n{submission_str}"

        embed_contest_list.add_field(name="Active Contest", value=active_contest, inline=False)
        if len(past_contests) > 0:
            past_contests_lst = []
            for contest in past_contests:
                submissions = await self.client.db.fetchval("SELECT COUNT(*) FROM contest_submissions WHERE contest_id = $1", contest.get('contest_id'))
                details = f"<#{contest.get('channel_id')}>, {plural(submissions):submission}"
                past_contests_lst.append(f"**Contest #{contest.get('contest_id')}: {contest.get('name')}**\n{details}\n")
            past_contests = "\n".join(past_contests_lst)

        else:
            past_contests = "No past contests."
        embed_contest_list.add_field(name="Past Contests", value=past_contests, inline=False)
        await ctx.send(embed=embed_contest_list)





    @checks.has_permissions_or_role(manage_roles=True)
    @contest.command(name='start')
    async def contest_start(self, ctx: DVVTcontext, channel: discord.TextChannel, *, name: str):
        """
        Start a contest in a specified channel.
        """
        if (contest_obj := await self.client.db.fetchrow("SELECT * FROM contests WHERE guild_id = $1 AND active = TRUE or voting = TRUE", ctx.guild.id)) is not None:
            return await ctx.send(f"There is an active contest running already (Contest {contest_obj.get('contest_id')}). \nEnd the submission and voting process before starting a new contest.")
        contest_id = await self.client.db.fetchval("INSERT INTO contests(guild_id, contest_starter_id, contest_channel_id, created, name) VALUES($1, $2, $3, $4, $5) RETURNING contest_id", ctx.guild.id, ctx.author.id, channel.id, round(time.time()), name, column='contest_id')
        embed_success = discord.Embed(title="Contest Started", description=f"This contest's ID is `{contest_id}`.\n\nThe contest is now in the **SUBMISSION** stage.\nUsers can submit entries using `/submit <attachment>`.\n\n`dv.contest vote {contest_id}` will change the contest to **VOTING** stage.\n`dv.contest end {contest_id}` will end the contest and let the leaderboard be public.", color=self.client.embed_color)
        embed = discord.Embed(title="A contest has just started.", description="Use `/submit <attachment>` to submit your entry!", color=self.client.embed_color).set_author(name=f"Contest #{contest_id}: {name}")
        await channel.send(embed=embed)
        with contextlib.suppress(discord.Forbidden):
            await ctx.author.send(embed=embed_success)
        await ctx.send(embed=embed_success.set_footer(text="A copy of this has been sent to your DMs."))

    @checks.has_permissions_or_role(manage_roles=True)
    @contest.command(name='vote')
    async def contest_vote(self, ctx: DVVTcontext, contest_id: int):
        """
        Changes a contest to the **Voting** stage. No new submissions can be entered, but voting will commence.
        Requires all pending entries to be approved/denied.
        """
        if (contest := await self.client.db.fetchrow("SELECT * FROM contests WHERE contest_id = $1 AND guild_id = $2", contest_id, ctx.guild.id)) is None:
            return await ctx.send(f"A contest with the ID `{contest_id}` doesn't exist in your server.")
        contest = Contest(contest)
        if contest.active is not True:
            if contest.voting is not True:
                return await ctx.send(f"Looks like Contest `{contest_id}` is already over.")
            else:
                return await ctx.send(f"Contest `{contest_id}` is already in the voting stage.")
        contest_submissions = await self.client.db.fetch("SELECT * FROM contest_submissions WHERE contest_id = $1", contest_id)
        if len(contest_submissions) > 0:
            warnings = []
            for sub in contest_submissions:
                sub = ContestSubmission(sub)
                if sub.approve_id is None and sub.approved is not True:
                    warnings.append(f"You need to approve/deny [Submission #{sub.entry_id}](https://discord.com/channels/{ctx.guild.id}/{approving_channel_id}/{sub.approve_id}) before proceeding.")
            if len(warnings) > 0:
                return await ctx.send(embed=discord.Embed(title="Unable to proceed", description="\n".join(warnings), color=discord.Color.red()))
        confirmview = confirm(ctx, self.client, 30.0)
        confirmembed = discord.Embed(title=f"Are you sure you want to stop submissions?", description="This will make this contest move on to the VOTING stage.", color=discord.Color.yellow())
        confirmview.response = await ctx.send(embed=confirmembed, view=confirmview)
        await confirmview.wait()
        if confirmview.returning_value is not True:
            confirmembed.color = discord.Color.red()
            return await confirmview.response.edit(embed=confirmembed)
        else:
            confirmembed.color = discord.Color.green()
            await confirmview.response.edit(embed=confirmembed)

        await self.client.db.execute("UPDATE contests SET active = FALSE, voting = TRUE WHERE contest_id = $1", contest_id)
        async with ctx.typing():
            for sub in contest_submissions:
                sub = ContestSubmission(sub)
                try:
                    await ctx.guild.get_channel(contest.contest_channel_id).get_partial_message(sub.msg_id).edit(view=VoteView(self.client, False))
                except Exception as e:
                    await ctx.send(f"Could not add a Vote button for entry {sub.entry_id}: {str(e)}")
        return await ctx.send(embed=discord.Embed(title=f"Contest #{contest_id} is now in the VOTING stage.", description=f"Users can now vote for their favorite entries in <#{contest.contest_channel_id}>", color=discord.Color.green()))



    @commands.slash_command(name="submit")
    async def contest_submit(self, ctx: discord.ApplicationContext, *, submission: discord.Option(discord.Attachment, description="Your submission for the contest.")):
        """
        Submit your entry for a contest!
        """
        user_has_submitted_before = False
        if (contest_obj := await self.client.db.fetchrow("SELECT * FROM contests WHERE guild_id = $1 AND (active = TRUE or voting = TRUE)", ctx.guild.id)) is None:
            return await ctx.respond("There are no contests taking place now.\n\nGet **Media Events Ping** to be notified when a contest starts!", view=GetMediaEventsPing(), ephemeral=True)
        else:
            await ctx.defer(ephemeral=True)
            contest_id = contest_obj.get('contest_id')
            if contest_obj.get('active') is True:
                if submission.content_type not in ['image/jpeg', 'image/png']:
                    filename = submission.filename.split('.')
                    if len(filename) > 1:
                        extension = filename[-1]
                        return await ctx.respond(f"You can only submit JPEG or PNG images for the contest.\n\nConvert your submission to a JPEG or PNG image and try to submit again.\nhttps://www.google.com/search?q={extension}+to+jpeg+png+converter", view=GetMediaEventsPing(), ephemeral=True)
                    else:
                        return await ctx.respond("You can only submit JPEG or PNG images for the contest.\n\nConvert your submission to a JPEG or PNG image and try to submit again.", view=GetMediaEventsPing(), ephemeral=True)
                if (existing_submission := await self.client.db.fetchrow("SELECT * FROM contest_submissions WHERE contest_id = $1 AND submitter_id = $2", contest_id, ctx.author.id)) is not None:
                    user_has_submitted_before = True
                    existing_submission = ContestSubmission(existing_submission)
                    print(existing_submission)
                    confirmview = confirm(ctx, self.client, 30.0)
                    existing = False
                    if existing_submission.approved is True:
                        existing = True
                        confirmview.response = await ctx.respond("You already have a submission that's approved. Are you sure you want to resubmit again?", view=confirmview)
                    elif existing_submission.approve_id is not None:
                        existing = True
                        confirmview.response = await ctx.respond("You already have a submission that's waiting to be approved. Are you sure you want to resubmit again?", view=confirmview)
                    else:
                        pass
                    if existing is True:
                        await confirmview.wait()
                        if confirmview.returning_value is not True:
                            return

                last_entry_no = await self.client.db.fetchval("SELECT entry_id FROM contest_submissions WHERE contest_id = $1 ORDER BY entry_id DESC limit 1", contest_id) or 0
                next_entry_no = last_entry_no + 1
                if (approve_channel := ctx.guild.get_channel(approving_channel_id)) is not None:

                    if user_has_submitted_before is True:
                        await_approval_embed = discord.Embed(title=f"Submission #{existing_submission.entry_id}", color=discord.Color.yellow()).set_image(url=submission.url)
                    else:
                        await_approval_embed = discord.Embed(title=f"Submission #{next_entry_no}", color=discord.Color.yellow()).set_image(url=submission.url)
                    if user_has_submitted_before is True:
                        next_entry_no = existing_submission.entry_id
                        if existing_submission.approve_id is not None:
                            p_message = approve_channel.get_partial_message(existing_submission.approve_id)
                            try:
                                await p_message.edit(embed=await_approval_embed, view=SubmissionApproval(self.client, contest_id, next_entry_no, ctx.author.id))
                            except discord.NotFound:
                                approve_message = await approve_channel.send(embed=await_approval_embed, view=SubmissionApproval(self.client, contest_id, next_entry_no, ctx.author.id))
                                await self.client.db.execute("UPDATE contest_submissions SET second_media_link = $1, approve_id = $2 WHERE contest_id = $3 AND entry_id = $4 AND submitter_id = $5", submission.url, approve_message.id, contest_id, existing_submission.entry_id, ctx.author.id)
                                await ctx.respond(f"<:DVB_True:887589686808309791> **Your submission has been sent to the admins for approval!**\nYou will be DMed about whether your submission is approved or not. Please keep your DMs with {self.client.user.name} open.", ephemeral=True)
                                with contextlib.suppress(discord.Forbidden):
                                    dm_embed = discord.Embed(title="Submission Awaiting Approval", description="Your submission has been sent to the admins for approval. You will be DMed regarding the status of your submsission.", color=self.client.embed_color).set_image(url=submission.url)
                                    await ctx.author.send(embed=dm_embed)
                                    return
                            else:
                                await self.client.db.execute("UPDATE contest_submissions SET approve_id = $1, approved = FALSE, second_media_link = $2 WHERE contest_id = $3 AND entry_id = $4 AND submitter_id = $5", p_message.id, submission.url, contest_id, existing_submission.entry_id, ctx.author.id)
                                await ctx.respond(f"<:DVB_True:887589686808309791> **Your submission has been sent to the admins for approval!**\nYou will be DMed about whether your submission is approved or not. Please keep your DMs with {self.client.user.name} open.", ephemeral=True)
                                with contextlib.suppress(discord.Forbidden):
                                    dm_embed = discord.Embed(title="Submission Awaiting Approval", description="Your submission has been sent to the admins for approval. You will be DMed regarding the status of your submsission.", color=self.client.embed_color).set_image(url=submission.url)
                                    await ctx.author.send(embed=dm_embed)
                                    return
                        else:
                            approve_message = await approve_channel.send(embed=await_approval_embed, view=SubmissionApproval(self.client, contest_id, next_entry_no, ctx.author.id))
                            await self.client.db.execute("UPDATE contest_submissions SET second_media_link = $1, approve_id = $2, approved = FALSE WHERE contest_id = $3 AND entry_id = $4 AND submitter_id = $5", submission.url, approve_message.id, contest_id, existing_submission.entry_id, ctx.author.id)
                            await ctx.respond(f"<:DVB_True:887589686808309791> **Your submission has been sent to the admins for approval!**\nYou will be DMed about whether your submission is approved or not. Please keep your DMs with {self.client.user.name} open.", ephemeral=True)
                            with contextlib.suppress(discord.Forbidden):
                                dm_embed = discord.Embed(title="Submission Awaiting Approval", description="Your submission has been sent to the admins for approval. You will be DMed regarding the status of your submsission.", color=self.client.embed_color).set_image(url=submission.url)
                                await ctx.author.send(embed=dm_embed)
                                return

                    approve_message = await approve_channel.send(embed=await_approval_embed, view=SubmissionApproval(self.client, contest_id, next_entry_no, ctx.author.id))
                    await self.client.db.execute("INSERT INTO contest_submissions(contest_id, entry_id, submitter_id, media_link, approve_id) VALUES($1, $2, $3, $4, $5)", contest_id, next_entry_no, ctx.author.id, submission.url, approve_message.id)
                    await ctx.respond(f"<:DVB_True:887589686808309791> **Your submission has been sent to the admins for approval!**\nYou will be DMed about whether your submission is approved or not. Please keep your DMs with {self.client.user.name} open.", ephemeral=True)
                    with contextlib.suppress(discord.Forbidden):
                        dm_embed = discord.Embed(title="Submission Awaiting Approval", description="Your submission has been sent to the admins for approval. You will be DMed regarding the status of your submsission.", color=self.client.embed_color).set_image(url=submission.url)
                        await ctx.author.send(embed=dm_embed)
                else:
                    await ctx.respond("I could not find a channel to send your entry to await approval.", ephemeral=True)
            elif contest_obj.get('voting') is True:
                await ctx.respond("The time to submit your entry is over. Sorry if you missed it!\n\nGet **Media Events Ping** to be notified when a contest starts!", view=GetMediaEventsPing(), ephemeral=True)

    @checks.has_permissions_or_role(manage_roles=True)
    @contest.command(name="end")
    async def contest_end(self, ctx: DVVTcontext, contest_id: int):
        """
        End a contest. This will:
        1) Send a custom leaderboard in the specified contest channel.
        2) Remove all upvote buttons and add the names and number of votes to each contest entry.
        """
        return await ctx.send("This command is still in development :(")

    @checks.has_permissions_or_role(manage_roles=True)
    @contest.command(name="leaderboard")
    async def contest_leaderboard(self, ctx: DVVTcontext, contest_id: int):
        """
        See all the leaderboard and check out all the entries of a previous contest.
        Cannot be used for ongoing contests.
        """
        return await ctx.send("This command is still in development :(")


    @checks.dev()
    @contest.command(name='forceend')
    async def contest_forceend(self, ctx: DVVTcontext, contest_id: int):
        """
        Force ends a contest, regardless of its state.
        """
        await self.client.db.execute("UPDATE contests SET active = FALSE, voting = FALSE WHERE contest_id = $1", contest_id)
        await ctx.send("Contest ended.")

