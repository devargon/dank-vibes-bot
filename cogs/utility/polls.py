import re
import discord
from utils import checks
from discord.ext import commands, tasks
import asyncio
from typing import Optional
from utils.format import generate_loadbar
import time

class PollButtons(discord.ui.View):
    def __init__(self, choices: list, client, identifier):
        self.choices = choices
        self.client = client
        self.response = None
        self.identifier = identifier

        super().__init__(timeout=None)

        async def manage_callback(button: discord.ui.Button, interaction: discord.Interaction):
            await interaction.response.send_message("<a:typing:839487089304141875> **Processing your vote...**", ephemeral=True)
            poll_data = await self.client.pool_pg.fetchrow("SELECT poll_name, poll_id, created FROM polls WHERE message_id = $1", interaction.message.id)
            if poll_data is None:
                return await interaction.edit_original_message(content="There is no poll associated with this message.")
            if poll_data.get('created') > round(time.time())+30*24*60*60:
                return await interaction.edit_original_message(content="This poll has been created more than 30 days ago and is no longer valid.")
            poll_id = poll_data.get('poll_id')
            option = button.label
            await self.client.pool_pg.execute("DELETE FROM pollvotes WHERE user_id = $1 AND poll_id = $2", interaction.user.id, poll_id)
            await self.client.pool_pg.execute("INSERT INTO pollvotes (poll_id, user_id, choice) VALUES ($1, $2, $3)", poll_id, interaction.user.id, option)
            await interaction.edit_original_message(content=f"For the poll **{poll_data.get('poll_name')}**, you voted: **{option}**\n\nYour vote has been recorded!")

        class pollbutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await manage_callback(self, interaction)


        for option in self.choices:
            self.add_item(pollbutton(label=option, style=discord.ButtonStyle.primary, custom_id=f"{self.identifier}_{option}"))







class polls(commands.Cog):
    def __init__(self, client):
        self.poll_views_added = False
        self.client = client

    def generate_embed(self, author: str, author_icon: Optional[str], poll_name: str, polldata: dict):
        embed = discord.Embed(title=poll_name, color=self.client.embed_color)
        embed.set_footer(text="The poll data updates every 15 seconds.")
        if author_icon is not None:
            embed.set_author(name=author, icon_url=author_icon)
        else:
            embed.set_author(name=author)
        total = sum([polldata[key] for key in polldata])
        for index, key in enumerate(polldata):
            if polldata[key] == 0:
                progress_bar = generate_loadbar(0, length=8)
                percent = 0
            else:
                progress_bar = generate_loadbar(polldata[key] / total, length=8)
                percent = round(polldata[key]/total*100, 1)
            embed.add_field(name=f"({index+1}) {key} ({polldata[key]} votes)", value=f"{progress_bar} {percent}%", inline=False)
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.poll_views_added:
            all_polls = await self.client.pool_pg.fetch("SELECT * FROM polls")
            for poll in all_polls:
                poll_m_id = poll.get('message_id')
                poll_choices = poll.get('choices').split('|')
                self.client.add_view(PollButtons(poll_choices, self.client, poll.get('invoked_message_id')), message_id=poll_m_id)


    @checks.perm_insensitive_roles()
    @commands.guild_only()
    @commands.command(name="poll", aliases=["quickpoll", "createpoll"])
    async def create_poll(self, ctx, *, question_and_choices = None):
        """
        Creates an interactive poll.
        The `question_and_choices` will be parsed to search for the question and the options.
        It should be in this format:
        `question | option 1 | option 2 (optional) | option 3 (optional) | option4 (optional) | option5 (optional)`
        There can only be a 'maximum of 5 options.
        The options can be separated by a pipe (`|`) or a comma (`,`).
        Example: If I wanted to ask if Almond was sussy or Minty was, I would use:
        > `dv.poll Who is sussy? | Almond | Minty`
        This will result in a poll with the question "Who is sussy?" and "Almond" and "Minty" as the options.
        A question can only have a maximum of 100 characters.
        An option can only have a maximum of 30 characters.
        """
        if question_and_choices is None:
            return await ctx.send("You need to provide a question and options. See `dv.help poll` for more information.")
        question_and_choices = question_and_choices.split("|")
        if len(question_and_choices) == 0:
            return await ctx.send("You need to provide a question and options. See `dv.help poll` for more information.")
        question_and_choices = [var.strip() for var in question_and_choices if var != ""]
        if len(question_and_choices) == 1:
            return await ctx.send(f"You only provided the question, `{question_and_choices[0]}`. You need to provide at least 2 options. See `dv.help poll` for more information.")
        if len(question_and_choices) < 3:
            return await ctx.send("You provided a question and less than 2 options. You need to provide at least 2 options. See `dv.help poll` for more information.")
        if len(question_and_choices) > 6:
            return await ctx.send("You provided a question and more than 5 options. You can only have a maximum of 5 options. See `dv.help poll` for more information.")
        question = question_and_choices[0]
        choices = question_and_choices[1:]
        choices_dict = {}
        for option in choices:
            choices_dict[option] = 0
        embed = self.generate_embed(f"{ctx.author}'s Poll", ctx.author.display_avatar.url, question, choices_dict)
        timeadded = round(time.time())
        poll_view = PollButtons(choices, self.client, ctx.message.id)
        msg = await ctx.send(embed=embed, view=poll_view)
        poll_view.response = msg
        await self.client.pool_pg.execute("INSERT INTO polls(guild_id, channel_id, invoked_message_id, message_id, creator_id, poll_name, choices, created) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)", ctx.guild.id, ctx.channel.id, ctx.message.id, poll_view.response.id, ctx.author.id, question, "|".join(choices), timeadded)
        await poll_view.wait()

