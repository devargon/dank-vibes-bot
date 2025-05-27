import contextlib
import os
import random
import typing
import asyncio
from collections import Counter
from time import time
from datetime import datetime

import amari
import discord
from discord import SlashCommandGroup
from discord.ext import commands, tasks, menus, pages

import cogs.giveaways
from cogs.giveaways.giveaway_utils import *
from main import dvvt

from utils import checks
from utils.buttons import confirm
from utils.context import DVVTcontext
from utils.converters import BetterBetterRoles, BetterMessageID
from utils.menus import CustomMenu
from utils.paginator import SingleMenuPaginator
from utils.specialobjects import AwaitingAmariData, NoAmariData
from utils.time import humanize_timedelta
from utils.format import plural, stringtime_duration, grammarformat, human_join, print_exception, proper_userf

voteid = 874897331252760586 if os.getenv('state') == '1' else 683884762997587998
elite_gw_channel = 871737332431216661 if os.getenv('state') == '1' else 741254464303923220
level_100id = 943883531573157889 if os.getenv('state') == '1' else 717120742512394323
gen_chat_id = 871737314831908974 if os.getenv('state') == '1' else 608498967474601995
gwstaff_id = 983277305889697823  if os.getenv('state') == '1' else 627284965222121482
gw_ping = 983284295579893790 if os.getenv('state') == '1' else 758175760909074432
elitegw_ping = 895815588289581096 if os.getenv('state') == '1' else 758174135276142593


DVB_True = "<:DVB_True:887589686808309791>"
DVB_False = "<:DVB_False:887589731515392000>"
DVB_Neutral = "<:DVB_Neutral:887589643686670366>"


class VoteLink(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label='Vote for Dank Vibes at Top.gg',
                                        url="https://top.gg/servers/1288032530569625660/vote",
                                        emoji=discord.PartialEmoji.from_str('<a:dv_iconOwO:837943874973466664>')))

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
        self.interaction: discord.Interaction = None
        self.user = user
        super().__init__(timeout=30)

    @discord.ui.button(label="Edit Multi", emoji="✏️", style=discord.ButtonStyle.grey)
    async def edit_multi(self, button: discord.Button, interaction: discord.Interaction):
        self.interaction = interaction
        self.value = "edit"
        self.stop()

    @discord.ui.button(label="Delete Role's Multi", emoji="🗑", style=discord.ButtonStyle.red)
    async def delete_role(self, button: discord.Button, interaction: discord.Interaction):
        self.interaction = interaction
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
        #print(bypass_roles)
        if bypass_roles is None:
            bypass_roles = []
        else:
            bypass_roles = split_string_into_list(bypass_roles, return_type=int)
        #print(bypass_roles)
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
                    await self.ctx.send("You didn't input any roles.", delete_after=10.0)
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
                                    #print(result_role.id, bypass_roles)
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
                    await self.ctx.send(summary, delete_after=20.0)
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
        #print(blacklisted_roles)
        if blacklisted_roles is None:
            blacklisted_roles = []
        else:
            blacklisted_roles = split_string_into_list(blacklisted_roles, return_type=int)
        #print(blacklisted_roles)
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
                    await self.ctx.send("You didn't input any roles.", delete_after=10.0)
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
                                    #print(result_role.id, blacklisted_roles)
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
                    await self.ctx.send(summary, delete_after=20.0)
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
                await self.ctx.send("Role not found.", delete_after=10.0)
            else:
                embed.description = f"You selected **{r.name}**.\n\nChoose an option below."
                choose_edit_or_delete = EditOrDeleteMultiEntry(self.ctx.author)
                await select_multi_view.response.edit(embed=embed, view=choose_edit_or_delete)
                await choose_edit_or_delete.wait()
                for b in choose_edit_or_delete.children:
                    b.disabled = True
                if choose_edit_or_delete.interaction is not None:
                    await choose_edit_or_delete.interaction.response.edit_message(view=choose_edit_or_delete)
                #print(choose_edit_or_delete.value)
                if choose_edit_or_delete.value is None:
                    pass
                elif choose_edit_or_delete.value == "edit":
                    draft_msg = await self.ctx.send("Give a number for the multi count for the role **{}**.".format(r.name))
                    try:
                        m = await self.client.wait_for("message", check=lambda m: m.author == self.ctx.author and m.channel == self.ctx.channel, timeout=60)
                    except asyncio.TimeoutError:
                        await self.ctx.send("You did not respond in time.", delete_after=10.0)
                    else:
                        try:
                            multi_count = int(m.content)
                        except ValueError:
                            await self.ctx.send("You did not provide a valid number for the multi count.", delete_after=10.0)
                        else:
                            if multi_count < 1:
                                await self.ctx.send("You must provide a number greater than 0.", delete_after=10.0)
                            else:
                                multi[str(r.id)] = multi_count
                                await self.client.db.execute("INSERT INTO giveawayconfig (guild_id, channel_id, multi) VALUES ($1, $2, $3) ON CONFLICT (channel_id) DO UPDATE SET multi = $3", self.ctx.guild.id, self.channel.id, json.dumps(multi))
                                await self.ctx.send("<:DVB_True:887589686808309791> **Successfully updated!**", delete_after=5.0)
                                with contextlib.suppress(Exception):
                                    await draft_msg.delete()
                                    await m.delete()

                elif choose_edit_or_delete.value == "delete":
                    multi.pop(str(r.id))
                    await self.client.db.execute("INSERT INTO giveawayconfig (guild_id, channel_id, multi) VALUES ($1, $2, $3) ON CONFLICT (channel_id) DO UPDATE SET multi = $3", self.ctx.guild.id, self.channel.id, json.dumps(multi))
                    await self.ctx.send("<:DVB_True:887589686808309791> **Successfully updated!**", delete_after=5.0)
                await select_multi_view.response.edit(view=choose_edit_or_delete)
        else:
            if select_multi_view.result == "add_multi":
                try:
                    select_multi_view.children[0].options[0].default = True
                except:
                    pass
            await select_multi_view.response.edit(embed=embed, view=select_multi_view)
            def check(m: discord.Message):
                return m.author == self.ctx.author and m.channel == self.ctx.channel
            draft_msg = await self.ctx.send("Please **enter the role** (like how you would do with `dv.roleinfo` and the **multi as a number**, separated by **a comma**.\nExample: `rolename, 1`, `\<@&12345678>, 2`, `12345678, 3`")
            try:
                response_msg = await self.client.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                pass
            else:
                msg_con = response_msg.content
                u = msg_con.split(",")
                msg_con = [ele.strip() for ele in u]
                if len(msg_con) != 2:
                    await self.ctx.send("Invalid input, you did not provide a role and a multi separated by commas (example: `@role, 1`)", delete_after=10.0)
                else:
                    unconverted_obj = msg_con[0]
                    try:
                        r = await BetterBetterRoles().convert(self.ctx, unconverted_obj)
                    except Exception as e:
                        await self.ctx.send(f"You did not provide a valid role: {e}", delete_after=10.0)
                    else:
                        if r is None:
                            await self.ctx.send("You did not provide a valid role.", delete_after=10.0)
                        else:
                            if str(r.id) in multi:
                                await self.ctx.send(f"You already have a multi set for the role **{r}**. If you want to edit the multi or delete it, select it from the menu in the previous step.", delete_after=15.0)
                            else:
                                try:
                                    multi_count = int(msg_con[1])
                                except ValueError:
                                    await self.ctx.send("You did not input a valid number for the multi count.", delete_after=10.0)
                                else:
                                    if multi_count < 1:
                                        await self.ctx.send("The multi count should be more than 0.", delete_after=10.0)
                                    else:
                                        multi[str(r.id)] = multi_count
                                        await self.client.db.execute("INSERT INTO giveawayconfig (guild_id, channel_id, multi) VALUES ($1, $2, $3) ON CONFLICT (channel_id) DO UPDATE SET multi = $3", self.ctx.guild.id, self.channel.id, json.dumps(multi))
                                        await self.ctx.send(f"<:DVB_True:887589686808309791> **Successfully updated!**", delete_after=5.0)
            with contextlib.suppress(Exception):
                await draft_msg.delete()
        with contextlib.suppress(Exception):
            await select_multi_view.response.delete()
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
            for b in self.children:
                b.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"You have left the giveaway, and your `{len(entries)}` entries have been removed.", ephemeral=True)
        else:
            await interaction.response.send_message(f"You have already left the giveaway.", ephemeral=True)

    @discord.ui.button(label="View your entries", style=discord.ButtonStyle.grey)
    async def ViewEntries(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        await interaction.response.edit_message(embed=self.embed, view=self)



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
            self.add_item(discord.ui.Button(label=f"View {proper_userf(user)}'s Giveaway", url=self.url, disabled=False))
        else:
            self.add_item(discord.ui.Button(label=f"View Giveaway", url=self.url, disabled=False))



class GiveawayView(discord.ui.View):
    def __init__(self, client, cog):
        self.cog: cogs.giveaways.giveaways = cog
        self.client: dvvt = client
        self.thankers = []
        super().__init__(timeout=None)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str("<a:dv_DankVibes1OwO:1318037798720245820>"), label="Join giveaway", style=discord.ButtonStyle.green, custom_id="dvb:giveawayjoin")
    async def JoinGiveaway(self, button: discord.ui.Button, interaction: discord.Interaction):
        can_bypass = None
        edit_final = False
        giveawaymessage = interaction.message
        giveawayentry = await self.cog.fetch_giveaway(giveawaymessage.id)
        if len(giveawayentry.multi.keys()) > 0:
            giveaway_uses_multiple_entries = True
        else:
            giveaway_uses_multiple_entries = False
        entries_to_insert = []
        if giveawayentry.amari_level > 0:
            giveaway_has_amarilevelreq = True
        else:
            giveaway_has_amarilevelreq = False
        if giveawayentry.amari_weekly_xp > 0:
            giveaway_has_weeklyxp = True
        else:
            giveaway_has_weeklyxp = False
        if giveawayentry.active:
            entered = False
            user_entries = await self.cog.fetch_user_entries(interaction.user.id, giveawaymessage.id)
            summary_embed = discord.Embed(color=self.client.embed_color)
            descriptions = []
            if len(giveawayentry.blacklisted_roles) > 0:
                for role in interaction.user.roles:
                    if role.id in giveawayentry.blacklisted_roles:
                        return await interaction.response.send_message(
                            embed=discord.Embed(title="Failed to join giveaway",
                                                description=f"You have the role {role.mention} which is blacklisted from entering this giveaway.",
                                                color=discord.Color.red()), ephemeral=True)
            if len(giveawayentry.bypass_roles) > 0:
                # print('giveaway has bypass roles')
                for r_id in giveawayentry.bypass_roles:
                    if discord.utils.get(interaction.user.roles, id=r_id):
                        can_bypass = True
                        break
                    else:
                        continue
            if can_bypass is not True and (len(giveawayentry.required_roles) > 0 or giveaway_has_weeklyxp or giveaway_has_amarilevelreq):
                if len(giveawayentry.required_roles) > 0:
                    # print('giveaway has required roles')
                    missing_roles = []
                    for r_id in giveawayentry.required_roles:
                        if (r := interaction.guild.get_role(r_id)) is not None:
                            if r not in interaction.user.roles:
                                missing_roles.append(f"<@&{r_id}>")
                            else:
                                pass
                    if len(missing_roles) > 0:
                        desc = f"<:DVB_False:887589731515392000> You do not have the following roles to join this giveaway: {', '.join(missing_roles)}"
                        remarks = []
                        def level_5():
                            if str(678318524933996557) in desc and len(missing_roles) == 1:
                                return True
                            else:
                                return False

                        def level_10():
                            if str(758172014439301150) in desc and len(missing_roles) == 1:
                                return True
                            else:
                                return False

                        def level_20():
                            if str(678318476913541150) in desc and len(missing_roles) == 1:
                                return True
                            else:
                                return False

                        def level_30():
                            if str(944519382577586196) in desc and len(missing_roles) == 1:
                                return True
                            else:
                                return False

                        def level_50():
                            if str(944519459580821524) in desc and len(missing_roles) == 1:
                                return True
                            else:
                                return False

                        def elite_giveaway_ping():
                            if str(758174135276142593) in desc and len(missing_roles) == 1:
                                return True

                        def donator100m():
                            if str(769491608189927434) in desc and len(missing_roles) == 1:
                                return True
                            else:
                                return False

                        def msg_250():
                            if str(899185283881381889) in desc and len(missing_roles) == 1:
                                return True, 899185283881381889, 250

                        def msg_500():
                            if str(1134925296395616297) in desc and len(missing_roles) == 1:
                                return True, 1134925296395616297, 500

                        def msg_1000():
                            if str(1134925331560669357) in desc and len(missing_roles) == 1:
                                return True, 1134925331560669357, 1000

                        def gway_only_requires_voting() -> bool:
                            if str(voteid) in desc and len(missing_roles) == 1:
                                return True

                        if gway_only_requires_voting():
                            remarks.append(f"You can get <@&{voteid}> by voting for Dank Vibes!")
                        elif level_5():
                            remarks.append(f"You can get <@&678318524933996557> by chatting in Dank Vibes and levelling up to **Level 5** in **AmariBot**, our message XP bot.**.")
                        elif level_10():
                            remarks.append(f"You can get <@&758172014439301150> by chatting in Dank Vibes and levelling up to **Level 10** in **AmariBot**, our message XP bot.**.")
                        elif level_20():
                            remarks.append(f"You can get <@&678318476913541150> by chatting in Dank Vibes and levelling up to **Level 20** in **AmariBot**, our message XP bot.**.")
                        elif level_30():
                            remarks.append(f"You can get <@&944519382577586196> by chatting in Dank Vibes and levelling up to **Level 30** in **AmariBot**, our message XP bot.**.")
                        elif level_50():
                            remarks.append(f"You can get <@&944519459580821524> by chatting in Dank Vibes and levelling up to **Level 50** in **AmariBot**, our message XP bot.**.")
                        elif donator100m():
                            remarks.append(f"You can get <@&769491608189927434> by donating **⏣ 100,000,000** worth of Dank Memer items/coins in <#652729093649072168>, <#786944439360290826>, or <#722874833540481054>.")
                        elif (req := msg_250() or msg_1000() or msg_500()):
                            remarks.append(f"You can get <@&{req[1]}> by chatting in <#608498967474601995> and reaching **{req[2]} messages sent** in `dv.mymessages`.")
                        elif elite_giveaway_ping():
                            remarks.append(f"You can get <@&758174135276142593> by running `-rank elite giveaway ping` in <#698462922682138654>, or selecting the **Elite Giveaway Ping** role under **Dank Pings** in <#782586550486695936>.")
                        if gway_only_requires_voting():
                            final_desc = f"To join this giveaway, vote for Dank Vibes on Top.gg!\n\nIt doesn't take longer than 30 seconds, and we appreciate your votes :)"
                        else:
                            final_desc = desc + "\n\n" + "\n".join(remarks)

                        requirements_embed = discord.Embed(title=f"Unable to join the \"{giveawayentry.title}\" giveaway", description=final_desc, color=discord.Color.yellow())
                        if gway_only_requires_voting():
                            requirements_embed.color = 0xEBCEDA
                            requirements_embed.set_footer(text="Click on the button below to vote!")
                        return await interaction.response.send_message(
                            embed=requirements_embed,
                            view=VoteLink() if gway_only_requires_voting() else None,
                            ephemeral=True
                        )

                if giveaway_has_weeklyxp or giveaway_has_amarilevelreq:
                    qualified = False
                    await interaction.response.send_message(embed=discord.Embed(title="Please wait...",
                                                                                description=f"I'm communicating with AmariBot to know what your Level and/or Weekly XP is!").set_thumbnail(
                        url="https://cdn.discordapp.com/avatars/339254240012664832/0cfec781df368dbce990d440d075a2d7.png?size=1024"),
                        ephemeral=True)
                    edit_final = True
                    failembed = discord.Embed(title="An error occured when I tried talking to AmariBot.",
                                              color=discord.Color.red()).set_thumbnail(
                        url="https://media.discordapp.net/attachments/656173754765934612/671895577986072576/Status.png")
                    user_amari_details, last_updated, error = await self.client.fetch_amari_data(interaction.user.id,
                                                                                                 interaction.guild.id)
                    if error is not None or user_amari_details == AwaitingAmariData or user_amari_details == NoAmariData:
                        if not isinstance(user_amari_details, amari.objects.User):
                            if user_amari_details == NoAmariData or isinstance(error, amari.exceptions.NotFound):
                                failembed.description = f"I could not find your/{interaction.guild.name}'s AmariBot data. Is AmariBot in the server?"
                            elif user_amari_details == AwaitingAmariData:
                                failembed.description = f"I am still waiting for data from AmariBot. Please try again in a few seconds."
                        else:
                            if user_amari_details is None:
                                if isinstance(error, amari.exceptions.InvalidToken):
                                    failembed.description = "**An error occured when trying to contact AmariBot. This error can only be solved by the developer.**\nThe developer has been notified and will try to solve this issue as soon as possible."
                                    traceback_error = print_exception(error, "Ignoring Exception in AmariDataGetter:")
                                    traceback_embed = discord.Embed(title="Traceback",
                                                                    description=traceback_error,
                                                                    color=discord.Color.red())
                                    await interaction.response.edit_original_message(embed=failembed)
                                    return await self.client.error_channel().send(embed=traceback_embed)
                                elif isinstance(error, amari.exceptions.RatelimitException):
                                    failembed.description = f"**{self.client.user.name} has been ratelimited from contacting AmariBot.**\nI will temporarily be unable to contact AmariBot until the ratelimit is over."
                                elif isinstance(error, amari.exceptions.AmariServerError):
                                    failembed.description = "**AmariBot is having problems.**\nI am unable to contact AmariBot until their servers are back online."
                                else:
                                    failembed.description = f"**There was an error while talking to AmariBot.**\n```{error}\n```"
                        return await interaction.edit_original_message(embed=failembed)
                    else:
                        if user_amari_details is None:
                            # print('obj was none')
                            level = 0
                            weekly_xp = 0
                        else:
                            level = user_amari_details.level
                            weekly_xp = user_amari_details.weeklyexp if user_amari_details.weeklyexp is not None else 0
                        missing_amari_requirements = []
                        if giveaway_has_amarilevelreq is True and level < giveawayentry.amari_level:
                            missing_amari_requirements.append(
                                f"<a:DVB_arrow:975663275306024971> Your current Level is **{level}**. __You need to be **Level {giveawayentry.amari_level}** to enter the giveaway.__")

                        if giveaway_has_weeklyxp is True and weekly_xp < giveawayentry.amari_weekly_xp:
                            missing_amari_requirements.append(
                                f"<a:DVB_arrow:975663275306024971> You currently have **{weekly_xp}** Weekly EXP. __You need another {giveawayentry.amari_weekly_xp - weekly_xp} Weekly EXP to join the giveaway__, which has a requirement of **{giveawayentry.amari_weekly_xp}** Weekly EXP.")
                        if len(missing_amari_requirements) > 0:
                            desc = '\n'.join(missing_amari_requirements)
                            em = discord.Embed(title=f"Unable to join the \"{giveawayentry.title}\" giveaway", description=desc,
                                               color=discord.Color.yellow())
                            em.set_footer(
                                text=f"Data was last updated {humanize_timedelta(seconds=round(time()) - last_updated)} ago.")
                            if error is not None:
                                em.add_field(name="Note",
                                             value=f"I detected an issue while trying to talk to AmariBot. This may affect your ability to join the giveaway.\n\nDetails: ```\n{error}```")

                            return await interaction.edit_original_message(embed=em)
            if giveaway_uses_multiple_entries:
                entries = Counter(entry.get('entrytype') for entry in user_entries)
                entry_list = [
                    {'role_id': 0, 'allowed_entries': 1, 'valid_role': True, 'entered_entries': entries.get(0, 0)}]
                for role_id, multi_count in giveawayentry.multi.items():
                    role_id = int(role_id)
                    role = interaction.guild.get_role(role_id)
                    if role is None:
                        entry_list.append({'role_id': role_id, 'allowed_entries': 0, 'valid_role': False, 'entered_entries': entries.get(role_id, 0)})
                    else:
                        entry_list.append({'role_id': role_id, 'allowed_entries': multi_count, 'valid_role': True, 'entered_entries': entries.get(role_id, 0)})
                for entry_dict in entry_list:
                    newly_entered_entries = 0
                    if entry_dict['valid_role'] is True:
                        if entry_dict['entered_entries'] < entry_dict['allowed_entries']:
                            if entry_dict['role_id'] == 0:
                                for i in range(entry_dict['allowed_entries'] - entry_dict['entered_entries']):
                                    entries_to_insert.append((giveawaymessage.id, interaction.user.id, entry_dict['role_id']))
                                    newly_entered_entries += 1
                                    entered = True
                                string = f"{DVB_True} **{entry_dict['entered_entries'] + newly_entered_entries}**/{entry_dict['allowed_entries']} Normal Entry" + (f" (`+{newly_entered_entries}`)" if newly_entered_entries > 0 else "")
                            else:
                                role = interaction.guild.get_role(entry_dict['role_id'])
                                if role in interaction.user.roles:
                                    for i in range(entry_dict['allowed_entries'] - entry_dict['entered_entries']):
                                        entries_to_insert.append((giveawaymessage.id, interaction.user.id, entry_dict['role_id']))
                                        newly_entered_entries += 1
                                        entered = True
                                    string = f"{DVB_True} **{entry_dict['entered_entries'] + newly_entered_entries}**/{entry_dict['allowed_entries']} Entries for being **{role.mention}**" + (f" (`+{newly_entered_entries}`)" if newly_entered_entries > 0 else "")
                                else:
                                    string = f"{DVB_Neutral} **{entry_dict['entered_entries']}**/{entry_dict['allowed_entries']} Entries for being **{role.mention}**"
                        else:
                            if entry_dict['allowed_entries'] > 0:
                                if entry_dict['role_id'] == 0:
                                    string = f"{DVB_True} **{entry_dict['entered_entries']}**/{entry_dict['allowed_entries']} Normal Entry"
                                else:
                                    role = interaction.guild.get_role(entry_dict['role_id'])
                                    if role in interaction.user.roles:
                                        string = f"{DVB_True} **{entry_dict['entered_entries']}**/{entry_dict['allowed_entries']} Entries for being {role.mention}"
                                    else:
                                        string = f"{DVB_Neutral} **{entry_dict['entered_entries']}**/{entry_dict['allowed_entries']} Entries for being **{role.name}**"
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
                    # print('user already entered')
                    summary_embed.description = f"Your total entries: {len(user_entries)}"
                else:
                    entries_to_insert.append((giveawaymessage.id, interaction.user.id, 0))
                    entered = True
                summary_embed.description = f"Your total entries: 1"
            if entered is True:
                content = "You have successfully entered the giveaway!"
                await self.client.db.executemany("INSERT INTO giveawayentrants VALUES($1, $2, $3)", entries_to_insert)
            else:
                content = "You have already entered the giveaway."
            final_number_of_entries = len(await self.cog.fetch_user_entries(interaction.user.id, giveawaymessage.id))
            if interaction.channel_id in [1027858329806045234, 871737314831908974]:
                text_content = "It is suggested that you be in https://discord.gg/6YgNFh5YHY to claim the prize!"
                if content != "You have already entered the giveaway.":
                    with contextlib.suppress(Exception):
                        await interaction.user.send(content=f"<:DVB_True:887589686808309791> Your entry for the giveaway **{giveawayentry.title}** has been counted.\n{text_content}")
            else:
                text_content = ""
            if giveaway_uses_multiple_entries is True:
                embed = discord.Embed(description=f"Your total entries: {final_number_of_entries}")
                embed.title = content
                embed.color = discord.Color.green()
                summary_embed.title = content
                summary_embed.set_footer(text=f"Your total entries: {final_number_of_entries}")
                if edit_final is True:
                    await interaction.edit_original_message(content=text_content, embed=embed, view=MultiEntryView(giveawaymessage.id, self.cog, self.client, summary_embed))
                else:
                    await interaction.response.send_message(content=text_content, embed=embed, view=MultiEntryView(giveawaymessage.id, self.cog, self.client, summary_embed), ephemeral=True)
            else:
                summary_embed.title = content
                summary_embed.description = f"Your total entries: {final_number_of_entries}"
                summary_embed.color = discord.Color.green()
                if edit_final is True:
                    await interaction.edit_original_message(content=text_content, embed=summary_embed, view=SingleEntryView(giveawaymessage.id, self.cog, self.client))
                else:
                    await interaction.response.send_message(content=text_content, embed=summary_embed, view=SingleEntryView(giveawaymessage.id, self.cog, self.client), ephemeral=True)
        else:
            return await interaction.response.send_message("It appears that this giveaway doesn't exist or has ended.", embed = None, ephemeral=True)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str("<:DVB_information_check:955345547542294559>"), custom_id="dvb:giveawayshowinfo")
    async def showgiveawayinfo(self, button: discord.ui.Button, interaction: discord.Interaction):
        giveawaymessage = interaction.message
        giveawayentry = await self.cog.fetch_giveaway(giveawaymessage.id)
        if giveawayentry is None:
            await interaction.response.send_message("This giveaway is invalid.", ephemeral=True)
            return
        embed = await self.cog.format_giveaway_details_embed(giveawayentry)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str("<:dv_textThankyouOwO:1318048861243047976>"), style=discord.ButtonStyle.grey, custom_id='dvb:giveawaythankyou')
    async def thankyou(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user not in self.thankers:
            await interaction.response.send_message("Thank you!", ephemeral=True)
            self.thankers.append(interaction.user)

    @discord.ui.button(emoji=discord.PartialEmoji.from_str("<:DVB_users:913426937362391111>"), custom_id='dvb:giveawayusers')
    async def showgiveawayusers(self, button: discord.ui.Button, interaction: discord.Interaction):
        giveawaymessage = interaction.message
        giveawayentry = await self.cog.fetch_giveaway(giveawaymessage.id)
        if giveawayentry is None:
            await interaction.response.send_message("This giveaway is invalid.", ephemeral=True)
            return
        users = await self.client.db.fetch("SELECT DISTINCT(user_id) FROM giveawayentrants WHERE message_id = $1", giveawaymessage.id)
        users_formatted = []
        for user in users:
            user_id = user.get('user_id')
            user = self.client.get_user(user_id)
            if user is not None:
                users_formatted.append(f"**{proper_userf(user)}** {user.mention}")
            else:
                users_formatted.append(f"{user_id}")
        page_embeds = []
        if len(users_formatted) > 0:
            chunks = [discord.utils.as_chunks(users_formatted, 20)]
            for index, group in enumerate(chunks):
                embed = discord.Embed(title="Giveaway Entrants", description='\n'.join(users_formatted), color=self.client.embed_color)
                embed.set_footer(text=f"{len(users_formatted)} entrants | Page {index + 1}/{len(chunks)}")
                page_embeds.append(embed)
        else:
            embed = discord.Embed(title="Giveaway Entrants", description="No one has joined this giveaway yet", color=self.client.embed_color)
            embed.set_footer(text=f"{len(users_formatted)} entrants | Page 1/1")
            page_embeds.append(embed)
        paginator = SingleMenuPaginator(pages=page_embeds)
        await paginator.respond(interaction, ephemeral=True)



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
        self.cached_embeds = {}
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
                        b.disabled = True
                    #await gawmessage.edit(view=view)
                    entries = await self.client.db.fetch("SELECT * FROM giveawayentrants WHERE message_id = $1", g_entry.message_id)
                    random.shuffle(entries)
                    winners = []
                    while len(winners) != g_entry.winners and len(entries) > 0:
                        ### For winners to be selected, they must still be in the server.
                        winner = random.choice(entries)
                        member = guild.get_member(winner.get("user_id"))
                        if member is not None:
                            if member not in winners:
                                winners.append(member)
                        entries.remove(winner)
                    msg_link = f"https://discord.com/channels/{guild.id}/{channel.id}/{g_entry.message_id}"
                    host = guild.get_member(g_entry.host_id)
                    if len(winners) == 0:
                        ended_msg = await channel.send(f"I could not find a winner from the **{g_entry.title}** giveaway.", view=GiveawayEndView(msg_link, host))
                        await self.client.db.execute("UPDATE giveaways SET ended_message_id = $1 WHERE message_id = $2", ended_msg.id, g_entry.message_id)
                        if host is not None:
                            hostembed = discord.Embed(
                                title=f"Your {g_entry.title} giveaway has ended!",
                                description=f"No winners were picked, either becuase of an error or there were no entrants.",
                                url=msg_link,
                                color=self.client.embed_color, timestamp=discord.utils.utcnow())
                            self.client.remove_queued_edit(gawmessage.id)
                            g_entry.active = False
                            end_embed = await self.format_giveaway_embed(g_entry, winners = [])
                            self.client.add_to_edit_queue(gawmessage, embed=end_embed, view=view)
                            self.dm_queue.append((host, None, hostembed, None))
                    else:
                        embed = await self.format_giveaway_embed(g_entry, winners)
                        self.client.remove_queued_edit(gawmessage.id)
                        self.client.add_to_edit_queue(message=gawmessage.channel.get_partial_message(gawmessage.id), embed=embed, view=view)
                        message = f"{random.choice(guild.emojis)} **{entrant_no}** user(s) entered, {human_join([winner.mention for winner in winners], final='and')} snagged away **{g_entry.title}**!"
                        ended_msg = await channel.send(message, view=GiveawayEndView(msg_link, host))
                        await self.client.db.execute("UPDATE giveaways SET ended_message_id = $1 WHERE message_id = $2", ended_msg.id, g_entry.message_id)
                        winnerdmmsg = ['Generic', "Depending on the type of giveaway you won, you will either receive the prize within 24 hours or need to claim from the giveaway host. If you're unsure, feel free to check with a moderator from <#870880772985344010>."]
                        if channel.id in [701771740912549938]:
                            winnerdmmsg = ["Dank Memer Flash Giveaway", "As this is a flash giveaway, the prize will be given to you almost immediately. \nYou must accept the trade sent from the giveaway host, or you will be rerolled."]
                        elif channel.id in [626704430468825089]: #gang
                            winnerdmmsg = ["Dank Memer Direct Giveaway", "Your prize has been directly transferred to you. Congratulations!"]
                        elif channel.id in [741254464303923220, 803039330310029362, 1045478841465974834]: #elite, daily tro, daily crown
                            winnerdmmsg = ["Dank Memer Normal Giveaway", "Your prize will be paid out shortly! If you have not received your prize past 24 hours, open a ticket in <#870880772985344010>."]
                        elif channel.id in [847375661332299786]:
                            winnerdmmsg = ["Karuta", "Please claim your prize by DMing/pinging the host within **24** hours after winning."]
                        elif channel.id in [847830388713586738]:
                            winnerdmmsg = ["OwO Bot", "Please wait **24 hours** before contacting the host if you haven't received your prize."]
                        elif channel.id in [853113922272624650]:
                            winnerdmmsg = ["Pokemon", "Please wait **24 hours** before contacting the host if you haven't received your prize."]
                        elif channel.id in [650244237744537630]:
                            winnerdmmsg = ["Nitro", "You might need to claim the nitro from the sponsor/giveaway host within a limited time, depending on the giveaway's requirements."]
                        elif channel.id in [992065949320630363]:
                            winnerdmmsg = ["Celeb - Dank Memer", "Please check the giveaway channel (<#992065949320630363>) for instructions on claiming your prize.\nIn the meantime, please **do NOT ping or DM staff** about your payouts. We are working hard to make sure it's ready for you."]
                        elif channel.id in [992366430857203833]:
                            winnerdmmsg = ["Celeb - Nitro", "Please check the giveaway channel (<#992366430857203833>) for instructions on claiming your prize.\nIn the meantime, please **do NOT ping or DM staff** about your payouts. We are working hard to make sure it's ready for you."]
                        elif channel.id in [991019248467976202]:
                            winnerdmmsg = ["Celeb - Karuta", "Please DM `Ari#0005` to claim your prize!\n\n**If you won a Free Dye Job**, please await further instructions. You'll be pinged soon to claim it."]


                        winembed = discord.Embed(title=f"You've won the {g_entry.title} giveaway!",
                                                 description=f"{winnerdmmsg[1]}\n\n[Link to giveaway]({msg_link})",
                                                 color=0x2fbf71, timestamp=discord.utils.utcnow()).set_footer(text=f"Giveaway type: {winnerdmmsg[0]}")
                        winembed.set_author(name=guild.name, icon_url=guild.icon.url)
                        content = "🎉 **Congratulations on winning one of our celeb giveaways!** 🎉 \nThank you for being a part of our 3 year celebrations 🥳" if channel.id in [992065949320630363, 992366430857203833, 991019248467976202] else None
                        for winner in winners:
                            self.dm_queue.append((winner, content, winembed, None))

                        if host is not None:
                            hostembed = discord.Embed(
                                title=f"Your {g_entry.title} giveaway has ended!",
                                description=f"{human_join([f'**{winner} ({winner.id})**' for winner in winners], final='and')} won the giveaway.",
                                url=msg_link,
                                color=0xed7d3a, timestamp=discord.utils.utcnow())
                            self.dm_queue.append((host, None, hostembed, None))
                    return True
            else:
                raise GiveawayChannelNotFound
        else:
            raise GiveawayGuildNotFound

    async def fetch_giveaway(self, message: int) -> GiveawayEntry:
        record = await self.client.db.fetchrow("SELECT * FROM giveaways WHERE message_id = $1", message)
        return GiveawayEntry(record)

    async def format_giveaway_details_embed(self, entry: GiveawayEntry) -> discord.Embed:
        guild = self.client.get_guild(entry.guild_id)
        embed = discord.Embed(title=entry.title, color=self.client.embed_color, timestamp=datetime.fromtimestamp(entry.end_time))
        host = self.client.get_user(entry.host_id)
        host = f"{host.mention} (`{host}`)" if host else entry.host_id
        descriptions = []
        descriptions.append(f"**Host:** {host}")
        if (user := self.client.get_user(entry.donor_id)) is not None:
            descriptions.append(f"**Donor:** {user.mention} (`{proper_userf(user)}`)")
        embed.description = "\n".join(descriptions)
        date_and_time = []
        date_and_time.append(f"**Created on:** <t:{entry.end_time - entry.duration}:F>")
        date_and_time.append(f"**Duration:** {humanize_timedelta(seconds=entry.duration)}")
        date_and_time.append(f"**Time left:** {humanize_timedelta(seconds=entry.end_time - round(time()))}")
        date_and_time.append(f"**Ends:** <t:{entry.end_time}:F> <t:{entry.end_time}:R>")
        embed.add_field(name="\u200b", value="\n".join(date_and_time), inline=False)

        embed.description = "\n".join(descriptions)
        if (entry.required_roles or entry.amari_weekly_xp > 0 or entry.amari_level > 0) and guild is not None:
            req_list = []
            amari_reqs = []
            req_str = ""
            if entry.required_roles is not None:
                for req in entry.required_roles:
                    role = guild.get_role(req)
                    role = role.mention if role else f"{req} (Unknown role)"
                    req_list.append(role)
            if entry.amari_level > 0:
                amari_reqs.append(f"<:DVB_Amari:975377537658134528> Amari **Level**: `{entry.amari_level}`")
            if entry.amari_weekly_xp > 0:
                amari_reqs.append(f"<:DVB_Amari:975377537658134528> Amari **Weekly XP**: `{entry.amari_weekly_xp} XP`")
            if len(req_list) > 0:
                req_str += ", ".join(req_list)
            if len(amari_reqs) > 0:
                if req_str == "":
                    req_str = "\n".join(amari_reqs)
                else:
                    req_str = req_str + "\n" + "\n".join(amari_reqs)
                embed.add_field(name="Requirements", value=req_str, inline=True)
        if entry.bypass_roles and guild is not None:
            req_list = []
            for req in entry.bypass_roles:
                role = guild.get_role(req)
                role = role.mention if role else f"{req} (Unknown role)"
                req_list.append(role)
            if len(req_list) > 0:
                embed.add_field(name="Bypass Roles", value=", ".join(req_list))
        if entry.blacklisted_roles and guild is not None:
            req_list = []
            for req in entry.blacklisted_roles:
                role = guild.get_role(req)
                role = role.mention if role else f"{req} (Unknown role)"
                req_list.append(role)
            if len(req_list) > 0:
                embed.add_field(name="Blacklisted Roles", value="\n ".join(req_list))
        if entry.multi and guild is not None:
            req_list = []
            for role_id, number_of_entries in entry.multi.items():
                role = guild.get_role(int(role_id))
                if role is not None:
                    req_list.append(f"{role.mention}: **{number_of_entries}** extra entries")
            if len(req_list) > 0:
                embed.add_field(name="Extra Entries", value="\n ".join(req_list), inline=False)
        embed.set_footer(text=f"{plural(entry.winners):winner} will be picked for this giveaway.")
        return embed

    async def format_giveaway_embed(self, entry: GiveawayEntry, winners: typing.Optional[list] = None) -> discord.Embed:
        guild = self.client.get_guild(entry.guild_id)
        embed = discord.Embed(title=entry.title, color=self.client.embed_color)
        if entry.active is True and winners is not None:
            descriptions = ["Press the button to enter!"]
        else:
            descriptions = []
        user = self.client.get_user(entry.host_id)
        user_str = user.mention if user else entry.host_id
        descriptions.append(f"**Host:** {user_str}")
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
        if (entry.required_roles or entry.amari_weekly_xp > 0 or entry.amari_level > 0) and guild is not None:
            req_list = []
            amari_reqs = []
            req_str = ""
            if entry.required_roles is not None:
                for req in entry.required_roles:
                    role = guild.get_role(req)
                    role = role.mention if role else f"{req} (Unknown role)"
                    req_list.append(role)
            if entry.amari_level > 0:
                amari_reqs.append(f"<:DVB_Amari:975377537658134528> Amari **Level**: `{entry.amari_level}`")
            if entry.amari_weekly_xp > 0:
                amari_reqs.append(f"<:DVB_Amari:975377537658134528> Amari **Weekly XP**: `{entry.amari_weekly_xp} XP`")
            if len(req_list) > 0:
                req_str += ", ".join(req_list)
            if len(amari_reqs) > 0:
                if req_str == "":
                    req_str = "\n".join(amari_reqs)
                else:
                    req_str = req_str + "\n" + "\n".join(amari_reqs)
            embed.add_field(name="Requirements", value=req_str, inline=True)
        if entry.channel_id in [992065949320630363, 992366430857203833] and (winners is None or len(winners) == 0):
            if entry.multi and guild is not None:
                req_list = []
                for role_id, number_of_entries in entry.multi.items():
                    role = guild.get_role(int(role_id))
                    if role is not None:
                        req_list.append(f"{role.mention}: **{number_of_entries}** extra entries")
                if len(req_list) > 0:
                    embed.add_field(name="Extra Entries", value="\n ".join(req_list), inline=False)
        if winners is not None and len(winners) > 0:
            embed.add_field(name="Winners", value=str(human_join([w.mention for w in winners], ", ", "and")), inline=False)
        embed.set_footer(text=f"{plural(entry.winners):winner} will be picked.")
        title_lower = entry.title.lower()
        if "boost" in title_lower:
            embed.set_thumbnail(url="https://emoji.discord.st/emojis/c340b8cc-587c-4c39-a162-52c4499a3ee1.gif")
        elif "nitro" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/810398162702958662.gif?size=128&quality=lossless")
        elif "odd" in title_lower and "eye" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1058460091113816165.gif")
        elif "tro" in title_lower or "trophy" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/940712966213496842.gif?quality=lossless")
        elif "pem" in title_lower or "medal" in title_lower:    
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/948673104870252564.gif?size=128&quality=lossless")
        elif "bolt" in title_lower or "cutter" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/831023529255632898.webp?quality=lossless")
        elif "million" in title_lower or "mil" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/837629198415691786.webp?size=96&quality=lossless")
        elif "coin" in title_lower or "pec" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/942212715454271518.gif?quality=lossless")
        elif "crown" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/834862725120917544.webp?quality=lossless")
        elif "karen" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/860196324762452028.webp?quality=lossless")
        elif "credit" in title_lower and entry.channel_id != 853113922272624650:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/892546328406663168.webp?quality=lossless")
        elif "enchanted" in title_lower and "badosz" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/931295850292989973.gif?quality=lossless")
        elif "lottery" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/828630267983298580.webp?quality=lossless")
        elif "cupid" in title_lower or "toes" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/718136880163586169.webp?quality=lossless")
        elif "bank" in title_lower or "note" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/830509316888985621.webp?quality=lossless")
        elif "ribbon" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/890646381482614824.webp?quality=lossless")
        elif "phallic" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/841123648911966219.gif?quality=lossless")
        elif "laptop" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/830509316674813974.webp?quality=lossless")
        elif "fool" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/826974895295692840.webp?quality=lossless")
        elif "santa" in title_lower:
            if "hat" in title_lower:
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/921546940032880660.webp?quality=lossless")
            elif "bag" in title_lower:
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/862415055622635560.webp?quality=lossless")
        elif "pepe" in title_lower and "sus" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/890646381189009438.webp?quality=lossless")
        elif "stocking" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/920812196567597067.webp?quality=lossless")
        elif "cursed" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/933194488241864704.webp?quality=lossless")
        elif "blob" in title_lower:
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/933188762782011454.gif?quality=lossless")
        else:
            guild = self.client.get_guild(entry.guild_id)
            if guild is not None and guild.icon is not None:
                embed.set_thumbnail(url=guild.icon.url)
        if entry.multi and guild is not None:
            req_list = []
            for role_id, number_of_entries in entry.multi.items():
                role = guild.get_role(int(role_id))
                if role is not None:
                    req_list.append(f"{role.mention}: **{number_of_entries}** extra entries")
            if len(req_list) > 0:
                embed.add_field(name="Extra Entries", value="\n ".join(req_list), inline=False)
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
                        continue
                    p_message = channel.get_partial_message(entry.message_id)
                    cached_embed = self.cached_embeds.get(entry.message_id, None)
                    self.cached_embeds[entry.message_id] = embed
                    if cached_embed is not None:
                        if cached_embed.to_dict() == embed.to_dict():
                            continue

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
                        await self.client.get_user(312876934755385344).send(f"```\nFailed to end {entry}: {e}\n```")
                    else:
                        await self.client.db.execute("UPDATE giveaways SET active = False WHERE message_id = $1",
                                                     entry.message_id)
        except Exception as e:
            print(f"Checking/ending giveaways received an error: {e}")

    @commands.group(name="giveawayconfig", aliases=["gwconfig"], invoke_without_command=True)
    @checks.has_permissions_or_role(manage_roles=True)
    async def giveawayconfig(self, ctx: DVVTcontext):
        """
        Giveaway configurations can be set for specific channels. In each channel, you can choose roles that can bypass the giveaway requirement, roles that are blacklisted from joining or roles that can gain extra entries from the giveaway.
        This command will show you all existing configurations for various channels in the server.
        """
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
        paginator = SingleMenuPaginator(pages=embeds)
        await paginator.send(ctx)

    @giveawayconfig.command(name="add", aliases=["create", "new"])
    @checks.has_permissions_or_role(manage_roles=True)
    async def giveawayconfig_add(self, ctx: DVVTcontext, channel: discord.TextChannel = None):
        """
        Creates a fresh new giveaway profile for a channel.
        """
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
        """
        Edits the giveaway profile for a channel.
        Unlike many other bots, there is only one command for editing bypass, blacklist and multi roles all in one go.
        You can choose what you want to edit by selecting the buttons, and following the instructions for adding or removing roles.
        """
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

    @giveawayconfig.command(name="remove", aliases=["delete"])
    @checks.has_permissions_or_role(manage_roles=True)
    async def giveawayconfig_remove(self, ctx: DVVTcontext, channel: discord.TextChannel = None):
        """
        Deletes a channel's existing giveaway profile.
        """
        if channel is None:
            return await ctx.send(f"You must specify a channel to delete its giveaway profile.")
        if (existing_config := await self.client.db.fetchrow("SELECT * FROM giveawayconfig WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, channel.id)) is None:
            return await ctx.send(
                f"You do not have a giveaway profile set for {channel.mention}.")
        else:
            confirmview = confirm(ctx, self.client, 30)
            confirmview.response = await ctx.send(f"**Are you sure** you want to **delete** the giveaway profile for {channel.name}?\nThis action cannot be undone.", view=confirm)
            await confirmview.wait()
            if confirmview.returning_value is not True:
                return await confirmview.response.edit(content=confirmview.response.content + "\n\nNo action was done.")
            await self.client.db.execute("DELETE FROM giveawayconfig WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, channel.id)
            return await ctx.send(f"The giveaway profile for {channel.mention} has been deleted.")

    giveaway_group = SlashCommandGroup("giveaway", "Giveaway commands")

    @giveaway_group.command(name='start', description="Start a giveaway!")
    @checks.has_permissions_or_role(manage_roles=True)
    async def start_giveaway(self, ctx: discord.ApplicationContext,
                             duration: discord.Option(str, "The duration of the giveaway"),
                             prize: discord.Option(str, "The prize of the giveaway"),
                             winners: discord.Option(int, "The number of winners for the , defaults to 1", min_value=1, max_value=30, default=1) = 1,
                             donor: discord.Option(discord.Member, "The user who donated for this giveaway.") = None,
                             message: discord.Option(str, "The message to display for the giveaway") = None,
                             required_role: discord.Option(discord.Role, "The role required to participate in the giveaway") = None,
                             required_role2: discord.Option(discord.Role, "A second required role to participate in the giveaway") = None,
                             required_role3: discord.Option(discord.Role, "A third required role to participate in the giveaway") = None,
                             amari_level: discord.Option(int, "An optional Amari Level requirement") = 0,
                             amari_weekly_xp: discord.Option(int, "An optional Amari Weekly XP requirement") = 0,
                             channel: discord.Option(discord.TextChannel, "Specify another channel to start the giveaway there") = None,
                             ping: discord.Option(str, "Ping a giveaway ping immediately after giveaway starts.", choices=['gang', 'elite', 'nitro', 'owo', 'karuta']) = None,
                             rolemulti1: discord.Option(discord.Role, "Role for the first multi") = None,
                             multi1: discord.Option(int, "Number of the first multi") = None,
                             rolemulti2: discord.Option(discord.Role, "Role for the second multi") = None,
                             multi2: discord.Option(int, "Number of the second multi") = None,
                             ):
        # gang channel check
        if channel is None:
            channel = ctx.channel
        pings = {
            'gang': {
                'role_id': 758175760909074432,
                'required_role': [627284965222121482],
                'required_channel': [701771740912549938, 626704430468825089, 630587061665267713, 1376848574247206972],
                'text': "Join the giveaway above ♡"
            },
            'elite': {
                'role_id': 758174135276142593,
                'required_role': [627284965222121482],
                'required_channel': [701771740912549938, 741254464303923220, 630587061665267713, 1376848574247206972],
                'text': "Join the Elite giveaway above ♡"
            },
            'karuta': {
                'role_id': 847846998429139014,
                'required_role': [843756047964831765],
                'required_channel': [847375661332299786],
                'text': "Join the Karuta giveaway above and thank the sponsor! ♡"
            },
            'owo': {
                'role_id': 847538763412668456,
                'required_role': [837595910661603330],
                'required_channel': [847830388713586738],
                'text': "Join the OwO giveaway above and thank the sponsor! ♡",
            'nitro': {
                'role_id': 685233344136609812,
                'required_role': [627284965222121482],
                'required_channel': [650244237744537630],
                'text': "Join the **Nitro** giveaway above ♡"
            }

            }
        }
        if ping is not None:
            ping_config = pings.get(ping, None)
        else:
            ping_config = None
        if os.getenv('state') == '0':
            print(f"ping is not None: {ping is not None}\nping_config is not None: {ping_config is not None}")
            if ping is not None:
                if ping_config is not None:
                    required_roles_for_ping = ping_config.get('required_role', [])
                    if len(required_roles_for_ping) > 0 and not ctx.author.guild_permissions.manage_roles:
                        if any([discord.utils.get(ctx.author.roles, id=required_roleid) for required_roleid in required_roles_for_ping]):
                            pass
                        else:
                            display_required_roles_ping = ", ".join((f"<@&{rrid}>" for rrid in required_roles_for_ping))
                            await ctx.respond(f"You need one of the following roles to use the `{ping}` ping: {display_required_roles_ping}", ephemeral=True)
                            ping = None
                    required_channels_for_ping = ping_config.get('required_channel', [])
                    if len(required_channels_for_ping) > 0:
                        if channel.id in required_channels_for_ping:
                            pass
                        else:
                            display_required_channels_ping = ", ".join(
                                (f"<#{c_id}>" for c_id in required_channels_for_ping))
                            await ctx.respond(
                                f"The `{ping}` ping can only be used in these channels: {display_required_channels_ping}",
                                ephemeral=True)
                            ping = None
                else:
                    await ctx.respond("Invalid `ping` parameter.", ephemeral=True)
        channel = ctx.guild.get_channel(channel.id) # properly get the permissions
        if not (channel.permissions_for(ctx.author).send_messages and channel.permissions_for(ctx.author).view_channel):
            return await ctx.respond(f"You are not allowed to start a giveaway in {channel.mention}, as you are not allowed to view that channel or send messages in it.", ephemeral=True)
        required_roles = []
        required_roles_set_by_server = False
        if required_role is not None:
            required_roles.append(required_role)
        if required_role2 is not None:
            required_roles.append(required_role2)
        if required_role3 is not None:
            required_roles.append(required_role3)
        """if channel.id == elite_gw_channel:
            if (voterole := ctx.guild.get_role(voteid)) is not None:
                if voterole not in required_roles:
                    required_roles.append(voterole)
                    required_roles_set_by_server = True"""
        result = await self.client.db.fetchrow("SELECT * FROM giveawayconfig WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, channel.id)
        g_config = GiveawayConfig(result)
        if g_config.blacklisted_roles is None:
            g_config.blacklisted_roles = []
        blacklisted_roles = []
        for r_id in g_config.blacklisted_roles:
            if (r := ctx.guild.get_role(r_id)) is not None:
                blacklisted_roles.append(r)
        blacklisted_set_by_server = False
        if len(blacklisted_roles) > 0:
            blacklisted_set_by_server = True

        if g_config.bypass_roles is None:
            g_config.bypass_roles = []
        bypass_roles = []
        for r_id in g_config.bypass_roles:
            if (r := ctx.guild.get_role(r_id)) is not None:
                bypass_roles.append(r)
        if bypass_roles is None:
            bypass_roles = []
        bypass_set_by_server = False
        if len(bypass_roles) > 0:
            bypass_set_by_server = True

        if g_config.multi is None:
            g_config.multi = {}

        multi = {}
        for r_id, m_count in g_config.multi.items():
            if (r := ctx.guild.get_role(int(r_id))) is not None:
                multi[r] = m_count
        if rolemulti1 is not None and multi1 is not None:
            multi[rolemulti1] = multi1
        if rolemulti2 is not None and multi2 is not None:
            multi[rolemulti2] = multi2

        multi_set_by_server = False
        if len(multi.keys()) > 0:
            multi_set_by_server = True

        try:
            duration: int = stringtime_duration(duration)
        except ValueError:
            await ctx.respond("You didn't provide a proper duration.", ephemeral=True)
            return
        if duration is None:
            await ctx.respond("You didn't provide a proper duration.", ephemeral=True)
            return
        if prize.endswith('_hidecount'):
            prize = prize[:-10]
            show_count = False
        else:
            show_count = True
        if ctx.guild.premium_subscriber_role in required_roles:
            cfm_view = confirm(ctx, self.client, 30)
            embed = discord.Embed(title="Hmm...", description=f"Looks like you have {ctx.guild.premium_subscriber_role.mention} (a booster role) as a requirement for joining this giveaway.\n\nDo you want to remove the bypass roles for this giveaway? This will make it such that only boosters can join it.", color=discord.Color.yellow())
            cfm_view.response = await ctx.respond(embed=embed, view=cfm_view, ephemeral=True)
            await cfm_view.wait()
            if cfm_view.returning_value is True:
                bypass_roles = []
            else:
                pass
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
            req_r_str = f"**Required roles**: {', '.join(r.mention for r in required_roles)}"
            if required_roles_set_by_server:
                req_r_str += " (set by server)"
            descriptions.append(req_r_str)
        if len(blacklisted_roles) > 0:
            bl_r_str = f"**Blacklisted roles**: {', '.join(r.mention for r in blacklisted_roles)}"
            if blacklisted_set_by_server:
                bl_r_str += " (set by server)"
            descriptions.append(bl_r_str)
        if required_roles:
            if len(bypass_roles) > 0:
                by_r_str = f"**Bypass roles**: {', '.join(r.mention for r in bypass_roles)}"
                if bypass_set_by_server:
                    by_r_str += " (set by server)"
                descriptions.append(by_r_str)
        if show_count is not True:
            descriptions.append("**Hide the entrant count**: <:DVB_True:887589686808309791> **Yes**")
        if len(multi.keys()) > 0:
            multi_stdout = "\n".join([f"{r.mention}: x{m_count}" for r, m_count in multi.items()])
            m_r_str = f"**Multi roles**: {multi_stdout}"
            if multi_set_by_server:
                m_r_str += "\n(set by server)"
            descriptions.append(m_r_str)
        if amari_level > 0:
            descriptions.append(f"<:DVB_Amari:975377537658134528> **Amari Level**: {amari_level}")
        if amari_weekly_xp > 0:
            descriptions.append(f"<:DVB_Amari:975377537658134528> **Amari Weekly XP**: {amari_weekly_xp}")

        if channel != ctx.channel:
            descriptions.append(f"\nGiveaway will be started in another channel ({channel.mention})")
        role_to_ping_id = ping_config.get('role_id', None) if ping_config is not None else None
        if ping is not None and role_to_ping_id is not None:
            descriptions.append(f"<@&{role_to_ping_id}> will be pinged once the giveaway starts.\n**Make sure you're pinging the right role in the right channel.**")
        embed = discord.Embed(title="Are you ready to start this giveaway?", description="\n".join(descriptions), color=self.client.embed_color)
        confirmview = confirm(ctx, self.client, timeout=180)
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
        if required_roles:
            bypass_role_list_str = ",".join([str(role.id) for role in bypass_roles]) if type(bypass_roles) == list and len(bypass_roles) > 0 else None
        else:
            bypass_role_list_str = None
        giveawaymessage = await channel.send(embed=discord.Embed(title="<a:DVB_Loading:909997219644604447> Initializing giveaway...", color=self.client.embed_color))
        multi = {str(r.id): m_count for r, m_count in multi.items()}
        await self.client.db.execute("INSERT INTO giveaways (guild_id, channel_id, message_id, title, host_id, donor_id, winners, required_roles, blacklisted_roles, amari_level, amari_weekly_xp, bypass_roles, multi, duration, end_time, showentrantcount) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)",
                                     ctx.guild.id, channel.id, giveawaymessage.id, prize, ctx.author.id, donor.id if donor is not None else None, winners, required_role_list_str, blacklisted_role_list_str, amari_level, amari_weekly_xp, bypass_role_list_str, json.dumps(multi), duration, round(time() + duration), show_count)
        giveawayrecord = await self.fetch_giveaway(giveawaymessage.id)
        embed = await self.format_giveaway_embed(giveawayrecord, None)
        g_view = GiveawayView(self.client, self)
        # make button disabled if is hidecount
        g_view.children[3].disabled = not show_count
        await giveawaymessage.edit(embed=embed, view=g_view)
        if donor is None:
            donor = ctx.author
        if message is not None:
            dis_name = f"{donor.display_name} (sponsor)" if len(donor.display_name) <= 22 else donor.display_name
            webh = await self.client.get_webhook(giveawaymessage.channel)
            if webh is not None:
                try:
                    await webh.send(message, username=dis_name, avatar_url=donor.display_avatar.url, allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))
                except:
                    await giveawaymessage.channel.send(embed=discord.Embed(description=message, color=self.client.embed_color).set_author(name=dis_name, icon_url=donor.display_avatar.url))
                else:
                    pass
            else:
                await giveawaymessage.channel.send(embed=discord.Embed(description=message, color=self.client.embed_color).set_author(name=dis_name, icon_url=donor.display_avatar.url))
        if ping is not None and role_to_ping_id is not None:
            msg = ping_config.get('text', "Join the giveaway above ♡")
            msg = await channel.send(f"<@&{role_to_ping_id}>\n{msg}", allowed_mentions=discord.AllowedMentions(roles=True, everyone=False))
            await msg.add_reaction('<:dv_wCyanHeartOwO:837700662192111617>')
        if channel != ctx.channel:
            await ctx.respond(f"{DVB_True} Giveaway started!", ephemeral=True)
        await asyncio.sleep(180.0)
        g_view.children[2].disabled = True
        await giveawaymessage.edit(view=g_view)
        if len(g_view.thankers) > 3:
            thankers = [user.display_name for user in g_view.thankers]
            if len(thankers) <= 20:
                thank_str = human_join(thankers, final='and')
            else:
                thank_str = ", ".join(thankers[:20]) + f" and {len(thankers) - 20} others"
            gen_chat = ctx.guild.get_channel(gen_chat_id)

            if gen_chat is not None:
                await gen_chat.send(f"**{thank_str}** {'has' if len(thankers) == '0' else 'have'} thanked **{donor.mention}** for their **{prize}** giveaway in {giveawaymessage.channel.mention}! {random.choice(['<:dv_textThankyouOwO:837712265469231166>', '<:dv_catBlushOwO:837713048738332672>', '<a:dv_ghostLoveOwO:837712735927533609>', '<:dv_heartFloatOwO:837681322474340432>', '<:dv_frogLoveOwO:837667445316517929>', '<:dv_nyaHugOwO:837669886020812870>', '<a:dv_nyaHugOwO:837735002191560714>', '<a:dv_pandaHeartsOwO:837769010691047485>', '<a:dv_pandaLoveOwO:837769036333973555>', '<a:dv_pandaSnuggleOwO:837771845767528468>', '<:dv_pandaPeaceOwO:837699353191776346>', '<:dv_paulLoveOwO:837712577466597446>', '<:dv_remHeartOwO:837681472965181511>', '<:dv_textThankyouOwO:837712265469231166>'])}")
                


    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='trophy', aliases=['tro'])
    async def trophy_giveaway(self, ctx):
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
        duration = 86400
        prize = "<a:dv_iconOwO:837943874973466664> 1 Pepe Trophy"
        winner = 1
        if winner < 1:
            return await ctx.send("You must have at least one winner.")
        elif winner > 80:
            return await ctx.send("You cannot have more than 80 winners.")
        if len(prize) > 70:
            return await ctx.send("The prize's name cannot be longer than 70 characters.")
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
                if prize == "<a:dv_iconOwO:837943874973466664> 1 Pepe Trophy":
                    additional_message = "Enter the daily trophy giveaway above! <:DVB_Trophy:911244980599804015>"
                else:
                    additional_message = f"Join the giveaway above ♡"
                await ctx.send(f"<@&{pingrole}>", allowed_mentions=discord.AllowedMentions(everyone=False, roles=True, users=True))

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

    @checks.has_permissions_or_role(manage_roles=True)
    @giveaway.command(name="cancel", aliases=['c'])
    async def giveaway_cancel(self, ctx, message_id: BetterMessageID = None):
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
            return
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
            return
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
    async def giveaway_reroll(self, ctx, message_id: typing.Optional[BetterMessageID] = None, winner: int = None):
        """
        Rerolls the winner for a giveaway.
        """
        if message_id is None:
            if ctx.message.reference is None:
                return "A Message ID is required, or you need to reply to a message containing a giveaway."
            message_id = ctx.message.reference.message_id
        result = await self.client.db.fetchrow("SELECT * FROM giveaways WHERE message_id = $1 AND guild_id = $2", message_id, ctx.guild.id)
        if result is None:
            with contextlib.suppress(Exception):
                await ctx.send(f"No giveaway was found with the message ID {message_id}.", delete_after=5.0)
            with contextlib.suppress(Exception):
                await ctx.message.delete()
            return
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
            winnerdmmsg = ['Generic',
                           "Depending on the type of giveaway you won, you will either receive the prize within 24 hours or need to claim from the giveaway host. If you're unsure, feel free to check with a moderator from <#870880772985344010>."]
            if channel.id in [701771740912549938]:
                winnerdmmsg = ["Dank Memer",
                               "As this is a flash giveaway, the prize will be given to you almost immediately. \nYou must accept the trade sent from the giveaway host, or you will be rerolled."]
            if channel.id in [701771740912549938, 626704430468825089, 741254464303923220, 803039330310029362]:
                winnerdmmsg = ["Dank Memer",
                               "Please be patient and wait for a DM from `Atlas#2867` notifying you to claim your prize.\nKindly claim within **3** hours after receiving the Atlas DM, do **not** try to claim before the DM."]
            elif channel.id in [847375661332299786]:
                winnerdmmsg = ["Karuta",
                               "Please claim your prize by DMing/pinging the host within **24** hours after winning."]
            elif channel.id in [847830388713586738]:
                winnerdmmsg = ["OwO Bot",
                               "Please wait **24 hours** before contacting the host if you haven't received your prize."]
            elif channel.id in [853113922272624650]:
                winnerdmmsg = ["Pokemon",
                               "Please wait **24 hours** before contacting the host if you haven't received your prize."]
            elif channel.id in [650244237744537630]:
                winnerdmmsg = ["Nitro",
                               "You might need to claim the nitro from the sponsor/giveaway host within a limited time, depending on the giveaway's requirements."]
            msg_link = f"https://discord.com/channels/{ctx.guild.id}/{giveaway.channel_id}/{giveaway.message_id}"
            winembed = discord.Embed(title=f"You've won the __reroll__ for the {giveaway.title} giveaway!",
                                     description=f"{winnerdmmsg[1]}\n\n[Link to giveaway]({msg_link})",
                                     color=0x2fbf71, timestamp=discord.utils.utcnow()).set_footer(
                text=f"Giveaway type: {winnerdmmsg[0]}")
            winembed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
            for winner in winners:
                try:
                    await winner.send(embed=winembed)
                except:
                    pass



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
                message_link = f"https://discord.com/channels/{ctx.guild.id}/{giveaway.channel_id}/{giveaway.message_id}"
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
        #gang channel check
        if os.getenv('state') == '0':
            if ctx.channel.id not in [701771740912549938, 626704430468825089, 630587061665267713, 1376848574247206972]:
                return await ctx.send("You cannot use this command in this channel! �")
        if text is None:
            text = "Join the giveaway above ♡"
        emojis = ['<a:dv_aBCNodOwO:837756826564952096>', '<a:dv_bunbunDanceOwO:837749889496514570>', '<a:dv_aHeartsWaveOwO:837741729321844847>', '<a:dv_aPinkOwO:837756828866707497>', '<a:dv_aWiggleOwO:837756830053695560>', '<a:dv_bunbunDanceOwO:837764938734108693>', '<a:dv_pandaMadOwO:837772023110303834>', '<a:dv_foxCuddlesOwO:837744615499104266>', '<a:dv_nekoWaveOwO:837756827255963718>', '<a:dv_pandaHeartsOwO:837769010691047485>', '<a:dv_pandaLoveOwO:837769036333973555>', '<a:dv_pandaExcitedOwO:837772105822502912>', '<a:dv_panHeartsOwO:837712562434342952>', '<a:dv_pikaWaveOwO:837712214935732265>', '<a:dv_qbFlowerOwO:837773808269525052>', '<a:dv_qbThumbsupOwO:837666232811257907>', '<a:dv_squirrelBodyRollOwO:837726627160129558>', '<a:dv_squirrelHappyOwO:837711561338519572>', '<a:dv_wButterflyOwO:837787067912159233>', '<a:dv_wScribbleHeartOwO:837782023631798302>', '<a:dv_wYellowMoonOwO:837787073066303551>', '<a:dv_wpinkHeartOwO:837781949337960467>', '<a:dv_wRainbowHeartOwO:837787078171033660>']
        emoji = random.choice(emojis)
        msg = await ctx.send(f"{emoji} **<@&758175760909074432>** {emoji}\n{text}", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=True))
        await msg.add_reaction('<:dv_wCyanHeartOwO:837700662192111617>')

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.cooldown(240, 1, commands.BucketType.guild)
    @giveaway.command(name='elite')
    async def giveaway_elite(self, ctx, *, text=None):
        await ctx.message.delete()
        #elite channel check
        if os.getenv('state') == '0':
            if ctx.channel.id not in [701771740912549938, 741254464303923220, 630587061665267713, 1376848574247206972, 803039330310029362]:
                return await ctx.send("You cannot use this command in this channel! �")
        if text is None:
            text = "Join the Elite giveaway above ♡"
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
            text = "Join the Booster giveaway above ♡"
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
            if ctx.channel.id not in [650244237744537630, 630587061665267713, 1376848574247206972]:
                return await ctx.send("You cannot use this command in this channel! �")
        if text is None:
            text = "Join the Nitro giveaway above ♡"
        emojis = ['<a:dv_aBCNodOwO:837756826564952096>', '<a:dv_bunbunDanceOwO:837749889496514570>', '<a:dv_aHeartsWaveOwO:837741729321844847>', '<a:dv_aPinkOwO:837756828866707497>', '<a:dv_aWiggleOwO:837756830053695560>', '<a:dv_bunbunDanceOwO:837764938734108693>', '<a:dv_pandaMadOwO:837772023110303834>', '<a:dv_foxCuddlesOwO:837744615499104266>', '<a:dv_nekoWaveOwO:837756827255963718>', '<a:dv_pandaHeartsOwO:837769010691047485>', '<a:dv_pandaLoveOwO:837769036333973555>', '<a:dv_pandaExcitedOwO:837772105822502912>', '<a:dv_panHeartsOwO:837712562434342952>', '<a:dv_pikaWaveOwO:837712214935732265>', '<a:dv_qbFlowerOwO:837773808269525052>', '<a:dv_qbThumbsupOwO:837666232811257907>', '<a:dv_squirrelBodyRollOwO:837726627160129558>', '<a:dv_squirrelHappyOwO:837711561338519572>', '<a:dv_wButterflyOwO:837787067912159233>', '<a:dv_wScribbleHeartOwO:837782023631798302>', '<a:dv_wYellowMoonOwO:837787073066303551>', '<a:dv_wpinkHeartOwO:837781949337960467>', '<a:dv_wRainbowHeartOwO:837787078171033660>']
        emoji = random.choice(emojis)
        msg = await ctx.send(f"{emoji} **<@&685233344136609812>** {emoji}\n{text}", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=True))
        await msg.add_reaction('<:dv_wCyanHeartOwO:837700662192111617>')

    def cog_unload(self):
        self.end_giveaways.stop()
        self.change_entrantcount.stop()