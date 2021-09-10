import discord
from datetime import datetime
from discord.ext import commands
from utils import checks
import asyncio
from discord.ext import commands, menus
from utils.menus import CustomMenu
import json
from utils.buttons import *
emojis = ["<:checkmark:841187106654519296>", "<:crossmark:841186660662247444>"]

class start_or_end(discord.ui.View):
    def __init__(self, ctx: DVVTcontext, client, timeout):
        self.timeout = timeout
        self.context = ctx
        self.response = None
        self.client = client
        self.returning_value = None
        super().__init__(timeout=timeout)

    @discord.ui.button(label="When lockdown starts", style=discord.ButtonStyle.primary, emoji="▶")
    async def start_message(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.returning_value = 0
        for b in self.children:
            b.disabled = True
        await self.response.edit(view=self)
        self.stop()

    @discord.ui.button(label="When lockdown ends", style=discord.ButtonStyle.primary, emoji="⏹")
    async def mention(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.returning_value = 1
        for b in self.children:
            b.disabled = True
        await self.response.edit(view=self)
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        ctx = self.context
        author = ctx.author
        if interaction.user != author:
            await interaction.response.send_message("These buttons aren't for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        self.returning_value = None
        for b in self.children:
            b.disabled = True
        await self.response.edit(view=self)


async def send_lockdown_message(self, channel: discord.TextChannel, message: str, extra_message: str = None):
    try:
        embedjson = json.loads(message)
    except json.decoder.JSONDecodeError:
        embed = discord.Embed(title="This channel is under lockdown! 🔒",
                              description=message, color=self.client.embed_color)
        embed.set_footer(icon_url=channel.guild.icon.url, text=channel.guild.name)
        return await channel.send(content=extra_message, embed=embed)
    else:
        if "title" in embedjson and "description" in embedjson:
            try:
                return await channel.send(content=extra_message, embed=discord.Embed.from_dict(embedjson))
            except discord.HTTPException:
                embed = discord.Embed(title="This channel is under lockdown! 🔒",
                                      description=message, color=self.client.embed_color)
                embed.set_footer(icon_url=channel.guild.icon.url, text=channel.guild.name)
                return await channel.send(content=extra_message, embed=embed)
        else:
            embed = discord.Embed(title="This channel is under lockdown! 🔒",
                                  description=message, color=self.client.embed_color)
            embed.set_footer(icon_url=channel.guild.icon.url, text=channel.guild.name)
            return await channel.send(content=extra_message, embed=embed)

class lockdown_pagination(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=20)

    async def format_page(self, menu, page):
        embed = discord.Embed(color=0x57F0F0, title=self.title)
        embed.description = "\n".join(page)
        return embed

class lockdown(commands.Cog):
    def __init__(self, client):
        self.client = client

    @checks.has_permissions_or_role(administrator=True)
    @commands.group(name="lockdown", invoke_without_command=True)
    async def lockdown(self, ctx):
        """
        Lockdown Guide for Dank Vibes Bot
        """
        message = """
        This lockdown feature allows you to create separate groups of channels (or lockdown profiles) to be able to lock and unlock many channels at once. It also allows you to set a separate message for each profile. When quoting profile names, add quotations `""` for names with spaces, unless you're using `view`, `delete`, `start` and `end`.
        **__Editing lockdown profiles__**
        `lockdown create [profile_name] [channel]`
        Creates a lockdown profile with the name specified in `profile_name`.
        
        `lockdown add [profile_name] [channel1] <channel2> ...`
        Adds channels to the specified lockdown profile. You can add more than one channel in this command to add various channels at once.
        
        `lockdown remove [profile_name] [channel1] <channel2> ...`
        Removes channels from the specified lockdown profile. You can add more than one channel in this command to remove various channels at once.
        
        `lockdown delete [profille_name]`
        Deletes all channels in a lockdown profile, hence removing a lockdown profile.
        
        `lockdown view <profile_name>`
        Using this command without any arguments will show the lockdown profiles. Viewing a lockdown profile will show you the channels in it.
        
        `lockdown msg [profile_name] [message_or_json_embed]`
        This will set a message for the lockdown profile when it is used to lock channels.
        
        **__Using lockdown profiles__**
        `lockdown start [profile_name]`
        Locks down all channels in a lockdown profile. If a message is specified, it will send that message when locking down the channels.
        
        `lockdown end [profile_name]`
        Unlocks down all channels in a lockdown profile. It will send a default message when unlocking channels.
        """
        await ctx.send(embed=discord.Embed(title=f"{self.client.user.name}'s Lockdown Guide", description=message, color=self.client.embed_color, timestamp=datetime.utcnow()))

    @checks.has_permissions_or_role(administrator=True)
    @lockdown.command(name="create")
    async def lockdown_create(self, ctx, name=None, channel:discord.TextChannel=None):
        """
        Create a Lockdown profile for certain channels to be locked in that profile. The channel in this command is the first channel to be added to the lockdown profile. To have a lockdown profile name with spaces, use quotes around the name.
        """
        if name is None:
            return await ctx.send("You need to specify what you want the name of the lockdown profile to be. `lockdown create [profile_name] [channel]`")
        elif channel is None:
            return await ctx.send("You need to specify what you want the first channel in the lockdown profile to be. `lockdown create [profile_name] [channel]`")
        if len(name) > 18:
            return await ctx.send(f"Your requested profile name is {len(name)} characters long. It can only be 18 characters long.")
        name = name.lower()
        existing_profile = await self.client.pool_pg.fetchrow("SELECT * FROM lockdownprofiles WHERE profile_name = $1 and guild_id = $2", name, ctx.guild.id)
        if existing_profile is not None:
            return await ctx.send(f"<:DVB_eyeroll:878146268277374976> You already have a profile with the name `{name}`. You can add or remove channels to that profile with `lockdown add [profile_name] [channel]` and `lockdown remove [profile_name] [channel]` respectively. You can also remove the lockdown profile with `lockdown delete [profile_name]`.")
        await self.client.pool_pg.execute("INSERT INTO lockdownprofiles VALUES($1, $2, $3)", ctx.guild.id, name, channel.id)
        return await ctx.send(embed=discord.Embed(title="Success!", description = f"The lockdown profile with the name **{name}** has been created and **{channel}** has been added to the lockdown profile.", color=discord.Color.green()))

    @checks.has_permissions_or_role(administrator=True)
    @lockdown.command(name="add")
    async def lockdown_add(self, ctx, profile_name=None, channels: commands.Greedy[discord.TextChannel]=None):
        """
        Adds a channel to a lockdown profile.
        """
        if profile_name is None:
            return await ctx.send("You need to specify the name of the lockdown profile. `lockdown add [profile_name] [channel]`")
        elif channels is None:
            return await ctx.send("You need to specify the channel to be added to the profile. `lockdown add [profile_name] [channel]`")
        profile_name = profile_name.lower()
        lockdown_profile = await self.client.pool_pg.fetch("SELECT * FROM lockdownprofiles WHERE profile_name = $1 and guild_id = $2", profile_name, ctx.guild.id)
        if len(lockdown_profile) == 0:
            return await ctx.send(f"There is no such lockdown profile with the name **{profile_name}**.")
        added_channels = []
        already_added_channels = []
        results = await self.client.pool_pg.fetch("SELECT channel_id FROM lockdownprofiles WHERE profile_name=$1 and guild_id = $2", profile_name, ctx.guild.id)
        results = [result.get('channel_id') for result in results]
        channels = list(dict.fromkeys(channels))
        for channel in channels:
            if channel.id in results:
                already_added_channels.append(channel.mention)
            else:
                await self.client.pool_pg.execute("INSERT INTO lockdownprofiles VALUES($1, $2, $3)", ctx.guild.id, profile_name, channel.id)
                added_channels.append(channel.mention)
        if len(added_channels) != 0:
            added_channels = ", ".join(added_channels)
            desccontent = f"**{added_channels}** has been added to the lockdown profile **{profile_name}**."
        else:
            desccontent = ""
        if len(already_added_channels) != 0:
            already_added_channels = ", ".join(already_added_channels)
            desccontent += f"\n{already_added_channels} was/were not added to the lockdown profile **{profile_name}** as it already exists in the profile."
        return await ctx.send(embed=discord.Embed(title="Success!", description=desccontent, color=discord.Color.green() if len(already_added_channels) == 0 else discord.Color.orange()))

    @checks.has_permissions_or_role(administrator=True)
    @lockdown.command(name="view")
    async def lockdown_view(self, ctx, *, profile_name=None):
        """
        View the channels in a lockdown profile. When executed without any arguments, it will show the list of profiles instead.
        """
        if profile_name is not None:
            profile_name = profile_name.lower()
            lockdown_profile = await self.client.pool_pg.fetch("SELECT * FROM lockdownprofiles WHERE profile_name = $1 and guild_id = $2",
                                                               profile_name, ctx.guild.id)
            if len(lockdown_profile) == 0:
                return await ctx.send(f"There is no such lockdown profile with the name **{profile_name}**.")
            channel_list = []
            deleted_channels = 0
            for ele in lockdown_profile:
                channel = self.client.get_channel(ele.get('channel_id'))
                if channel is None:
                    await self.client.pool_pg.execute("DELETE FROM lockdownprofiles WHERE profile_name = $1 and channel_id = $2 and guild_id = $3", profile_name, ele.get('channel_id'), ctx.guild.id)
                    deleted_channels += 1
                else:
                    channel_list.append(f"• {channel.mention}")
            if deleted_channels > 0:
                channel_list.append(f"\n{deleted_channels} channels have been removed from this profile as {self.client.user.name} was unable to find those channels.")
            title = f"Channels in {profile_name}"
            pages = CustomMenu(source=lockdown_pagination(channel_list, title), clear_reactions_after=True, timeout=30)
            await pages.start(ctx)
        else:
            results = await self.client.pool_pg.fetch("SELECT * FROM lockdownprofiles WHERE guild_id = $1", ctx.guild.id)
            if len(results) == 0:
                return await ctx.send("There are no lockdown profiles in this guild. Use `lockdown create` to create a lockdown profile.")
            profiles = {}
            for result in results:
                if result.get('profile_name') not in profiles:
                    profiles[result.get('profile_name')] = 1
                else:
                    profiles[result.get('profile_name')] += 1
            msgcontent = ""
            for profile in profiles:
                msgcontent += f"{profile}\n<:Reply:871808167011549244> `{profiles[profile]}` channels\n"
            embed = discord.Embed(title=f"Lockdown profiles in {ctx.guild.name}", description=msgcontent, color=self.client.embed_color)
            embed.add_field(name="Tips", value="Use `lockdown start <profile_name>` to lock down channels in a lockdown profile.\nUse `lockdown view <profile_name>` to view the channels in a lockdown profile.", inline=False)
            embed.set_footer(text="help! i'm actually a human imprisoned behind the bot :(", icon_url="https://cdn.discordapp.com/emojis/818151528162263090.gif?v=1")
            await ctx.send(embed=embed)

    @checks.has_permissions_or_role(administrator=True)
    @lockdown.command(name="remove")
    async def lockdown_remove(self, ctx, profile_name=None, channels: commands.Greedy[discord.TextChannel]=None):
        """
        Removes a channel from a lockdown profile.
        """
        if profile_name is None:
            return await ctx.send("You need to specify the name of the lockdown profile. `lockdown remove [profile_name] [channel]`")
        elif channels is None:
            return await ctx.send("You need to specify the channel to be added to the profile. `lockdown remove [profile_name] [channel]`")
        profile_name = profile_name.lower()
        lockdown_profile = await self.client.pool_pg.fetch("SELECT * FROM lockdownprofiles WHERE profile_name = $1 and guild_id = $2", profile_name, ctx.guild.id)
        if len(lockdown_profile) == 0:
            return await ctx.send(f"There is no such lockdown profile with the name **{profile_name}**.")
        removed_channels = []
        non_existent_channels = []
        results = await self.client.pool_pg.fetch("SELECT channel_id FROM lockdownprofiles WHERE profile_name=$1 and guild_id = $2", profile_name, ctx.guild.id)
        results = [result.get('channel_id') for result in results]
        channels = list(dict.fromkeys(channels))
        for channel in channels:
            if channel.id in results:
                await self.client.pool_pg.execute("DELETE FROM lockdownprofiles where guild_id = $1 and profile_name = $2 and channel_id = $3", ctx.guild.id, profile_name, channel.id)
                removed_channels.append(channel.mention)
            else:
                non_existent_channels.append(channel.mention)
        if len(removed_channels) != 0:
            removed_channels = ", ".join(removed_channels)
            desccontent = f"**{removed_channels}** has been removed from the lockdown profile **{profile_name}**."
        else:
            desccontent = ""
        if len(non_existent_channels) != 0:
            non_existent_channels = ", ".join(non_existent_channels)
            desccontent += f"\n{non_existent_channels} aren't in the profile **{profile_name}** so they were not removed."
        return await ctx.send(embed=discord.Embed(title="Success!", description=desccontent, color=discord.Color.green() if len(non_existent_channels) == 0 else discord.Color.orange()))

    @checks.has_permissions_or_role(administrator=True)
    @lockdown.command(name="delete", aliases = ["clear"])
    async def lockdown_delete(self, ctx, *, profile_name=None):
        """
        This **deletes** a lockdown profile!
        """
        if profile_name is None:
            return await ctx.send(
                "You need to specify the name of the lockdown profile. `lockdown delete [profile_name]`")
        profile_name = profile_name.lower()
        lockdown_profile = await self.client.pool_pg.fetch(
            "SELECT * FROM lockdownprofiles WHERE profile_name = $1 and guild_id = $2", profile_name, ctx.guild.id)
        if len(lockdown_profile) == 0:
            return await ctx.send(f"There is no such lockdown profile with the name **{profile_name}**.")
        confirmview = confirm(ctx, self.client, 30.0)
        embed = discord.Embed(title="Action awaiting confirmation", description=f"Are you sure you want to remove the lockdown profile **{profile_name}** with {len(lockdown_profile)} channels? **This action is irreversible!**", color=discord.Color.orange())
        msg = await ctx.send(embed=embed, view=confirmview)
        confirmview.response = msg
        await confirmview.wait()
        if confirmview.returning_value is None:
            embed.color, embed.description = discord.Color.red(), "You didn't respond in time."
            return await msg.edit(embed=embed)
        if confirmview.returning_value == False:
            embed.color, embed.description = discord.Color.red(), "Action cancelled."
            return await msg.edit(embed=embed)
        if confirmview.returning_value == True:
            await self.client.pool_pg.execute("DELETE FROM lockdownprofiles WHERE profile_name = $1 and guild_id = $2", profile_name, ctx.guild.id)
            await self.client.pool_pg.execute("DELETE FROM lockdownmsgs WHERE profile_name = $1 and guild_id = $2", profile_name, ctx.guild.id)
            embed.color, embed.description = discord.Color.green(), f"The lockdown profile **{profile_name}** has been removed."
            return await msg.edit(embed=embed)

    @checks.has_permissions_or_role(administrator=True)
    @lockdown.command(name="start", aliases = ["initiate"])
    async def lockdown_start(self, ctx, *, profile_name = None):
        """
        Locks down all channels in the specified lockdown profile.
        """
        if profile_name is None:
            return await ctx.send(
                "You need to specify the name of the lockdown profile. `lockdown start [profile_name]`")
        profile_name = profile_name.lower()
        lockdown_profile = await self.client.pool_pg.fetch(
            "SELECT * FROM lockdownprofiles WHERE profile_name = $1 and guild_id = $2", profile_name, ctx.guild.id)
        if len(lockdown_profile) == 0:
            return await ctx.send(f"There is no such lockdown profile with the name **{profile_name}**.")
        confirmview = confirm(ctx, self.client, 30.0)
        embed = discord.Embed(title="Awaiting Lockdown confirmation...", description=f"Are you sure you want to lock down {len(lockdown_profile)} channels in the lockdown profile **{profile_name}**?", color=discord.Color.orange())
        message = await ctx.send(
            embed=embed, view = confirmview)
        confirmview.response = message
        await confirmview.wait()
        if confirmview.returning_value is None:
            embed.description, embed.color = "You didn't react on time.", discord.Color.red()
            return await message.edit(embed=embed)
        elif confirmview.returning_value == False:
            embed.description, embed.color = "Command stopped.", discord.Color.red()
            return await message.edit(embed=embed)
        elif confirmview.returning_value == True:
            embed.description, embed.color = "<a:DVB_Lock:884390743714725889> Locking channels...", discord.Color.green()
            await message.edit(embed=embed)
            channels_not_found = []
            channels_missing_perms = []
            channels_success = []
            special_cases = []
            lockdownmsg_entry = await self.client.pool_pg.fetchrow(
                "SELECT startmsg FROM lockdownmsgs WHERE guild_id = $1 and profile_name = $2", ctx.guild.id,
                profile_name)
            lockdownmsg = None
            if lockdownmsg_entry is not None:
                lockdownmsg = lockdownmsg_entry.get('startmsg')
            for entry in lockdown_profile:
                channel = ctx.guild.get_channel((entry.get('channel_id')))
                if channel is None:
                    channels_not_found.append(str(entry.get('channel_id')))
                else:
                    try:
                        overwrites = channel.overwrites_for(ctx.guild.default_role)
                        if channel.name == "support":
                            overwrites.view_channel = False
                            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites,
                                                          reason=f"Denied view channel permissions through lockdown issued by {ctx.author} for channels in the {profile_name} Lockdown Profile")
                            special_cases.append((channel.mention, "Denied view channel Permissions",))
                        else:
                            overwrites.send_messages = False
                            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites,
                                                          reason=f"Lockdown issued by {ctx.author} for channels in the {profile_name} Lockdown Profile")
                            if lockdownmsg is not None:
                                await send_lockdown_message(self, channel, lockdownmsg)
                            channels_success.append(channel.mention)
                    except discord.Forbidden:
                        channels_missing_perms.append(channel.mention)
            msg_content = f"{len(channels_success)} channels were successfully locked."
            if len(channels_missing_perms) > 0:
                msg_content += f"\nI was not able to lock down these channels due to missing permissions: {', '.join(channels_missing_perms)}"
            if len(channels_not_found) > 0:
                msg_content += f"\nI was not able to lock down these channels as I could not find them: {', '.join(channels_not_found)}"
            if 0 < len(special_cases) < 30:
                msg_content += f"\n\nThese channels had special actions:\n"
                for case in special_cases:
                    msg_content += f"{case[0]} - {case[1]}"
            await ctx.send(msg_content)


    @checks.has_permissions_or_role(administrator=True)
    @lockdown.command(name="end")
    async def lockdown_end(self, ctx, *, profile_name = None):
        """
        Unlocks all channels in the specified lockdown profile.
        """
        if profile_name is None:
            return await ctx.send(
                "You need to specify the name of the lockdown profile. `lockdown end [profile_name]`")
        profile_name = profile_name.lower()
        lockdown_profile = await self.client.pool_pg.fetch("SELECT * FROM lockdownprofiles WHERE profile_name = $1 and guild_id = $2", profile_name, ctx.guild.id)
        if len(lockdown_profile) == 0:
            return await ctx.send(f"There is no such lockdown profile with the name **{profile_name}**.")
        confirmview = confirm(ctx, self.client, 30.0)
        embed = discord.Embed(title="Awaiting Lockdown confirmation...", description=f"Are you sure you want to unlock {len(lockdown_profile)} channels in the lockdown profile **{profile_name}**?", color=discord.Color.orange())
        message = await ctx.send(embed=embed, view = confirmview)
        confirmview.response = message
        await confirmview.wait()
        if confirmview.returning_value is None:
            embed.description, embed.color = "You didn't react on time.", discord.Color.red()
            return await message.edit(embed=embed)
        elif confirmview.returning_value == False:
            embed.description, embed.color = "Command stopped.", discord.Color.red()
            return await message.edit(embed=embed)
        elif confirmview.returning_value == True:
            embed.description, embed.color = "<a:DVB_Unlock:884392509432807424> Unlocking channels...", discord.Color.green()
            await message.edit(embed=embed)
            channels_not_found = []
            channels_missing_perms = []
            channels_success = []
            special_cases = []
            lockdownmsg_entry = await self.client.pool_pg.fetchrow(
                "SELECT endmsg FROM lockdownmsgs WHERE guild_id = $1 and profile_name = $2", ctx.guild.id, profile_name)
            lockdownmsg = None
            if lockdownmsg_entry is not None:
                lockdownmsg = lockdownmsg_entry.get('endmsg')
            for entry in lockdown_profile:
                channel = ctx.guild.get_channel((entry.get('channel_id')))
                if channel is None:
                    channels_not_found.append(str(entry.get('channel_id')))
                else:
                    try:
                        overwrites = channel.overwrites_for(ctx.guild.default_role)
                        if channel.name == "support":
                            overwrites.view_channel = True
                            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites,
                                                          reason=f"Allowed to view support channel through lockdown end issued by {ctx.author} for channels in the {profile_name} Lockdown Profile")
                            special_cases.append((channel.mention, "Allowed view channel Permissions",))
                        else:
                            overwrites.send_messages = None
                            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites,
                                                          reason=f"Lockdown removed, issued by {ctx.author} for channels in the Lockdown Profile '{profile_name}'")
                            channels_success.append(channel.mention)
                            if lockdownmsg is not None:
                                await send_lockdown_message(self, channel, lockdownmsg)
                    except discord.Forbidden:
                        channels_missing_perms.append(channel.mention)
            msg_content = f"{len(channels_success)} channels were successfully unlocked."
            if len(channels_missing_perms) > 0:
                msg_content += f"\nI was not able to unlock these channels due to missing permissions: {', '.join(channels_missing_perms)}"
            if len(channels_not_found) > 0:
                msg_content += f"\nI was not able to unlock these channels as I could not find them: {', '.join(channels_not_found)}"
            if 0 < len(special_cases) < 30:
                msg_content += f"\n\nThese channels had special actions:\n"
                for case in special_cases:
                    msg_content += f"{case[0]} - {case[1]}"
            await ctx.send(msg_content)

    @checks.has_permissions_or_role(administrator=True)
    @lockdown.command(name="msg", aliases = ["message"])
    async def lockdown_message(self, ctx, profile_name = None, *, message = None):
        """
        Changes the lockdown message for a specific lockdown profile. You can add a embed as the lockdown message by getting the JSON code of an embed via Carlbot. Otherwise, a normal message will be shown in a generic embed's description.
        ⚠️ This only applies to lockdown messages, and not unlock messages.
        To view the message for a lockdown profile, just use the command without a message.
        """
        if profile_name is None:
            return await ctx.send("You need to specify the name of the lockdown profile. `lockdown delete [profile_name]`")
        profile_name = profile_name.lower()
        lockdown_profile = await self.client.pool_pg.fetch(
            "SELECT * FROM lockdownprofiles WHERE profile_name = $1 and guild_id = $2", profile_name, ctx.guild.id)
        if len(lockdown_profile) == 0:
            return await ctx.send(f"There is no such lockdown profile with the name **{profile_name}**.")
        startEndview = start_or_end(ctx, self.client, 30.0)
        embed = discord.Embed(title="Selecting lockdown message...",
                              description=f"Choose the message that you are viewing/editing for the lockdown profile **{profile_name}**.",
                              color=self.client.embed_color)
        msg = await ctx.send(embed=embed, view=startEndview)
        startEndview.response = msg
        await startEndview.wait()
        startEndview.response = msg
        if startEndview.returning_value is None:
            embed.color = discord.Color.red()
            embed.description = "You didn't select an option."
            return await msg.edit(embed=embed)
        if message is None:
            lockdownmsg_entry = await self.client.pool_pg.fetchrow("SELECT * FROM lockdownmsgs WHERE guild_id = $1 and profile_name = $2", ctx.guild.id, profile_name)
            if lockdownmsg_entry is not None:
                if startEndview.returning_value == 0:
                    lockdownmsg = lockdownmsg_entry.get('startmsg')
                elif startEndview.returning_value == 1:
                    lockdownmsg = lockdownmsg_entry.get('endmsg')
                else:
                    lockdownmsg = None
                if lockdownmsg is not None:
                    return await send_lockdown_message(self, ctx.channel, lockdownmsg, f"This is the message sent when channels are {'locked' if startEndview.returning_value == 0 else 'unlocked'} in the lockdown profile **{profile_name}**")
            return await ctx.send(f"There is no message set for **{'unlocking' if startEndview.returning_value == 0 else 'locking'}** channels in the lockdown profile **{profile_name}**. You can set one with `dv.lockdown msg {profile_name} [message_in_plain_text_or_json]`.")
        lockdownprofilemsg = await self.client.pool_pg.fetchrow("SELECT * FROM lockdownmsgs WHERE profile_name = $1 and guild_id = $2", profile_name, ctx.guild.id)
        slug = 'startmsg' if startEndview.returning_value == 0 else 'endmsg'
        if lockdownprofilemsg is not None:
            if startEndview.returning_value == 0:
                await self.client.pool_pg.execute("UPDATE lockdownmsgs SET startmsg = $1 WHERE profile_name = $2 and guild_id = $3", message, profile_name, ctx.guild.id)
            elif startEndview.returning_value == 1:
                await self.client.pool_pg.execute("UPDATE lockdownmsgs SET endmsg = $1 WHERE profile_name = $2 and guild_id = $3", message, profile_name, ctx.guild.id)
        else:
            if startEndview.returning_value == 0:
                await self.client.pool_pg.execute("INSERT INTO lockdownmsgs (guild_id, profile_name, startmsg) VALUES($1, $2, $3)", ctx.guild.id, profile_name, message)
            elif startEndview.returning_value == 1:
                await self.client.pool_pg.execute("INSERT INTO lockdownmsgs (guild_id, profile_name, endmsg) VALUES($1, $2, $3)", ctx.guild.id, profile_name, message)
        return await send_lockdown_message(self, ctx.channel, message, f"I have successfully set your lockdown message for the lockdown profile **{profile_name}**. This is how it will look like:")