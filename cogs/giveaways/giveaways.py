import contextlib
import os
import random
import typing
import asyncio
from collections import Counter
from time import time, perf_counter
from datetime import datetime

import discord
from discord import SlashCommandGroup
from discord.ext import commands, tasks, menus, pages

import cogs.giveaways
from cogs.giveaways.giveaway_utils import *
from main import dvvt

from utils import checks
from utils.buttons import confirm
from utils.context import DVVTcontext
from utils.converters import BetterBetterRoles
from utils.menus import CustomMenu
from utils.time import humanize_timedelta
from utils.errors import ArgumentBaseError
from utils.format import plural, stringtime_duration, grammarformat, human_join

voteid = 874897331252760586 if os.getenv('state') == '1' else 683884762997587998
level_100id = 943883531573157889 if os.getenv('state') == '1' else 717120742512394323


DVB_True = "<:DVB_True:887589686808309791>"
DVB_False = "<:DVB_False:887589731515392000>"
DVB_Neutral = "<:DVB_Neutral:887589643686670366>"


class GiveawayList(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=menu.ctx.bot.embed_color, timestamp=discord.utils.utcnow())
        for entry in entries:
            embed.add_field(name=f"{entry[0]}", value=entry[1], inline=False)
        embed.set_footer(text=f"{len(entries)} giveaways | Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed

class ListMultis(discord.ui.Select):
    def __init__(self, list_of_roles:list):
        self.list_of_roles = list_of_roles
        self.role_id = None
        options = []
        options.append(discord.SelectOption(label="Add a new multi", value="add_multi", description="Add a new entry multi for a role.", emoji="➕"))
        for role, multi in self.list_of_roles:
            options.append(discord.SelectOption(label=f"{role.name} - {multi} extra entries", value=str(role.id), description=f"Edit this role's entry multi or delete it.", emoji="✏️"))
        super().__init__(placeholder="Select a role to edit...",
                         min_values = 1,
                         max_values = 1,
                         options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "add_multi":
            self.role_id = "add_multi"
        else:
            try:
                self.role_id = int(self.values[0])
            except ValueError:
                pass
        self.view.result = self.role_id
        await interaction.response.defer()
        self.view.stop()

class ChooseMultiFromList(discord.ui.View):
    def __init__(self, list_of_roles, user):
        self.list_of_roles = list_of_roles
        self.user = user
        self.result = None
        self.response = None
        super().__init__(timeout=45)

        self.add_item(ListMultis(self.list_of_roles))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(embed = discord.Embed(description="Only the author (`{}`) can interact with this message.".format(self.user), color=discord.Color.red()), ephemeral=True)
            return False
        else:
            return True

    async def on_timeout(self):
        self.result = None

class EditOrDeleteMultiEntry(discord.ui.View):
    def __init__(self, user):
        self.value = None
        self.user = user
        super().__init__(timeout=30)

    @discord.ui.button(label="Edit Multi", emoji="✏️", style=discord.ButtonStyle.grey)
    async def edit_multi(self, button: discord.Button, interaction: discord.Interaction):
        self.value = "edit"
        self.stop()

    @discord.ui.button(label="Delete Role's Multi", emoji="🗑", style=discord.ButtonStyle.red)
    async def delete_role(self, button: discord.Button, interaction: discord.Interaction):
        self.value = "delete"
        self.stop()

    async def on_timeout(self):
        self.value = None
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(embed = discord.Embed(description="Only the author (`{}`) can interact with this message.".format(self.user), color=discord.Color.red()), ephemeral=True)
            return False
        return True



class GiveawayConfigCategories(discord.ui.View):
    def __init__(self, client: dvvt, channel: discord.TextChannel, original_embed: discord.Embed, ctx: DVVTcontext):
        self.client: dvvt = client
        self.channel: discord.TextChannel = channel
        self.original_embed: discord.Embed = original_embed
        self.ctx: DVVTcontext = ctx
        self.response: discord.Message = None
        super().__init__(timeout=30)


    @discord.ui.button(style=discord.ButtonStyle.grey, label="Edit bypass roles", disabled = False)
    async def edit_bypass_roles(self, button: discord.ui.Button, interaction: discord.Interaction):
        bypass_roles = await self.client.db.fetchval("SELECT bypass_roles FROM giveawayconfig WHERE guild_id = $1 AND channel_id = $2", self.ctx.guild.id, self.channel.id)
        print(bypass_roles)
        if bypass_roles is None:
            bypass_roles = []
        else:
            bypass_roles = split_string_into_list(bypass_roles, return_type=int)
        print(bypass_roles)
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item == button:
                    item.style = discord.ButtonStyle.green
            item.disabled = True
        await interaction.response.edit_message(view=self)
        add_remove_view = AddOrRemoveView()
        add_remove_view.response = await self.ctx.send("Are you going to **add** or **remove** bypass roles?", view=add_remove_view)
        await add_remove_view.wait()
        if add_remove_view.value is None:
            pass
        else:
            if add_remove_view.value == "add":
                draft_msg = await self.ctx.send(f"Please enter the roles you want to be able to bypass the giveaway.\nYou can input multiple roles, but roles must be **separated by a comma**. Just enter them like how you would do with `dv.roleinfo`.\nExample:\n    -`@RoleMention, @RoleMention , @RoleMention`\n    -`roleid , roleid , roleid`\n    -`\"role name\", \"role name\", \"role name\"`\n\n")
            else:
                draft_msg = await self.ctx.send(f"Please enter the roles you want to be **removed** from the bypass list.\nYou can input multiple roles, but roles must be **separated by a comma**. Just enter them like how you would do with `dv.roleinfo`.\nExample:\n    -`@RoleMention, @RoleMention , @RoleMention`\n    -`roleid , roleid , roleid`\n    -`\"role name\", \"role name\", \"role name\"`\n\n")
            def check(m: discord.Message):
                return m.author == self.ctx.author and m.channel == self.ctx.channel
            try:
                input_msg = await self.client.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                await self.ctx.send("You took too long to respond.", delete_after=5.0)
            else:
                input_bypass_roles = split_string_into_list(input_msg.content, return_type=str)
                if len(input_bypass_roles) < 1:
                    await self.ctx.send("You didn't input any roles.")
                else:
                    converted_roles = []
                    invalid_roles = []
                    for unconverted_obj in input_bypass_roles:
                        try:
                            result_role = await BetterBetterRoles().convert(self.ctx, unconverted_obj)
                        except Exception as e:
                            invalid_roles.append((unconverted_obj, "Invalid role"))
                        else:
                            if result_role is not None:
                                if add_remove_view.value == "add":
                                    print(result_role.id, bypass_roles)
                                    if result_role.id in bypass_roles:
                                        invalid_roles.append((f"{result_role.name} - {result_role.id}", "Already in list of bypassed roles"))
                                    else:
                                        converted_roles.append(result_role.id)
                                elif add_remove_view.value == "remove":
                                    if result_role.id not in bypass_roles:
                                        invalid_roles.append((f"{result_role.name} - {result_role.id}", "Not in list of bypassed roles"))
                                    else:
                                        converted_roles.append(result_role.id)
                            else:
                                invalid_roles.append((unconverted_obj, "Invalid role"))
                    await input_msg.delete()
                    summary = ""
                    if len(converted_roles) == 0:
                        summary += "<:DVB_Neutral:887589643686670366> WARNING: You didn't input any valid roles.\n"
                    if add_remove_view.value == "add":
                        bypass_roles.extend(converted_roles)
                    elif add_remove_view.value == "remove":
                        for role in converted_roles:
                            if role in bypass_roles:
                                bypass_roles.remove(role)
                    bypass_roles_lst = bypass_roles
                    bypass_roles = ",".join([str(ob) for ob in bypass_roles_lst])
                    await self.client.db.execute("INSERT INTO giveawayconfig(guild_id, channel_id, bypass_roles) VALUES($1, $2, $3) ON CONFLICT(channel_id) DO UPDATE SET bypass_roles=$3", self.ctx.guild.id, self.channel.id, bypass_roles)
                    field_value = ", ".join([f"<@&{role}>" for role in bypass_roles_lst])
                    self.original_embed.set_field_at(0, name="Bypass Roles", value=field_value if len(field_value) > 0 else "None")
                    summary = "<:DVB_True:887589686808309791> **Successfully updated!**\n" + summary
                    if len(invalid_roles) > 0:
                        list_of_invalid_roles = "\n".join([f"`{role_name}` - {reason}" for role_name, reason in invalid_roles])
                        summary += f"\nI could not add/remove these roles:\n{list_of_invalid_roles}"
                    await self.ctx.send(summary)
            await draft_msg.delete()
        if button.style == discord.ButtonStyle.grey: # if the buttons were disabled due to timeout, do not enable them again
            pass
        else:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = False
                    item.style = discord.ButtonStyle.grey
        await self.response.edit(embed=self.original_embed, view=self)


    @discord.ui.button(style=discord.ButtonStyle.grey, label="Edit Blacklisted roles", disabled=False)
    async def edit_blacklisted_roles(self, button: discord.ui.Button, interaction: discord.Interaction):
        blacklisted_roles = await self.client.db.fetchval("SELECT blacklisted_roles FROM giveawayconfig WHERE guild_id = $1 AND channel_id = $2", self.ctx.guild.id, self.channel.id)
        print(blacklisted_roles)
        if blacklisted_roles is None:
            blacklisted_roles = []
        else:
            blacklisted_roles = split_string_into_list(blacklisted_roles, return_type=int)
        print(blacklisted_roles)
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item == button:
                    item.style = discord.ButtonStyle.green
            item.disabled = True
        await interaction.response.edit_message(view=self)
        add_remove_view = AddOrRemoveView()
        add_remove_view.response = await self.ctx.send("Are you going to **add** or **remove** blacklisted roles?", view=add_remove_view)
        await add_remove_view.wait()
        if add_remove_view.value is None:
            pass
        else:
            if add_remove_view.value == "add":
                draft_msg = await self.ctx.send(f"Please enter the roles you want blacklisted from entering giveaways in this channel.\nYou can input multiple roles, but roles must be **separated by a comma**. Just enter them like how you would do with `dv.roleinfo`.\nExample:\n    -`@RoleMention, @RoleMention , @RoleMention`\n    -`roleid , roleid , roleid`\n    -`\"role name\", \"role name\", \"role name\"`\n\n")
            else:
                draft_msg = await self.ctx.send(f"Please enter the roles you want to be **removed** from the blacklisted roles list.\nYou can input multiple roles, but roles must be **separated by a comma**. Just enter them like how you would do with `dv.roleinfo`.\nExample:\n    -`@RoleMention, @RoleMention , @RoleMention`\n    -`roleid , roleid , roleid`\n    -`\"role name\", \"role name\", \"role name\"`\n\n")

            def check(m: discord.Message):
                return m.author == self.ctx.author and m.channel == self.ctx.channel

            try:
                input_msg = await self.client.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                await self.ctx.send("You took too long to respond.", delete_after=5.0)
            else:
                input_blacklisted_roles = split_string_into_list(input_msg.content, return_type=str)
                if len(input_blacklisted_roles) < 1:
                    await self.ctx.send("You didn't input any roles.")
                else:
                    converted_roles = []
                    invalid_roles = []
                    for unconverted_obj in input_blacklisted_roles:
                        try:
                            result_role = await BetterBetterRoles().convert(self.ctx, unconverted_obj)
                        except Exception as e:
                            invalid_roles.append((unconverted_obj, "Invalid role"))
                        else:
                            if result_role is not None:
                                if add_remove_view.value == "add":
                                    print(result_role.id, blacklisted_roles)
                                    if result_role.id in blacklisted_roles:
                                        invalid_roles.append((f"{result_role.name} - {result_role.id}", "Already in list of blacklisted roles"))
                                    else:
                                        converted_roles.append(result_role.id)
                                elif add_remove_view.value == "remove":
                                    if result_role.id not in blacklisted_roles:
                                        invalid_roles.append((f"{result_role.name} - {result_role.id}", "Not in list of blacklisted roles"))
                                    else:
                                        converted_roles.append(result_role.id)
                            else:
                                invalid_roles.append((unconverted_obj, "Invalid role"))
                    await input_msg.delete()
                    summary = ""
                    if len(converted_roles) == 0:
                        summary += "<:DVB_Neutral:887589643686670366> WARNING: You didn't input any valid roles.\n"
                    if add_remove_view.value == "add":
                        blacklisted_roles.extend(converted_roles)
                    elif add_remove_view.value == "remove":
                        for role in converted_roles:
                            if role in blacklisted_roles:
                                blacklisted_roles.remove(role)
                    blacklisted_roles_lst = blacklisted_roles
                    blacklisted_roles = ",".join([str(ob) for ob in blacklisted_roles_lst])
                    await self.client.db.execute("INSERT INTO giveawayconfig(guild_id, channel_id, blacklisted_roles) VALUES($1, $2, $3) ON CONFLICT(channel_id) DO UPDATE SET blacklisted_roles=$3", self.ctx.guild.id, self.channel.id, blacklisted_roles)
                    field_value = ", ".join([f"<@&{role}>" for role in blacklisted_roles_lst])
                    self.original_embed.set_field_at(1, name="Blacklisted Roles", value=field_value if len(field_value) > 0 else "None")
                    summary = "<:DVB_True:887589686808309791> **Successfully updated!**\n" + summary
                    if len(invalid_roles) > 0:
                        list_of_invalid_roles = "\n".join([f"`{role_name}` - {reason}" for role_name, reason in invalid_roles])
                        summary += f"\nI could not add/remove these roles:\n{list_of_invalid_roles}"
                    await self.ctx.send(summary)
            await draft_msg.delete()
        if button.style == discord.ButtonStyle.grey: # if the buttons were disabled due to timeout, do not enable them again
            pass
        else:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = False
                    item.style = discord.ButtonStyle.grey
        await self.response.edit(embed=self.original_embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.grey, label="Edit Multi Roles", disabled=False)
    async def edit_multi(self, button: discord.ui.Button, interaction: discord.Interaction):
        multi = await self.client.db.fetchval("SELECT multi FROM giveawayconfig WHERE guild_id = $1 AND channel_id = $2", self.ctx.guild.id, self.channel.id)
        if multi is None:
            multi = {}
        else:
            multi = json.loads(multi)
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item == button:
                    item.style = discord.ButtonStyle.green
            item.disabled = True
        await interaction.response.edit_message(view=self)
        multi_list = []
        if len(multi) > 0:
            multi_list = []
            for role_id, multi_count in multi.items():
                if (multi_role := self.ctx.guild.get_role(int(role_id))) is not None:
                    multi_list.append((multi_role, multi_count))
        select_multi_view = ChooseMultiFromList(multi_list, interaction.user)
        embed = discord.Embed(title="Choose Multi Roles", description="Choose the multi roles you want to edit/remove, or add a new one.", color=self.client.embed_color)
        select_multi_view.response = await self.ctx.send(embed=embed, view=select_multi_view)
        await select_multi_view.wait()
        for b in select_multi_view.children:
            b.disabled = True
        if select_multi_view.result is None:
            pass
        elif type(select_multi_view.result) == int:
            r = self.ctx.guild.get_role(select_multi_view.result)
            if r is None:
                await self.ctx.send("Role not found.")
            else:
                embed.description = f"You selected **{r.name}**.\n\nChoose an option below."
                choose_edit_or_delete = EditOrDeleteMultiEntry(self.ctx.author)
                await select_multi_view.response.edit(embed=embed, view=choose_edit_or_delete)
                await choose_edit_or_delete.wait()
                print(choose_edit_or_delete.value)
                if choose_edit_or_delete.value is None:
                    pass
                elif choose_edit_or_delete.value == "edit":
                    await self.ctx.send("You requested to edit the role")
                elif choose_edit_or_delete.value == "delete":
                    multi.pop(str(r.id))
                    await self.client.db.execute("INSERT INTO giveawayconfig (guild_id, channel_id, multi) VALUES ($1, $2, $3) ON CONFLICT (channel_id) DO UPDATE SET multi = $3", self.ctx.guild.id, self.channel.id, json.dumps(multi))
                    await self.ctx.send("<:DVB_True:887589686808309791> **Successfully updated!**")
                for b in choose_edit_or_delete.children:
                    b.disabled = True
                await select_multi_view.response.edit(view=choose_edit_or_delete)
        else:
            if select_multi_view.result == "add_multi":
                embed.description += f"\nRole selected: **Add Multi Role**."
            await select_multi_view.response.edit(embed=embed, view=select_multi_view)

        multi_role_list = []
        for multi_role_id in multi:
            if (multi_role := self.ctx.guild.get_role(int(multi_role_id))) is not None:
                multi_role_list.append(f" - {multi_role.mention} x{multi[multi_role_id]}")
        if len(multi_role_list) > 0:
            self.original_embed.set_field_at(index=2, name="Multi Roles", value="\n".join(multi_role_list), inline=False)
        else:
            self.original_embed.set_field_at(index=2, name="Multi Roles", value="None", inline=False)

        if button.style == discord.ButtonStyle.grey:  # if the buttons were disabled due to timeout, do not enable them again
            pass
        else:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = False
                    item.style = discord.ButtonStyle.grey
        await self.response.edit(embed=self.original_embed, view=self)

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
                item.style = discord.ButtonStyle.grey
        await self.response.edit(embed=self.original_embed, view=self)
        await self.response.reply("This message has timed out. If you need to continue editing the giveaway configuration, please run the command again.")

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(embed = discord.Embed(description="Only the author (`{}`) can interact with this message.".format(self.ctx.author), color=discord.Color.red()), ephemeral=True)
            return False
        else:
            return True


class MultiEntryView(discord.ui.View):
    def __init__(self, giveawaymessage_id, cog, client, embed):
        self.giveawaymessage_id = giveawaymessage_id
        self.cog = cog
        self.client = client
        self.embed = embed
        super().__init__(timeout=None)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str("<:leave:893542866071203910>"), label="Leave Giveaway", style=discord.ButtonStyle.red)
    async def LeaveGiveaway(self, button: discord.ui.Button, interaction: discord.Interaction):
        entries = await self.cog.fetch_user_entries(interaction.user.id, self.giveawaymessage_id)
        if len(entries) > 0:
            await self.client.db.execute("DELETE FROM giveawayentrants WHERE user_id = $1 AND message_id = $2", interaction.user.id, self.giveawaymessage_id)
            await interaction.response.send_message(f"You have left the giveaway, and your `{len(entries)}` entries have been removed.", ephemeral=True)
        else:
            await interaction.response.send_message(f"You have already left the giveaway.", ephemeral=True)

    @discord.ui.button(label="View your entries", style=discord.ButtonStyle.green)
    async def ViewEntries(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.edit_original_message(embed=self.embed)


class SingleEntryView(discord.ui.View):
    def __init__(self, giveawaymessage_id, cog, client):
        self.giveawaymessage_id = giveawaymessage_id
        self.cog = cog
        self.client = client
        super().__init__(timeout=None)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str("<:leave:893542866071203910>"), label="Leave Giveaway", style=discord.ButtonStyle.red)
    async def LeaveGiveaway(self, button: discord.ui.Button, interaction: discord.Interaction):
        entries = await self.cog.fetch_user_entries(interaction.user.id, self.giveawaymessage_id)
        if len(entries) > 0:
            await self.client.db.execute("DELETE FROM giveawayentrants WHERE user_id = $1 AND message_id = $2", interaction.user.id, self.giveawaymessage_id)
            await interaction.response.send_message(f"You have left the giveaway, and your `{len(entries)}` entries have been removed.", ephemeral=True)
        else:
            await interaction.response.send_message(f"You have already left the giveaway.", ephemeral=True)


class GiveawayEndView(discord.ui.View):
    def __init__(self, url, user: typing.Optional[typing.Any] = None):
        self.user = user
        self.url = url
        super().__init__(timeout=None)
        if self.user is not None:
            self.add_item(discord.ui.Button(label=f"View {user}'s Giveaway", url=self.url, disabled=False))
        else:
            self.add_item(discord.ui.Button(label=f"View Giveaway", url=self.url, disabled=False))



class GiveawayView(discord.ui.View):
    def __init__(self, client, cog):
        self.cog: cogs.giveaways.giveaways = cog
        self.client: dvvt = client
        super().__init__(timeout=None)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str("<a:dv_iconOwO:837943874973466664>"), label="Join giveaway", style=discord.ButtonStyle.green, custom_id="dvb:giveawayjoin")
    async def JoinGiveaway(self, button: discord.ui.Button, interaction: discord.Interaction):
        giveawaymessage = interaction.message
        giveawayentry = await self.cog.fetch_giveaway(giveawaymessage.id)
        if len(giveawayentry.multi.keys()) > 0:
            giveaway_uses_multiple_entries = True
        else:
            giveaway_uses_multiple_entries = False
        entries_to_insert = []
        if giveawayentry.active:
            entered = False
            user_entries = await self.cog.fetch_user_entries(interaction.user.id, giveawaymessage.id)
            summary_embed = discord.Embed(color=self.client.embed_color)
            if giveaway_uses_multiple_entries:
                entries = Counter(entry.get('entrytype') for entry in user_entries)
                entry_list = []
                entry_list.append({'role_id': 0, 'allowed_entries': 1, 'valid_role': True, 'entered_entries':entries.get(0, 0)})
                for role_id, multi_count in giveawayentry.multi.items():
                    role_id = int(role_id)
                    role = interaction.guild.get_role(role_id)
                    if role is None:
                        entry_list.append({'role_id': role_id, 'allowed_entries': 0, 'valid_role': False, 'entered_entries': entries.get(role_id, 0)})
                    else:
                        entry_list.append({'role_id': role_id, 'allowed_entries': multi_count, 'valid_role': True, 'entered_entries': entries.get(role_id, 0)})
                descriptions = []
                for entry_dict in entry_list:
                    newly_entered_entries = 0
                    if entry_dict['valid_role'] is True:
                        if entry_dict['entered_entries'] < entry_dict['allowed_entries']:
                            if entry_dict['role_id'] == 0:
                                print(giveawayentry.required_roles)
                                if len(giveawayentry.required_roles) > 0:
                                    print('giveaway has required roles')
                                    missing_roles = []
                                    for r_id in giveawayentry.required_roles:
                                        if not discord.utils.get(interaction.user.roles, id=r_id):
                                            missing_roles.append(f"<@&{r_id}>")

                                        else:
                                            print('user has role')
                                    print(missing_roles)
                                    if len(missing_roles) > 0:
                                        return await interaction.response.send_message(f"<:DVB_False:887589731515392000> You do not have the following roles to join this giveaway: {', '.join(missing_roles)}", ephemeral=True)
                                entered = True
                                for i in range(entry_dict['allowed_entries'] - entry_dict['entered_entries']):
                                    entries_to_insert.append((giveawaymessage.id, interaction.user.id, entry_dict['role_id']))
                                    newly_entered_entries += 1
                                string = f"{DVB_True} **{entry_dict['entered_entries'] + newly_entered_entries}**/{entry_dict['allowed_entries']} Normal Entry" + (f" (`+{newly_entered_entries}`)" if newly_entered_entries > 0 else "")
                            else:
                                entered = True
                                role = interaction.guild.get_role(entry_dict['role_id'])
                                if role in interaction.user.roles:
                                    for i in range(entry_dict['allowed_entries'] - entry_dict['entered_entries']):
                                        entries_to_insert.append((giveawaymessage.id, interaction.user.id, entry_dict['role_id']))
                                        newly_entered_entries += 1
                                    string = f"{DVB_True} **{entry_dict['entered_entries'] + newly_entered_entries}**/{entry_dict['allowed_entries']} Entries for being {role.mention}" + (f" (`+{newly_entered_entries}`)" if newly_entered_entries > 0 else "")
                                else:
                                    string = f"{DVB_Neutral} **{entry_dict['entered_entries']}**/{entry_dict['allowed_entries']} Entries for being {role.name} (You don't have the role)"
                        else:
                            if entry_dict['allowed_entries'] > 0:
                                if entry_dict['role_id'] == 0:
                                    string = f"{DVB_True} **{entry_dict['entered_entries']}**/{entry_dict['allowed_entries']} Normal Entry"
                                else:
                                    role = interaction.guild.get_role(entry_dict['role_id'])
                                    if role in interaction.user.roles:
                                        string = f"{DVB_True} **{entry_dict['entered_entries']}**/{entry_dict['allowed_entries']} Entries for being {role.mention}"
                                    else:
                                        string = f"{DVB_Neutral} **{entry_dict['entered_entries']}**/{entry_dict['allowed_entries']} Entries for being {role.name} (You don't have the role)"
                            else:
                                string = ""
                    else:
                        string = f"{DVB_False} **{entry_dict['entered_entries']}**/{entry_dict['allowed_entries']} Invalid role ({entry_dict['role_id']})"
                    if len(string) > 0:
                        descriptions.append(string)
                summary_embed.description = "\n".join(descriptions)
                final_number_of_entries = len(await self.cog.fetch_user_entries(interaction.user.id, giveawaymessage.id))
                summary_embed.set_footer(text=f"Your total entries: {final_number_of_entries}")
            else:
                if len(user_entries) > 0:
                    summary_embed.description = f"Your total entries: {len(user_entries)}"
                else:
                    if len(giveawayentry.required_roles) > 0:
                        print('giveaway has required roles')
                        missing_roles = []
                        for r_id in giveawayentry.required_roles:
                            if not discord.utils.get(interaction.user.roles, id=r_id):
                                missing_roles.append(f"<@&{r_id}>")

                            else:
                                print('user has role')
                        print(missing_roles)
                        if len(missing_roles) > 0:
                            return await interaction.response.send_message(f"<:DVB_False:887589731515392000> You do not have the required roles to join this giveaway: {', '.join(missing_roles)}", ephemeral=True)
                    entries_to_insert.append((giveawaymessage.id, interaction.user.id, 0))
                    entered = True
                summary_embed.description = f"Your total entries: 1"
            if entered is True:
                content = "You have successfully entered the giveaway!"
                await self.client.db.executemany("INSERT INTO giveawayentrants VALUES($1, $2, $3)", entries_to_insert)
            else:
                content = "You have already entered the giveaway."
            final_number_of_entries = len(await self.cog.fetch_user_entries(interaction.user.id, giveawaymessage.id))
            if giveaway_uses_multiple_entries is True:
                summary_embed.set_footer(text=f"Your total entries: {final_number_of_entries}")
                await interaction.response.send_message(content, embed=summary_embed, view=SingleEntryView(giveawaymessage.id, self.cog, self.client), ephemeral=True)
            else:
                summary_embed.description = f"Your total entries: {final_number_of_entries}"

        else:
            return await interaction.response.send_message("It appears that this giveaway doesn't exist or has ended.", ephemeral=True)


class AddOrRemoveView(discord.ui.View):
    def __init__(self):
        self.response: discord.Message = None
        self.value = None
        super().__init__(timeout=20)

    @discord.ui.button(style=discord.ButtonStyle.green, label="Add Roles")
    async def add_button(self, nested_button: discord.ui.Button, nested_interaction: discord.Interaction):
        self.value = "add"
        await self.response.delete()
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Remove Roles")
    async def remove_button(self, nested_button: discord.ui.Button, nested_interaction: discord.Interaction):
        self.value = "remove"
        await self.response.delete()
        self.stop()

    async def on_timeout(self) -> None:
        await self.response.delete()
        self.stop()


class giveaways(commands.Cog):
    """
    Giveaway commands
    """
    def __init__(self, client):
        self.client: dvvt = client
        self.giveawayview_added = False
        self.change_entrantcount.start()
        self.check_giveaways.start()
        self.dm_queue = []
        self.process_dms.start()

    @tasks.loop(seconds=1)
    async def process_dms(self):
        if len(self.dm_queue) > 0:
            while len(self.dm_queue) > 0:
                # example item in queue: (user_id, content, embed, view)
                user, content, embed, view = self.dm_queue.pop(0)
                try:
                    await user.send(content, embed=embed, view=view)
                except Exception as e:
                    print(e)

    async def fetch_user_entries(self, user_id, message_id):
        return await self.client.db.fetch("SELECT * FROM giveawayentrants WHERE user_id = $1 and message_id = $2", user_id, message_id)

    async def end_giveaway(self, g_entry: GiveawayEntry):
        guild: discord.Guild = self.client.get_guild(g_entry.guild_id)
        if guild is not None:
            channel = guild.get_channel(g_entry.channel_id)
            if channel is not None:
                try:
                    gawmessage = await channel.fetch_message(g_entry.message_id)
                except:
                    raise GiveawayMessageNotFound
                else:
                    entrant_no = await self.client.db.fetchval("SELECT COUNT(DISTINCT user_id) FROM giveawayentrants WHERE message_id = $1", g_entry.message_id)
                    view = discord.ui.View.from_message(gawmessage)
                    for b in view.children:
                        if isinstance(b, discord.ui.Button):
                            b.disabled = True
                    #await gawmessage.edit(view=view)
                    entries = await self.client.db.fetch("SELECT * FROM giveawayentrants WHERE message_id = $1", g_entry.message_id)
                    winners = []
                    while len(winners) != g_entry.winners and len(entries) > 0:
                        ### For winners to be selected, they must still be in the server.
                        winner = random.choice(entries)
                        if winner.get("user_id") not in winners:
                            member = guild.get_member(winner.get("user_id"))
                            if member is not None:
                                winners.append(member)
                        entries.remove(winner)
                    msg_link = f"https://discord.com/channels/{guild.id}/{channel.id}/{g_entry.message_id}"
                    host = guild.get_member(g_entry.host_id)
                    if len(winners) == 0:
                        await channel.send(f"I could not find a winner from the **{g_entry.title}** giveaway.", view=GiveawayEndView(msg_link, host))
                        if host is not None:
                            hostembed = discord.Embed(
                                title=f"Your {g_entry.title} giveaway has ended!",
                                description=f"No winners were picked, either becuase of an error or there were no entrants.",
                                url=msg_link,
                                color=self.client.embed_color, timestamp=discord.utils.utcnow())
                            self.client.remove_queued_edit(gawmessage.id)
                            g_entry.active = False
                            end_embed = await self.format_giveaway_embed(g_entry, winners = [])
                            self.client.add_to_edit_queue(message=gawmessage.channel.get_partial_message(gawmessage.id), embed=end_embed, view=view, index=0)
                            self.dm_queue.append((host, None, hostembed, None))
                    else:
                        embed = await self.format_giveaway_embed(g_entry, winners)
                        self.client.remove_queued_edit(gawmessage.id)
                        self.client.add_to_edit_queue(message=gawmessage.channel.get_partial_message(gawmessage.id), embed=embed, view=view, index=0)
                        message = f"{random.choice(guild.emojis)} **{entrant_no}** user(s) entered, {human_join([winner.mention for winner in winners], final='and')} snagged away **{g_entry.title}**!"
                        await channel.send(message, view=GiveawayEndView(msg_link, host))
                        winembed = discord.Embed(title=f"You've won the {g_entry.title} giveaway!",
                                                 description=f"Please be patient and wait for a DM from `Atlas#2867`. Do **not** try to claim before the DM!\n\n[Link to giveaway]({msg_link})",
                                                 color=self.client.embed_color, timestamp=discord.utils.utcnow())
                        winembed.set_author(name=guild.name, icon_url=guild.icon.url)
                        for winner in winners:
                            self.dm_queue.append((winner, None, winembed, None))

                        if host is not None:
                            hostembed = discord.Embed(
                                title=f"Your {g_entry.title} giveaway has ended!",
                                description=f"{human_join([f'**{winner} ({winner.id})**' for winner in winners], final='and')} won the giveaway.",
                                url=msg_link,
                                color=self.client.embed_color, timestamp=discord.utils.utcnow())
                            self.dm_queue.append((host, None, hostembed, None))
                    return True
            else:
                raise GiveawayChannelNotFound
        else:
            raise GiveawayGuildNotFound

    async def fetch_giveaway(self, message: int) -> GiveawayEntry:
        record = await self.client.db.fetchrow("SELECT * FROM giveaways WHERE message_id = $1", message)
        return GiveawayEntry(record)

    async def format_giveaway_embed(self, entry: GiveawayEntry, winners: typing.Optional[list] = None) -> discord.Embed:
        now = perf_counter()
        guild = self.client.get_guild(entry.guild_id)
        embed = discord.Embed(title=entry.title, color=self.client.embed_color, timestamp = datetime.fromtimestamp(entry.end_time))
        descriptions = ["Press the button to enter!"]
        user = self.client.get_user(entry.host_id)
        user = user.mention if user else entry.host_id
        descriptions.append(f"**Host:** {user}")
        if winners is None:
            if entry.active is True:
                descriptions.append(f"**Duration:** {humanize_timedelta(seconds=entry.duration)}")
                descriptions.append(f"**Ends:** <t:{entry.end_time}:F> <t:{entry.end_time}:R>")
            else:
                if winners is None:
                    descriptions.append(f"**Would've ended on:** <t:{entry.end_time}:F>")
                    embed.set_author(icon_url="https://cdn.discordapp.com/attachments/871737314831908974/961853829731741716/cancel.png", name="Giveaway Cancelled")
                elif winners is not None and len(winners) == 0:
                    descriptions.append(f"**Ended:** <t:{round(time())}>")
        else:
            descriptions.append(f"**Ended:** <t:{round(time())}>")
        if entry.showentrantcount is True:
            count = await self.client.db.fetchval("SELECT COUNT(distinct user_id) FROM giveawayentrants WHERE message_id = $1", entry.message_id)
            count = 0 if count is None else count
            descriptions.append(f"**Entrants:** {count}")
        if (user := self.client.get_user(entry.donor_id)) is not None:
            descriptions.append(f"**Donor:** {user.mention}")
        embed.description = "\n".join(descriptions)
        if entry.required_roles and guild is not None:
            req_list = []
            for req in entry.required_roles:
                role = guild.get_role(req)
                role = role.mention if role else f"{req} (Unknown role)"
                req_list.append(role)
            if len(req_list) > 0:
                embed.add_field(name="Requirements", value="\n ".join(req_list), inline=True)
        if entry.blacklisted_roles and guild is not None and winners is None:
            req_list = []
            for req in entry.blacklisted_roles:
                role = guild.get_role(req)
                role = role.mention if role else f"{req} (Unknown role)"
                req_list.append(role)
            if len(req_list) > 0:
                embed.add_field(name="Blacklisted Roles", value="\n ".join(req_list))
        if entry.bypass_roles and guild is not None and winners is None:
            req_list = []
            for req in entry.bypass_roles:
                role = guild.get_role(req)
                role = role.mention if role else f"{req} (Unknown role)"
                req_list.append(role)
            if len(req_list) > 0:
                embed.add_field(name="Bypass Roles", value="\n ".join(req_list))
        if entry.multi and guild is not None and winners is None:
            req_list = []
            for role_id, number_of_entries in entry.multi.items():
                role = guild.get_role(int(role_id))
                if role is not None:
                    req_list.append(f"{role.mention}: **{number_of_entries}** extra entries")
            if len(req_list) > 0:
                embed.add_field(name="Extra Entries", value="\n ".join(req_list))
        if winners is not None and len(winners) > 0:
            embed.add_field(name="Winners", value=str(human_join([w.mention for w in winners], ", ", "and")), inline=False)
        embed.set_footer(text=f"{plural(entry.winners):winner} will be picked for this giveaway, which ends")
        title_lower = entry.title.lower()
        if "tro" in title_lower or "trophy" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/940712966213496842.gif?quality=lossless")
        elif "pem" in title_lower or "medal" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/948673104870252564.gif?size=128&quality=lossless")
        elif "bolt" in title_lower or "cutter" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/831023529255632898.webp?quality=lossless")
        elif "million" in title_lower or "mil" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/837629198415691786.webp?size=96&quality=lossless")
        elif "coin" in title_lower or "pec" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/942212715454271518.gif?quality=lossless")
        else:
            guild = self.client.get_guild(entry.guild_id)
            if guild is not None and guild.icon is not None:
                embed.set_thumbnail(url=guild.icon.url)
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.giveawayview_added:
            self.client.add_view(GiveawayView(self.client, self))
            self.giveawayview_added = True


    @tasks.loop(seconds=30.0)
    async def change_entrantcount(self):
        await self.client.wait_until_ready()
        try:
            results = await self.client.db.fetch("SELECT * FROM giveaways WHERE showentrantcount = true AND end_time > $1 AND active = True", round(time()))
            if len(results) > 0:
                for entry in results:
                    entry = GiveawayEntry(entry)
                    embed = await self.format_giveaway_embed(entry, None)
                    channel = self.client.get_channel(entry.channel_id)
                    if channel is None:
                        await self.client.db.execute("UPDATE giveaways SET active = False WHERE message_id = $1", entry.message_id)
                        continue
                    p_message = channel.get_partial_message(entry.message_id)
                    if discord.utils.get([m[0] for m in self.client.editqueue], id=p_message.id) is not None:
                        # print('item already in queue')
                        continue
                    self.client.add_to_edit_queue(message=p_message, embed=embed)
        except Exception as e:
            print(f"Editing count received an error: {e}")


    @tasks.loop(seconds=1.0)
    async def check_giveaways(self):
        # first, it will run an sql statement to check for giveaways where end_time < the time now, and active is True
        # if there are more than 0 giveaways that have fit the requirement
        # it will iterate over each giveaway.
        # it will first convert each giveaway into a record, then run it through a function to get winners?
        # the function will be responsible to adding the dms to a dm queue and edit to editqueue maybe?
        # i have to do that so this task won't delay if the edit is delayed, for example (due to polls etc)
        # after that that function (probably end_giveaways) should return True,
        # if it returns True, the giveaway will be edited to active = False, and continue on iterating
        #
        # what the end_giveaway function should do, is to get the number of winners, generate an embed and do the stuff above
        # yea that's all bye have fun
        await self.client.wait_until_ready()
        try:
            result = await self.client.db.fetch("SELECT * FROM giveaways WHERE end_time < $1 AND active = $2", round(time()), True)
            if len(result) > 0:
                for entry in result:
                    entry = GiveawayEntry(entry)
                    try:
                        await self.end_giveaway(entry)
                    except (GiveawayGuildNotFound, GiveawayChannelNotFound, GiveawayMessageNotFound) as e:
                        await self.client.db.execute("UPDATE giveaways SET active = False WHERE message_id = $1", entry.message_id)
                    except Exception as e:
                        await self.client.get_user(650647680837484556).send(f"```\nFailed to end {entry}: {e}\n```")
                    else:
                        await self.client.db.execute("UPDATE giveaways SET active = False WHERE message_id = $1",
                                                     entry.message_id)
        except Exception as e:
            print(f"Checking/ending giveaways received an error: {e}")

    @commands.group(name="giveawayconfig", aliases=["gwconfig"], invoke_without_command=True)
    @checks.has_permissions_or_role(manage_roles=True)
    async def giveawayconfig(self, ctx: DVVTcontext):
        existing_configs = await self.client.db.fetch("SELECT * FROM giveawayconfig WHERE guild_id = $1", ctx.guild.id)
        if len(existing_configs) > 0:
            embeds = []
            title = "Giveaway Configurations"

            for chunks in discord.utils.as_chunks(existing_configs, 7):
                embed = discord.Embed(title=title, color=self.client.embed_color, timestamp=discord.utils.utcnow())
                for entry in chunks:
                    bypass_role_list = []
                    blacklist_role_list = []
                    multi_role_list = []
                    if (channel := ctx.guild.get_channel(entry.get('channel_id'))) is not None:
                        if (bypass_roles := entry.get('bypass_roles')) is not None:
                            bypass_roles = split_string_into_list(bypass_roles, return_type=int)
                            for bypass_role_id in bypass_roles:
                                if (bypass_role := ctx.guild.get_role(bypass_role_id)) is not None:
                                    bypass_role_list.append(bypass_role.mention)
                        if (blacklisted_roles := entry.get('blacklisted_roles')) is not None:
                            blacklisted_roles = split_string_into_list(blacklisted_roles, return_type=int)
                            for blacklist_role_id in blacklisted_roles:
                                if (blacklist_role := ctx.guild.get_role(blacklist_role_id)) is not None:
                                    blacklist_role_list.append(blacklist_role.mention)
                        if (multi := entry.get('multi')) is not None:
                            multi = json.loads(multi)
                            for multi_role_id in multi:
                                if (multi_role := ctx.guild.get_role(int(multi_role_id))) is not None:
                                    multi_role_list.append(f"{multi_role.mention} x{multi[multi_role_id]}")
                        field_value = f"{channel.mention}"
                        if len(bypass_role_list) > 0:
                            field_value += f"\n    • Bypass Roles: {', '.join(bypass_role_list)}"
                        else:
                            field_value += f"\n    • Bypass Roles: None"

                        if len(blacklist_role_list) > 0:
                            field_value += f"\n    • Blacklisted Roles: {', '.join(blacklist_role_list)}"
                        else:
                            field_value += f"\n    • Blacklisted Roles: None"

                        if len(multi_role_list) > 0:
                            field_value += f"\n    • Multi Roles: {', '.join(multi_role_list)}"
                        else:
                            field_value += f"\n    • Multi Roles: None"

                        embed.add_field(name=f"\u200b", value=field_value, inline=False)
                embeds.append(embed)
        else:
            embeds = [discord.Embed(title="Giveaway Configurations", color=self.client.embed_color, description="You have no configuration set for any channels in this server. Use `dv.giveawayconfig add [channel]` to do so.")]
        paginator = pages.Paginator(pages=embeds)
        await paginator.send(ctx)

    @giveawayconfig.command(name="add", aliases=["create", "new"])
    @checks.has_permissions_or_role(manage_roles=True)
    async def giveawayconfig_add(self, ctx: DVVTcontext, channel: discord.TextChannel = None):
        if channel is None:
            return await ctx.send(f"You must specify a channel to add a giveaway profile for.")
        if (existing_config := await self.client.db.fetchrow("SELECT * FROM giveawayconfig WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, channel.id)) is not None:
            return await ctx.send(f"You already have a giveaway profile set for {channel.mention}. Use `dv.giveawayconfig edit {channel.mention}` to edit it.")
        else:
            await self.client.db.execute("INSERT INTO giveawayconfig(guild_id, channel_id) VALUES ($1, $2)", ctx.guild.id, channel.id)
            await ctx.send(f"You have successfully created a giveaway profile for {channel.mention}! Use `dv.giveawayconfig edit {channel.mention}` to edit it.")


    @giveawayconfig.command(name="edit", aliases=["modify"])
    @checks.has_permissions_or_role(manage_roles=True)
    async def giveawayconfig_edit(self, ctx: DVVTcontext, channel: discord.TextChannel = None):
        if channel is None:
            return await ctx.send("You must specify a channel to edit the giveaway profile for.")
        config_entry = await self.client.db.fetchrow("SELECT * FROM giveawayconfig WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, channel.id)
        if config_entry is None:
            return await ctx.send(f"You don't have a giveaway profile set for this channel. Use `dv.giveawayconfig add {channel.mention}` to do so.")
        embed = discord.Embed(description=f"**Giveaway Profile Configuration for {channel.mention}**", color=self.client.embed_color)
        bypass_roles = split_string_into_list(config_entry.get('bypass_roles'), return_type=int)
        bypass_role_list = []
        for bypass_role_id in bypass_roles:
            if (bypass_role := ctx.guild.get_role(bypass_role_id)) is not None:
                bypass_role_list.append(bypass_role.mention)
        if len(bypass_role_list) > 0:
            embed.add_field(name="Bypass Roles", value=", ".join(bypass_role_list), inline=False)
        else:
            embed.add_field(name="Bypass Roles", value="None", inline=False)
        blacklist_roles = split_string_into_list(config_entry.get('blacklisted_roles'), return_type=int)
        blacklist_role_list = []
        for blacklist_role_id in blacklist_roles:
            if (blacklist_role := ctx.guild.get_role(blacklist_role_id)) is not None:
                blacklist_role_list.append(blacklist_role.mention)
        if len(blacklist_role_list) > 0:
            embed.add_field(name="Blacklisted Roles", value=", ".join(blacklist_role_list), inline=False)
        else:
            embed.add_field(name="Blacklisted Roles", value="None", inline=False)
        multi_role_list = []
        if (multi := config_entry.get('multi')) is not None:
            multi = json.loads(multi)
            for multi_role_id in multi:
                if (multi_role := ctx.guild.get_role(int(multi_role_id))) is not None:
                    multi_role_list.append(f" - {multi_role.mention} x{multi[multi_role_id]}")
        if len(multi_role_list) > 0:
            embed.add_field(name="Multi Roles", value=",\n".join(multi_role_list), inline=False)
        else:
            embed.add_field(name="Multi Roles", value="None", inline=False)

        GiveawayConfigEditView = GiveawayConfigCategories(self.client, channel, embed, ctx)
        GiveawayConfigEditView.response = await ctx.send(embed=embed, view=GiveawayConfigEditView)




    class RoleFlags(commands.FlagConverter, case_insensitive=True, delimiter=' ', prefix='--'):
        channel: typing.Optional[discord.TextChannel]
        time: typing.Optional[str]
        prize: typing.Optional[str]
        winner: typing.Optional[str]
        msg: typing.Optional[str]
        noping: typing.Optional[str]

    giveaway_group = SlashCommandGroup("giveaway", "Giveaway commands", guild_ids=[871734809154707467])

    @giveaway_group.command(name='start', description="Start a giveaway!")
    @checks.has_permissions_or_role(manage_roles=True)
    async def start_giveaway(self, ctx: discord.ApplicationContext,
                             duration: discord.Option(str, "The duration of the giveaway"),
                             winners: discord.Option(int, "The number of winners for the giveaway", min_value=1, max_value=30),
                             prize: discord.Option(str, "The prize of the giveaway"),
                             donor: discord.Option(discord.Member, "The user who donated for this giveaway.") = None,
                             message: discord.Option(str, "The message to display for the giveaway") = None,
                             required_role: discord.Option(discord.Role, "The role required to participate in the giveaway") = None,
                             required_role2: discord.Option(discord.Role, "A second required role to participate in the giveaway") = None,
                             required_role3: discord.Option(discord.Role, "A third required role to participate in the giveaway") = None
                             ):
        required_roles = []
        if required_role is not None:
            required_roles.append(required_role)
        if required_role2 is not None:
            required_roles.append(required_role2)
        if required_role3 is not None:
            required_roles.append(required_role3)
        blacklisted_roles: typing.List[discord.Role] = None
        blacklisted_set_by_server = False
        bypass_roles: typing.List[discord.Role] = None
        bypass_set_by_server = False
        try:
            duration: int = stringtime_duration(duration)
        except ValueError:
            await ctx.respond("You didn't provide a proper duration.", ephemeral=True)
            return
        if duration is None:
            await ctx.respond("You didn't provide a proper duration.", ephemeral=True)
            return
        if duration > 2592000:
            await ctx.respond("Giveaways can't be longer than 30 days.", ephemeral=True)
            return
        if prize.endswith('_hidecount'):
            prize = prize[:-10]
            show_count = False
        else:
            show_count = True

        if len(prize) > 128:
            await ctx.respond(
                f"The character count of the prize ({len(prize)}) exceeds the limit of 128 characters. If shortened to the limit, your prize will be: ```\n{prize[:128]}\n```",
                ephemeral=True
            )
        descriptions = ["You're about to start a giveaway with the following details:"]
        descriptions.append(f"**Prize**: {prize}")
        descriptions.append(f"**Duration**: {humanize_timedelta(seconds=duration)}")
        descriptions.append(f"**Number of winners**: {winners}")
        if donor is not None:
            descriptions.append(f"**Donor**: {donor.mention}")
        if required_roles:
            descriptions.append(f"**Required roles**: {', '.join(r.mention for r in required_roles)}")
        if blacklisted_roles is not None:
            bl_r_str = f"**Blacklisted roles**: {', '.join(r.mention for r in blacklisted_roles)}"
            if blacklisted_set_by_server:
                bl_r_str += " (set by server)"
            descriptions.append(bl_r_str)
        if bypass_roles is not None:
            by_r_str = f"**Bypass roles**: {', '.join(r.mention for r in bypass_roles)}"
            if bypass_set_by_server:
                by_r_str += " (set by server)"
            descriptions.append(by_r_str)
        if show_count is not True:
            descriptions.append("**Hide the entrant count**: <:DVB_True:887589686808309791> **Yes**")
        embed = discord.Embed(title="Are you ready to start this giveaway?", description="\n".join(descriptions), color=self.client.embed_color)
        confirmview = confirm(ctx, self.client, timeout=30)
        confirmview.response = await ctx.respond(embed=embed, view=confirmview, ephemeral=True)
        await confirmview.wait()
        if confirmview.returning_value is not True:
            embed.color = discord.Color.red()
            if confirmview.returning_value is None:
                embed.description += "\n\n__Timeout__\nYou didn't respond in time. The giveaway has been cancelled."
            elif confirmview.returning_value is False:
                embed.description += "\n\n__Cancelled__\nYou cancelled the giveaway."
            return await confirmview.response.edit_original_message(embed=embed)
        required_role_list_str = ",".join([str(role.id) for role in required_roles]) if len(required_roles) > 0 else None
        blacklisted_role_list_str = ",".join([str(role.id) for role in blacklisted_roles]) if type(blacklisted_roles) == list and len(blacklisted_roles) > 0 else None
        bypass_role_list_str = ",".join([str(role.id) for role in bypass_roles]) if type(bypass_roles) == list and len(bypass_roles) > 0 else None
        giveawaymessage = await ctx.channel.send(embed=discord.Embed(title="<a:DVB_Loading:909997219644604447> Initializing giveaway...", color=self.client.embed_color))
        multi = {}
        await self.client.db.execute("INSERT INTO giveaways (guild_id, channel_id, message_id, title, host_id, donor_id, winners, required_roles, blacklisted_roles, bypass_roles, multi, duration, end_time, showentrantcount) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)",
                                     ctx.guild.id, ctx.channel.id, giveawaymessage.id, prize, ctx.author.id, donor.id if donor is not None else None, winners, required_role_list_str, blacklisted_role_list_str, bypass_role_list_str, str(multi), duration, round(time() + duration), show_count)
        giveawayrecord = await self.fetch_giveaway(giveawaymessage.id)
        embed = await self.format_giveaway_embed(giveawayrecord, None)
        self.client.add_to_edit_queue(message=giveawaymessage, embed=embed, view=GiveawayView(self.client, self))
        if donor is not None:
            webh = await self.client.get_webhook(giveawaymessage.channel)
            if webh is not None:
                try:
                    await webh.send(message, username=donor.display_name, avatar_url=donor.display_avatar.url, allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))
                except:
                    pass
                else:
                    return
            await giveawaymessage.channel.send(embed=discord.Embed(description=message, color=self.client.embed_color).set_author(name=donor, icon_url=donor.display_avatar.url))


    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='trophy', aliases=['tro'])
    async def trophy_giveaway(self, ctx, *, flags: RoleFlags):
        """
        Starts a trophy giveaway.

        Available flags:
        `--time <time>` The duration of the giveaway, default is 24 hours.
        `--prize <prize>` The prize for the giveaway, default is <a:dv_iconOwO:837943874973466664> **1 Pepe Trophy**.
        `--winner <number>` Number of winners, default is 1.
        `--msg <msg>` Message accompanied with the ping, default is enter the giveaway above
        `--noping True` If you do not want the bot to ping
        """
        channel = ctx.channel
        if os.getenv('state') == "0" and channel.id not in [630587061665267713, 803039330310029362, 882280305233383474] and not ctx.author.guild_permissions.manage_roles:
            return await ctx.send("This command can only be used in certain channels.")
        if flags.time is None:
            duration = 86400
        else:
            duration = stringtime_duration(flags.time)
            if duration is None:
                return await ctx.send("You did not provide a valid time.")
        if flags.prize is None:
            prize = "<a:dv_iconOwO:837943874973466664> 1 Pepe Trophy"
        else:
            prize = flags.prize[:127]
        if flags.winner is None:
            winner = 1
        else:
            try:
                winner = int(flags.winner)
            except ValueError:
                return await ctx.send("You did not provide a valid number of winners.")
        if winner < 1:
            return await ctx.send("You must have at least one winner.")
        elif winner > 80:
            return await ctx.send("You cannot have more than 80 winners.")
        if len(prize) > 70:
            return await ctx.send("The prize's name cannot be longer than 70 characters.")
        if flags.msg is not None and len(flags.msg) > 1000:
            return await ctx.send("The message that accompanies the ping cannot be longer than 1000 characters.")
        if duration > 2592000:
            return await ctx.send("The giveaway cannot last longer than 30 days.")
        ends_at = round(time()) + duration
        end_at_datetime = datetime.fromtimestamp(ends_at)
        giveawaymessage = await ctx.channel.send(embed=discord.Embed(title="<a:DVB_Loading:909997219644604447> Initializing giveaway...", color=self.client.embed_color))
        multi = {
            str(voteid): 1,
            str(level_100id): 1
        }
        await self.client.db.execute("INSERT INTO giveaways (guild_id, channel_id, message_id, title, host_id, donor_id, winners, required_roles, blacklisted_roles, bypass_roles, multi, duration, end_time) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)", ctx.guild.id, ctx.channel.id, giveawaymessage.id, prize, ctx.author.id, None, winner, "", "", "", json.dumps(multi), duration, round(time() + duration))
        giveawayrecord = await self.fetch_giveaway(giveawaymessage.id)
        embed = await self.format_giveaway_embed(giveawayrecord, None)
        await giveawaymessage.edit(embed=embed, view=GiveawayView(self.client, self))
        if flags.noping is not None:
            return
        pingrole = 758174135276142593 if os.getenv('state') == '0' else 895815588289581096
        author_said_yes = False
        pingmsg = await ctx.send(f"Do you want to ping <@&{pingrole}>? Say `yes` within **20 seconds** `[0/2]`")
        try:
            msg = await self.client.wait_for('message', timeout=20.0, check=lambda m: not m.author.bot and m.channel == ctx.channel and m.content == 'yes')
        except asyncio.TimeoutError:
            await ctx.send("Two people did not say `yes`. I will not be pinging the role.", delete_after=5.0)
        else:
            await msg.delete()
            if msg.author.id == ctx.author.id:
                author_said_yes = True
            await pingmsg.edit(content=f"Do you want to ping <@&{pingrole}>? Say `yes` within **60 seconds** `[1/2]`")
            try:
                msg = await self.client.wait_for('message', timeout=60.0, check=lambda m: not m.author.bot and m.channel == ctx.channel and m.content == 'yes' and m.author.id != ctx.author.id if author_said_yes else m.author.id == ctx.author.id)
            except asyncio.TimeoutError:
                await ctx.send("Two people did not say `yes`. I will not be pinging the role.", delete_after=5.0)
            else:
                await msg.delete()
                await pingmsg.edit(content=f"Do you want to ping <@&{pingrole}>? Say `yes` within **60 seconds** `[2/2]`", delete_after=2.0)
                if flags.msg is None:
                    if prize == "<a:dv_iconOwO:837943874973466664> 1 Pepe Trophy":
                        additional_message = "Enter the daily trophy giveaway above! <:DVB_Trophy:911244980599804015>"
                    else:
                        additional_message = f"React to the giveaway above ♡"
                else:
                    additional_message = flags.msg
                await ctx.send(f"<@&{pingrole}> {additional_message}", allowed_mentions=discord.AllowedMentions(everyone=False, roles=True, users=True))

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name="giveaway", aliases=['g'], invoke_without_command=True)
    async def giveaway(self, ctx):
        await ctx.help()

    @checks.has_permissions_or_role(manage_roles=True)
    @giveaway.command(name="start", aliases=['s'], usage="[duration] [winner] <requirement> [prize]")
    async def giveaway_start(self, ctx):
        """
        Starts a new giveaway. This command is non-functional, please use its slash command version instead.
        """
        return await ctx.send("Please use the slash command `/giveaway start` instead.")

    class BetterMessageID(commands.Converter):
        async def convert(self, ctx, argument):
            if argument is None:
                raise ArgumentBaseError(message="1You need to provide a message link or ID.")
            try:
                return int(argument)
            except ValueError:
                if not (argument.startswith('https') and 'discord.com/channels/' in argument):
                    raise ArgumentBaseError(message="2You did not provide a valid message link or ID. A message link should start with `https://discord.com/channels/`, `https://ptb.discord.com/channels/` or `https://canary.discord.com/channels/`.")
                split = argument.split('/')
                if split[4] == '@me':
                    raise ArgumentBaseError(message="3You provided a message from DMs, I need a message from a channel.")
                else:
                    try:
                        channel_id = int(split[5])
                    except:
                        raise ArgumentBaseError(message="4You did not provide a valid message link or ID. A message link should start with `https://discord.com/channels/`, `https://ptb.discord.com/channels/` or `https://canary.discord.com/channels/`.")
                    channel = ctx.guild.get_channel(channel_id)
                    if channel is None:
                        raise ArgumentBaseError(message="4You did not provide a valid message link or ID.")
                    else:
                        try:
                            message_id = int(split[6])
                            if channel.get_partial_message(message_id) is not None:
                                return message_id
                        except:
                            raise ArgumentBaseError(message="5You did not provide a valid message link or ID.")

    @checks.has_permissions_or_role(manage_roles=True)
    @giveaway.command(name="cancel", aliases=['c'])
    async def giveaway_cancel(self, ctx, message_id: BetterMessageID =None):
        """
        Cancels a giveaway. No winners will be announced.
        """
        if message_id is None:
            return await ctx.send("You need to provide a message link or ID.")
        result = await self.client.db.fetchrow("SELECT * FROM giveaways WHERE guild_id = $1 AND message_id = $2", ctx.guild.id, message_id)
        if result is None:
            with contextlib.suppress(Exception):
                await ctx.send(f"No giveaway was found with the message ID {message_id}.", delete_after=5.0)
            with contextlib.suppress(Exception):
                await ctx.message.delete()
        else:
            giveaway = GiveawayEntry(result)
            if giveaway.active:
                await self.client.db.execute("UPDATE giveaways SET active = False WHERE message_id = $1", message_id)
                with contextlib.suppress(Exception):
                    await ctx.send(f"Giveaway {message_id} has been cancelled.", delete_after=5.0)
                giveaway.active = False
                embed = await self.format_giveaway_embed(giveaway)
                channel = self.client.get_channel(giveaway.channel_id)
                try:
                    msg = await channel.fetch_message(giveaway.message_id)
                except discord.NotFound:
                    return
                view = discord.ui.View.from_message(msg)
                for b in view.children:
                    if isinstance(b, discord.ui.Button):
                        b.disabled = True
                self.client.remove_queued_edit(giveaway.message_id)
                with contextlib.suppress(Exception):
                    await msg.edit(view=view, embed=embed)
            else:
                with contextlib.suppress(Exception):
                    await ctx.send(f"Either this giveaway was cancelled, or it has already ended.", delete_after=5.0)
                with contextlib.suppress(Exception):
                    await ctx.message.delete()


    @checks.has_permissions_or_role(manage_roles=True)
    @giveaway.command(name="end", aliases=['e'])
    async def giveaway_end(self, ctx, message_id: BetterMessageID = None):
        """
        Ends a giveaway earlier than the end time, but winners will be announced.
        """
        if message_id is None:
            return await ctx.send("You need to provide a message link or ID.")
        result = await self.client.db.fetchrow("SELECT * FROM giveaways WHERE guild_id = $1 AND message_id = $2", ctx.guild.id, message_id)
        if result is None:
            with contextlib.suppress(Exception):
                await ctx.send(f"No giveaway was found with the message ID {message_id}.", delete_after=5.0)
            with contextlib.suppress(Exception):
                await ctx.message.delete()
        else:
            giveaway = GiveawayEntry(result)
            if giveaway.active:
                try:
                    await self.end_giveaway(giveaway)
                except (GiveawayGuildNotFound, GiveawayChannelNotFound, GiveawayMessageNotFound):
                    await ctx.message.delete()
                    await self.client.db.execute("UPDATE giveaways SET active = False WHERE message_id = $1", giveaway.message_id)
                else:
                    await self.client.db.execute("UPDATE giveaways SET active = False WHERE message_id = $1", giveaway.message_id)





    @checks.has_permissions_or_role(manage_roles=True)
    @giveaway.command(name="reroll", aliases=["r"])
    async def giveaway_reroll(self, ctx, message_id: BetterMessageID = None, winner: int = None):
        """
        Rerolls the winner for a giveaway.
        """
        result = await self.client.db.fetchrow("SELECT * FROM giveaways WHERE message_id = $1 AND guild_id = $2", message_id, ctx.guild.id)
        if result is None:
            with contextlib.suppress(Exception):
                await ctx.send(f"No giveaway was found with the message ID {message_id}.", delete_after=5.0)
            with contextlib.suppress(Exception):
                await ctx.message.delete()
        if winner is None:
            winnernum = 1
        else:
            winnernum = winner
        giveaway = GiveawayEntry(result)
        if giveaway.end_time > time() or giveaway.active is True:
            return await ctx.send("You can't reroll a giveaway that hasn't ended yet 😂🤣")
        entries = await self.client.db.fetch("SELECT * FROM giveawayentrants WHERE message_id = $1", message_id)
        winners = []
        while len(winners) != winnernum and len(entries) > 0:
            winner = random.choice(entries)
            if winner.get("user_id") not in winners:
                member = ctx.guild.get_member(winner.get("user_id"))
                if member is not None:
                    winners.append(member)
            entries.remove(winner)
        channel = self.client.get_channel(giveaway.channel_id)
        url = f"https://discord.com/channels/{ctx.guild.id}/{channel.id}/{giveaway.message_id}"
        with contextlib.suppress(Exception):
            await ctx.message.delete()
        if len(winners) == 0:
            await channel.send(f"I could not reroll for a winner from the **{giveaway.title}** giveaway.", delete_after=5.0)
        else:
            message = f"Congratulations, {grammarformat([winner.mention for winner in winners])}! You snagged away **{giveaway.title}** after a reroll!"
            await channel.send(message, view=GiveawayEndView(url=url))


    @checks.has_permissions_or_role(manage_roles=True)
    @giveaway.command(name="active", aliases = ['a', 'list', 'l'])
    async def giveaway_active(self, ctx):
        """
        Lists active giveaways.
        """
        giveaways = await self.client.db.fetch("SELECT * FROM giveaways WHERE guild_id=$1 AND active = $2", ctx.guild.id, True)
        embed = discord.Embed(title="All giveaways", color=self.client.embed_color)
        if len(giveaways) == 0:
            embed.description = "There are no active giveaways."
            return await ctx.send(embed=embed)
        else:
            giveaway_list = []
            for index, giveaway in enumerate(giveaways):
                giveaway = GiveawayEntry(giveaway)
                channel = ctx.guild.get_channel(giveaway.channel_id)
                if channel is None:
                    channel = "Unknown channel"
                message_link = f"https://discord.com/channels/{ctx.guild.id}/{giveaway.channel_id}/{giveaway.channel_id}"
                host = self.client.get_user(giveaway.host_id)
                if host is None:
                    host = "Unknown host"
                prize = f"{index+1}. {giveaway.title}"
                description = f"Hosted by **{host.mention if type(host) != str else host}** in **{channel.mention if type(channel) != str else channel}**\nEnds **<t:{giveaway.end_time}>**\n[Jump to giveaway]({message_link})"
                giveaway_list.append((prize, description))
            if len(giveaway_list) <= 10:
                for giveaway_details in giveaway_list:
                    embed.add_field(name=giveaway_details[0], value=giveaway_details[1], inline=False)
                return await ctx.send(embed=embed)
            else:
                pages = CustomMenu(source=GiveawayList(giveaway_list, embed.title), clear_reactions_after=True, timeout=60)
                return await pages.start(ctx)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.cooldown(240, 1, commands.BucketType.guild)
    @giveaway.command(name='gw')
    async def giveaway_gw(self, ctx, *, text = None):
        await ctx.message.delete()
        if os.getenv('state') == '0':
            if ctx.channel.id not in [701771740912549938, 626704430468825089, 630587061665267713, 616007729718231161]:
                return await ctx.send("You cannot use this command in this channel! �")
        if text is None:
            text = "React to the giveaway above ♡"
        emojis = ['<a:dv_aBCNodOwO:837756826564952096>', '<a:dv_bunbunDanceOwO:837749889496514570>', '<a:dv_aHeartsWaveOwO:837741729321844847>', '<a:dv_aPinkOwO:837756828866707497>', '<a:dv_aWiggleOwO:837756830053695560>', '<a:dv_bunbunDanceOwO:837764938734108693>', '<a:dv_pandaMadOwO:837772023110303834>', '<a:dv_foxCuddlesOwO:837744615499104266>', '<a:dv_nekoWaveOwO:837756827255963718>', '<a:dv_pandaHeartsOwO:837769010691047485>', '<a:dv_pandaLoveOwO:837769036333973555>', '<a:dv_pandaExcitedOwO:837772105822502912>', '<a:dv_panHeartsOwO:837712562434342952>', '<a:dv_pikaWaveOwO:837712214935732265>', '<a:dv_qbFlowerOwO:837773808269525052>', '<a:dv_qbThumbsupOwO:837666232811257907>', '<a:dv_squirrelBodyRollOwO:837726627160129558>', '<a:dv_squirrelHappyOwO:837711561338519572>', '<a:dv_wButterflyOwO:837787067912159233>', '<a:dv_wScribbleHeartOwO:837782023631798302>', '<a:dv_wYellowMoonOwO:837787073066303551>', '<a:dv_wpinkHeartOwO:837781949337960467>', '<a:dv_wRainbowHeartOwO:837787078171033660>']
        emoji = random.choice(emojis)
        msg = await ctx.send(f"{emoji} **<@&758175760909074432>** {emoji}\n{text}", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=True))
        await msg.add_reaction('<:dv_wCyanHeartOwO:837700662192111617>')

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.cooldown(240, 1, commands.BucketType.guild)
    @giveaway.command(name='elite')
    async def giveaway_elite(self, ctx, *, text=None):
        await ctx.message.delete()
        if os.getenv('state') == '0':
            if ctx.channel.id not in [701771740912549938, 741254464303923220, 626704430468825089, 630587061665267713, 616007729718231161]:
                return await ctx.send("You cannot use this command in this channel! �")
        if text is None:
            text = "React to the Elite giveaway above ♡"
        emojis = ['<a:dv_aBCNodOwO:837756826564952096>', '<a:dv_bunbunDanceOwO:837749889496514570>', '<a:dv_aHeartsWaveOwO:837741729321844847>', '<a:dv_aPinkOwO:837756828866707497>', '<a:dv_aWiggleOwO:837756830053695560>', '<a:dv_bunbunDanceOwO:837764938734108693>', '<a:dv_pandaMadOwO:837772023110303834>', '<a:dv_foxCuddlesOwO:837744615499104266>', '<a:dv_nekoWaveOwO:837756827255963718>', '<a:dv_pandaHeartsOwO:837769010691047485>', '<a:dv_pandaLoveOwO:837769036333973555>', '<a:dv_pandaExcitedOwO:837772105822502912>', '<a:dv_panHeartsOwO:837712562434342952>', '<a:dv_pikaWaveOwO:837712214935732265>', '<a:dv_qbFlowerOwO:837773808269525052>', '<a:dv_qbThumbsupOwO:837666232811257907>', '<a:dv_squirrelBodyRollOwO:837726627160129558>', '<a:dv_squirrelHappyOwO:837711561338519572>', '<a:dv_wButterflyOwO:837787067912159233>', '<a:dv_wScribbleHeartOwO:837782023631798302>', '<a:dv_wYellowMoonOwO:837787073066303551>', '<a:dv_wpinkHeartOwO:837781949337960467>', '<a:dv_wRainbowHeartOwO:837787078171033660>']
        emoji = random.choice(emojis)
        msg = await ctx.send(f"{emoji} **<@&758174135276142593>** {emoji}\n{text}", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=True))
        await msg.add_reaction('<:dv_wCyanHeartOwO:837700662192111617>')

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.cooldown(240, 1, commands.BucketType.guild)
    @giveaway.command(name='booster')
    async def giveaway_booster(self, ctx, *, text = None):
        await ctx.message.delete()
        if os.getenv('state') == '0':
            if ctx.channel.id not in [701771740912549938, 626704430468825089, 741254464303923220]:
                return await ctx.send("You cannot use this command in this channel! �")
        if text is None:
            text = "React to the Booster giveaway above ♡"
        emojis = ['<a:dv_aBCNodOwO:837756826564952096>', '<a:dv_bunbunDanceOwO:837749889496514570>', '<a:dv_aHeartsWaveOwO:837741729321844847>', '<a:dv_aPinkOwO:837756828866707497>', '<a:dv_aWiggleOwO:837756830053695560>', '<a:dv_bunbunDanceOwO:837764938734108693>', '<a:dv_pandaMadOwO:837772023110303834>', '<a:dv_foxCuddlesOwO:837744615499104266>', '<a:dv_nekoWaveOwO:837756827255963718>', '<a:dv_pandaHeartsOwO:837769010691047485>', '<a:dv_pandaLoveOwO:837769036333973555>', '<a:dv_pandaExcitedOwO:837772105822502912>', '<a:dv_panHeartsOwO:837712562434342952>', '<a:dv_pikaWaveOwO:837712214935732265>', '<a:dv_qbFlowerOwO:837773808269525052>', '<a:dv_qbThumbsupOwO:837666232811257907>', '<a:dv_squirrelBodyRollOwO:837726627160129558>', '<a:dv_squirrelHappyOwO:837711561338519572>', '<a:dv_wButterflyOwO:837787067912159233>', '<a:dv_wScribbleHeartOwO:837782023631798302>', '<a:dv_wYellowMoonOwO:837787073066303551>', '<a:dv_wpinkHeartOwO:837781949337960467>', '<a:dv_wRainbowHeartOwO:837787078171033660>']
        emoji = random.choice(emojis)
        msg = await ctx.send(f"{emoji} **<@&662876587687018507>** {emoji}\n{text}", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=True))
        await msg.add_reaction('<:dv_wCyanHeartOwO:837700662192111617>')

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.cooldown(240, 1, commands.BucketType.guild)
    @giveaway.command(name='nitro')
    async def giveaway_nitro(self, ctx, *, text=None):
        await ctx.message.delete()
        if os.getenv('state') == '0':
            if ctx.channel.id not in [650244237744537630, 630587061665267713, 616007729718231161]:
                return await ctx.send("You cannot use this command in this channel! �")
        if text is None:
            text = "React to the Nitro giveaway above ♡"
        emojis = ['<a:dv_aBCNodOwO:837756826564952096>', '<a:dv_bunbunDanceOwO:837749889496514570>', '<a:dv_aHeartsWaveOwO:837741729321844847>', '<a:dv_aPinkOwO:837756828866707497>', '<a:dv_aWiggleOwO:837756830053695560>', '<a:dv_bunbunDanceOwO:837764938734108693>', '<a:dv_pandaMadOwO:837772023110303834>', '<a:dv_foxCuddlesOwO:837744615499104266>', '<a:dv_nekoWaveOwO:837756827255963718>', '<a:dv_pandaHeartsOwO:837769010691047485>', '<a:dv_pandaLoveOwO:837769036333973555>', '<a:dv_pandaExcitedOwO:837772105822502912>', '<a:dv_panHeartsOwO:837712562434342952>', '<a:dv_pikaWaveOwO:837712214935732265>', '<a:dv_qbFlowerOwO:837773808269525052>', '<a:dv_qbThumbsupOwO:837666232811257907>', '<a:dv_squirrelBodyRollOwO:837726627160129558>', '<a:dv_squirrelHappyOwO:837711561338519572>', '<a:dv_wButterflyOwO:837787067912159233>', '<a:dv_wScribbleHeartOwO:837782023631798302>', '<a:dv_wYellowMoonOwO:837787073066303551>', '<a:dv_wpinkHeartOwO:837781949337960467>', '<a:dv_wRainbowHeartOwO:837787078171033660>']
        emoji = random.choice(emojis)
        msg = await ctx.send(f"{emoji} **<@&685233344136609812>** {emoji}\n{text}", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=True))
        await msg.add_reaction('<:dv_wCyanHeartOwO:837700662192111617>')

    def cog_unload(self):
        self.end_giveaways.stop()
        self.change_entrantcount.stop()