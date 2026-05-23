from textwrap import dedent

import discord
from discord.ext import commands

from custom_emojis import DVB_TRUE
from main import dvvt
from utils import checks
from utils.context import DVVTcontext

class SuggestDumbfightModal(discord.ui.DesignerModal):
    def __init__(self, dumbfight_type):
        title="Suggest Dumbfight Message"

        if dumbfight_type == "other":
            placeholder = "{winner} punched {loser} and he fell."
            label="What happens in a dumbfight"
            description="Include {winner} and/or {loser} where their names should appear."
        else:
            placeholder = "{loser} slipped on a banana peel and fell."
            label="What happens when you fight yourself"
            description="Include {loser} where the loser should appear."
        input2 = discord.ui.Label(label, discord.ui.InputText(placeholder=placeholder, style=discord.InputTextStyle.long),description=description)
        super().__init__(
            input2,
            title=title
        )

class InitiateDumbfightSuggestionButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,  # Discord style 1
            label="Suggest",
            custom_id="initiate_dumbfight_suggestion",
            emoji="✍️"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            view=DumbfightDesignerView(),
            ephemeral=True,
        )

class InitiateDumbfightSuggestionView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(InitiateDumbfightSuggestionButton())

class SuggestButton(discord.ui.Button):
    def __init__(self, *, fight_type):
        super().__init__(
            style=discord.ButtonStyle.primary,  # Discord style 1
            label="Suggest!",
            custom_id=f"suggest:{fight_type}",
            disabled=False,
        )
        self.fight_type=fight_type

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SuggestDumbfightModal(self.fight_type))


class DumbfightDesignerView(discord.ui.DesignerView):
    def __init__(self, *, timeout: float | None = None):
        super().__init__(timeout=timeout)

        container = discord.ui.Container(color=196599, spoiler=False)

        container.add_text("## What kind of dumbfight are you suggesting?")

        container.add_separator(divider=True, spacing=discord.SeparatorSpacingSize.large)

        container.add_section(
            discord.ui.TextDisplay("### Dumbfighting yourself"),
            accessory=SuggestButton(fight_type="self"),
        )

        container.add_gallery(discord.MediaGalleryItem("https://cataas.com/cat?width=400&height=200", description=None, spoiler=False))

        container.add_separator(divider=True,spacing=discord.SeparatorSpacingSize.small)

        container.add_section(
            discord.ui.TextDisplay("### Dumbfighting a friend"),
            accessory=SuggestButton(fight_type="other")
        )

        container.add_gallery(
            discord.MediaGalleryItem("https://cataas.com/cat?width=400&height=200", description=None, spoiler=False)
        )

        self.add_item(container)

class DumbfightSuggest(commands.Cog):
    def __init__(self, client):
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
            - 🧠 Your imagination is the LIMIT.
            - {DVB_TRUE} Use some common sense; The message doesn't have to be family friendly, but it must be appropriate.
            - 🙅‍♂️ Suggestions that already exist, are overly NSFW, or are not funny, will be REJECTED.
        """)
        embed.add_field(name="Rules for new dumbfight suggestions", value=rules, inline=False)
        embed.set_footer(text="What are you waiting for???", icon_url=None)
        await ctx.send(embed=embed, view=InitiateDumbfightSuggestionView())

