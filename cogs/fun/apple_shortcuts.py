import json
from typing import Union, List

import discord
from aiohttp import web
from discord import SlashCommandGroup, option
from discord.ext import commands
import secrets
import server
from datetime import datetime
import alexflipnote

from main import dvvt
from utils.context import DVVTcontext

class ShortcutsDevice:
    def __init__(self, record):
        self.id: int = record["id"]
        self.device_name: str = record["device_name"]
        self.device_model: str = record["device_model"]
        self.guild_id: int = record["guild_id"]
        self.user_id: int = record["user_id"]
        self.created_at: datetime = record["created_at"]
        self.updated_at: Union[datetime, None] = record["updated_at"]
        self.actions: List[ShortcutsDeviceAction] = []

class ShortcutsDeviceAction:
    def __init__(self, record):
        self.id: int = record["id"]
        self.device_id: str = record["device_id"]
        self.action_type: str = record["action_type"]
        self.action_name: Union[str, None] = record["action_name"]
        self.simple_value: Union[str, None] = record["simple_value"]
        self.extra_data: Union[dict, None] = json.loads(record["extra_data"]) if record["extra_data"] else None
        self.created_at: datetime = record["created_at"]
        self.updated_at: Union[datetime, None] = record["updated_at"]




class AppleShortcuts(commands.Cog):
    def __init__(self, client: dvvt):
        self.client = client
        self.server = client.server
        self.alex_api = alexflipnote.Client()

    async def fetch_all_devices_for_user_id(self, user_id: int) -> List[ShortcutsDevice]:
        records = await self.client.db.fetch("SELECT * FROM shortcuts_devices WHERE user_id = $1", user_id)
        devices = []
        for record in records:
            device = ShortcutsDevice(record)
            actions = await self.client.db.fetch("SELECT * FROM shortcuts_device_actions WHERE device_id = $1 ORDER BY id", device.id)
            for action_record in actions:
                action = ShortcutsDeviceAction(action_record)
                device.actions.append(action)
            devices.append(device)
        return devices

    async def fetch_device_by_token(self, token: str) -> Union[ShortcutsDevice, None]:
        record = await self.client.db.fetchrow("SELECT * FROM shortcuts_devices WHERE token = $1", token)
        if not record:
            return None
        device = ShortcutsDevice(record)
        actions = await self.client.db.fetch("SELECT * FROM shortcuts_device_actions WHERE device_id = $1 ORDER BY id", device.id)
        for action_record in actions:
            action = ShortcutsDeviceAction(action_record)
            device.actions.append(action)
        return device

    @server.add_route(path="/api/shortcuts/battery_status", method="POST", cog="fun")
    async def receive_battery_status(self, request: web.Request):
        token = request.headers.get("Authorization")
        if token is None:
            return web.Response(status=401, text="Unauthorized")
        token = token.replace("shortcuts_", "")
        device = await self.fetch_device_by_token(token)
        if not device:
            return web.Response(status=403, text="Forbidden")
        data = await request.json()
        if not isinstance(data, dict):
            return web.Response(status=400, text="Bad Request: Expected JSON object")
        if "pct" not in data or "pwr" not in data or "model" not in data:
            return web.Response(status=400, text="Bad Request")
        percentage: int = data.get("pct")
        if not isinstance(percentage, int) or percentage < 0 or percentage > 100:
            return web.Response(status=400, text="Bad Request")
        power: bool = data.get("pwr")
        if not isinstance(power, bool):
            return web.Response(status=400, text="Bad Request")
        model: str = data.get("model")
        if not isinstance(model, str) or len(model) > 50:
            model = "Device"
        guild = self.client.get_guild(device.guild_id)
        if guild:
            member = guild.get_member(device.user_id)
            if member:
                role_male = discord.utils.get(member.roles, id=1325161462494134292)
                role_female = discord.utils.get(member.roles, id=1325161531775651900)
                pronoun = "his" if role_male else "her" if role_female else "their"
                title = f"{member.display_name} just plugged in {pronoun} {model}." if power else f"{member.display_name} just unplugged {pronoun} {model}."
                description = f"## **Battery:** {percentage}%"

                embed = discord.Embed(description=description, color=self.client.embed_color)

                embed.set_footer(icon_url="https://cdn.jim-nielsen.com/ios/512/shortcuts-2018-10-03.png?rf=1024", text="Shortcuts")
                embed.set_author(name=title, icon_url=member.display_avatar.with_size(128).url)
                battery_image = await self.alex_api.battery_ios(percentage, power)
                battery_img_bytes = await battery_image.read()
                filename = f"battery_{percentage}_{power}.png"
                file = discord.File(fp=battery_img_bytes, filename=filename)
                embed.set_thumbnail(url=f"attachment://{filename}")
                if device.actions:
                    last_action = device.actions[-1]
                    if last_action.extra_data:
                        last_power_state = last_action.extra_data.get("pwr")
                        last_percentage = last_action.extra_data.get("pct")
                        if last_power_state:
                            embed.description += f"\n{member.display_name}'s {model} **started** charging at **{last_percentage}%** {discord.utils.format_dt(last_action.created_at, 'R')}."
                        else:
                            embed.description += f"\n{member.display_name}'s {model} **stopped** charging at **{last_percentage}%** {discord.utils.format_dt(last_action.created_at, 'R')}."
                channel = None
                if guild.id == 1288032530569625660:
                    channel = guild.get_channel(1288032530569625663)
                elif guild.id == 871734809154707467:
                    channel = guild.get_channel(871737314831908974)
                if channel:
                    await channel.send(embed=embed, file=file)
                    await self.client.db.execute(
                        "INSERT INTO shortcuts_device_actions (device_id, action_type, action_name, simple_value, extra_data) VALUES ($1, $2, $3, $4, $5)",
                        device.id, "battery", "charge" if power else "discharge", f"{percentage}", json.dumps(data)
                    )
        return web.Response(status=204)

    shortcuts_devices_group = SlashCommandGroup("shortcutsdevices", "Manage devices linked to Shortcuts automtation.")

    @shortcuts_devices_group.command(name="list")
    async def shortcuts_devices_management(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(color=self.client.embed_color).set_author(name=f"{self.client.user.display_name}'s Devices", icon_url=self.client.user.display_avatar.with_size(128).url)
        devices = await self.fetch_all_devices_for_user_id(ctx.author.id)
        if not devices:
            embed.description = "You have no devices registered."
        else:
            for index, device in enumerate(devices, start=1):
                last_action_str = ""
                if device.actions:
                    last_action = device.actions[-1]
                    last_action_str = f"Last action: {last_action.action_name or last_action.action_type} at {discord.utils.format_dt(last_action.created_at)}"
                embed.add_field(
                    name=f"{index}. " + device.device_name + f" ({device.device_model})",
                    value=f"Created: {discord.utils.format_dt(device.created_at)}\n{last_action_str}",
                    inline=False
                )
        await ctx.respond(embed=embed)

    @shortcuts_devices_group.command(name="add")
    @option("device_type", description="Select a supported device type.", choices=["iPhone", "iPad", "Mac"])
    async def shortcuts_add_device(self, ctx: discord.ApplicationContext, device_name: str, device_type: str):
        if len(device_name) > 50:
            return await ctx.respond("Device name cannot be longer than 50 characters.", ephemeral=True)

        device_token = secrets.token_urlsafe(32)
        await self.client.db.execute(
            "INSERT INTO shortcuts_devices (token, device_name, device_model, guild_id, user_id) VALUES ($1, $2, $3, $4, $5)",
            device_token, device_name, device_type, ctx.guild.id, ctx.author.id
        )
        await ctx.respond(f"Device **{device_name}** added successfully. Your token for the device is below, copy it as you will not see it again.", ephemeral=True)
        await ctx.respond(device_token, ephemeral=True)

    @shortcuts_devices_group.command(name="remove")
    async def shortcuts_remove_device(self, ctx: discord.ApplicationContext, device_id: int):
        device = await self.client.db.fetchrow("SELECT * FROM shortcuts_devices WHERE id = $1 AND user_id = $2", device_id, ctx.author.id)
        if not device:
            return await ctx.respond("Device not found or you do not have permission to remove it.", ephemeral=True)

        await self.client.db.execute("DELETE FROM shortcuts_devices WHERE id = $1", device_id)
        await self.client.db.execute("DELETE FROM shortcuts_device_actions WHERE device_id = $1", device_id)
        await ctx.respond(f"Device **{device['device_name']}** removed successfully.", ephemeral=True)

