import asyncio
import json
import time
from collections import defaultdict
from datetime import datetime
from typing import Optional, Dict, Any, Union

import amari.objects
import discord
from discord.ext import commands, tasks

from cogs.admin.contests import interactionconfirm
from cogs.amari_import.amari_import_dao import AmariImportDAO
from custom_emojis import DVB_TRUE, DVB_FALSE, DVB_STATUS_GREEN, DVB_STATUS_RED, DVB_STATUS_YELLOW
from main import dvvt
from utils import checks
from utils.buttons import confirm, SingleURLButton
from utils.context import DVVTcontext
from utils.format import print_exception, box, comma_number
from utils.specialobjects import AmariImportTask, AmariImportWorker, AmariImportTaskLog

lastUpdatedQueuePositions = {}


class CooldownManager:
    """Manages cooldowns for different operations"""

    def __init__(self):
        self.amari_transfer_cooldowns = defaultdict(float)
        self.cancel_amari_transfer_cooldowns = defaultdict(float)
        self.delete_channel_amari_transfer_cooldowns = defaultdict(float)
        self.amari_transfer_pending_confirmations = {}

    def check_cooldown(self, user_id: int, cooldown_type: str, cooldown_time: int = 30) -> Optional[int]:
        """
        Check if user is on cooldown for a specific operation.
        Returns remaining cooldown time in seconds if on cooldown, None otherwise.
        """
        cooldown_dict = getattr(self, f"{cooldown_type}_cooldowns", None)
        if cooldown_dict is None:
            return None

        now = time.time()
        last_used = cooldown_dict[user_id]

        if now - last_used < cooldown_time:
            return int(cooldown_time - (now - last_used))

        return None

    def update_cooldown(self, user_id: int, cooldown_type: str):
        """Update the cooldown timestamp for a user and operation type"""
        cooldown_dict = getattr(self, f"{cooldown_type}_cooldowns", None)
        if cooldown_dict is not None:
            cooldown_dict[user_id] = time.time()


class AmariDataManager:
    """Handles Amari data operations"""

    AMARI_DATA_FILE = "dankvibes-amari-data-20250405.json"
    AMARI_LEVELS_FILE = "assets/data/amari_levels.json"

    def __init__(self, client: dvvt):
        self.client = client
        self._amari_levels_cache = None

    async def get_user_old_amari_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's old Amari data from the JSON file"""
        # Check for alternate user ID first
        dv_user_id = await self.client.db.fetchval(
            "SELECT alternate_user_id FROM amari_import_altn_userids WHERE target_user_id = $1",
            user_id
        ) or user_id

        try:
            with open(self.AMARI_DATA_FILE, "r", encoding="utf-8") as f:
                content = json.load(f)
                return next((d for d in content if d.get("id") == str(dv_user_id)), None)
        except FileNotFoundError:
            return None

    async def get_current_amari_data(self, guild_id: int, user_id: int) -> Optional[amari.objects.User]:
        """Get user's current Amari data from the server"""
        try:
            return await self.client.AmariClient.fetch_user(guild_id, user_id)
        except amari.exceptions.NotFound:
            return None

    def get_amari_levels(self) -> list:
        """Get Amari level data with caching"""
        if self._amari_levels_cache is None:
            try:
                with open(self.AMARI_LEVELS_FILE, "r", encoding="utf-8") as f:
                    self._amari_levels_cache = json.load(f)
            except FileNotFoundError:
                self._amari_levels_cache = []
        return self._amari_levels_cache

    def calculate_expected_level(self, total_exp: int) -> int:
        """Calculate expected level based on total experience"""
        amari_levels = self.get_amari_levels()

        for level_data in amari_levels:
            if level_data.get("exp", 0) > total_exp:
                return level_data.get("level", 1) - 1

        return 0

    def get_xp_for_level(self, level: int) -> int:
        """Get the XP required for a specific Amari level"""
        amari_levels = self.get_amari_levels()
        for level_data in amari_levels:
            if level_data.get("level") == level:
                return level_data.get("exp", 0)
        return 0


class AmariImportEmbed(discord.Embed):
    """Custom embed for Amari import operations"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs, color=0x57F0F0)
        self.set_author(
            name="Amari Transfer",
            icon_url="https://cdn.discordapp.com/emojis/1135328388849090692.webp?size=96"
        )


class EmbedFormatter:
    """Handles embed formatting for Amari import tasks"""

    @staticmethod
    def format_task_embed(amari_import_task: AmariImportTask) -> discord.Embed:
        """Format the main task embed with current status and information"""
        base_embed = AmariImportEmbed(
            title=f"Request #{amari_import_task.id}",
            timestamp=discord.utils.utcnow()
        )

        # Add XP information
        xp_to_add = amari_import_task.amari_xp_to_add
        expected_amari_level = amari_import_task.expected_amari_level
        expected_total_amari_xp = amari_import_task.expected_total_amari_xp

        base_embed.add_field(
            name="Your Amari stats at old Dank Vibes",
            value=f"📈 **XP**: `{comma_number(xp_to_add)}`",
            inline=False)
        base_embed.add_field(
            name="Your NEW ✨ Amari stats (expected)",
            value=f"📊 **Level**: `{comma_number(expected_amari_level)}`\n📈 **XP**: `{comma_number(expected_total_amari_xp)}`",
            inline=False
        )

        status_config = EmbedFormatter._get_status_config(amari_import_task.status)
        queue_position_str = "Please wait..."
        if amari_import_task.position == 0:
            queue_position_str = "You're at the front!"
        elif amari_import_task.position > 0:
            queue_position_str = str(amari_import_task.position)

        # Build description
        descriptions = []
        if amari_import_task.status in ["PENDING", "IN_PROGRESS"]:
            descriptions.append(f"Position in queue: **{queue_position_str}**")
            descriptions.append("")

        descriptions.append("## Status: " + status_config["emoji"] + status_config["name"])

        # Add ticket message if present
        if amari_import_task.ticket_message:
            descriptions.append("")
            base_embed.add_field(name="Message", value=amari_import_task.ticket_message)
            descriptions.append(f"Ticket message: {amari_import_task.ticket_message}")

        base_embed.color = status_config["color"]
        descriptions.extend(status_config["messages"])

        base_embed.description = "\n".join(descriptions)
        base_embed.set_footer(text="Last updated at")

        return base_embed

    @staticmethod
    def _get_status_config(status: str) -> Dict[str, Any]:
        """Get color and messages for different task statuses"""
        status_configs = {
            "PENDING": {
                "name": "Pending",
                "emoji": DVB_STATUS_YELLOW,
                "color": discord.Color.yellow(),
                "messages": []
            },
            "IN_PROGRESS": {
                "name": "In Progress",
                "emoji": DVB_STATUS_YELLOW,
                "color": discord.Color.yellow(),
                "messages": []
            },
            "FAILED": {
                "name": "Failed",
                "emoji": DVB_STATUS_RED,
                "color": discord.Color.red(),
                "messages": []
            },
            "ADMIN_SKIPPED": {
                "name": "Skipped (Admin)",
                "emoji": DVB_STATUS_RED,
                "color": discord.Color.red(),
                "messages": []
            },
            "ADMIN_CANCELLED": {
                "name": "Cancelled",
                "emoji": DVB_STATUS_RED,
                "color": discord.Color.red(),
                "messages": []
            },
            "CANCELLED": {
                "name": "Cancelled",
                "emoji": DVB_STATUS_RED,
                "color": discord.Color.red(),
                "messages": [
                    "",
                    "This task was cancelled. Please open a new Amari stats transfer request."
                ]
            },
            "COMPLETED": {
                "name": "Completed",
                "emoji": DVB_STATUS_GREEN,
                "color": discord.Color.green(),
                "messages": [
                    "",
                    "Your Amari stats has been transferred here. If you think this is wrong, open a ticket in <#1343892378687377408>."
                ]
            }
        }

        return status_configs.get(status, {
            "color": discord.Color.default(),
            "messages": []
        })


class ErrorHandler:
    """Handles error reporting and user notifications"""

    def __init__(self, client: dvvt):
        self.client = client

    async def handle_view_error(self, interaction: discord.Interaction, error: Exception, view_name: str):
        """Handle errors that occur in view callbacks"""
        traceback_error = print_exception(f"Ignoring exception in {view_name}", error)

        descriptions = [
            f"User: `{interaction.user} {interaction.user.id}` {interaction.user.mention}",
        ]

        error_embed = discord.Embed(
            title=f"Error handling {view_name} button callback",
            description="\n".join(descriptions),
            color=discord.Color.red()
        )
        error_embed.add_field(name="Error", value=box(traceback_error)[:1024])

        await self.client.error_channel.send(
            f"Error handling {view_name} button callback",
            embed=error_embed
        )

        error_message = (
            "# ⚠️ An error occurred and I cannot proceed. \n\n"
            "The developers have been notified. Please try this again later!"
        )

        if interaction.response.is_done():
            await interaction.followup.send(error_message, ephemeral=True)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)


class TicketManager:
    """Handles ticket creation and management"""

    TICKET_CATEGORY_ID = 1358041831551537183

    def __init__(self, client: dvvt):
        self.client = client

    async def create_confirmation_ticket(
            self,
            interaction: discord.Interaction
    ) -> Optional[discord.TextChannel]:
        """Create a ticket channel for confirmation"""
        try:
            ticket_category = await interaction.guild.fetch_channel(self.TICKET_CATEGORY_ID)
            if not ticket_category:
                return None

            member_in_guild = await interaction.guild.fetch_member(interaction.user.id)
            if member_in_guild is None:
                return None

            ticket_channel = await interaction.guild.create_text_channel(
                name="pending-amari-confirmation",
                reason=f"Request initiated by {interaction.user} ({interaction.user.id})",
                category=ticket_category,
                overwrites={
                    interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    member_in_guild: discord.PermissionOverwrite(
                        add_reactions=False,
                        send_messages=False,
                        view_channel=True,
                        use_application_commands=False,
                        use_external_apps=False,
                        send_messages_in_threads=False,
                        read_messages=True,
                        read_message_history=True,
                        create_public_threads=False,
                        create_private_threads=False,
                        create_instant_invite=False
                    )
                }
            )

            return ticket_channel

        except Exception:
            return None


class TaskManagementView(discord.ui.View):
    """View for managing individual tasks (non-persistent)"""

    def __init__(self, client: dvvt, task: AmariImportTask, initiator_id: int):
        self.client = client
        self.task = task
        self.initiator_id = initiator_id
        self.amari_import_dao = AmariImportDAO(client)
        super().__init__(timeout=30.0)  # 30 second timeout

    @discord.ui.button(
        label="Delete Task",
        style=discord.ButtonStyle.danger,
        emoji="🗑️"
    )
    async def delete_task_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.initiator_id:
            return await interaction.response.send_message(
                f"{DVB_FALSE} Only the person who initiated this command can delete the task.",
                ephemeral=True
            )

        try:
            rows_changed = await self.amari_import_dao.deleteTaskById(self.task.id)
            if rows_changed > 0:
                button.label = "Task Deleted"
                button.disabled = True
                button.style = discord.ButtonStyle.grey

                embed = discord.Embed(
                    title=f"Task #{self.task.id} - DELETED",
                    description="This task has been manually deleted by a developer.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )

                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.response.send_message(
                    f"{DVB_FALSE} Failed to delete task - it may have already been removed.",
                    ephemeral=True
                )
        except Exception as e:
            await interaction.response.send_message(
                f"{DVB_FALSE} Error deleting task: {str(e)}",
                ephemeral=True
            )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        try:
            await self.message.edit(view=self)
        except:
            pass  # Message might be deleted


class TaskStatusView(discord.ui.View):
    """View for managing the background task status (non-persistent)"""

    def __init__(self, client: dvvt, initiator_id: int):
        self.client = client
        self.initiator_id = initiator_id
        super().__init__(timeout=60.0)

    def get_cog(self, interaction: discord.Interaction):
        return interaction.client.get_cog("amari_import")

    @discord.ui.button(
        label="Start Task",
        style=discord.ButtonStyle.green,
        emoji="▶️"
    )
    async def start_task_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.initiator_id:
            return await interaction.response.send_message(
                f"{DVB_FALSE} Only the person who initiated this command can control the task.",
                ephemeral=True
            )
        cog = self.get_cog(interaction)
        if not cog:
            return await interaction.response.send_message(
                f"{DVB_FALSE} AmariImport cog not found.",
                ephemeral=True
            )
        if cog.amari_import_task.is_running():
            return await interaction.response.send_message(
                f"{DVB_FALSE} The task is already running.",
                ephemeral=True
            )
        try:
            await cog.amari_import_task.start()
            await interaction.response.send_message(
                f"{DVB_TRUE} Background task started successfully.",
                ephemeral=True
            )
            await self._update_status_embed(interaction)
        except Exception as e:
            await interaction.response.send_message(
                f"{DVB_FALSE} Error starting task: {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(
        label="Stop Task (Graceful)",
        style=discord.ButtonStyle.red,
        emoji="⏹️"
    )
    async def stop_task_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.initiator_id:
            return await interaction.response.send_message(
                f"{DVB_FALSE} Only the person who initiated this command can control the task.",
                ephemeral=True
            )
        cog = self.get_cog(interaction)
        if not cog:
            return await interaction.response.send_message(
                f"{DVB_FALSE} AmariImport cog not found.",
                ephemeral=True
            )
        if not cog.amari_import_task.is_running():
            return await interaction.response.send_message(
                f"{DVB_FALSE} The task is not currently running.",
                ephemeral=True
            )
        try:
            cog.amari_import_task.stop()
            await interaction.response.send_message(
                f"{DVB_TRUE} Task stop requested (will finish current loop).",
                ephemeral=True
            )
            await asyncio.sleep(0.5)
            await self._update_status_embed(interaction)
        except Exception as e:
            await interaction.response.send_message(
                f"{DVB_FALSE} Error stopping task: {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(
        label="Cancel Task (Immediate)",
        style=discord.ButtonStyle.red,
        emoji="❌"
    )
    async def cancel_task_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.initiator_id:
            return await interaction.response.send_message(
                f"{DVB_FALSE} Only the person who initiated this command can control the task.",
                ephemeral=True
            )
        cog = self.get_cog(interaction)
        if not cog:
            return await interaction.response.send_message(
                f"{DVB_FALSE} AmariImport cog not found.",
                ephemeral=True
            )
        if not cog.amari_import_task.is_running():
            return await interaction.response.send_message(
                f"{DVB_FALSE} The task is not currently running.",
                ephemeral=True
            )
        try:
            cog.amari_import_task.cancel()
            await interaction.response.send_message(
                f"{DVB_TRUE} Task cancel requested (will stop immediately).",
                ephemeral=True
            )
            await asyncio.sleep(0.5)
            await self._update_status_embed(interaction)
        except Exception as e:
            await interaction.response.send_message(
                f"{DVB_FALSE} Error cancelling task: {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(
        label="Refresh Status",
        style=discord.ButtonStyle.grey,
        emoji="🔄"
    )
    async def refresh_status_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.initiator_id:
            return await interaction.response.send_message(
                f"{DVB_FALSE} Only the person who initiated this command can refresh the status.",
                ephemeral=True
            )
        await interaction.response.defer()
        await self._update_status_embed(interaction)

    async def _update_status_embed(self, interaction: discord.Interaction):
        cog = self.get_cog(interaction)
        if not cog:
            return
        task = cog.amari_import_task

        if task.is_running():
            status_text = f"{DVB_STATUS_GREEN} Running"
            status_color = discord.Color.green()
        elif task.failed():
            status_text = f"{DVB_STATUS_RED} Failed"
            status_color = discord.Color.red()
        else:
            status_text = f"{DVB_STATUS_YELLOW} Stopped"
            status_color = discord.Color.yellow()

        exception_info = "None"
        if task.failed() and hasattr(task, 'exception') and task.exception():
            exception_info = f"```py\n{str(task.exception())[:1000]}```"

        embed = discord.Embed(
            title="Background Task Status",
            color=status_color,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Status", value=status_text, inline=True)
        embed.add_field(
            name="Current Iteration",
            value=f"`{getattr(task, 'current_loop', 'N/A')}`",
            inline=True
        )
        embed.add_field(
            name="Next Iteration",
            value=f"<t:{int(task.next_iteration.timestamp()) if getattr(task, 'next_iteration', None) else 0}:R>",
            inline=True
        )
        embed.add_field(
            name="Loop Count",
            value=f"`{task.completed_loops() if hasattr(task, 'completed_loops') else 'N/A'}`",
            inline=True
        )
        embed.add_field(
            name="Is Being Cancelled",
            value=f"`{task.is_being_cancelled() if hasattr(task, 'is_being_cancelled') else 'N/A'}`",
            inline=True
        )
        embed.add_field(
            name="Failed",
            value=f"`{task.failed() if hasattr(task, 'failed') else 'N/A'}`",
            inline=True
        )
        if exception_info != "None":
            embed.add_field(
                name="Last Exception",
                value=exception_info,
                inline=False
            )
        embed.set_footer(text="Last updated")
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception:
            pass

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass

class AmariRequestTicketManagementView(discord.ui.View):
    """View for managing Amari transfer request tickets"""

    def __init__(self, client: dvvt):
        self.client = client
        self.amari_import_dao = AmariImportDAO(self.client)
        self.cooldown_manager = CooldownManager()
        self.error_handler = ErrorHandler(self.client)
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.grey,
        custom_id="button:cancel_amari_transfer_request"
    )
    async def cancel_amari_transfer_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            # Check cooldown
            remaining = self.cooldown_manager.check_cooldown(
                interaction.user.id, "cancel_amari_transfer", 30
            )
            if remaining:
                return await interaction.response.send_message(
                    f"{DVB_FALSE} Please wait **{remaining} seconds** before trying again.",
                    ephemeral=True
                )

            task = await self.amari_import_dao.fetchTaskByTicketChannelId(interaction.channel_id)
            if not task:
                return await interaction.response.send_message(
                    f"{DVB_FALSE} An Amari transfer request in this channel was not found.",
                    ephemeral=True
                )

            # Check if task can be cancelled
            cancel_result = self._check_cancel_eligibility(task)
            if cancel_result:
                return await interaction.response.send_message(cancel_result, ephemeral=True)

            # Cancel the task
            rows_changed = await self.amari_import_dao.deleteTaskById(task.id)
            if rows_changed > 0:
                await self._handle_successful_cancellation(interaction, button, task)
            else:
                raise ValueError(
                    f"Error when deleting task #{task.id}: rowsChanged expected > 0 but got {rows_changed}")

        except Exception as e:
            await self.error_handler.handle_view_error(interaction, e, "AmariRequestTicketManagementView")

    @discord.ui.button(
        label="Delete Channel",
        style=discord.ButtonStyle.grey,
        custom_id="button:delete_channel"
    )
    async def delete_channel_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            # Check cooldown
            remaining = self.cooldown_manager.check_cooldown(
                interaction.user.id, "delete_channel_amari_transfer", 30
            )
            if remaining:
                return await interaction.response.send_message(
                    f"{DVB_FALSE} Please wait **{remaining} seconds** before trying again.",
                    ephemeral=True
                )

            task = await self.amari_import_dao.fetchTaskByTicketChannelId(interaction.channel_id)
            if not task:
                return await interaction.response.send_message(
                    f"{DVB_FALSE} An Amari transfer request in this channel was not found.",
                    ephemeral=True
                )

            # Check permissions (hardcoded admin check)
            if interaction.user.id not in [312876934755385344]:
                return await interaction.response.defer()

            if task.status != "COMPLETED":
                return await interaction.response.send_message(
                    f"{DVB_FALSE} Your Amari transfer request is not completed.",
                    ephemeral=True
                )

            await interaction.channel.delete()

        except Exception as e:
            await self.error_handler.handle_view_error(interaction, e, "AmariRequestTicketManagementView")

    def _check_cancel_eligibility(self, task: AmariImportTask) -> Optional[str]:
        """Check if a task can be cancelled and return error message if not"""
        status_messages = {
            "IN_PROGRESS": f"{DVB_FALSE} Your Amari transfer request is currently in progress, and you cannot cancel it.",
            "COMPLETED": f"{DVB_FALSE} Your Amari transfer request is completed. This channel will be deleted automatically within 2 days.",
            "FAILED": f"{DVB_FALSE} Your Amari transfer request failed. The developer will look into the failure, and the ticket cannot be closed at this time.",
            "ADMIN_SKIPPED": f"{DVB_FALSE} Your Amari transfer request was interrupted by an admin. Please open a ticket.",
            "ADMIN_CANCELLED": f"{DVB_FALSE} Your Amari transfer request was interrupted by an admin. Please open a ticket."
        }

        if task.status in status_messages:
            return status_messages[task.status]
        elif task.status != "PENDING":
            return f"{DVB_FALSE} Unknown task status."

        return None

    async def _handle_successful_cancellation(self, interaction: discord.Interaction, button: discord.ui.Button,
                                              task: AmariImportTask):
        """Handle the UI updates and notifications after successful cancellation"""
        button.label = "Task cancelled"
        button.style = discord.ButtonStyle.red
        button.disabled = True
        task.status = "CANCELLED"

        embed = EmbedFormatter.format_task_embed(task)
        await interaction.response.edit_message(embed=embed, view=self)

        await interaction.followup.send(
            f"{DVB_TRUE} **This task has been cancelled**.\n\n"
            "Provided your Amari stats have not been transferred, you may request/initiate a new Amari stats transfer again.\n\n"
            "This channel will be deleted automatically.",
            ephemeral=True
        )

        await asyncio.sleep(60)
        await interaction.channel.delete()


class AmariRequestView(discord.ui.View):
    """Main view for initiating Amari transfer requests"""

    def __init__(self, client: dvvt):
        self.client = client
        self.amari_import_dao = AmariImportDAO(self.client)
        self.cooldown_manager = CooldownManager()
        self.error_handler = ErrorHandler(self.client)
        self.amari_data_manager = AmariDataManager(self.client)
        self.ticket_manager = TicketManager(self.client)
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Request Amari Transfer",
        emoji=discord.PartialEmoji.from_str("<:DV_AmariBot:1358007654659788990>"),
        style=discord.ButtonStyle.green,
        custom_id="button:request_amari_transfaer"
    )
    async def request_amari_transfer_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            # Check cooldown (skip for specific user)
            if interaction.user.id not in [312876934755385344, 1376832460356321311]:
                remaining = self.cooldown_manager.check_cooldown(
                    interaction.user.id, "amari_transfer", 30
                )
                if remaining:
                    return await interaction.response.send_message(
                        f"{DVB_FALSE} Please wait **{remaining} seconds** before trying again.",
                        ephemeral=True
                    )
                self.cooldown_manager.update_cooldown(interaction.user.id, "amari_transfer")

            # Check if feature is enabled
            guild_settings = await self.client.get_guild_settings(interaction.guild_id)
            if not guild_settings.enable_amari_transfer:
                return await interaction.response.send_message(
                    f"{DVB_FALSE} Amari transfer requests are currently **disabled/not allowed**. Please try again later.",
                    ephemeral=True
                )

            # Check if user already has a task
            all_user_tasks = await self.amari_import_dao.fetchAllTasksForUser(interaction.user.id)
            if len(all_user_tasks) > 999:
                return await interaction.response.send_message(
                    f"{DVB_FALSE} You have previously opened an Amari transfer request. You are not allowed to open more than 1 request.\n"
                    "Please open a ticket in <#1343892378687377408> if you think this is an error.",
                    ephemeral=True
                )

            await interaction.response.defer(ephemeral=True, invisible=False)

            # Get user's old and current Amari data
            amari_data_result = await self._get_user_amari_data(interaction)
            if isinstance(amari_data_result, str):  # Error message
                return await interaction.followup.send(amari_data_result, ephemeral=True)

            old_amari_details, current_amari_details = amari_data_result
            old_xp = old_amari_details.get("exp", 0)
            old_level = old_amari_details.get("level", 0)
            current_exp = current_amari_details.exp
            resulting_exp = current_exp + old_xp
            expected_level = self.amari_data_manager.calculate_expected_level(resulting_exp)

            # Create confirmation ticket
            ticket_channel = await self.ticket_manager.create_confirmation_ticket(
                interaction
            )

            if not ticket_channel:
                return await interaction.followup.send(
                    f"{DVB_FALSE} I could not create your ticket. Please try again later.",
                    ephemeral=True
                )

            # Handle confirmation process
            await self._handle_confirmation_process(
                interaction, ticket_channel, current_exp, old_level, old_xp, expected_level, resulting_exp
            )

        except Exception as e:
            await self.error_handler.handle_view_error(interaction, e, "AmariRequestView")

    async def _get_user_amari_data(self, interaction: discord.Interaction):
        """Get user's old and current Amari data, return error message if not found"""
        # Get old Amari data
        users_old_amari_data = await self.amari_data_manager.get_user_old_amari_data(interaction.user.id)
        if users_old_amari_data is None:
            return (f"{DVB_FALSE} I couldn't find your AmariBot XP or level from the old Dank Vibes.\n"
                    "Please open a ticket in <#1343892378687377408> if you think this is an error.")

        # Get current Amari data
        current_amari_details = await self.amari_data_manager.get_current_amari_data(
            interaction.guild_id, interaction.user.id
        )
        if current_amari_details is None:
            return (f"{DVB_FALSE} I could not get your AmariBot XP or level **here**.\n"
                    "Please open a ticket in <#1343892378687377408> if you think this is an error.")

        return users_old_amari_data, current_amari_details

    async def _handle_confirmation_process(
            self,
            interaction: discord.Interaction,
            ticket_channel: discord.TextChannel,
            current_exp: int,
            old_level: int,
            old_xp: int,
            expected_level: int,
            resulting_exp: int
    ):
        """Handle the confirmation process in the ticket channel"""
        # Create confirmation view and send initial message
        confirm_view = interactionconfirm(interaction.user, self.client, 30.0)

        confirmation_embed = AmariImportEmbed(
            title="Amari Transfer Confirmation",
            description="You're about to add your XP from the **old Dank Vibes** to the XP you've earned here in this server."
        )
        confirmation_embed.add_field(
            name="Your Amari stats at old Dank Vibes",
            value=f"📊 **Level**: `{comma_number(old_level)}`\n📈 **XP**: `{comma_number(old_xp)}`",
            inline=False)
        confirmation_embed.add_field(
            name="Your current XP",
            value=f"`{comma_number(current_exp)}`",
            inline=False
        )
        confirmation_embed.add_field(
            name="Your NEW ✨ Amari stats (expected)",
            value=f"📊 **Level**: `{comma_number(expected_level)}`\n📈 **XP**: `{comma_number(resulting_exp)}`",
            inline=False
        )
        confirmation_embed.add_field(name="\u200b",
                                     value="Disclaimer: Your level and XP is calculated based the XP you gained in old Dank Vibes + the XP you gained here, and is not final.\nIf you think the numbers shown above are inaccurate, please press **No** and open a ticket at <#1343892378687377408>.",
                                     inline=False)

        confirm_view.response = top_channel_message = await ticket_channel.send(
            f"{interaction.user.mention}, please review your Amari stats below. If everything looks correct, press **Yes** to proceed.",
            embed=confirmation_embed,
            view=confirm_view
        )

        await interaction.followup.send(
            f"Please head to {ticket_channel.mention} to continue the process!",
            view=SingleURLButton(link=top_channel_message.jump_url, text="Go to channel"),
            ephemeral=True
        )

        # Wait for confirmation
        await confirm_view.wait()

        if confirm_view.returning_value is None:
            await self._handle_confirmation_timeout(ticket_channel, interaction.user)
        elif confirm_view.returning_value is False:
            await self._handle_confirmation_declined(confirm_view, ticket_channel, interaction.user)
        else:
            await self._handle_confirmation_accepted(
                confirm_view, top_channel_message, interaction.user,
                ticket_channel, old_xp, expected_level, resulting_exp
            )

    async def _handle_confirmation_timeout(self, ticket_channel: discord.TextChannel, user: discord.User):
        """Handle confirmation timeout"""
        await ticket_channel.send(
            f"{DVB_FALSE} You did not respond to the confirmation. This ticket will be closed.\n"
            "You may start a new transfer at any time."
        )
        await asyncio.sleep(10)
        await ticket_channel.delete(reason=f"Request initiated by {user} ({user.id}); timeout to confirmation")

    async def _handle_confirmation_declined(self, confirm_view, ticket_channel: discord.TextChannel,
                                            user: discord.User):
        """Handle confirmation declined"""
        await confirm_view.interaction.response.send_message(
            f"{DVB_FALSE} You chose not to transfer your Amari stats here. This ticket will be closed.\n"
            "You may start a new transfer at any time."
        )
        await asyncio.sleep(10)
        await ticket_channel.delete(reason=f"Request initiated by {user} ({user.id}); cancelled confirmation")

    async def _handle_confirmation_accepted(
            self,
            confirm_view,
            top_channel_message: discord.Message,
            user: discord.User,
            ticket_channel: discord.TextChannel,
            old_xp: int,
            expected_level: int,
            resulting_exp: int
    ):
        """Handle confirmation accepted"""
        resulting_task = await self.amari_import_dao.createAmariImportTask(
            user.id, ticket_channel.id, top_channel_message.id, old_xp, expected_level, resulting_exp
        )

        embed_to_edit = EmbedFormatter.format_task_embed(resulting_task)
        await top_channel_message.edit(content=user.mention, embed=embed_to_edit, view=AmariRequestTicketManagementView(self.client))
        lastUpdatedQueuePositions[resulting_task.id] = resulting_task.position
        datetime_display_now = discord.utils.utcnow().strftime("%d%m%yT%H:%M:%S")
        await ticket_channel.edit(name=f"{resulting_task.id}-{user.name}-amaritransfer-{datetime_display_now}", topic=f"Amari transfer ticket for {user.mention} created on {discord.utils.format_dt(ticket_channel.created_at)} and submitted into queue on {discord.utils.format_dt(discord.utils.utcnow())}")
        await confirm_view.interaction.response.send_message(
            f"# You are in the queue.\n{DVB_TRUE} Your Amari transfer request has been submitted. You will be notified when it's your turn."
        )


class TaskProcessor:
    """Handles processing of Amari import tasks"""

    def __init__(self, client: dvvt, amari_import_dao: AmariImportDAO, debug_mode: bool = False):
        self.client = client
        self.amari_data_manager = AmariDataManager(self.client)
        self.amari_import_dao = amari_import_dao
        self.debug_mode = debug_mode

    def _debug_print(self, message: str):
        """Print debug messages only if debug mode is enabled"""
        if self.debug_mode:
            print(f"[TaskProcessor DEBUG] {message}")

    async def process_tasks(self):
        """Main task processing loop"""
        self._debug_print("Starting task processing cycle")

        all_tasks = await self.amari_import_dao.fetchAllTasksInQueue()
        self._debug_print(f"Fetched {len(all_tasks)} tasks from queue")

        if len(all_tasks) == 0:
            self._debug_print("No tasks in queue, sleeping for 30 seconds")
            await asyncio.sleep(30)
            return

        self._debug_print(f"Found tasks:")
        for task in all_tasks:
            self._debug_print(task)

        for index, task in enumerate(all_tasks, start=1):
            self._debug_print(f"Processing task {index}/{len(all_tasks)} - ID: {task.id}, Status: {task.status}")

            if task.position == 0:  # First in queue
                self._debug_print("Task is first in queue, processing immediately")
                await self._process_first_task(task)
            else:
                if not lastUpdatedQueuePositions.get(task.id) == task.position:
                    await self._simple_update_embed(task)
                else:
                    self._debug_print(f"Task {task.id} does not have a difference in queue position. skipping embed update.")

                if task.position <= 3 and not task.notified_near_front:
                    self._debug_print(f"Task {task.id} is near front of queue, sending notification")
                    await self._notify_near_front(task)

        self._debug_print("Completed processing cycle")

    async def _process_first_task(self, task: AmariImportTask):
        """Process the first task in the queue"""
        self._debug_print(f"Starting to process first task - ID: {task.id}")

        if task.status != "PENDING":
            self._debug_print(f"Task status is {task.status}, skipping processing")
            return

        self._debug_print(f"Fetching ticket channel with ID: {task.ticket_channel_id}")
        try:
            task_ticket_channel = await self.client.fetch_channel(task.ticket_channel_id)
            self._debug_print("Successfully fetched ticket channel")
        except Exception as e:
            self._debug_print(f"Failed to fetch ticket channel: {e}")
            await self._mark_task_failed(task, None, f"Ticket channel not found {e}")
            return

        self._debug_print(f"Sending start notification to user {task.user_id}")
        await task_ticket_channel.send(
            f"# Your Amari import will start in a moment.\n\n"
            f"You are now at the front of the queue.\n<@{task.user_id}>"
        )

        # Update task status to IN_PROGRESS
        self._debug_print("Updating task status to IN_PROGRESS")
        task.status = "IN_PROGRESS"
        task.updated_at = discord.utils.utcnow()

        embed = EmbedFormatter.format_task_embed(task)

        self._debug_print(f"Updating embed message with ID: {task.ticket_message_id}")
        try:
            await task_ticket_channel.get_partial_message(task.ticket_message_id).edit(embed=embed)
            lastUpdatedQueuePositions[task.id] = task.position
            self._debug_print("Successfully updated existing embed message")
        except Exception:
            self._debug_print("Failed to update existing message, creating new one")
            try:
                new_message = await task_ticket_channel.send(embed=embed)
                task.ticket_message_id = new_message.id
                self._debug_print(f"Created new embed message with ID: {new_message.id}")
            except Exception as e:
                self._debug_print(f"Failed to create new embed message: {e}")
                await self._mark_task_failed(task, None, f"Could not update message: {e}")
                return

        self._debug_print("Saving task updates to database")
        await task.update(self.client)

        try:
            current_amari_details = await self.amari_data_manager.get_current_amari_data(
                task.ticket_guild_id, task.user_id
            )
            resultingexp = current_amari_details.exp + task.amari_xp_to_add
            expected_level = self.amari_data_manager.calculate_expected_level(resultingexp)
            await task_ticket_channel.send(f"**Debug purposes, ignore this message.**\n-# Your current level is `{comma_number(current_amari_details.level)}`. \n-# Your current XP is `{comma_number(current_amari_details.exp)}`. \n-# I will add `{comma_number(task.amari_xp_to_add)}` XP, resulting in `{comma_number(resultingexp)}`. \n-# Your resulting level will be`{comma_number(expected_level)}`.")
            commands_to_run = []
            if expected_level <= 200:
                commands_to_run.append(f"*gl <@{task.user_id}> {expected_level}")
                level_from_which_to_add_xp_after = expected_level

            else:
                commands_to_run.append(f"*gl <@{task.user_id}> 200")
                level_from_which_to_add_xp_after = 200
            current_xp_added = self.amari_data_manager.get_xp_for_level(level_from_which_to_add_xp_after)
            remaining_xp_to_add = resultingexp - current_xp_added
            while remaining_xp_to_add > 100000:
                commands_to_run.append(f"*modifyexp <@{task.user_id}> 100000")
                remaining_xp_to_add -= 100000
            commands_to_run.append(f"*modifyexp <@{task.user_id}> {remaining_xp_to_add}")
            for command in commands_to_run:
                await task_ticket_channel.send(command)
            # TODO: Implement actual Amari/selfbot transfer logic here
            print("TODO")
        except Exception as e:
            await self._mark_task_failed(
                task, task_ticket_channel,
                print_exception("Direct task processing failed due to the following exception", e),
                user_friendly_error="The Amari transfer task has failed due to an unexpected error. Please try again later."
            )
        else:
            await self._complete_task(task, task_ticket_channel)
            lastUpdatedQueuePositions.pop(task.id, None)

    async def _notify_near_front(self, task: AmariImportTask):
        """Notify users who are near the front of the queue"""
        self._debug_print(f"Checking if task {task.id} needs near-front notification")

        if task.notified_near_front:
            self._debug_print("Task already notified, skipping")
            return

        self._debug_print(f"Fetching ticket channel for near-front notification: {task.ticket_channel_id}")
        try:
            task_ticket_channel = await self.client.fetch_channel(task.ticket_channel_id)
            self._debug_print("Successfully fetched ticket channel for notification")
        except Exception as e:
            self._debug_print(f"Failed to fetch ticket channel for notification: {e}")
            await self._mark_task_failed(task, None, f"Ticket channel not found {e}")
            return

        self._debug_print(f"Sending near-front notification to user {task.user_id}")
        await task_ticket_channel.send(
            f"# Your Amari import will start soon.\n\n"
            f"You are near the front of the queue.\n<@{task.user_id}>"
        )

        self._debug_print("Marking task as notified and updating database")
        task.notified_near_front = True
        task.updated_at = discord.utils.utcnow()

        embed = EmbedFormatter.format_task_embed(task)

        self._debug_print("Updating embed for near-front notification")
        try:
            await task_ticket_channel.get_partial_message(task.ticket_message_id).edit(embed=embed)
            lastUpdatedQueuePositions[task.id] = task.position
            self._debug_print("Successfully updated embed for near-front notification")
        except Exception:
            self._debug_print("Failed to update existing embed, creating new one")
            try:
                new_message = await task_ticket_channel.send(embed=embed)
                task.ticket_message_id = new_message.id
                self._debug_print(f"Created new embed message for notification: {new_message.id}")
            except Exception as e:
                self._debug_print(f"Failed to create new embed for notification: {e}")
                await self._mark_task_failed(task, None, f"Could not update message: {e}")
                return

        await task.update(self.client)

    async def _complete_task(self, task: AmariImportTask, task_ticket_channel: discord.abc.GuildChannel):
        """Mark task as completed"""
        self._debug_print(f"Completing task {task.id}")

        task.status = "COMPLETED"
        task.updated_at = discord.utils.utcnow()
        task.stopped_at = discord.utils.utcnow()

        embed = EmbedFormatter.format_task_embed(task)

        self._debug_print("Saving completed task to database")
        await task.update(self.client)

        self._debug_print("Sending completion message and updating embed")
        try:
            await task_ticket_channel.get_partial_message(task.ticket_message_id).edit(embed=embed)
            lastUpdatedQueuePositions.pop(task.id, None)
            self._debug_print(f"Edit embed message API call")
            await task_ticket_channel.send(
                f"# {DVB_TRUE} Completed\n\nYour Amari stats has been successfully transferred. This channel will be deleted automatically."
            )
            self._debug_print("Successfully sent completion message")
        except Exception:
            self._debug_print("Failed to send completion message (ignoring error)")
            pass  # Ignore message update errors for completed tasks

    async def _mark_task_failed(self, task: AmariImportTask, task_ticket_channel: Union[discord.abc.GuildChannel, None], error_message: str, user_friendly_error: str = "This task has failed due to an error."):
        """Mark a task as failed with error message"""
        self._debug_print(f"Marking task {task.id} as failed: {error_message}")

        task.error_message = error_message
        task.status = "FAILED"
        task.updated_at = discord.utils.utcnow()
        task.ticket_message = user_friendly_error

        self._debug_print("Saving failed task to database")
        await task.update(self.client)

        if task_ticket_channel is not None:
            embed = EmbedFormatter.format_task_embed(task)
            self._debug_print("Sending failed message and updating embed")
            try:
                await task_ticket_channel.get_partial_message(task.ticket_message_id).edit(embed=embed)
                self._debug_print(f"Edit embed message API call")
                await task_ticket_channel.send(
                    f"# {DVB_FALSE} Failed\n\nI was unable to complete transferring your Amari stats due to an error. A developer has been notified of this issue and will assist you soon.\n\n-# CC: <@312876934755385344>"
                )
                self._debug_print("Successfully sent failed message")
            except Exception:
                pass

    async def _simple_update_embed(self, task):
        self._debug_print(f"Performing simple embed update ot task {task.id}")
        embed = EmbedFormatter.format_task_embed(task)

        task_ticket_channel = self.client.get_channel(task.ticket_channel_id)
        if task_ticket_channel is None:
            try:
                task_ticket_channel = await self.client.fetch_channel(task.ticket_channel_id)
                self._debug_print("Successfully fetched ticket channel")
            except Exception as e:
                self._debug_print(f"Failed to fetch ticket channel: {e}")
                await self._mark_task_failed(task, None, f"Ticket channel not found {e}")
                return
        embed = EmbedFormatter.format_task_embed(task)
        self._debug_print("Sending failed message and updating embed")
        try:
            await task_ticket_channel.get_partial_message(task.ticket_message_id).edit(embed=embed)
            lastUpdatedQueuePositions[task.id] = task.position
            self._debug_print(f"Edit embed message API call")
        except Exception:
            pass



class AmariImport(commands.Cog, name="amari_import"):
    """Main cog for Amari import functionality"""

    def __init__(self, client: dvvt):
        self.client = client
        self.amari_import_dao = AmariImportDAO(client)
        self.task_processor = TaskProcessor(client, self.amari_import_dao, debug_mode=True)

    @commands.Cog.listener()
    async def on_ready(self):
        """Initialize views and start background tasks when bot is ready"""
        self.client.add_view(AmariRequestView(self.client))
        self.client.add_view(AmariRequestTicketManagementView(self.client))
        await self.amari_import_task.start()

    @checks.dev()
    @commands.command(name="requestamari")
    async def send_initiate_amari_request_message(self, ctx: DVVTcontext):
        """Send the initial Amari transfer request message"""
        embed = AmariImportEmbed(
            description=(
                "This Amari stats transfer feature is for members of the old Dank Vibes before it was nuked.\n\n"
                "You will not be able to use this feature if you're a new member of Dank Vibes after December 2024.\n\n"
                "This feature will transfer over your XP from your old AmariBot stats to your current stats here.\n"
                "To begin, click the button below."
            )
        )
        await ctx.send(embed=embed, view=AmariRequestView(self.client))

    @commands.group(name="amariaccount", invoke_without_command=True)
    @checks.has_permissions_or_role(administrator=True)
    async def amariaccount(self, ctx: DVVTcontext):
        """Manage alternate Discord accounts for Amari data transfer."""
        await ctx.send_help(ctx.command)

    @checks.has_permissions_or_role(administrator=True)
    @amariaccount.command(name="link")
    async def amariaccount_link(self, ctx: DVVTcontext, member: discord.Member, alternate_user_id: int):
        """Add an alternate user ID for Amari data lookup"""
        existing_record = await self.client.db.fetchrow("SELECT * FROM amari_import_altn_userids WHERE target_user_id = $1", member.id)

        if existing_record is not None:
            await self.client.db.execute("DELETE FROM amari_import_altn_userids WHERE id = $1", existing_record.get("id"))

        await self.client.db.execute(
            "INSERT INTO amari_import_altn_userids(creator_user_id, target_user_id, alternate_user_id) VALUES($1, $2, $3)", ctx.author.id, member.id, alternate_user_id
        )

        await ctx.maybe_reply(
            f"{DVB_TRUE} Updated: I will look for {alternate_user_id}'s Amari stats from old Dank Vibes "
            f"to transfer to {member.mention}'s Amari stats here."
        )

    @checks.has_permissions_or_role(administrator=True)
    @amariaccount.command(name="unlink")
    async def amariaccount_unlink(self, ctx: DVVTcontext, member: discord.Member):
        """Remove an alternate user ID for a member"""
        existing_record = await self.client.db.fetchrow("SELECT * FROM amari_import_altn_userids WHERE target_user_id = $1", member.id)

        if existing_record is not None:
            await self.client.db.execute( "DELETE FROM amari_import_altn_userids WHERE id = $1", existing_record.get("id"))
            await ctx.maybe_reply(f"{DVB_TRUE} Alternate User ID for {member.mention} was deleted.")
        else:
            await ctx.maybe_reply(f"{DVB_FALSE} {member.mention} does not have an alternate User ID set.")

    @commands.group(name="amaritransfer", invoke_without_command=True)
    @checks.dev()
    async def amaritransfer(self, ctx: DVVTcontext):
        """Manage Amari data transfer tasks and queue."""
        await ctx.send_help(ctx.command)

    @checks.dev()
    @amaritransfer.command(name="list", aliases=["amariusertasks"])
    async def amaritransfer_tasks(self, ctx: DVVTcontext, user: discord.User = None):
        """View all tasks for a specific user"""
        if user is None:
            user = ctx.author

        try:
            tasks = await self.amari_import_dao.fetchAllTasksForUser(user.id)

            if not tasks:
                return await ctx.maybe_reply(f"{DVB_FALSE} No tasks found for {user.mention} (`{user.id}`).")

            # Create embed with task list
            embed = AmariImportEmbed(
                title=f"Tasks for {user.display_name}",
                description=f"Found **{len(tasks)}** task(s) for {user.mention} (`{user.id}`)"
            )

            # Group tasks by status for better organization
            status_groups = defaultdict(list)
            for task in tasks:
                status_groups[task.status].append(task)

            # Add fields for each status group
            for status, status_tasks in status_groups.items():
                status_config = EmbedFormatter._get_status_config(status)
                task_list = []

                for task in status_tasks:
                    created_timestamp = f"<t:{int(task.created_at.timestamp())}:R>"
                    task_list.append(
                        f"**#{task.id}** - Created {created_timestamp}"
                    )

                embed.add_field(
                    name=f"{status_config.get('emoji', '❓')} {status_config.get('name')} ({len(status_tasks)})",
                    value="\n".join(task_list),
                    inline=False
                )

            embed.set_footer(text=f"Use {ctx.prefix}amaritask <ID> to view a specific task")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.maybe_reply(f"{DVB_FALSE} Error retrieving tasks: {str(e)}")

    @checks.dev()
    @amaritransfer.command(name="view", aliases=["amaritask"])
    async def amaritransfer_view(self, ctx: DVVTcontext, task_id: int):
        """View a specific task by ID with management options"""
        try:
            task = await self.amari_import_dao.fetchTaskById(task_id)

            if not task:
                return await ctx.maybe_reply(
                    f"{DVB_FALSE} Task with ID `{task_id}` not found."
                )

            # Get user info
            try:
                user = await self.client.fetch_user(task.user_id)
                user_info = f"{user.mention} (`{user.id}`)"
            except:
                user_info = f"Unknown User (`{task.user_id}`)"

            # Create detailed embed
            status_config = EmbedFormatter._get_status_config(task.status)
            embed = AmariImportEmbed( title=f"Task #{task.id}")

            embed.color = status_config.get('color', discord.Color.default())

            embed.add_field(name="User", value=user_info, inline=True)
            embed.add_field(name="Status",
                            value=f"{status_config.get('emoji', '❓')} {status_config.get('name')}",
                            inline=True)
            embed.add_field(name="XP to Add", value=f"`{comma_number(task.amari_xp_to_add)} XP`", inline=True)
            embed.add_field(name="Expected Level", value=f"`{comma_number(task.expected_amari_level)}`", inline=True)
            embed.add_field(name="Expected Total XP", value=f"`{comma_number(task.expected_total_amari_xp)} XP`",
                            inline=True)
            embed.add_field(name="Channel ID", value=f"`{task.ticket_channel_id}`", inline=True)
            embed.add_field(name="Created", value=f"<t:{int(task.created_at.timestamp())}:F>", inline=False)
            embed.add_field(name="Last Updated", value=f"<t:{int(task.updated_at.timestamp())}:F>", inline=False)

            if task.stopped_at:
                embed.add_field(name="Stopped", value=f"<t:{int(task.stopped_at.timestamp())}:F>", inline=False)

            if task.error_message:
                embed.add_field(name="Error Message", value=f"```{task.error_message[:1000]}```", inline=False)

            if task.ticket_message:
                embed.add_field(name="Ticket Message", value=task.ticket_message[:1000], inline=False)

            # Create view for task management
            view = TaskManagementView(self.client, task, ctx.author.id)
            message = await ctx.send(embed=embed, view=view)
            view.message = message

        except Exception as e:
            await ctx.maybe_reply(f"{DVB_FALSE} Error retrieving task: {str(e)}")

    @checks.dev()
    @amaritransfer.command(name="status", aliases=["amaritaskstatus"])
    async def amaritransfer_status(self, ctx: DVVTcontext):
        """View the status of the background task with control options"""
        try:
            task = self.amari_import_task

            # Determine status
            if task.is_running():
                status_text = f"{DVB_STATUS_GREEN} Running"
                status_color = discord.Color.green()
            elif task.failed():
                status_text = f"{DVB_STATUS_RED} Failed"
                status_color = discord.Color.red()
            else:
                status_text = f"{DVB_STATUS_YELLOW} Stopped"
                status_color = discord.Color.yellow()

            # Get exception info if available
            exception_info = "None"
            if task.failed() and hasattr(task, 'exception') and task.exception():
                exception_info = f"```py\n{str(task.exception())[:1000]}```"

            embed = AmariImportEmbed(title="Background Task Status")
            embed.color = status_color
            embed.add_field(name="Status", value=status_text, inline=True)
            embed.add_field(name="Current Iteration", value=f"`{getattr(task, 'current_loop', 'N/A')}`", inline=True)
            embed.add_field(name="Next Iteration", value=f"<t:{int(task.next_iteration.timestamp()) if task.next_iteration else 0}:R>", inline=True)
            embed.add_field(name="Loop Count", value=f"`{task.completed_loops() if hasattr(task, 'completed_loops') else 'N/A'}`", inline=True)
            embed.add_field(name="Is Being Cancelled", value=f"`{task.is_being_cancelled()}`", inline=True)
            embed.add_field(name="Failed", value=f"`{task.failed()}`", inline=True)

            if exception_info != "None":
                embed.add_field(name="Last Exception", value=exception_info, inline=False)

            embed.set_footer(text="Use the buttons below to control the task")
            embed.timestamp = discord.utils.utcnow()

            # Create view for task control
            view = TaskStatusView(self.client, ctx.author.id)
            message = await ctx.send(embed=embed, view=view)
            view.message = message

        except Exception as e:
            await ctx.maybe_reply(f"{DVB_FALSE} Error retrieving task status: {str(e)}")

    @tasks.loop(seconds=5)
    async def amari_import_task(self):
        """Background task that processes Amari import requests"""
        await self.client.wait_until_ready()
        await self.task_processor.process_tasks()

    @amari_import_task.error
    async def amari_import_task_error(self, error):
        error_embed = discord.Embed(title=f"Error in amari import task",
                                    description=box(print_exception("", error)), color=discord.Color.red())
        await self.client.error_channel.send(embed=error_embed)
        tasks = await self.amari_import_dao.fetchAllTasksInQueue()
        first_task = tasks[0] if tasks else None
        if first_task and first_task.status == "IN_PROGRESS":
            try:
                task_ticket_channel = self.client.get_channel(first_task.ticket_channel_id) or await self.client.fetch_channel(first_task.ticket_channel_id)
            except Exception as e:
                task_ticket_channel = None
            await self.task_processor._mark_task_failed(
                first_task, task_ticket_channel, print_exception("Indirect task processing failed due to the following exception", error),
                user_friendly_error="The Amari transfer task has failed due to an unexpected error. Please try again later."
            )



    @checks.dev()
    @amaritransfer.command(name="queue")
    async def amaritransfer_queue(self, ctx: DVVTcontext):
        """View the first 10 tasks currently in the Amari transfer queue."""
        tasks = await self.amari_import_dao.fetchAllTasksInQueue()
        if not tasks:
            return await ctx.maybe_reply(f"{DVB_FALSE} The Amari transfer queue is currently empty.")

        embed = AmariImportEmbed(
            title="Amari Transfer Queue",
            description=f"Showing the first **{min(10, len(tasks))}** of **{len(tasks)}** tasks in the queue."
        )

        for i, task in enumerate(tasks[:10], start=1):
            user_mention = f"<@{task.user_id}>"
            created = f"<t:{int(task.created_at.timestamp())}:R>"
            status_config = EmbedFormatter._get_status_config(task.status)
            embed.add_field(
                name=f"{i}. Task #{task.id} {status_config.get('emoji', '❓')} {status_config.get('name')}",
                value=(
                    f"User: {user_mention} (`{task.user_id}`)\n"
                    f"XP to Add: `{comma_number(task.amari_xp_to_add)} XP`\n"
                    f"Expected Level: `{comma_number(task.expected_amari_level)}`\n"
                    f"Expected Total XP: `{comma_number(task.expected_total_amari_xp)} XP`\n"
                    f"Created: {created}\n"
                    f"Position: `{task.position}`"
                ),
                inline=False
            )

        embed.set_footer(text="Use amaritransfer view <ID> to see more details about a task.")
        await ctx.send(embed=embed)


def setup(bot):
    """Setup function for the cog"""
    bot.add_cog(AmariImport(bot))