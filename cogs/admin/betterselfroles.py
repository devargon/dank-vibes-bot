import asyncio
import re
from typing import Union

import discord
from emoji import UNICODE_EMOJI

from utils import checks
from discord.ext import commands
from utils.format import get_command_name, split_string_into_list, human_join
from utils.converters import BetterRoles, AllowDeny, BetterMessageID

from cogs.admin.contests import SubmissionApproval, VoteView, HowToSubmit1, DisplayVoteView

custom_emoji_regex = re.compile('<(a?):([A-Za-z0-9_]+):([0-9]+)>')

class RoleMenu(discord.ui.Select):
    def __init__(self, options, select_placeholder, roles, msg_id, max_selectable):
        if max_selectable is None:
            max_selectable = len(options)
        super().__init__(options=options,
                         placeholder=select_placeholder if type(select_placeholder) == str else None,
                         custom_id=str(msg_id),
                         min_values=0,
                         max_values=max_selectable,
                         )

    async def callback(self, interaction: discord.Interaction):
        client = self.view.client
        await interaction.response.defer(ephemeral=True)
        to_remove_roles = []
        to_add_roles = []
        invalid_roles = []
        for selected_role_ids in self.values:
            selected_role = interaction.guild.get_role(int(selected_role_ids))
            if selected_role is not None:
                if selected_role in interaction.user.roles:
                    if self.max_values == 1:
                        to_remove_roles.append(selected_role)
                    else:
                        invalid_roles.append(f"You already have the {selected_role.mention} role.")
                else:
                    to_add_roles.append(selected_role)
            else:
                invalid_roles.append(f"Role {selected_role_ids} not found.")

        for str_role_id in [option.value for option in self.options]:
            if (r := interaction.guild.get_role(int(str_role_id))) is not None:
                if str_role_id not in self.values and r in interaction.user.roles:
                    to_remove_roles.append(r)
        for role in to_remove_roles:
            try:
                await interaction.user.remove_roles(role)
            except discord.Forbidden:
                to_remove_roles.remove(role)
                invalid_roles.append(f"I am not allowed to remove {role.mention} from you.")
            except discord.HTTPException:
                to_remove_roles.remove(role)
                invalid_roles.append(f"Something went wrong while removing {role.mention}.")
            else:
                pass
        remarks = ""
        if len(to_add_roles) > 0:
            if len(to_add_roles) > 1:
                max = await client.db.fetchval("SELECT max_gettable_role FROM selfroles WHERE message_id = $1", interaction.message.id)
                if max is not None:
                    remarks = f"\n\nYou can only get {max} roles from this message."
                    to_add_roles = to_add_roles[:max-1]
            required_roles = await client.db.fetchval("SELECT required_role FROM selfroles WHERE message_id = $1", interaction.message.id)
            required_roles = split_string_into_list(required_roles, int)
            if len(required_roles) == 0:
                allowed_to_get_roles = True
            else:
                allowed_to_get_roles = False
                for r_id in required_roles:
                    if discord.utils.get(interaction.user.roles, id=r_id):
                        allowed_to_get_roles = True
                        break
            if not allowed_to_get_roles:
                to_add_roles = []
                remarks = "You need to be a " + human_join(
                    [f"__<@&{r_id}>__" for r_id in required_roles]) + " to get this role."
            else:
                for role in to_add_roles:
                    try:
                        await interaction.user.add_roles(role)
                    except discord.Forbidden:
                        to_add_roles.remove(role)
                        invalid_roles.append(f"I am not allowed to add {role.mention} to you.")
                    except discord.HTTPException:
                        to_add_roles.remove(role)
                        invalid_roles.append(f"Something went wrong while adding {role.mention}.")
                    else:
                        pass
        embed = discord.Embed(title="Updated your roles!", color=0xDFA9B1)
        if len(to_remove_roles) > 0:
            embed.add_field(name="<:DVB_RoleRemove:969888937394991114> Removed roles",
                            value="\n".join([f"➳ {role_ob.mention}" for role_ob in to_remove_roles]), inline=True)
        if len(to_add_roles) > 0:
            embed.add_field(name="<:DVB_RoleAdd:969888937290104902> Added roles",
                            value="\n".join([f"➳ {role_ob.mention}" for role_ob in to_add_roles]), inline=True)
        if len(to_remove_roles) + len(to_add_roles) == 0:
            embed.add_field(name="No changes were made to your roles.", value="\u200b", inline=True)
        if len(invalid_roles) > 0 or len(remarks) > 0:
            embed.add_field(name="\u200b", value="\n".join([f"- {rolestr}" for rolestr in invalid_roles]) if len(
                invalid_roles) > 0 else remarks, inline=False)
        await interaction.followup.send(embed=embed)



def format_emoji(arg: str) -> Union[discord.PartialEmoji, str, None]:
    """
    Returns an emoji that can be recognised by Discord's API.
    """
    if arg is not None:
        check = re.match(custom_emoji_regex, arg) is not None
        if check is True:
            arg = discord.PartialEmoji.from_str(arg)
        else:
            if arg in UNICODE_EMOJI['en']:
                pass
            else:
                raise EmojiNotFound
    return arg

class EmojiNotFound(Exception):
    pass

class EmojisDoNotMatchRoles(Exception):
    pass

class DescriptionsDoNotMatchRoles(Exception):
    pass

class RoleSelectMenu(discord.ui.View):
    def __init__(self, client):
        self.client = client
        super().__init__(timeout=None)

class random_color(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [758176387806396456]
        labels = ["Random Color"]
        emojis = ["<:prism:898494225874833428>"]
        ids = ['sr:randomcolor']
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.mention}** has been added to you.", ephemeral=True)
                else:
                    await interaction.user.remove_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.mention}** has been removed from you.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[emojis.index(emoji)], style=discord.ButtonStyle.grey, custom_id = ids[emojis.index(emoji)]))

class BoostPing(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [662876587687018507]
        emojis = ["<:BoosterGwPing:898495751372554261>"]
        ids = ['sr:boostergwping']
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if discord.utils.get(interaction.user.roles, id = 645934789160992768):
                    if role not in interaction.user.roles:
                        await interaction.user.add_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.mention}** has been added to you.", ephemeral=True)
                    else:
                        await interaction.user.remove_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.mention}** has been removed from you.", ephemeral=True)
                else:
                    await interaction.response.send_message("To get this role, you need to be a __Booster__.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label = "Booster Giveaway Ping", style=discord.ButtonStyle.grey, custom_id = ids[emojis.index(emoji)]))

class VIPHeist(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [817459252913635438]
        emojis = ["<:heistpepe:898493464684142663>"]
        ids = ['sr:vipheistping']
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if discord.utils.get(interaction.user.roles, id = 758173667682287616):
                    if role not in interaction.user.roles:
                        await interaction.user.add_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.mention}** has been added to you.", ephemeral=True)
                    else:
                        await interaction.user.remove_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.mention}** has been removed from you.", ephemeral=True)
                else:
                    await interaction.response.send_message("To get any of these roles, you need to be a __750M Donator (Dank Memer)__.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label="VIP Heist Ping", style=discord.ButtonStyle.grey, custom_id = ids[emojis.index(emoji)]))

class BetterSelfroles(commands.Cog):
    def __init__(self, client):
        self.client= client
        self.persistent_views_added = False

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.wait_until_ready()
        self.client.add_view(DisplayVoteView(self.client))
        self.client.add_view(VoteView(self.client, False))
        self.client.add_view(HowToSubmit1())
        sr_results = await self.client.db.fetch("SELECT * FROM selfroles")
        for result in sr_results:
            placeholder_for_select = result.get('placeholder_for_select')
            role_ids = result.get('role_ids')
            emojis = split_string_into_list(result.get('emojis'), str, include_empty_elements=True)
            print(emojis)
            descriptions = split_string_into_list(result.get('descriptions'), str, include_empty_elements=True)
            roles = []
            guild = self.client.get_guild(result.get('guild_id'))
            print(f"guild obj: `{guild}`, type: {type(guild)}, name: {str(guild)}")
            if guild is not None:
                role_ids = split_string_into_list(result.get('role_ids'), int)
                print(f"list of role_ids: {role_ids}")
                for role_id in role_ids:
                    role = guild.get_role(role_id)
                    if role is not None:
                        roles.append(role)
                    else:
                        print(f"`{role_id}` was none")
                        print(f"{type(role_id)}, {guild}")
                print(roles)
                options = []
                if len(emojis) == 0:
                    emojis = [None] * len(roles)
                if len(descriptions) == 0:
                    descriptions = [None] * len(roles)
                if emojis is not None and len(roles) != len(emojis):
                    raise EmojisDoNotMatchRoles
                elif descriptions is not None and len(roles) != len(descriptions):
                    raise DescriptionsDoNotMatchRoles
                for role, emoji, description in zip(roles, emojis, descriptions):
                    try:
                        emoji = format_emoji(emoji)
                    except EmojiNotFound:
                        emoji = None
                    op = discord.SelectOption(
                        label=role.name,
                        value=str(role.id),
                        description=description if isinstance(description, str) and len(description) > 0 else None,
                        emoji=emoji
                    )
                    options.append(op)
                roleview = RoleSelectMenu(self.client)
                roleview.add_item(RoleMenu(options, placeholder_for_select, roles, str(result.get('message_id')), result.get('max_gettable_role')))
                self.client.add_view(roleview)
        selfrolemessages = await self.client.db.fetchrow("SELECT random_color,  boostping, vipheist FROM selfrolemessages WHERE guild_id = $1", 595457764935991326)
        categories = ['random_color', 'boostping', 'vipheist']
        if selfrolemessages is not None:
            if not self.selfroleviews_added:
                if len(selfrolemessages) == 0:
                    self.selfroleviews_added = True
                    return
                if selfrolemessages.get('random_color'):
                    self.client.add_view(random_color())
                if selfrolemessages.get('boostping'):
                    self.client.add_view(BoostPing(), message_id=selfrolemessages.get('boostping'))
                if selfrolemessages.get('vipheist'):
                    self.client.add_view(VIPHeist(), message_id=selfrolemessages.get('vipheist'))
        unapproved_contest_entries = await self.client.db.fetch("SELECT * FROM contest_submissions WHERE approve_id IS NOT NULL and approved = FALSE")
        if len(unapproved_contest_entries) > 0:
            for entry in unapproved_contest_entries:
                h = SubmissionApproval(self.client, entry.get('contest_id'), entry.get('entry_id'), entry.get('submitter_id'))
                self.client.add_view(h)
        voting_active = await self.client.db.fetchval("SELECT voting FROM contests WHERE voting IS TRUE")

        self.selfroleviews_added = True


    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='fixselfroles')
    async def fixselfroles(self, ctx, message_id: BetterMessageID):
        """
        Attempt to fix the current implemented self roles by regenerating the buttons/selectmenus used for them.
        """
        selfrole_config = await self.client.db.fetchrow("SELECT * FROM selfroles WHERE message_id = $1", message_id)
        if selfrole_config is None:
            return await ctx.send(f"There is no self role set for a message with the ID `{message_id}`.")
        else:
            type = selfrole_config.get('type')
            title = selfrole_config.get('title')
            placeholder_for_select = selfrole_config.get('placeholder_for_select')
            role_ids = selfrole_config.get('role_ids')
            emojis = selfrole_config.get('emojis')
            descriptions = selfrole_config.get('descriptions')
            required_role = selfrole_config.get('required_role')
            role_ids = split_string_into_list(role_ids, int, ',')
            if len(role_ids) == 0:
                return await ctx.send("There are no roles to display for this self role.")
            emojis = split_string_into_list(emojis, str, ',', include_empty_elements=True)
            descriptions = split_string_into_list(descriptions, str, ',', include_empty_elements=True)

            roles = []
            for r_id in role_ids:
                if (role := ctx.guild.get_role(r_id)) is not None:
                    roles.append(role)
            if len(emojis) == 0:
                emojis = [None]*len(roles)
            if len(descriptions) == 0:
                descriptions = [None]*len(roles)
            if len(emojis) != len(roles):
                raise EmojisDoNotMatchRoles
            if len(descriptions) != len(roles):
                raise DescriptionsDoNotMatchRoles

            if 'select' in type:
                options = []
                if emojis is not None and len(roles) != len(emojis):
                    raise EmojisDoNotMatchRoles
                elif descriptions is not None and len(roles) != len(descriptions):
                    raise DescriptionsDoNotMatchRoles
                for role, emoji, description in zip(roles, emojis, descriptions):
                    try:
                        emoji = format_emoji(emoji)
                    except EmojiNotFound:
                        emoji = None
                    op = discord.SelectOption(
                        label=role.name,
                        value=str(role.id),
                        description=description if isinstance(description, str) and len(description) > 0 else None,
                        emoji=emoji
                    )
                    options.append(op)
                roleview = RoleSelectMenu(self.client)
                roleview.add_item(RoleMenu(options, placeholder_for_select, roles, message_id, selfrole_config.get('max_gettable_role')))
                if (chan := ctx.guild.get_channel(selfrole_config.get('channel_id'))) is not None:
                    try:
                        m = await chan.fetch_message(message_id)
                    except Exception as e:
                        return await ctx.send(f"Failed to fetch message with ID `{message_id}`: {e}")
                    else:
                        await m.edit(view=roleview)
                        await ctx.send("Done!")
                else:
                    return await ctx.send(f"Channel `{selfrole_config.get('channel_id')}` not found.")
            elif 'buttons' in type:
                pass
