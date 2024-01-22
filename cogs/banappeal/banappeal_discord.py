import discord
from .banappealdb import BanAppealDB, BanAppeal
from datetime import datetime, timedelta
import asyncio
import contextlib
from discord.ext import commands
from main import dvvt

class BanAppealDiscord(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    async def generate_embed(self, appeal: BanAppeal):
        embed = discord.Embed(title=f"Ban Appeal #{appeal.appeal_id}", color=discord.Color.green() if appeal.appeal_status == 2 else discord.Color.red() if appeal.appeal_status == 1 else discord.Color.light_gray());
        appealing_user = await self.client.get_or_fetch_user(appeal.user_id)
        if appealing_user:
            ap_user_disp = f"@{appealing_user.name}" if appealing_user.discriminator == "0" else f"{appealing_user.name}#{appealing_user.discriminator}"
        else:
            ap_user_disp = str(appeal.user_id)
        embed.set_author(name=ap_user_disp, icon_url=appealing_user.display_avatar.with_size(32).url)
        descriptions = []
        descriptions.append("Banned for: " + appeal.ban_reason if appeal.ban_reason is not None else "Not specified")
        descriptions.append("")
        if appeal.appeal_status == 0:
            descriptions.append("Pending, **awaiting review**")
            embed.set_footer(text="Pending") # Add a loading graphic?
        elif appeal.appeal_status in [1, 2]:
            status_str = "Denied" if appeal.appeal_status == 1 else "Approved"
            embed.set_footer(text=status_str)
            embed.timestamp = appeal.reviewed_timestamp
            if appeal.reviewer_id:
                reviewer_moderator = await self.client.get_or_fetch_user(appeal.reviewer_id)
                reviewer_disp = f"{reviewer_moderator.mention} ({reviewer_moderator.id})" if reviewer_moderator else f"{appeal.user_id}"
                status_str += f" by {reviewer_disp}"
            if appeal.reviewed_timestamp:
                status_str += f" on <t:{round(appeal.reviewed_timestamp.timestamp())}:F>"
            descriptions.append(status_str)
            if appeal.reviewer_response:
                embed.set_footer(text=embed.footer.text + " with remarks")
                descriptions.append(f"Reviewer remarks: {appeal.reviewer_response}")
            embed.set_footer(text=embed.footer.text + " on ")
        else:
            descriptions.append("Status unknown")
        descriptions.append("** **")
        descriptions.append(f"Appeal responses")
        embed.description = "\n".join(descriptions)
        if appeal.version == 1:
            qn_1 = "Do you understand why you were banned/what do you think led to your ban?"
            qn_2 = "How will you change to be a positive member of the community?"
            qn_3 = "Is there any other information you would like to provide?"
            qn_id = 1
            embed.add_field(name=f"_{qn_id}. {qn_1}_", value=appeal.appeal_answer1 or "_ _")
            qn_id += 1
            embed.add_field(name=f"_{qn_id}. {qn_2}_", value=appeal.appeal_answer2 or "_ _")
            qn_id += 1
            embed.add_field(name=f"_{qn_id}. {qn_3}_", value=appeal.appeal_answer3 or "_ _")
        return embed



