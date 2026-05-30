from itertools import batched
from textwrap import dedent

import discord
from discord import Interaction
from discord.ext import commands
from typing import Union

from custom_emojis import DVB_TRUE, DVB_STATUS_YELLOW, DVB_STATUS_GREY, DVB_STATUS_GREEN, DVB_STATUS_RED
from utils.paginator import SingleMenuPaginator
from main import dvvt
from utils import checks
from utils.context import DVVTcontext

class CancelViewButton(discord.ui.Button):
    def __init__(self, label="Cancel", style=discord.ButtonStyle.red):
        super().__init__(style=style, label=label)

    async def callback(self, interaction: Interaction):
        await interaction.delete_original_response()
        self.view.stop()

class SuggestDumbfightModal(discord.ui.DesignerModal):
    def __init__(self, client: dvvt, dumbfight_type, existing_input: Union[str, None] = None):
        title="Suggest Dumbfight Message"

        if dumbfight_type == "other":
            placeholder = "{winner} punched {loser} and he fell."
            label="What happens in a DUMBFIGHT"
            description="Include {winner} and/or {loser} where their names should appear."
        else:
            placeholder = "{loser} slipped on a banana peel and fell."
            label="What happens when you FIGHT YOURSELF"
            description="Include {loser} where the loser should appear."
        input2 = discord.ui.Label(label, discord.ui.InputText(placeholder=placeholder, style=discord.InputTextStyle.long, value=existing_input, min_length=1,max_length=150),description=description)
        super().__init__(
            input2,
            title=title
        )
        self.client = client
        self.fight_type = dumbfight_type

    async def callback(self, interaction: discord.Interaction):
        fight_message = self.children[0].item.value
        # Validation
        validation_passed = True
        embed = False
        if self.fight_type == "other" and ("{loser}" not in fight_message and "{winner}" not in fight_message):
            embed = discord.Embed(
                title="Your submission does not fulfil the following requirements:",
                description="The dumbfight message **MUST** include either `{winner}` or `{loser}` so the winner or loser can be shown." + f"\n```\n{fight_message}\n```",
                color=discord.Color.red()
            )
            validation_passed = False
        elif self.fight_type == "self" and "{loser}" not in fight_message:
            embed = discord.Embed(
                title="Your submission does not fulfil the following requirements:",
                description="The dumbfight message **MUST** include either `{winner}` or `{loser}` so the winner or loser can be shown." + f"\n```\n{fight_message}\n```",
                color=discord.Color.red()
            )
            validation_passed = False
        if not validation_passed:
            return await interaction.response.send_message(
                embed=embed,
                view=discord.ui.View(TriggerDumbfightSuggestionModalButton(self.client, self.fight_type, fight_message, style=discord.ButtonStyle.red, label="Try again"),
                                     timeout=30, disable_on_timeout=True), ephemeral=True
            )

        if self.fight_type == "self":
            target_and_winner = "**@Frenzy**"
        elif interaction.user.id != 560251854399733760:
            target_and_winner = interaction.user.mention
        else:
            member = await interaction.guild.get_or_fetch(discord.Member, 312876934755385344)
            target_and_winner = member.mention if member else "<@312876934755385344>"
        fight_message_example = fight_message.replace("{winner}", target_and_winner).replace("{loser}", "**@Frenzy**")
        view = discord.ui.DesignerView(
            discord.ui.TextDisplay(content=f"**Please check below to make sure the dumbfight message looks right.**"),
            discord.ui.Separator(divider=True, spacing=discord.SeparatorSpacingSize.small),
            discord.ui.TextDisplay(content=f"## <:DVB_DF_FRENZY:1508080750195376169> Frenzy\ndv.df {target_and_winner}"),
            discord.ui.Separator(divider=False, spacing=discord.SeparatorSpacingSize.large),
            discord.ui.TextDisplay(content=f"## <:DVB_DF_DVB:1508080709762289725> {self.client.user.name}"),
            discord.ui.Container(discord.ui.TextDisplay(content=f"{fight_message_example}\n**@Frenzy** lost and is now muted for 120 seconds."),color=0xff0000),
            discord.ui.ActionRow(SubmitDumbfightSuggestionButton(self.client, self.fight_type, fight_message), TriggerDumbfightSuggestionModalButton(self.client, fight_type=self.fight_type, existing_input=fight_message, style=discord.ButtonStyle.red, label="Edit"), CancelViewButton("Cancel", discord.ButtonStyle.grey)),
            timeout=30, disable_on_timeout=True)
        return await interaction.response.send_message(view=view, ephemeral=True)

class SubmitDumbfightSuggestionButton(discord.ui.Button):
    def __init__(self, client: dvvt, fight_type: str, dumbfight_message: str):
        super().__init__(
            style=discord.ButtonStyle.green, label="Looks good - Submit"
        )
        self.client = client
        self.fight_type = fight_type
        self.dumbfight_message = dumbfight_message
    async def callback(self, interaction: discord.Interaction):
        if self.fight_type not in ['other', 'self']:
            print(self.fight_type, type(self.fight_type))
            cont = discord.ui.Container(discord.ui.TextDisplay(content=f"### Dumbfight suggestion Not Submitted\nDumbfight suggestion type was not 'other' or 'self'. Please try again later."), color=discord.Color.red())
        else:
            await self.client.db.execute("INSERT INTO dumbfight_suggestions(user_id, fight_type, message) VALUES($1, $2, $3)", interaction.user.id, self.fight_type, self.dumbfight_message)
            cont = discord.ui.Container(discord.ui.TextDisplay(content=f"### Dumbfight suggestion Submitted! {DVB_TRUE}\n-# You may submit another one below if you wish to.\nFight type: `{self.fight_type}`\n```\n{self.dumbfight_message}\n```"), color=discord.Color.green())
        view = discord.ui.DesignerView(cont, discord.ui.ActionRow(InitiateDumbfightSuggestionButton(self.client)), timeout=1, disable_on_timeout=True)
        await interaction.response.edit_message(view=view)





class InitiateDumbfightSuggestionButton(discord.ui.Button):
    def __init__(self, client: dvvt):
        super().__init__(
            style=discord.ButtonStyle.green,  # Discord style 1
            label="Suggest",
            custom_id="initiate_dumbfight_suggestion",
            emoji="✍️",
            row=0
        )
        self.client = client

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            view=DumbfightDesignerView(self.client),
            ephemeral=True,
        )


class ViewDumbfightSuggestionsButton(discord.ui.Button):
    def __init__(self, client: dvvt):
        super().__init__(
            style = discord.ButtonStyle.grey,
            label = "View your submissions",
            custom_id="view_dumbfight_submissions"
        )
        self.client = client

    async def callback(self, interaction: discord.Interaction):
        user_submissions = await self.client.db.fetch("SELECT * FROM dumbfight_suggestions WHERE user_id = $1",
                                                      interaction.user.id)
        if not user_submissions:
            embed = discord.Embed(title="Your submissions",
                                  description="You have no submissions. Click the Suggest button below to make one.",
                                  color=self.client.embed_color)
            view = discord.ui.View(timeout=30, disable_on_timeout=True).add_item(
                InitiateDumbfightSuggestionButton(self.client))
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            pages = []
            pages_of_submissions = list(batched(user_submissions, 5))
            for index, submissions in enumerate(pages_of_submissions, 1):
                embed = discord.Embed(title="Your submissions", color=self.client.embed_color)
                embed.set_footer(text=f"Page {index} of {len(pages_of_submissions)}")
                descriptions = []
                for submission in submissions:
                    submission_id = submission.get('id')
                    message = submission.get('message').replace("{winner}", "**@Argon**").replace("{loser}",
                                                                                                  "**@Frenzy**")
                    fight_type = "Fighting others" if submission.get(
                        'fight_type') == "other" else "Fighting yourself" if submission.get(
                        'fight_type') == "self" else submission.get('fight_type')
                    status = submission.get('status')
                    status_emoji = DVB_STATUS_GREY
                    status_name = "Unknown"
                    if status == "pending_approval":
                        status_emoji = DVB_STATUS_YELLOW
                        status_name = "Pending Approval"
                    if status == "approved":
                        status_emoji = DVB_STATUS_GREEN
                        status_name = "Approved"
                    if status == "rejected":
                        status_emoji = DVB_STATUS_RED
                        status_name = "Rejected"

                    descriptions.append(f"#{submission_id}. {message}")
                    descriptions.append(f"-# {status_emoji} {status_name} | {fight_type}")
                    descriptions.append("")
                embed.description = "\n".join(descriptions)
                pages.append(embed)

            paginator = SingleMenuPaginator(pages=pages, author_check=True, timeout=30)
            await paginator.respond(interaction=interaction, ephemeral=True)


class ViewDumbfightExamplesButton(discord.ui.Button):
    def __init__(self, client):
        self.client = client

        super().__init__(
            label="View examples",
            style=discord.ButtonStyle.secondary,
            emoji="📋",
            custom_id="view_dumbfight_examples",
        )

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Dumbfight Message Examples",
            description=(
                "These are only examples. Use your creativity to suggest new ones!"
            ),
            color=self.client.embed_color,
        )

        embed.set_author(
            name=self.client.user.name,
            icon_url=self.client.user.display_avatar.url,
        )

        embed.add_field(
            name="Dumbfighting someone else",
            value=(
                "• `{winner}` EMOTIONALLY DAMAGED `{loser}`.\n"
                "• `{winner}` told `{loser}` to mine straight down in Minecraft.\n"
                "• `{winner}` told `{loser}` that their Discord kitten doesn't love them.\n"
                "• `{loser}` became a Discord Mod.\n"
                "• `{loser}` put milk before cereal in front of `{winner}`."
            ),
            inline=False,
        )

        embed.add_field(
            name="Dumbfighting yourself",
            value=(
                "• `{loser}` punched themselves in the face.\n"
                "• `{loser}` stepped on their own feet.\n"
                "• `{loser}` tickled themselves until they couldn't take it."
            ),
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class InitiateDumbfightSuggestionView(discord.ui.View):
    def __init__(self, client: dvvt):
        super().__init__(timeout=None)
        self.client = client
        self.add_item(InitiateDumbfightSuggestionButton(client))
        self.add_item(ViewDumbfightSuggestionsButton(client))
        self.add_item(ViewDumbfightExamplesButton(client))



class TriggerDumbfightSuggestionModalButton(discord.ui.Button):
    def __init__(self, client: dvvt, fight_type: str, existing_input: Union[str, None] = None, style: discord.ButtonStyle = discord.ButtonStyle.primary, label: str = "Suggest", ):
        self.client = client
        super().__init__(
            style=style,  # Discord style 1
            label=label,
            custom_id=f"suggest:{fight_type}",
            disabled=False,
        )
        self.fight_type=fight_type
        self.existing_input = existing_input

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SuggestDumbfightModal(self.client, self.fight_type, self.existing_input))
        await interaction.delete_original_response()


class DumbfightDesignerView(discord.ui.DesignerView):
    def __init__(self, client: dvvt, timeout: float | None = None):
        self.client = client

        super().__init__(timeout=timeout)

        container = discord.ui.Container(color=196599, spoiler=False)

        container.add_text("## What kind of dumbfight are you suggesting?\n-# 🎥 Play the videos to show how this feature works.")

        container.add_separator(divider=True, spacing=discord.SeparatorSpacingSize.large)

        container.add_section(
            discord.ui.TextDisplay("### Dumbfighting yourself"),
            accessory=TriggerDumbfightSuggestionModalButton(client, fight_type="self"),
        )

        container.add_gallery(discord.MediaGalleryItem("https://dvbot-media.nogra.app/core/dfsuggestions/dumbfight_self_se.mp4", description=None, spoiler=False))

        container.add_separator(divider=True,spacing=discord.SeparatorSpacingSize.small)

        container.add_section(
            discord.ui.TextDisplay("### Dumbfighting a friend"),
            accessory=TriggerDumbfightSuggestionModalButton(client, fight_type="other")
        )

        container.add_gallery(
            discord.MediaGalleryItem("https://dvbot-media.nogra.app/core/dfsuggestions/dumbfight_others_se.mp4", description=None, spoiler=False)
        )

        self.add_item(container)

class DumbfightSuggest(commands.Cog):
    def __init__(self, client: dvvt):
        self.client: dvvt = client

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="dfmessages")
    async def suggest_dumbfight_messages(self, ctx: DVVTcontext):
        """
        Suggest messages for dumb fight.
        """
        description = dedent("""
        We are adding more messages to the **dumbfight** command to make fights more varied and entertaining 😮 and we want your help!

        If you have an idea for a **funny fight outcome**, submit it. You may submit as many as you want. We will review each suggestion and decide whether it fits!
        """)
        embed = discord.Embed(title="Suggest new messages for `dumbfight`!", description=description,
                              color=self.client.embed_color)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/755117384653733999.webp?animated=true")
        embed.add_field(name="Requirements", value="TBC", inline=False)
        rules = dedent(f"""
            - 😆 It should (obviously) be funny or enjoyable.
            - 🧠 Your imagination is the LIMIT. It could be related to a server joke, or a meme. Up to you, really.
            - {DVB_TRUE} Use some common sense; The message doesn't have to be family friendly, but it must be appropriate.
            - 🙅‍♂️ Suggestions that already exist, are overly NSFW, or are not funny, will be REJECTED.
        """)
        embed.add_field(name="Rules for new dumbfight suggestions", value=rules, inline=False)
        embed.set_footer(text="What are you waiting for???", icon_url=None)
        await ctx.send(embed=embed, view=InitiateDumbfightSuggestionView(self.client))

