from abc import ABC
from discord.ext import menus

from main import dvvt
from utils.converters import BetterInt, BetterTimeConverter
from utils.specialobjects import ServerConfiguration
from .contests import Contests
from .serverrule import ServerRule
from .joining import Joining
from .betterselfroles import BetterSelfroles
from utils import checks
from utils.buttons import *
from utils.format import grammarformat, stringtime_duration
from utils.time import humanize_timedelta
from utils.menus import CustomMenu
from time import time
import os

verify_role = 911541857807384677


def return_emoji(truefalse: bool):
    if truefalse:
        return "<:DVB_True:887589686808309791> "
    else:
        return "<:DVB_False:887589731515392000>"


class verifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="✅", label="Verify", style=discord.ButtonStyle.blurple, custom_id='dv:verify')
    async def verifybutton(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send("<a:DVB_Loading:909997219644604447> Verifying you...", ephemeral=True)
        verifyrole = interaction.guild.get_role(verify_role)
        if verifyrole:
            await interaction.user.remove_roles(verifyrole)
        roleids = [905980110954455070, 905980110157541446, 905980109268324402, 905980108148461599, 905980107435442186] \
            if os.getenv('state') == '1' else \
            [837591810389442600, 671426678807068683, 671426686100963359, 671426692077584384, 649499248320184320]
        roles = [interaction.guild.get_role(roleid) for roleid in roleids]
        for role in roles:
            if role not in interaction.user.roles:
                await interaction.user.add_roles(role, reason="User completed manual verification")
        await interaction.followup.send("You've been verified! You should now be able to talk.", ephemeral=True)

class Blacklist(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, description="To know more about a blacklist, do `dv.blacklists <ID>`. ", color=menu.ctx.bot.embed_color, timestamp=discord.utils.utcnow())
        for entry in entries:
            embed.add_field(name=f"{entry[0]}", value=entry[1], inline=False)
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed

class UpdateNumberofDays(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        self.number_of_days: int = None
        self.interaction: discord.Interaction = None
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="How many days old should a user's account be?"))

    async def callback(self, interaction: discord.Interaction):
        try:
            self.number_of_days = int(self.children[0].value)
        except ValueError:
            return await interaction.response.send_message("You need to input a number, please try again.")
        else:
            self.interaction = interaction
            self.stop()


class UpdateStatusText(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        self.status_text: str = None
        self.interaction: discord.Interaction = None
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Status Text", required=True, style=discord.InputTextStyle.short, min_length = 1, max_length=128))

    async def callback(self, interaction: discord.Interaction):
        status_text = self.children[0].value
        self.status_text = status_text.strip()
        self.interaction = interaction
        self.stop()


class UpdateRoleID(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        self.role_id: int = None
        self.interaction: discord.Interaction = None
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="ID of the role", required=True, placeholder="Only Role IDs are accepted.", style=discord.InputTextStyle.short))

    async def callback(self, interaction: discord.Interaction):
        role_id = self.children[0].value
        role_id = role_id.strip()
        try:
            self.role_id = int(role_id)
        except ValueError:
            await interaction.response.send_message("You did not provide a valid Role ID.", ephemeral=True)
        self.interaction = interaction
        self.stop()


class ServerConfigView(discord.ui.View):
    def __init__(self, ctx: DVVTcontext, serverconfig: ServerConfiguration, client):
        self.ctx = ctx
        self.active = True
        self.serverconfig: ServerConfiguration = serverconfig
        self.client: dvvt = client
        self.response = None
        super().__init__(timeout=20)

        def update_bool(truefalse):
            if truefalse is None or truefalse is False:
                return True
            elif truefalse is True:
                return False

        def get_style(arg):
            if arg is not True:
                return discord.ButtonStyle.red
            else:
                return discord.ButtonStyle.green

        class BaseToggleButton(discord.ui.Button):
            def __init__(self, serverconfig: ServerConfiguration, client, *args, **kwargs):
                self.serverconfig: ServerConfiguration = serverconfig
                self.client: dvvt = client
                super().__init__(*args, **kwargs)

            async def callback(self, interaction: discord.Interaction):
                if self.custom_id == "owodailylb":
                    self.serverconfig.owodailylb = update_bool(self.serverconfig.owodailylb)
                    self.style = get_style(self.serverconfig.owodailylb)
                elif self.custom_id == "verification":
                    self.serverconfig.verification = update_bool(self.serverconfig.verification)
                    self.style = get_style(self.serverconfig.verification)
                elif self.custom_id == "censor":
                    self.serverconfig.censor = update_bool(self.serverconfig.censor)
                    self.style = get_style(self.serverconfig.censor)
                elif self.custom_id == "owoweeklylb":
                    self.serverconfig.owoweeklylb = update_bool(self.serverconfig.owoweeklylb)
                    self.style = get_style(self.serverconfig.owoweeklylb)
                elif self.custom_id == "votelb":
                    self.serverconfig.votelb = update_bool(self.serverconfig.votelb)
                    self.style = get_style(self.serverconfig.votelb)
                elif self.custom_id == "timeoutlog":
                    self.serverconfig.timeoutlog = update_bool(self.serverconfig.timeoutlog)
                    self.style = get_style(self.serverconfig.timeoutlog)
                elif self.custom_id == 'pls_ar':
                    self.serverconfig.pls_ar = update_bool(self.serverconfig.pls_ar)
                    self.style = get_style(self.serverconfig.pls_ar)
                elif self.custom_id == 'mrob_ar':
                    self.serverconfig.mrob_ar = update_bool(self.serverconfig.mrob_ar)
                    self.style = get_style(self.serverconfig.mrob_ar)
                elif self.custom_id == "statusroleenabled":
                    self.serverconfig.statusroleenabled = update_bool(self.serverconfig.statusroleenabled)
                    self.style = get_style(self.serverconfig.statusroleenabled)
                elif self.custom_id == "auto_decancer":
                    self.serverconfig.auto_decancer = update_bool(self.serverconfig.auto_decancer)
                    self.style = get_style(self.serverconfig.auto_decancer)
                await self.serverconfig.update(self.client)
                await interaction.response.edit_message(embed=self.view.get_embed(), view=self.view)

        class ChangeRoleID(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                modal = UpdateRoleID(title="Change Status Reward's Role ID")
                await interaction.response.send_modal(modal)
                await modal.wait()
                if modal.role_id is not None:
                    role = interaction.guild.get_role(modal.role_id)
                    if role is None:
                        if modal.interaction.response.is_done():
                            await modal.interaction.followup.send(f"A role with ID **{modal.role_id}** does not exist.", ephemeral=True)
                        else:
                            await modal.interaction.response.send_message(f"A role with ID **{modal.role_id}** does not exist.", ephemeral=True)
                    else:
                        if role.is_default() or role.is_bot_managed() or role.is_premium_subscriber() or role.managed or role.is_integration():
                            if modal.interaction.response.is_done():
                                await modal.interaction.followup.send(f"**{role}** is integrated/managed and cannot be added.", ephemeral=True)
                            else:
                                await modal.interaction.response.send_message(f"**{role}** is integrated/managed and cannot be added.", ephemeral=True)
                        else:
                            self.view.serverconfig.statusroleid = modal.role_id
                            await self.view.serverconfig.update(self.view.client)
                            await interaction.edit_original_message(embed=self.view.get_embed(), view=self.view)
                            if modal.interaction.response.is_done():
                                await modal.interaction.followup.send(f"Status role has been changed to **{role.name}**.", ephemeral=True)
                            else:
                                await modal.interaction.response.send_message(f"Status role has been changed to **{role.name}**.", ephemeral=True)
                else:
                    if modal.interaction.response.is_done():
                        await modal.interaction.followup.send("You did not provide a valid Role ID.", ephemeral=True)
                    else:
                        await modal.interaction.response.send_message("You did not provide a valid Role ID.", ephemeral=True)

        class ChangeBanDays(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                modal = UpdateNumberofDays(title="Change Ban Days")
                await interaction.response.send_modal(modal)
                await modal.wait()
                self.view.serverconfig.autoban_duration = modal.number_of_days
                await self.view.serverconfig.update(self.view.client)
                summary = f"Number of days has been changed to `{modal.number_of_days}`.\nUsers whose age is under {self.view.serverconfig.autoban_duration} days will be banned when they join. Use `dv.dungeon bypass <user>` to bypass it."
                if modal.interaction.response.is_done():
                    await modal.interaction.followup.send(summary, ephemeral=True)
                else:
                    await modal.interaction.response.send_message(summary, ephemeral=True)
                await interaction.edit_original_message(embed=self.view.get_embed(), view=self.view)

        class StatusText(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                modal = UpdateStatusText(title="Change the status text")
                await interaction.response.send_modal(modal)
                await modal.wait()
                self.view.serverconfig.statustext = modal.status_text
                await self.view.serverconfig.update(self.view.client)
                summary = f"Status text has been changed to `{modal.status_text}`."
                if self.view.serverconfig.statusmatchtype.lower() == 'strict':
                    summary += "Users will have to have statuses that exactly match that text."
                elif self.view.serverconfig.statusmatchtype.lower() == 'contains':
                    summary += "Users will have to have statuses that **contains** that text. They can add any other text to their status on top of *that text*."
                if modal.interaction.response.is_done():
                    await modal.interaction.followup.send(summary, ephemeral=True)
                else:
                    await modal.interaction.response.send_message(summary, ephemeral=True)
                await interaction.edit_original_message(embed=self.view.get_embed(), view=self.view)

        class ChangeStatusMatchType(discord.ui.Select):
            def __init__(self, current):

                options = []
                for name, desc in [("Strict", "Users MUST have ONLY the text in their status."), ("Contains", "Users can have the text + any other text in their status.")]:
                    options.append(discord.SelectOption(label=name, description=desc, default=(current == name)))
                super().__init__(placeholder="Choose a type of match", min_values=1, max_values=1, options=options)

            async def callback(self, interaction: discord.Interaction):
                chosen = self.values[0]
                self.view.serverconfig.statusmatchtype = chosen
                await self.view.serverconfig.update(self.view.client)
                summary = f"Status match type has been changed to `{chosen}`."
                if chosen.lower() == 'strict':
                    summary += "Users will have to have statuses that exactly match that text."
                elif chosen.lower() == 'contains':
                    summary += "Users will have to have statuses that **contains** that text. They can add any other text to their status on top of *that text*."
                for op in self.options:
                    if op.label == chosen:
                        op.default = True
                    else:
                        op.default = False
                await interaction.response.edit_message(embed=self.view.get_embed(), view=self.view)
                await interaction.followup.send(summary, ephemeral=True)
                for op in self.options:
                    if op.label == chosen:
                        op.default = True

        self.add_item(BaseToggleButton(self.serverconfig, self.client, label="OwO Daily Leaderboard", custom_id="owodailylb", style=get_style(self.serverconfig.owodailylb)))
        self.add_item(BaseToggleButton(self.serverconfig, self.client, label="OwO Weekly Leaderboard", custom_id="owoweeklylb", style=get_style(self.serverconfig.owoweeklylb)))
        self.add_item(BaseToggleButton(self.serverconfig, self.client, label="Vote Leaderboard", custom_id="votelb", style=get_style(self.serverconfig.votelb)))
        self.add_item(BaseToggleButton(self.serverconfig, self.client, label="Verification", custom_id="verification", style=get_style(self.serverconfig.verification)))
        self.add_item(BaseToggleButton(self.serverconfig, self.client, label="Censor", custom_id="censor", style=get_style(self.serverconfig.censor)))
        self.add_item(BaseToggleButton(self.serverconfig, self.client, label="Timeout Log", custom_id="timeoutlog", style=get_style(self.serverconfig.timeoutlog)))
        self.add_item(BaseToggleButton(self.serverconfig, self.client, label="pls command AR", custom_id="pls_ar", style=get_style(self.serverconfig.pls_ar)))
        self.add_item(BaseToggleButton(self.serverconfig, self.client, label="MafiaBot Rob AR", custom_id="mrob_ar", style=get_style(self.serverconfig.mrob_ar)))
        self.add_item(BaseToggleButton(self.serverconfig, self.client, label="Auto Decancer", custom_id="auto_decancer", style=get_style(self.serverconfig.auto_decancer)))
        self.add_item(BaseToggleButton(self.serverconfig, self.client, label="Status Role", custom_id="statusroleenabled", style=get_style(self.serverconfig.statusroleenabled)))
        self.add_item(ChangeRoleID(label="Status Reward -> Role ID (Click here to change)"))
        self.add_item(StatusText(label="Status Text (Click here to change)"))
        self.add_item(ChangeBanDays(label="Ban Days (Click here to change)"))
        self.add_item(ChangeStatusMatchType(self.serverconfig.statusmatchtype))

    def get_embed(self):
        embed = discord.Embed(title="Dank Vibes Server Configuration", color=self.client.embed_color)
        embed.add_field(name=f"OwO Daily Leaderboard - {return_emoji(self.serverconfig.owodailylb)}", value=f"Shows the OwO Daily Leaderboard when it resets.")
        embed.add_field(name=f"OwO Weekly Leaderboard - {return_emoji(self.serverconfig.owoweeklylb)}", value=f"Shows the OwO Weekly Leaderboard when it resets.")
        embed.add_field(name=f"Verification - {return_emoji(self.serverconfig.verification)}", value=f"Runs member verification related tasks.")
        embed.add_field(name=f"Censor - {return_emoji(self.serverconfig.votelb)}", value=f"Deletes blacklisted words.")
        embed.add_field(name=f"Vote Leaderboard - {return_emoji(self.serverconfig.votelb)}", value=f"Shows the Vote Leaderboard every 24 hours.")
        embed.add_field(name=f"Timeout Log - {return_emoji(self.serverconfig.timeoutlog)}", value=f"Logs timeouts in #mod-log.")
        embed.add_field(name=f"`pls` AR - {return_emoji(self.serverconfig.pls_ar)}", value=f"Responds to `pls ...` in #general or #bot-lounge.")
        embed.add_field(name=f"Auto Decancer - {return_emoji(self.serverconfig.auto_decancer)}", value="Decancer user's names when they join")
        embed.add_field(name=f"MafiaBot Rob AR - {return_emoji(self.serverconfig.mrob_ar)}", value=f"Responds to `m.rob`.")
        embed.add_field(name=f"Status Rewards - {return_emoji(self.serverconfig.statusroleenabled)}", value=f"Whether status role rewards are enabled.")
        embed.add_field(name=f"Status Text - `{self.serverconfig.statustext}`", value=f"The text in a user's status to be able to obtain the role.", inline=False)
        embed.add_field(name=f"Status Role - `{self.ctx.guild.get_role(self.serverconfig.statusroleid) or self.serverconfig.statusroleid}`", value=f"The ID of the role that can be obtained.", inline=False)
        embed.add_field(name=f"Status Matching - `{self.serverconfig.statusmatchtype}`", value=f"How should the status text be matched.\n`Strict`: Must be exactly the same.\n`Contains`: Must contain the text but any other text can be addded.", inline=False)
        embed.add_field(name=f"Days for auto-ban - `{self.serverconfig.autoban_duration}`", value=f"The minimum number of days a user's account should be created.")
        embed.set_footer(text=self.ctx.guild.name, icon_url=self.ctx.guild.icon.url)
        return embed

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(embed=discord.Embed(
                description="Only the author (`{}`) can interact with this message.".format(self.ctx.author),
                color=discord.Color.red()), ephemeral=True)
            return False
        else:
            return True

    async def on_timeout(self) -> None:
        for b in self.children:
            b.disabled = True
        await self.response.edit(view=self)
        self.active = False
        self.stop()


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    pass


class Admin(Contests, BetterSelfroles, Joining, ServerRule, commands.Cog, name='admin', metaclass=CompositeMetaClass):
    """
    Server Commands
    """
    def __init__(self, client):
        self.client: dvvt = client
        self.queue = []
        self.selfroleviews_added = False

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="verify")
    async def verify(self, ctx):
        """
        Sends the message that allows people to be verified with a button.
        """
        embed = discord.Embed(title="__**VERIFY**__", url="https://discord.gg/invite/dankmemer",
                              description="Click the **Verify** button below this embed to gain access to the server. By clicking you agree to all the rules mentioned above!\n** **",
                              color=5763312)
        embed.set_footer(text="Dank Vibes",
                         icon_url="https://cdn.discordapp.com/icons/595457764935991326/a_58b91a8c9e75742d7b423411b0205b2b.gif")
        embed.set_image(url="https://cdn.discordapp.com/attachments/616007729718231161/910817422557196328/rawr_nya.gif")
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/icons/595457764935991326/a_fba2b3f7548d99cd344931e27930ec4d.gif?size=1024")
        await ctx.send(embed=embed, view=verifyView())

    @commands.command(name='serverconfig', aliases=["serverconf"])
    @commands.has_guild_permissions(manage_roles=True)
    async def serverconfig(self, ctx):
        """
        Shows guild's server configuration settings and also allows you to allow/disable them.
        """
        embed = discord.Embed(title=f"Server Configuration Settings For {ctx.guild.name}", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        serverconf = await self.client.get_guild_settings(ctx.guild.id)
        view = ServerConfigView(ctx, serverconf, self.client)
        embed = view.get_embed()
        view.response = await ctx.send(embed=embed, view=view)
        await view.wait()

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='blacklist', aliases=['bl'])
    async def blacklist(self, ctx, *, user: discord.Member = None):
        """Blacklist a user from using the bot."""
        if user is None:
            return await ctx.send('who tf do you want me to blacklist huh')
        if await self.client.db.fetchrow("SELECT * FROM blacklist WHERE user_id=$1 and blacklist_active = $2", user.id, True) is not None:
            return await ctx.send(f"{user.mention} is already blacklisted from using the bot.")
        reason = None
        duration = None
        error = None
        while reason is None:
            msg = f"What is the reason for blacklisting {user}?"
            if error:
                msg = error + '\n' + msg
            await ctx.send(msg)
            try:
                reason = await self.client.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            except asyncio.TimeoutError:
                return await ctx.send("Timed out. Please try again.")
            if reason.content.lower() == 'cancel':
                return await ctx.send(f"Pending blacklist cancelled.")
            if len(reason.content) > 1500:
                error = "The reason can only be up to 1500 characters."
            reason = 'No reason' if reason.content.lower() == 'none' else reason.content
        error = None
        while duration is None:
            msg = "How long is the blacklist for? To blacklist the user permanently, type `none`."
            if error:
                msg = error + '\n' + msg
            await ctx.send(msg)
            try:
                duration = await self.client.wait_for('message', timeout=60, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            except asyncio.TimeoutError:
                return await ctx.send("Timed out. Please try again.")
            if duration.content.lower() == 'cancel':
                return await ctx.send(f"Pending blacklist cancelled.")
            if duration.content.lower() == 'none':
                duration = 9223372036854775807
            else:
                duration = stringtime_duration(duration.content)
                if duration is None:
                    error = "Invalid duration. Please try again."
        if duration is not None and duration != 9223372036854775807:
            timeuntil = round(time()) + duration
        else:
            timeuntil = 9223372036854775807
        id = await self.client.db.fetchval("INSERT INTO blacklist(user_id, moderator_id, blacklist_active, reason, time_until) VALUES($1, $2, $3, $4, $5) RETURNING incident_id", user.id, ctx.author.id, True, reason, timeuntil, column='incident_id')
        self.client.blacklist[user.id] = timeuntil
        embed=discord.Embed(title=f"{user} is now blacklisted.", description=f"**Reason**: {reason}\n**Blacklisted for**: {'Eternity' if duration == 9223372036854775807 else humanize_timedelta(seconds=duration)}\nBlacklisted until: {'NA' if timeuntil == 9223372036854775807 else f'<t:{timeuntil}:R>'}", color=discord.Color.red())
        logembed = discord.Embed(title=f"Bot Blacklist: Case {id}", description=f"**Reason:** {reason}\n**Blacklisted for**: {'Eternity' if duration == 9223372036854775807 else humanize_timedelta(seconds=duration)}\n**Blacklisted until**: {'NA' if timeuntil == 9223372036854775807 else f'<t:{timeuntil}:R>'}\n**Responsible Moderator**: {ctx.author} ({ctx.author.id})", color=discord.Color.red())
        logembed.set_author(name=f"{user} ({user.id})", icon_url=user.display_avatar.url)
        embed.set_footer(text="To unblacklist someone, use the `unblacklist` command.")
        embed.set_thumbnail(url=user.display_avatar.url)
        if duration != 9223372036854775807:
            dm_description=[f"You have been blacklisted from using {self.client.user.name} by the developers or an Admin from Dank Vibes.", '', f"**Reason:** {reason}", f"**Blacklisted for**: {'Permanently' if duration == 9223372036854775807 else humanize_timedelta(seconds=duration)}"]
        else:
            dm_description=[f"You have been **permanently** blacklisted from using {self.client.user.name} by the developers or an Admin from Dank Vibes.", '', f"**Reason:** {reason}"]
        dm_description.append(f"You will not be able to:\n• run **any** commands\n• Receive highlights\n• Be nickbetted against\n• Infect a user.\n\nYou will however, be reminded to vote and get Dank Memer reminders.")
        dm_description.append('')
        if duration != 9223372036854775807:
            dm_description.append(f"Your blacklist will end on <t:{timeuntil}>.\n")
        dm_description.append("If you think this is a mistake and would like your blacklist to be removed, or need further clarification, please open a ticket in <#870880772985344010>.")
        dmembed = discord.Embed(title="⚠️ Warning!", description='\n'.join(dm_description), color=discord.Color.red())
        try:
            await user.send(embed=dmembed)
        except:
            await ctx.send("I was unable to tell them that they have been blacklisted in their DMs.")
        await self.client.get_channel(906433823594668052).send(embed=logembed)
        await ctx.send(embed=embed)


    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="blacklists")
    async def active_blacklists(self, ctx, *, inquery: Union[discord.Member, int, str] = None):
        """
        Lists the active blacklists.
        To see the list of flags, use this command without any arguments.
        """
        if inquery is None:
            embed = discord.Embed(title="Blacklist Utilities", description="`--active` - list active blacklists.\n``--inactive` - list inactive blacklists.\n`<num>` - show a specific blacklist.\n`<member>` - list a member's blacklist.\n`--all` lists all past blacklists.", color=discord.Color.green())
            return await ctx.send(embed=embed)
        if type(inquery) == int:
            result = await self.client.db.fetchrow("SELECT * FROM blacklist WHERE incident_id = $1", inquery)
            if result is None:
                return await ctx.send(f"There is no such blacklist with the ID {inquery}.")
            member = ctx.guild.get_member(result.get('user_id'))
            embed = discord.Embed(title=f"Blacklist {inquery}", description=f"__Reason for blacklist__\n{result.get('reason')}", color=discord.Color.red() if result.get('blacklist_active') else discord.Color.green())
            embed.set_author(icon_url=member.display_avatar.url, name=f"{member} ({member.id})")
            embed.add_field
            embed.add_field(name="Is blacklist active?", value=result.get('blacklist_active'), inline=True)
            if result.get('blacklist_active'):
                embed.add_field(name="Blacklist until", value="Eternity" if result.get('time_until') == 9223372036854775807 else f"<t:{result.get('time_until')}:R>", inline=True)
            moderator = self.client.get_user(result.get('moderator_id'))
            embed.add_field(name="Responsible Moderator:", value=f"{moderator} ({moderator.id})" if moderator is not None else result.get('moderator_id'), inline=True)
            return await ctx.send(embed=embed)
        if type(inquery) == discord.Member:
            query = 'SELECT * FROM blacklist WHERE user_id = $1', inquery.id
            title = f"{inquery}'s blacklists"
        elif type(inquery) == str:
            if ctx.message.content.endswith("--active") or ctx.message.content.endswith("--open"):
                query = "SELECT * FROM blacklist WHERE blacklist_active = True"
                title = "Active blacklists"
            elif ctx.message.content.endswith("--inactive") or ctx.message.content.endswith("--closed"):
                query = "SELECT * FROM blacklist WHERE blacklist_active = False"
                title = "Closed blacklists"
            elif ctx.message.content.endswith("--all"):
                query = "SELECT * FROM blacklist"
                title = "All blacklists"
            else:
                return await ctx.send("You did not provide a proper flag.")
        else:
            embed = discord.Embed(title="Blacklist Utilities", description="`--active` - list active blacklists.\n`--inactive` - list inactive blacklists.\n`<num>` - show a specific blacklist.\n`<member>` - list a member's blacklist.\n`--all` lists all past blacklists.", color=discord.Color.green())
            return await ctx.send(embed=embed)
        if len(query) == 2:
            result = await self.client.db.fetch(query[0], query[1])
        else:
            result = await self.client.db.fetch(query)
        blacklists = []
        for blacklist in result:
            member = self.client.get_user(blacklist.get('user_id'))
            moderator = self.client.get_user(blacklist.get('moderator_id'))
            name = f"{blacklist.get('incident_id')}. {member} ({member.id})" if member is not None else f"{blacklist.get('incident_id')}. {blacklist.get('user_id')}"
            details = f"Reason: {blacklist.get('reason')}\n"
            if blacklist.get('blacklist_active'):
                details += f"Until: <t:{blacklist.get('time_until')}:R>\n" if blacklist.get('time_until') != 9223372036854775807 else 'Until: Eternity\n'
            details += f"Active: {'<:DVB_True:887589686808309791>' if blacklist.get('blacklist_active') else '<:DVB_False:887589731515392000>'}\n"
            details += f"Moderator: {moderator} ({moderator.id})" if moderator is not None else f"Moderator: {blacklist.get('moderator_id')}"
            blacklists.append((name, details))
        if len(blacklists) <= 10:
            embed = discord.Embed(title=title, color=self.client.embed_color, timestamp=discord.utils.utcnow())
            for suggestion in blacklists:
                embed.add_field(name=suggestion[0], value=suggestion[1], inline=False)
            return await ctx.send(embed=embed)
        else:
            pages = CustomMenu(source=Blacklist(blacklists, title), clear_reactions_after=True, timeout=60)
            return await pages.start(ctx)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='unblacklist', aliases=['unbl'])
    async def unblacklist(self, ctx, *, user: discord.Member = None):
        """Unblacklist a user so that they can continue using the bot."""
        if user is None:
            return await ctx.send('who tf do you want me to unblacklist huh')
        active_blacklist = await self.client.db.fetchrow("SELECT * FROM blacklist WHERE user_id=$1 and blacklist_active = $2", user.id, True)
        if active_blacklist is None:
            return await ctx.send(f"{user.mention} is currently not blacklisted.")
        await self.client.db.execute("UPDATE blacklist SET blacklist_active = $1 WHERE user_id = $2 and incident_id = $3", False, user.id, active_blacklist.get('incident_id'))
        embed = discord.Embed(title=f"{user} is now unblacklisted.", color=discord.Color.green())
        logembed = discord.Embed(title=f"Bot Unblacklist: Case {active_blacklist.get('incident_id')}", description=f"**Reason:** Manually unblacklisted by {ctx.author}\n**Responsible Moderator**: {ctx.author} ({ctx.author.id})", color=discord.Color.green())
        logembed.set_author(name=f"{user} ({user.id})", icon_url=user.display_avatar.url)
        await ctx.send(embed=embed)
        await self.client.get_channel(906433823594668052).send(embed=logembed)
        
    @commands.command(name="setnickchannel", aliases = ["nickchannel"])
    @commands.has_guild_permissions(manage_roles=True)
    async def setchannel(self, ctx, channel:discord.TextChannel=None):
        """
        Set the channel for nickname requests to be sent to.
        """
        result = await self.client.db.fetch("SELECT * FROM channelconfigs where guild_id = $1", ctx.guild.id)
        if len(result) == 0:
            await self.client.db.execute("INSERT INTO channelconfigs(guild_id, nicknamechannel_id) VALUES($1, $2)", ctx.guild.id, channel.id)
            return await ctx.send(f"I will now send nickname requests to {channel.mention}.")
        else:
            await self.client.db.execute("UPDATE channelconfigs SET nicknamechannel_id = $1 where guild_id = $2", channel.id, ctx.guild.id)
            await self.client.db.execute("DELETE FROM nicknames")
            return await ctx.send(f"I will now send nickname requests to {channel.mention}.\nAll nickname requests sent in a previous channel have been forfeited.")

    @commands.command(name="setdmchannel", aliases = ["dmchannel"])
    @commands.has_guild_permissions(manage_roles=True)
    async def setdmchannel(self, ctx, channel:discord.TextChannel=None):
        """
        Set the channel for dmname requests to be sent to.
        """
        result = await self.client.db.fetch("SELECT * FROM channelconfigs where guild_id = $1", ctx.guild.id)
        if len(result) == 0:
            await self.client.db.execute("INSERT INTO channelconfigs(guild_id, dmchannel_id) VALUES($1, $2)", ctx.guild.id, channel.id)
            return await ctx.send(f"I will now send DM requests to {channel.mention}.")
        else:
            await self.client.db.execute("UPDATE channelconfigs SET dmchannel_id = $1 where guild_id = $2", channel.id, ctx.guild.id)
            await self.client.db.execute("DELETE FROM dmrequests")
            return await ctx.send(f"I will now send DM requests to {channel.mention}.\nAll DM requests sent in a previous channel have been forfeited.")

    @commands.command(name="viewconfig")
    @commands.has_guild_permissions(manage_roles=True)
    async def viewconfig(self, ctx, channel: discord.TextChannel = None):
        """
        Show configurations for nickname and DM requests.
        """
        result = await self.client.db.fetchrow("SELECT * FROM channelconfigs where guild_id = $1", ctx.guild.id)
        if len(result) == 0:
            return await ctx.send(f"No configuration for DM and nickname requests have been set yet. ")
        else:
            await ctx.send(embed=discord.Embed(title=f"Configurations for {ctx.guild.name}", description = f"Nickname requests: {ctx.guild.get_channel(result.get('nicknamechannel_id'))}\nDM requests: {ctx.guild.get_channel(result.get('dmchannel_id'))}", color = self.client.embed_color))

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="messagereset", aliases=["mreset"], invoke_without_command=True)
    async def messagelog(self, ctx):
        """
        Resets the database for counting messages sent.
        """
        confirm_view = confirm(ctx, self.client, 30.0)
        messagecount = await self.client.db.fetch("SELECT * FROM messagelog")
        if len(messagecount) == 0:  # if there's nothing to be deleted
            return await ctx.send("There's no message count to be removed.")
        totalvote = sum(userentry.get('messagecount') for userentry in messagecount)
        embed = discord.Embed(title="Action awaiting confirmation", description=f"There are {len(messagecount)} people who have chatted, amounting to a total of {totalvote} messages. Are you sure you want to reset the message count?", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        try:
            msg = await ctx.reply(embed=embed, view=confirm_view)
        except Exception as e:
            msg = await ctx.send(embed=embed, view=confirm_view)
        confirm_view.response = msg
        await confirm_view.wait()
        if confirm_view.returning_value is None:
            embed.color, embed.description = discord.Color.red(), "You didn't respond."
            return await msg.edit(embed=embed)
        if confirm_view.returning_value == False:
            embed.color, embed.description = discord.Color.red(), "Action cancelled."
            return await msg.edit(embed=embed)
        if confirm_view.returning_value == True:
            await self.client.db.execute("DELETE FROM messagelog")
            embed.color, embed.description = discord.Color.green(), "The message count has been cleared."
            await msg.edit(embed=embed)

    @commands.group(invoke_without_command=True, name="messageroles")
    @commands.has_guild_permissions(manage_roles=True)
    async def messageroles(self, ctx):
        """
        Configure the milestones for the roles.
        """
        embed = discord.Embed(title="Dank Vibes Message Count Autorole configuration", timestamp=discord.utils.utcnow(), color=self.client.embed_color)
        embed.add_field(name="How to configure the message count roles?",
                        value=f"`messageroles list` shows all milestones for message count roles.\n`messageroles add [messagecount] [role]` adds a milestone for message count roles.\n`messageroles remove [messagecount]` will remove the milestone for the specified message count.")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="Roles can be stated via a name, mention or ID.")
        await ctx.send(embed=embed)

    @messageroles.command(name="list", aliases = ["show"])
    @commands.has_guild_permissions(manage_roles=True)
    async def mrolelist(self, ctx):
        """
        Lists milestones for message count roles.
        """
        messagemilestones = await self.client.db.fetch("SELECT * FROM messagemilestones")
        if len(messagemilestones) == 0:
            embed = discord.Embed(title = "Message count milestones", description = "There are no milestones set for now. Use `messageroles add [messagecount] [role]` to add one.", color=self.client.embed_color) # there are no milestones set
            return await ctx.send(embed=embed)
        output = ''
        for row in messagemilestones:
            if len(output) >= 3780:
                embed = discord.Embed(title="Message count milestones", description=output, color=self.client.embed_color)
                await ctx.send(embed=embed)
            role = ctx.guild.get_role(row.get('roleid'))
            rolemention = role.mention if role is not None else "unknown-or-deleted-role"
            output += f"**{row.get('messagecount')} messagess: **{rolemention}\n"
        embed = discord.Embed(title="Message count milestones", description=output, color=self.client.embed_color, timestamp=discord.utils.utcnow())
        embed.set_footer(text="To edit the milestones, use the subcommands `add` and `remove`.")
        await ctx.send(embed=embed)

    @messageroles.command(name="add", aliases=["create"])
    @commands.has_guild_permissions(manage_roles=True)
    async def roleadd(self, ctx, messagecount = None, role:discord.Role = None):
        """
        Adds milestones for message roles.
        """
        if messagecount is None or role is None: # missing arguments
            return await ctx.send("The correct usage of this command is `messageroles add [messagecount] [role]`.")
        try:
            messagecount = int(messagecount)
        except ValueError:
            return await ctx.send("`messagecount` is not a valid number.")
        existing_milestones = await self.client.db.fetch("SELECT * FROM messagemilestones WHERE messagecount = $1", messagecount)
        if len(existing_milestones) > 0:
            await ctx.send(f"You have already set a milestone for **{messagecount} messages**. To set a new role, remove this milestone and add it again.")
            return
        await self.client.db.execute("INSERT INTO messagemilestones VALUES($1, $2)", messagecount, role.id)
        await ctx.send(f"**Done**\n**{role.name}** will be added to a member when they have sent a message **{messagecount} time(s)**.")

    @messageroles.command(name="remove", aliases=["delete"])
    @commands.has_guild_permissions(manage_roles=True)
    async def roleremove(self, ctx, messagecount=None):
        """
        Removes milestones for nessage count roles.
        """
        if messagecount is None:
            return await ctx.send("The correct usage of this command is `messageroles remove [messagecount]`.")
        try:
            messagecount = int(messagecount)
        except ValueError:
            return await ctx.send(f"`{messagecount}` as the messagecount is not a valid number.")
        existing_milestones = await self.client.db.fetch("SELECT * FROM messagemilestones WHERE messagecount = $1", messagecount)
        if len(existing_milestones) == 0:
            return await ctx.send(
                f"You do not have a milestone set for {messagecount} messages. Use `messageroles add [messagecount] [role]` to add one.")
        await self.client.db.execute("DELETE FROM messagemilestones WHERE messagecount = $1", messagecount) # Removes the milestone rule
        await ctx.send(f"**Done**\nThe milestone for having sent a message **{messagecount} time(s)** has been removed.")

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.cooldown(1, 15, commands.BucketType.guild)
    @commands.command(name='demote', aliases = ['suggestion49', 'suggest49'])
    async def demote(self, ctx, member: discord.Member=None, duration: BetterTimeConverter=None):
        """
        The infamous suggestion 49.
        """
        selfdemote = False
        if member is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to tell me who to demote, otherwise I'm demoting **you**.")
        if duration is None:
            duration = 30
        if ctx.author.guild_permissions.administrator != True and ctx.guild.get_role(684591962094829569) not in ctx.author.roles:
            await ctx.send("You have not met the requirements to demote someone else, hence you're being self-demoted.")
            selfdemote = True
            member = ctx.author
        staffroleids = [758172293133762591, 837595970464120842, 837595945616277504, 837595910661603330, 843756047964831765,
         758172863580209203, 758173099752423435, 758173535029559376, 735417263968223234, 627284965222121482,
         892266027495350333, 756667326623121568, 644711739618885652, 709107981568180327, 697314852162502698,
         758175645393223680, 608495204399448066, 870850266868633640, 674774385894096896, 795914641191600129,
         722871699325845626, 608503892002603029, 684591962094829569, 663502776952815626,
         735015819771379712, 895341539549659136]
        #staffroleids = [896052612284166204, 896052592797417492, 895815832465190933, 895815799812521994, 895815773208051763, 895815588289581096, 895815546292035625]
        staffroles = [ctx.guild.get_role(id) for id in staffroleids]
        for i in staffroles:
            if i is None:
                staffroles.remove(i)
        if not staffroles:
            return await ctx.send("I can't find any roles to remove.")
        removable = [role for role in staffroles if role in member.roles]
        tupremove = tuple(removable)
        if not tupremove:
            return await ctx.send(f"There are no roles that I can remove from {member} to demote them.")
        msg = await ctx.send(f"**Demoting {member.mention}...**")
        async with ctx.typing():
            try:
                await member.remove_roles(*tupremove, reason=f"Demoted by {ctx.author}")
            except Exception as e:
                return await msg.edit(content=f"There was an issue with removing roles. I've temporarily stopped demoting {member}. More details: {e}")
        lstofrolenames = [role.name for role in tupremove]
        if duration > 300:
            duration = 300
        try:
            await msg.edit(content=f"{member.mention} has been demoted for {humanize_timedelta(seconds=duration)}. They are no longer a  **{grammarformat(lstofrolenames)}.**")
        except discord.NotFound:
            await ctx.send(f"{member.mention} has been demoted for {humanize_timedelta(seconds=duration)}. Their removed roles are: **{grammarformat(lstofrolenames)}**")
        try:
            message = f"Alas! Due to you misbehaving, you have been demoted by **{ctx.author}**." if not selfdemote else "You have just self demoted yourself."
            await member.send(f"{message} You no longer have the roles: **{', '.join(role.name for role in tupremove)}**. \nYour roles might be readded afterwards. Or will they? <:dv_bShrugOwO:837687264263798814>")
        except:
            pass
        await asyncio.sleep(duration)
        try:
            await member.add_roles(*tupremove, reason='Demotion reversed automatically')
        except Exception as e:
            return await ctx.send(f"There was an issue with adding roles. I've temporarily stopped promoting {member}. More details: {e}")
        return await ctx.send(f"{member.mention} congratulations on your promotion to:  **{', '.join(role.name for role in tupremove)}**!")

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name="dungeon", invoke_without_command=True)
    async def dungeon(self, ctx):
        """
        This is the placeholder base command for `dungeon bypass`
        """
        return await ctx.help()

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='resetclowns')
    async def resetclowns(self, ctx):
        """
        Resets the state of clowns so no one will change to a clown in any channel.
        """
        self.client.clownmode = {}
        return await ctx.send("<:DVB_checkmark:955345523139805214> Reset clown mode")

    @checks.has_permissions_or_role(manage_roles=True)
    @dungeon.command(name="bypass")
    async def dungeon_bypass(self, ctx: DVVTcontext, *, user: discord.User):
        """
        Allow a user to bypass dungeon bans. If you run it again it will remove the bypass.
        """
        bypass_ban = await self.client.db.fetchval("SELECT bypass_ban FROM userconfig WHERE user_id = $1", user.id)
        if bypass_ban is not True:
            set = True
        else:
            set = False
        await self.client.db.execute("INSERT INTO userconfig (user_id, bypass_ban) VALUES($1, $2) ON CONFLICT(user_id) DO UPDATE SET bypass_ban = $2", user.id, set)
        if set is True:
            await ctx.send(f"{user} ({user.id}) will be allowed to bypass the auto ban regardless of their account age.")
        else:
            await ctx.send(f"{user} ({user.id}) will NOT be able to bypass the auto ban if their account age is less than the set specified age.")

