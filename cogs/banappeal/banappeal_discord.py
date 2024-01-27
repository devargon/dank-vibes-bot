import copy
import random

import discord
from discord import default_permissions, Option
from discord.ext import pages
from typing import List

from utils import checks
from utils.context import DVVTcontext
from utils.format import proper_userf
from .banappeal_views import BanAppealView, GetBannedView
from .banappealdb import BanAppealDB, BanAppeal
from datetime import datetime, timedelta
import asyncio
import contextlib
from discord.ext import commands
from main import dvvt

def truncate_string(string, length=27):
    truncatelength = length-3
    return (string[:truncatelength] + '..') if len(string) > length else string

class AppealSelectorBtn(discord.ui.Button):
    def __init__(self, appeal: BanAppeal, cog):
        self.appeal = appeal
        self.cog = cog
        super().__init__(
            style=discord.ButtonStyle.blurple if appeal.appeal_status == 0 else discord.ButtonStyle.red if appeal.appeal_status == 1 else discord.ButtonStyle.green if appeal.appeal_status == 2 else discord.ButtonStyle.grey,
            label=f"#{appeal.appeal_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        embed = await self.cog.generate_embed(self.appeal)
        v = BanAppealView(self.appeal)

        class DeleteMessageBtn(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                await interaction.message.delete()

        v.add_item(DeleteMessageBtn(style=discord.ButtonStyle.blurple, label="Delete this message", emoji="🚮"))
        await interaction.response.send_message(embed=embed, view=v)

class AppealSelector(discord.ui.View):
    def __init__(self, chunk_of_appeals, cog):
        self.cog = cog
        self.appeals = chunk_of_appeals
        super().__init__()

        for appeal in self.appeals:
            self.add_item(AppealSelectorBtn(appeal, self.cog))


class BanAppealDiscord(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    async def generate_appeals_pages(self, embed: discord.Embed, appeals: List[BanAppeal]) -> List[pages.Page]:
        pag_pages = []
        current_start_index = 1
        items_per_page = 5
        for chunk in discord.utils.as_chunks(appeals, items_per_page):
            embed_copy = embed.copy()
            current_end_index = current_start_index + len(chunk) - 1

            page_footer_text = f"Showing {current_start_index}-{current_end_index} of {len(appeals)}"
            embed_copy.set_footer(text=page_footer_text)
            for appeal in chunk:
                appealer = self.client.get_user(appeal.user_id)
                appealer_txt = f"{proper_userf(appealer)} ({appealer.id})" if appealer else str(appeal.user_id)
                title = f"#{appeal.appeal_id}: {appealer_txt}"
                ban_txt = truncate_string(appeal.ban_reason) if appeal.ban_reason else "None"
                created_txt = f"Created: <t:{round(appeal.appeal_timestamp.timestamp())}:F>"

                if appeal.appeal_status == 0:
                    status = f"🕒 Pending"
                elif appeal.appeal_status in [1, 2]:

                    status = f"❌ Denied" if appeal.appeal_status == 1 else f"✅ Approved"
                    if appeal.reviewer_id:
                        reviewer = self.client.get_user(appeal.reviewer_id)
                        status += f" by {reviewer.mention if reviewer else appeal.reviewer_id}"
                    if appeal.reviewed_timestamp:
                        status += f" at {discord.utils.format_dt(appeal.reviewed_timestamp, 'd')} {discord.utils.format_dt(appeal.reviewed_timestamp, 't')}"
                    if appeal.reviewer_response:
                        status += "\n<:Reply:871808167011549244> Remarks: " + truncate_string(appeal.reviewer_response)
                else:
                    status = f"❓ Unknown ({appeal.appeal_status}"
                embed_copy.add_field(name=title, value="\n".join([ban_txt,created_txt,status,"** **"]), inline=False)
            current_start_index += len(chunk)
            pg = pages.Page(embeds=[embed_copy], custom_view=AppealSelector(chunk, self))
            pag_pages.append(pg)
        return pag_pages

    @checks.dev()
    @commands.command(name="idk")
    async def idk(self, ctx: DVVTcontext):
        embed = discord.Embed(title="Welcome!", description="You're invited to participate in the preproduction test for Dank Vibes Bot's Ban Appeal feature. Read below before continuing:", color=self.client.embed_color)
        embed.add_field(name="What is this", value="This activity will simulate making an appeal through DV Bot's newest platform, a customized online ban appeal portal, after getting banned.", inline=False)
        embed2 = discord.Embed(title="How is it conducted?", description="1. Click the button below. You'll receive a DM from this bot - like how you'd get banned with Carl-bot - and subsequently be banned from this server.\n2. The DM sent to you will include a link to the ban appeal platform. Click on it.\n3. From then on, no guidance is provided. Just use the website like you would, if you wanted to make an appeal to be unbanned.", color=self.client.embed_color)
        embed3 = discord.Embed(title="⚠️ IMPORTANT!", description="**This ban appeal platform includes email notifications for when your ban appeal gets updated by a Moderator.**\nIt's not compulsory to use this feature, but I **highly recommend** you **DO** use it, to help me ensure that it works as intended. \nI'd also like to get your opinion/feedback on this feature, such as __whether the emails ended up in your Junk folder__.", color=discord.Color.yellow())
        embed4 = discord.Embed(title="What happens after?", description="Regardless of whether your ban gets accepted or denied, I'll probably come around asking for feedback from you. You can also provide me feedback as soon as you've submitted your appeal.", color=self.client.embed_color)
        embed4.set_footer(text="Thank you so much for participating!")
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/801435251951403048.gif")
        embed2.set_thumbnail(url="https://cdn.discordapp.com/emojis/825271478958030868.gif")
        embed3.set_thumbnail(url="https://cdn.discordapp.com/emojis/762334206449549362.gif")
        embed4.set_thumbnail(url="https://cdn.discordapp.com/emojis/832623591812104202.webp")
        await ctx.send(embeds=[embed, embed2, embed3, embed4], view=GetBannedView())





    @default_permissions(manage_roles=True)
    @checks.has_permissions_or_role(manage_roles=True)
    @commands.slash_command(name="appeals", description="Search for appeals with additional filters.")
    async def view_appeals(self, ctx,
                           appeal_id: Option(input_type=int, name="appeal_id", description="Find a specific appeal by its ID", required=False, default=None),
                           status: Option(input_type=str, name="status", description="Search for appeals with a specific status", choices=["Pending", "Approved", "Denied"], required=False, default=None),
                           user_id: Option(input_type=str, name="user_id", description="Search for appeals made by a user with this ID", required=False, default=None),
                           user: Option(input_type=discord.SlashCommandOptionType.user, name="user", description="(Overrides user_id) Search for appeals made by this user. Only users IN this server.", required=False, default=None),
                           order: Option(input_type=str, name="order", description="Order the list of appeals by...", choices=["Ascending", "Descending"], required=False, default="Ascending")
                           ):
        if status:
            if status == "Pending":
                status = 0
            elif status == "Approved":
                status = 2
            elif status == "Denied":
                status = 1
            else:
                status = None
        order_asc = True if order == "Ascending" else False

        banappealdb = BanAppealDB(self.client.db)
        if user_id:
            try:
                user_id = int(user_id)
            except ValueError:
                return await ctx.respond(f"`{user_id}` is not a valid user ID.")
        if user is not None:
            user_id = user.id

        appeals = await banappealdb.search_ban_appeals(order_asc=order_asc, status=status, appeal_id=appeal_id, user_id=user_id)
        embed = discord.Embed(title="Appeals", description="Filters: ",  color=self.client.embed_color)
        if appeal_id is None and status is None:
            embed.description += "None"
        if appeal_id is not None:
            embed.description += f"\n> Appeal ID: `{appeal_id}`"
        if status is not None:
            embed.description += f"\n> Status: `{'Pending' if status == 0 else 'Approved' if status == 2 else 'Denied'}`"
        if user_id is not None:
            embed.description += f"\n> User ID: `{user_id}`"
        embed.description += f"\n> Order of appeals: {'ascending' if order_asc else 'descending'}"

        if len(appeals) == 0:
            embed.description += "\n\nNo results found."
            embed.color = discord.Color.red()
            return await ctx.respond(embed=embed)

        paginator = pages.Paginator(pages=await self.generate_appeals_pages(embed, appeals), loop_pages=False)
        await paginator.respond(ctx.interaction, ephemeral=False)












