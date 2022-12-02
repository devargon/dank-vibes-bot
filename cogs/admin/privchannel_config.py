import discord
from discord.ext import commands
from main import dvvt
from utils import checks
from utils.context import DVVTcontext
from utils.specialobjects import PrivateChannel
from typing import Union, Optional


def truefalse(op: bool):
    if op is True:
        return "<:DVB_True:887589686808309791>"
    else:
        return "<:DVB_False:887589731515392000>"

class EnableDisable(discord.ui.Button):
    def __init__(self, label, current_setting, custom_id):
        super().__init__(
            style=discord.ButtonStyle.green if current_setting is True else discord.ButtonStyle.red,
            label=label,
            custom_id=custom_id,
        )

    async def callback(self, interaction: discord.Interaction):
        current_setting = getattr(self.view.privchannel, self.custom_id)
        if current_setting is True:
            new_setting = False
            self.style = discord.ButtonStyle.red
        else:
            new_setting = True
            self.style = discord.ButtonStyle.green
        setattr(self.view.privchannel, self.custom_id, new_setting)
        await self.view.privchannel.update(interaction.client)
        self.view.format_embed()
        await interaction.response.edit_message(embed=self.view.embed, view=self.view)

class TriggerModalUpdate(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        existing_reason = getattr(self.view.privchannel, self.custom_id)
        m = EditText(self.label, existing_reason, "New restriction reason", None)
        await interaction.response.send_modal(m)
        await m.wait()
        setattr(self.view.privchannel, self.custom_id, m.value)
        await self.view.privchannel.update(interaction.client)
        self.view.format_embed()
        await interaction.message.edit(embed=self.view.embed)


class EditText(discord.ui.Modal):
    def __init__(self, title, existing_value, label, placeholder):
        self.value = None
        super().__init__(title=title)
        self.add_item(discord.ui.InputText(
            style=discord.InputTextStyle.long,
            label=label,
            placeholder=placeholder,
            min_length=0,
            max_length=512,
            value=existing_value)
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.value = self.children[0].value if len(self.children[0].value) > 0 else None



class PrivatechannelConfigView(discord.ui.View):
    def __init__(self, privchannel: PrivateChannel):
        self.privchannel = privchannel
        self.embed = None
        super().__init__(timeout=None, disable_on_timeout=True)

        self.add_item(EnableDisable("Add Members", self.privchannel.add_members, "add_members"))
        self.add_item(EnableDisable("Remove Members", self.privchannel.remove_members, "remove_members"))
        self.add_item(EnableDisable("Edit Name", self.privchannel.add_members, "edit_name"))
        self.add_item(EnableDisable("Edit Topic", self.privchannel.edit_topic, "edit_topic"))
        self.add_item(EnableDisable("Ignore Member Limit", self.privchannel.add_members, "ignore_member_limit"))
        self.add_item(TriggerModalUpdate(style=discord.ButtonStyle.grey, label="Update restriction reason", custom_id="restriction_reason"))

    def format_embed(self):
        embed = discord.Embed(title=f"Configure `{self.privchannel.channel.name}`", description=f"Owned by {self.privchannel.owner}")
        embed.add_field(name="Permissions", value="\u200b", inline=False)
        embed.add_field(name="Add Members", value=truefalse(self.privchannel.add_members))
        embed.add_field(name="Remove Members", value=truefalse(self.privchannel.remove_members))
        embed.add_field(name="Edit Channel Name", value=truefalse(self.privchannel.edit_name))
        embed.add_field(name="Edit Channel Topic", value=truefalse(self.privchannel.edit_topic))
        embed.add_field(name="Ignore Member Limit", value=truefalse(self.privchannel.ignore_member_limit))
        embed.add_field(name="Restrictions reason", value=self.privchannel.restriction_reason or "None", inline=False)
        self.embed = embed


class PrivchannelConfig(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    async def get_owner_channel(self, owner: Optional[discord.Member] = None, channel: Optional[discord.TextChannel] = None) -> Union[PrivateChannel, None]:
        if owner is None:
            if channel is None:
                return None
            else:
                channel_db = await self.client.db.fetchrow("SELECT * FROM channels WHERE owner_id = $1 AND active = TRUE", channel.id)
        else:
            channel_db = await self.client.db.fetchrow("SELECT * FROM channels WHERE owner_id = $1 AND active = TRUE", owner.id)
        if channel_db is None:
            return None
        if owner is None:
            owner = channel.guild.get_member(channel_db.get('owner_id'))
        if channel is None:
            channel = self.client.get_channel(channel_db.get('channel_id'))

        return PrivateChannel(owner, channel, channel_db)


    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="cpvc")
    async def privchannel_config(self, ctx: DVVTcontext, owner: Optional[discord.Member] = None, channel: Optional[discord.TextChannel] = None):
        if owner is None and channel is None:
            return await ctx.send("You need to specify a channel or channel owner.")

        c = await self.get_owner_channel(owner, channel)
        if c is None:
            if owner is None:
                return await ctx.send(f"{channel.mention} is not a private channel.")
            else:
                return await ctx.send(f"{owner.mention} does not own a private channel.")
        v = PrivatechannelConfigView(c)
        v.format_embed()
        await ctx.send(embed=v.embed, view=v)
