import time
from datetime import datetime
from typing import Optional

from thefuzz import process

from utils import checks
from utils.context import DVVTcontext
from utils.format import comma_number, stringnum_toint

import discord
from discord.ext import commands, pages
from main import dvvt
from utils.specialobjects import DankItem


class InputItemValue(discord.ui.Modal):
    def __init__(self):
        self.itemvalue: int = None
        super().__init__(title="Enter Celeb Donation Value")
        self.add_item(discord.ui.InputText(label="Enter Value Here", placeholder="Accepted formats: 1k, 1e6, 1m, 1000000", required=True, style=discord.InputTextStyle.short))

    async def callback(self, interaction: discord.Interaction):
        content = self.children[0].value
        try:
            evaluated_content = stringnum_toint(content)
        except Exception as e:
            self.itemvalue = None
            await interaction.response.send_message(f"<:DVB_False:887589731515392000> `{content}` is an invalid number. Please try again.", ephemeral=True)
        else:
            if evaluated_content is None:
                await interaction.response.send_message(f"<:DVB_False:887589731515392000> `{content}` is an invalid number. Please try again.", ephemeral=True)
            else:
                self.itemvalue = evaluated_content
                await interaction.response.send_message("Value set to **⏣ {}**".format(comma_number(evaluated_content)), ephemeral=True)
        self.stop()

class ToggleDonateable(discord.ui.Button):
    def __init__(self, client, item):
        self.client: dvvt = client
        self.item: DankItem = item
        super().__init__(style=discord.ButtonStyle.green if item.celeb_donation is True else discord.ButtonStyle.red, label="Item can be donated" if item.celeb_donation is True else "Item CANNOT be donated")

    async def callback(self, interaction: discord.Interaction):
        if self.item.celeb_donation is True:
            self.item.celeb_donation = False
        else:
            self.item.celeb_donation = True
        await self.view.client.db.execute("UPDATE dankitems SET celeb_donation=$1 WHERE idcode=$2", self.item.celeb_donation, self.item.idcode)
        if self.item.celeb_donation is True:
            self.style = discord.ButtonStyle.green
            self.label = "Item can be donated"
            if not self.view.is_finished():
                self.view.children[1].disabled = False
        else:
            self.label = "Item CANNOT be donated"
            self.style = discord.ButtonStyle.red
            self.view.children[1].disabled = True

        await interaction.response.edit_message(view=self.view)


class UpdateValue(discord.ui.Select):
    def __init__(self, client, item):
        self.client: dvvt = client
        self.item: DankItem = item

        options = [
            discord.SelectOption(emoji="🤖", label=f"x1.25 Multi (⏣ {comma_number(get_celeb_value(self.item, ignore_overwrite=True))})", value="multi", description=f"This item's ORIGINAL value is ⏣ {comma_number(self.item.trade_value)}", default=True if self.item.celeb_overwrite_value is None else False),
            discord.SelectOption(emoji="🧑‍🔧", label=f"Manually set (⏣ {comma_number(get_celeb_value(self.item))})" if self.item.celeb_overwrite_value is not None else "Manually set", value='manual', default=True if self.item.celeb_overwrite_value is not None else False)
            ]
        super().__init__(placeholder="What value should I follow?", min_values=1, max_values=1, options=options, disabled=False if self.item.celeb_donation is True else True)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'multi':
            self.item.celeb_overwrite_value = None
            await self.client.db.execute("UPDATE dankitems SET celeb_overwrite_value = $1 WHERE idcode = $2", self.item.celeb_overwrite_value, self.item.idcode)
            self.options[1].label = "Manually set"
            self.options[0].default = True
            self.options[1].default = False
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(f"**{self.item.name}**'s donation value will be determined by the 1.25x multi (⏣ {comma_number(get_celeb_value(self.item))}).", ephemeral=True)
        else:
            modal = InputItemValue()
            await interaction.response.send_modal(modal)
            await modal.wait()
            if modal.itemvalue is not None:
                self.item.celeb_overwrite_value = modal.itemvalue
                await self.client.db.execute("UPDATE dankitems SET celeb_overwrite_value = $1 WHERE idcode = $2", self.item.celeb_overwrite_value, self.item.idcode)
                self.options[1].label = f"Manually set (⏣ {comma_number(self.item.celeb_overwrite_value)})"
                self.options[0].default = False
                self.options[1].default = True
                await interaction.edit_original_message(view=self.view)
                #await interaction.followup.send(f"**{self.item.name}**'s donation value is set to **⏣ {comma_number(get_celeb_value(self.item))}**.", ephemeral=True)

class UpdateCelebItem(discord.ui.View):
    def __init__(self, client, ctx, item: DankItem):
        self.client: dvvt = client
        self.ctx: DVVTcontext = ctx
        self.response = None
        self.item: DankItem = item
        super().__init__(timeout=60.0)

        self.add_item(ToggleDonateable(self.client, self.item))
        self.add_item(UpdateValue(self.client, self.item))



    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(embed=discord.Embed(
                description="Only the author (`{}`) can interact with this message.".format(self.ctx.author),
                color=discord.Color.red()), ephemeral=True)
            return False
        else:
            return True

    async def on_timeout(self):
        self.disable_all_items()
        await self.response.edit(view=self)


def get_celeb_value(item: DankItem, ignore_overwrite: Optional[bool] = False):
    if item.celeb_overwrite_value is not None and not ignore_overwrite:
        return item.celeb_overwrite_value
    else:
        return round(item.trade_value * 1.25)

class DankItems(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.group(name="dankitems", aliases=['items'], invoke_without_command=True)
    async def dankitems(self, ctx, item: str = None):
        """
        Fetches values of Dank Memer Items for donations. These values are based off trade values cached from Dank Memer, or manually set.
        """
        items = await self.client.db.fetch("SELECT * FROM dankitems ORDER BY name")
        if item is not None:
            item = item.lower()
            result, ratio = process.extractOne(item, [i.get('idcode') for i in items])
            if ratio > 65:
                for checking_item in items:
                    if checking_item.get('idcode') == result:
                        name = checking_item.get('name')
                        type = checking_item.get('type')
                        image_url = checking_item.get('image_url')
                        trade_value = checking_item.get('trade_value')
                        last_updated = checking_item.get('last_updated')
                        overwrite = checking_item.get('overwrite')
                        embed = discord.Embed(
                            title=name,
                            description=f"```\n⏣ {comma_number(trade_value)}\n```",
                            color=self.client.embed_color,
                            timestamp=datetime.fromtimestamp(last_updated))
                        field_details = f"**Type**: {type}\n**ID**: `{result}`"
                        if overwrite is True:
                            field_details += f"\nThis item's value is preset, not cached from Dank Memer."
                        embed.add_field(name="Details", value=field_details, inline=False)
                        embed.set_thumbnail(url=image_url)
                        embed.set_footer(text=f"Last updated")
                        await ctx.send(embed=embed)
                        return
            else:
                return await ctx.send(
                    f"<:DVB_False:887589731515392000> I could not find an item with the name `{item}`.")
        else:
            if len(items) == 0:
                return await ctx.send("There are no cached Dank Memer items to display.")
            else:
                items_sorted = {}
                for item in items:
                    name = item.get('name')
                    idcode = item.get('idcode')
                    type = item.get('type')
                    trade_value = item.get('trade_value')
                    if type in items_sorted.keys():
                        items_sorted[type].append((name, idcode, trade_value))
                    else:
                        items_sorted[type] = [(name, idcode, trade_value)]
                all_items = []
                pagegroups = []
                for type, lst in items_sorted.items():
                    embeds = []
                    for chunked_list in discord.utils.as_chunks(lst, 10):
                        desc = []
                        for name, idcode, trade_value in chunked_list:
                            all_items.append(f"**{name}** `{idcode}`: [⏣ {comma_number(trade_value)}](http://a/)")
                            desc.append(f"**{name}** `{idcode}`: [⏣ {comma_number(trade_value)}](http://a/)")
                        embed = discord.Embed(title=f"{type} Items", description="\n".join(desc),
                                              color=self.client.embed_color)
                        embeds.append(embed)
                    pagegroups.append(discord.ext.pages.PageGroup(pages=embeds, label=type, author_check=True,
                                                                  disable_on_timeout=True, description=None))
                all_items_embeds = []
                for all_items_chunked in discord.utils.as_chunks(all_items, 10):
                    embed = discord.Embed(title="All Items", description="\n".join(all_items_chunked),
                                          color=self.client.embed_color)
                    all_items_embeds.append(embed)
                pagegroups.append(
                    discord.ext.pages.PageGroup(pages=all_items_embeds, label="All Items", author_check=True,
                                                disable_on_timeout=True, description=None))
                paginator = pages.Paginator(pages=pagegroups, show_menu=True,
                                            menu_placeholder="Dank Memer Item Categories", )
                await paginator.send(ctx)

    @checks.has_permissions_or_role(manage_roles=True)
    @dankitems.command(name='set', aliases=['setvalue'])
    async def dankitems_set_value(self, ctx, item: str, value: str):
        """
        Set the value of a Dank Memer item, overwriting it and preventing it from being updated automatically.
        To reset a item's value, use `none` for the value, and use `pls shop <item>`.
        """
        items = await self.client.db.fetch("SELECT * FROM dankitems")
        if item is not None:
            item = item.lower()
            result, ratio = process.extractOne(item, [i.get('idcode') for i in items])
            if ratio > 65:
                for checking_item in items:
                    if checking_item.get('idcode') == result:
                        item = checking_item
                    else:
                        continue
        if type(item) == str:
            return await ctx.send(f"<:DVB_False:887589731515392000> I could not find an item with the name `{item}`.")
        processed_value = stringnum_toint(value)
        if processed_value is None:
            if value.lower() == 'none':
                processed_value = None
            else:
                return await ctx.send("<:DVB_False:887589731515392000> The value needs to be a number or `none`.")
        if processed_value is not None:
            await self.client.db.execute(
                "UPDATE dankitems SET trade_value = $1, overwrite = True, last_updated = $2 WHERE idcode = $3",
                processed_value, round(time.time()), item.get('idcode'))
            await ctx.send(
                f"<:DVB_True:887589686808309791> Set the value of **{item.get('name')}** to `⏣ {comma_number(processed_value)}`.\nTo reset it to Dank Memer trade values, use set `none` as the value.")
        else:
            await self.client.db.execute(
                "UPDATE dankitems SET trade_value = 0, overwrite = False, last_updated = $1 WHERE idcode = $2",
                round(time.time()), item.get('idcode'))
            await ctx.send(
                f"<:DVB_True:887589686808309791> Set the value of **{item.get('name')}** to `⏣ 0`.\nPlease run `pls shop {item.get('idcode')}` to update the {item.get('name')} to the current Dank Memer trade value.")

    @checks.has_permissions_or_role(manage_roles=True)
    @checks.not_in_gen()
    @commands.command(name='itemcalc', aliases=['ic'])
    async def item_calc(self, ctx: DVVTcontext, *, arg: str = None):
        """
        Calculates the total donation value of multiple Dank Memer items.
        The items should be entered in this format: `[item count] <item name> [item count] <item name> ...`
        Example: `dv.ic 1 pepe 3 tro`
        """
        if arg is None:
            return await ctx.send("You need to provide a list of Dank items to calculate the total worth.")
        all_dank_items = await self.client.db.fetch("SELECT * FROM dankitems")
        item_names = []
        item_codes = []
        item_worth = []
        for item in all_dank_items:
            item_names.append(item.get('name'))
            item_codes.append(item.get('idcode'))
            item_worth.append(item.get('trade_value'))
        items = []
        errors = []
        input_count = None
        input_name = None
        for item in arg.split(' '):
            if item.isdigit():
                input_count = int(item)
            else:
                item = item.lower()
                result, ratio = process.extractOne(item, item_codes)
                if ratio > 65:
                    item_index = item_codes.index(result)
                    if input_count is None:
                        input_count = 1
                    items.append((item_names[item_index], item_worth[item_index], input_count))
                    input_count = None
                else:
                    errormsg = f"`{item}`: Unable to find item"
                    if errormsg not in errors:
                        errors.append(errormsg)
        if len(errors) > 0:
            errorembed = discord.Embed(title="Encountered some errors when parsing:",
                                       description="\n".join(errors)[:3999], color=self.client.embed_color)
            await ctx.send(embed=errorembed)
        if len(items) > 0:
            total_worth = 0
            item_calc_result = []
            for item in items:
                total_worth += item[1] * item[2]
                item_calc_result.append(f"`{item[2]}` **{item[0]}**: `⏣ {comma_number(item[1] * item[2])}`")
            item_summary_embed = discord.Embed(title=f"Detected items", description="", color=self.client.embed_color)
            embed_count = 0
            hidden_items = 0
            for item in item_calc_result:
                if embed_count > 3:
                    hidden_items += 1
                else:
                    if len(item_summary_embed.description) + len(item) > 4000:
                        await ctx.send(embed=item_summary_embed)
                        embed_count += 1
                        item_summary_embed = discord.Embed(title=f"Detected items", description="",
                                                           color=self.client.embed_color)
                    if embed_count > 3:
                        hidden_items += 1
                    else:
                        item_summary_embed.description += f"{item}\n"
            if len(item_summary_embed.description) > 0:
                await ctx.send(embed=item_summary_embed)
            final_embed = discord.Embed(title="Total worth:", description=f"```\n⏣ {comma_number(total_worth)}\n```",
                                        color=self.client.embed_color)
            if hidden_items > 0:
                final_embed.set_footer(text=f"{hidden_items} items were hidden due to to many embeds sent.")
            await ctx.send(embed=final_embed)
        else:
            await ctx.send(embed=discord.Embed(title="You didn't input any items.", color=discord.Color.red()))

    @commands.group(name="celebitems", aliases=['citems'], invoke_without_command=True)
    async def celebitems(self, ctx, item: str = None):
        """
        **The values in this command only applies to donations for celebrations.**
        Fetches values of Dank Memer Items for donations. These values are based off trade values cached from Dank Memer, or manually set.
        """
        items = await self.client.db.fetch("SELECT * FROM dankitems ORDER BY name")
        if item is not None:
            item = item.lower()
            result, ratio = process.extractOne(item, [i.get('idcode') for i in items])
            if ratio > 65:
                for checking_item in items:
                    checking_item = DankItem(checking_item)
                    if checking_item.idcode == result:
                        name = checking_item.name
                        type = checking_item.type
                        image_url = checking_item.image_url
                        trade_value = get_celeb_value(checking_item)
                        last_updated = checking_item.last_updated
                        overwrite = checking_item.overwrite
                        celeb_donation = checking_item.celeb_donation
                        embed = discord.Embed(
                            title=name,
                            description=f"```\n⏣ {comma_number(trade_value)}\n```",
                            color=self.client.embed_color,
                            timestamp=datetime.fromtimestamp(last_updated))
                        if celeb_donation is not True:
                            embed.description = f"**This item __can't__ be donated for the celeb.**"
                            embed.color = discord.Color.red()
                        else:
                            field_details = f"**Type**: {type}\n**ID**: `{result}`"
                            if overwrite is True:
                                field_details += f"\nThis item's value is preset, not cached from Dank Memer."
                            embed.add_field(name="Details", value=field_details, inline=False)
                            embed.set_footer(text=f"Last updated")
                        embed.set_thumbnail(url=image_url)
                        await ctx.send("**Items shown in this command only applies to celeb donations.**\nFor normal donations, check `dv.items`.", embed=embed)
                        return
            else:
                return await ctx.send(
                    f"<:DVB_False:887589731515392000> I could not find an item with the name `{item}`.")
        else:
            if len(items) == 0:
                return await ctx.send("There are no cached Dank Memer items to display.")
            else:
                items_sorted = {}
                for item in items:
                    item = DankItem(item)
                    if item.celeb_donation is True:
                        name = item.name
                        idcode = item.idcode
                        type = item.type
                        trade_value = get_celeb_value(item)
                        if type in items_sorted.keys():
                            items_sorted[type].append((name, idcode, trade_value))
                        else:
                            items_sorted[type] = [(name, idcode, trade_value)]
                all_items = []
                pagegroups = []
                for type, lst in items_sorted.items():
                    embeds = []
                    for chunked_list in discord.utils.as_chunks(lst, 10):
                        desc = []
                        for name, idcode, trade_value in chunked_list:
                            all_items.append(f"**{name}** `{idcode}`: [⏣ {comma_number(trade_value)}](http://a/)")
                            desc.append(f"**{name}** `{idcode}`: [⏣ {comma_number(trade_value)}](http://a/)")
                        embed = discord.Embed(title=f"{type} Items", description="\n".join(desc),
                                              color=self.client.embed_color)
                        embeds.append(embed)
                    pagegroups.append(discord.ext.pages.PageGroup(pages=embeds, label=type, author_check=True,
                                                                  disable_on_timeout=True, description=None))
                all_items_embeds = []
                for all_items_chunked in discord.utils.as_chunks(all_items, 10):
                    embed = discord.Embed(title="All Items", description="\n".join(all_items_chunked),
                                          color=self.client.embed_color)
                    all_items_embeds.append(embed)
                pagegroups.append(
                    discord.ext.pages.PageGroup(pages=all_items_embeds, label="All Items", author_check=True,
                                                disable_on_timeout=True, description=None))
                paginator = pages.Paginator(pages=pagegroups, show_menu=True,
                                            menu_placeholder="Dank Memer Item Categories", )
                await paginator.send(ctx, target_message="**Items shown in this command only applies to celeb donations.**\nFor normal donations, check `dv.items`.")

    @checks.has_permissions_or_role(manage_roles=True)
    @celebitems.command(name='set', aliases=['setvalue'])
    async def celebitems_set_value(self, ctx, item: str):
        """
        Set the value of a Dank Memer item, overwriting it and preventing it from being updated automatically.
        To reset a item's value, use `none` for the value, and use `pls shop <item>`.
        """
        items = await self.client.db.fetch("SELECT * FROM dankitems")
        if item is not None:
            item = item.lower()
            result, ratio = process.extractOne(item, [i.get('idcode') for i in items])
            if ratio > 65:
                for checking_item in items:
                    if checking_item.get('idcode') == result:
                        item = checking_item
                    else:
                        continue
        if type(item) == str:
            return await ctx.send(f"<:DVB_False:887589731515392000> I could not find an item with the name `{item}`.")
        item = DankItem(item)
        embed = discord.Embed(title=item.name, description="Click on the buttons or dropdown below to edit Celeb configs for this item.", color=self.client.embed_color)
        embed.set_footer(text='wicked is a qt' if ctx.author.id == 602066975866355752 else 'wicked is emo')

        embed.set_author(name=f"{ctx.author} is editing...")
        embed.set_thumbnail(url=item.image_url)
        celebconfig = UpdateCelebItem(self.client, ctx, item)
        celebconfig.response = await ctx.send(embed=embed, view=celebconfig)




    @checks.has_permissions_or_role(manage_roles=True)
    @checks.not_in_gen()
    @commands.command(name='celebitemcalc', aliases=['celebic', 'cic'])
    async def celeb_item_calc(self, ctx: DVVTcontext, *, arg: str = None):
        """
        **The values in this command only applies to donations for celebrations.**
        Calculates the total donation value of multiple Dank Memer items.
        The items should be entered in this format: `[item count] <item name> [item count] <item name> ...`
        Example: `dv.ic 1 pepe 3 tro`
        """
        if arg is None:
            return await ctx.send("You need to provide a list of Dank items to calculate the total worth.")
        all_dank_items = await self.client.db.fetch("SELECT * FROM dankitems")
        item_names = []
        item_codes = []
        item_worth = []
        item_can_be_donated = []
        for item in all_dank_items:
            item = DankItem(item)
            item_names.append(item.name)
            item_codes.append(item.idcode)
            item_worth.append(get_celeb_value(item))
            item_can_be_donated.append(item.celeb_donation)
        items = []
        errors = []
        input_count = None
        input_name = None
        for item in arg.split(' '):
            if item.isdigit():
                input_count = int(item)
            else:
                item = item.lower()
                result, ratio = process.extractOne(item, item_codes)
                if ratio > 65:
                    item_index = item_codes.index(result)
                    if input_count is None:
                        input_count = 1
                    if item_can_be_donated[item_index]:
                        items.append((item_names[item_index], item_worth[item_index], input_count))
                    else:
                        errormsg = f"`{result}`: Cannot be donated for celeb"
                        if errormsg not in errors:
                            errors.append(errormsg)
                    input_count = None
                else:
                    errormsg = f"`{item}`: Unable to find item"
                    if errormsg not in errors:
                        errors.append(errormsg)
        if len(errors) > 0:
            errorembed = discord.Embed(title="Encountered some errors when parsing:",
                                       description="\n".join(errors)[:3999], color=self.client.embed_color)
            await ctx.send(embed=errorembed)
        if len(items) > 0:
            total_worth = 0
            item_calc_result = []
            for item in items:
                total_worth += item[1] * item[2]
                item_calc_result.append(f"`{item[2]}` **{item[0]}**: `⏣ {comma_number(item[1] * item[2])}`")
            item_summary_embed = discord.Embed(title=f"Detected items", description="", color=self.client.embed_color)
            embed_count = 0
            hidden_items = 0
            for item in item_calc_result:
                if embed_count > 3:
                    hidden_items += 1
                else:
                    if len(item_summary_embed.description) + len(item) > 4000:
                        await ctx.send(embed=item_summary_embed)
                        embed_count += 1
                        item_summary_embed = discord.Embed(title=f"Detected items", description="",
                                                           color=self.client.embed_color)
                    if embed_count > 3:
                        hidden_items += 1
                    else:
                        item_summary_embed.description += f"{item}\n"
            if len(item_summary_embed.description) > 0:
                await ctx.send(embed=item_summary_embed)
            final_embed = discord.Embed(title="Total worth:", description=f"```\n⏣ {comma_number(total_worth)}\n```",
                                        color=self.client.embed_color)
            if hidden_items > 0:
                final_embed.set_footer(text=f"{hidden_items} items were hidden due to to many embeds sent.")
            await ctx.send("**Items shown in this command only applies to celeb donations.**\nFor normal donations, check `dv.items`.", embed=final_embed)
        else:
            await ctx.send("**Items shown in this command only applies to celeb donations.**\nFor normal donations, check `dv.items`.", embed=discord.Embed(title="You didn't input any items.", color=discord.Color.red()))