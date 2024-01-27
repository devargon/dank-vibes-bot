import os
import re

import discord
from typing import Optional

from aiohttp import ClientSession

from cogs.banappeal.banappealdb import BanAppealDB, BanAppeal
from utils.format import proper_userf, print_exception


def get_appeal_no_from_embed(embed):
    appeal_match = re.match("Ban Appeal #(\d+)", embed.title)
    if appeal_match:
        try:
            appeal_no = int(appeal_match.group(1))
        except ValueError:
            appeal_no = None
    else:
        appeal_no = None
    return appeal_no

class BanAppealReasonModal(discord.ui.Modal):
    def __init__(self, selected_appeal_status, appeal_id):
        self.selected_appeal_status = selected_appeal_status
        self.appeal_id = appeal_id
        super().__init__(title="Add a remark for " + ("Denying" if selected_appeal_status == 1 else "Approving" if selected_appeal_status == 2 else "???") + f" Appeal #{appeal_id}", timeout=None)

        # Add a text input field for the remark
        self.remark = discord.ui.InputText(
            label=("Approved" if selected_appeal_status == 2 else "Denied" if selected_appeal_status == 1 else "???") + " Remarks",
            placeholder="It will be seen by the user, leave this field blank if you're not adding one.",
            style=discord.InputTextStyle.paragraph,
            max_length=512,
            required=False
        )
        self.add_item(self.remark)

    async def callback(self, interaction: discord.Interaction):
        result_embed = discord.Embed(title=f"Error in updating appeal #{self.appeal_id}", description="", color=discord.Color.red())
        if self.selected_appeal_status not in [1, 2]:
            result_embed.description = "You selected a invalid appeal status option (you can only select Approve/Deny)."
            return await interaction.response.send_message(embed=result_embed, ephemeral=True)
        user_remark = self.remark.value
        banappealdb = BanAppealDB(interaction.client.db)
        banappeal = await banappealdb.get_ban_appeal_by_appeal_id(self.appeal_id)

        if banappeal is None:
            result_embed.description = f"I could not find an appeal with the ID `{self.appeal_id}`."
            return await interaction.response.send_message(embed=result_embed, ephemeral=True)
        if banappeal.appeal_status == 1 or banappeal.appeal_status == 2:
            if banappeal.reviewer_id is not None:
                reviewer = await interaction.client.get_or_fetch_user(banappeal.reviewer_id)
            else:
                reviewer = discord.NotFound
            result_embed.description = f"This ban appeal was already " + ("**Denied**" if banappeal.appeal_status == 1 else "**Approved**") + " by " + ("Unknown" if reviewer == discord.NotFound else f"{reviewer.mention} ({reviewer.id})" if reviewer is not None else str(banappeal.reviewer_id) + ".")
            return await interaction.response.send_message(embed=result_embed, ephemeral=True)
        appealer = await interaction.client.get_or_fetch_user(banappeal.user_id)
        appealer_text = f"**{proper_userf(appealer)}** ({appealer.id})" if appealer is not None else str(banappeal.user_id)
        banned_guild = interaction.client.get_guild(banappeal.guild_id)
        err = None
        if self.selected_appeal_status == 2:
            if appealer is not None:
                try:
                    await banned_guild.unban(appealer, reason=f"Ban appeal #{banappeal.appeal_id} was approved by {proper_userf(interaction.user)}  ({interaction.user.id})")
                except discord.Forbidden:  # No permission to unban
                    err = "I'm unable to unban the user because I lack the necessary permissions. Ensure I have the \"Ban Members\" permission."
                except discord.HTTPException as e:
                    err = f"I'm unable to unban the user: {str(e)}"
            else:
                err = f"I'm unable to ban the user as I can't find them through their ID (`{banappeal.user_id}`)"
            if err:
                result_embed.description = err
                return await interaction.response.send_message(embed=result_embed, ephemeral=True)

        banappeal.appeal_status = self.selected_appeal_status
        banappeal.reviewer_id = interaction.user.id
        banappeal.reviewer_response = user_remark if user_remark is not None and len(user_remark) > 0 else None
        banappeal.reviewed_timestamp = discord.utils.utcnow()
        banappeal.updated = False

        await banappealdb.update_ban_appeal(banappeal)
        cog = interaction.client.get_cog('banappeal')
        cog.discordBanAppealUpdateQueue.append(banappeal)

        result_embed.color = discord.Color.green()
        result_embed.set_footer(text=proper_userf(interaction.user), icon_url=interaction.user.display_avatar.with_size(32).url)
        result_embed.title = f"You've updated appeal #{self.appeal_id}"
        result_embed.description = "You " + ("**denied**" if banappeal.appeal_status == 1 else "**approved**") + f" {appealer_text}'s appeal"
        if banappeal.reviewer_response is not None:
            result_embed.description += f" with the remarks: \n\n> {banappeal.reviewer_response}"
        else:
            result_embed.description += f" with no remarks."
        await interaction.response.send_message(embed=result_embed, ephemeral=True)

        if banappeal.email is not None:
            print(f"Appeal #{banappeal.appeal_id} has an email associated, will attempt to request the server to send an email.")
            middleman_server = os.getenv("APPEALS_SERVER_HOST")
            if not middleman_server:
                print(f"Middleman server env, APPEALS_SERVER_HOST has not been set.")
            else:
                try:
                    async with ClientSession(headers={"authorization": os.getenv("APPEALS_SHARED_SECRET")}) as session:
                        print(f"Sending Appeal #{banappeal.appeal_id} data to notify endpoint")
                        data = banappeal.to_public_dict()
                        if appealer:
                            data['username'] = appealer.display_name
                        a = await session.post(f"{middleman_server}/api/notify-update", json=data)
                        print(f"#{banappeal.appeal_id} data has been sent. Response: {a.status}")
                        await session.close()
                except Exception as e:
                    print_exception(f"Error while sending appeal #{banappeal.appeal_id} data to endpoint:", e)
        return



# noinspection PyMethodMayBeStatic
class BanAppealView(discord.ui.View):
    def __init__(self, banappeal: Optional[BanAppeal] = None):
        super().__init__(timeout=None)

        class AppealActionButton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                banappealdb = BanAppealDB(interaction.client.db)
                embed = interaction.message.embeds[0]
                appeal_no = get_appeal_no_from_embed(embed)
                if appeal_no is None:
                    return await interaction.response.send_message(
                        embed=discord.Embed(title=f"Error in updating appeal #{appeal_no}",
                                            description="Appeal ID not found in embed.",
                                            color=discord.Color.red()), ephemeral=True)
                appeal = await banappealdb.get_ban_appeal_by_appeal_id(appeal_no)
                if appeal is None:
                    return await interaction.response.send_message(
                        embed=discord.Embed(title=f"Error in updating appeal #{appeal_no}",
                                            description=f"An appeal with the ID `{appeal_no}` was not found.",
                                            color=discord.Color.red()), ephemeral=True)
                if self.custom_id == "appeal:approve":
                    modal = BanAppealReasonModal(2, appeal.appeal_id)
                    return await interaction.response.send_modal(modal=modal)
                elif self.custom_id == "appeal:deny":
                    modal = BanAppealReasonModal(1, appeal.appeal_id)
                    return await interaction.response.send_modal(modal=modal)
                elif self.custom_id == "appeal:get_user_id":
                    return await interaction.response.send_message(str(appeal.user_id) or "?", ephemeral=True)

        self.green_button = AppealActionButton(label='Approve + Unban', emoji=discord.PartialEmoji.from_str("<:DVB_checkmark:955345523139805214>"), style=discord.ButtonStyle.green, custom_id="appeal:approve")
        self.red_button = AppealActionButton(label='Deny', emoji=discord.PartialEmoji.from_str("<:DVB_crossmark:955345521151737896>"), style=discord.ButtonStyle.red, custom_id="appeal:deny")
        self.grey_button = AppealActionButton(label='User ID', style=discord.ButtonStyle.blurple, custom_id="appeal:get_user_id")

        if banappeal is not None:
            if banappeal.appeal_status in [1, 2]:
                self.green_button.disabled = True
                self.red_button.disabled = True
                if banappeal.appeal_status == 1:  # Denied
                    self.green_button.style = discord.ButtonStyle.grey
                if banappeal.appeal_status == 2:  # Approved
                    self.red_button.style = discord.ButtonStyle.grey

        self.add_item(self.green_button)
        self.add_item(self.red_button)
        self.add_item(self.grey_button)
