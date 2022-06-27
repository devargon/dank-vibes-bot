import itertools
import json

from discord.ext import menus, pages

from main import dvvt
from .lockdown import lockdown
from .censor import censor
from .browser_screenshot import BrowserScreenshot
from .sticky import Sticky
from .mod_slash import ModSlash
from .role import Role

from utils import checks
from utils.buttons import *
from utils.format import text_to_file, ordinal, human_join
from utils.time import humanize_timedelta
from utils.menus import CustomMenu
from utils.converters import BetterTimeConverter, MemberUserConverter

import os
from selenium import webdriver
from thefuzz import process
from collections import Counter
from datetime import timedelta, datetime
import time

class ViewEmbedJSONs(discord.ui.View):
    def __init__(self, embeds):
        self.embeds = embeds
        super().__init__(timeout=None)

    @discord.ui.button(label="View raw JSON embeds", style=discord.ButtonStyle.primary, emoji=discord.PartialEmoji.from_str("<:DVB_Embed:976499722070151258>"))
    async def view_raw_json(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        await interaction.response.edit_message(embeds=self.embeds, view=self)

modlog_channelID = 873616122388299837 if os.getenv('state') == '1' else 640029959213285387

class ListWatchlistNotifyMethods(discord.ui.Select):
    def __init__(self, client, default_index):
        self.default_index = default_index
        self.client = client
        options = []
        options.append(discord.SelectOption(label="None", value='none', description="You will not be notified about any watchlist joins.", default = False))
        options.append(discord.SelectOption(label="DM", value='dm', description="You will be DMed when a user on your watchlist joins this server.", emoji = discord.PartialEmoji.from_str("<:DVB_Letter:884743813166407701>"), default = True if default_index == 1 else False))
        options.append(discord.SelectOption(label = "Ping", value='ping', description = f"You will be pinged when a user on your watchlist joins this server.", emoji = discord.PartialEmoji.from_str("<:DVB_Ping:883744614295674950>"), default = True if default_index == 2 else False))
        super().__init__(placeholder='Change how you want to be notified for your watchlist...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        result = self.values[0]
        if result == 'none':
            xd = 0
        elif result == 'dm':
            xd = 1
        elif result == 'ping':
            xd = 2
        else:
            return await interaction.response.send_message("Invalid", ephemeral=True)
        await self.client.db.execute("INSERT INTO userconfig(user_id, watchlist_notify) VALUES($1, $2) ON CONFLICT(user_id) DO UPDATE SET watchlist_notify = $2", interaction.user.id, xd)
        if result == 'None':
            summary = "You will not be notified about any joins from your watchlist."
        elif result == 'dm':
            summary = "You will now be DMed when a user on your watchlist joins this server."
        elif result == 'ping':
            summary = "You will now be pinged when a user on your watchlist joins this server."
        else:
            summary = "Invalid"
        await interaction.response.send_message(summary, ephemeral=True)
        #self.options[xd].default = True
        #await interaction.response.edit_message(view=self.view)

class ChangeWatchlistNotify(discord.ui.View):
    def __init__(self, client, default_index, user):
        self.client = client
        self.default_index = default_index
        self.response = None
        self.user = user
        super().__init__(timeout=45)

        self.add_item(ListWatchlistNotifyMethods(client, default_index))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(embed=discord.Embed(description="Only the author (`{}`) can interact with this message.".format(self.user), color=discord.Color.red()), ephemeral=True)
            return False
        else:
            return True

    async def on_timeout(self):
        for b in self.children:
            b.disabled = True
        await self.response.edit(view=self)


class FrozenNicknames(menus.ListPageSource):
    def __init__(self, entries, title, inline):
        self.title = title
        self.inline = inline
        super().__init__(entries, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=menu.ctx.bot.embed_color, timestamp=discord.utils.utcnow())
        for entry in entries:
            embed.add_field(name=f"{entry[0]}", value=entry[1], inline=self.inline)
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed

class GetHeistPing(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Get the Heist Ping role", style=discord.ButtonStyle.green)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not discord.utils.get(interaction.user.roles, name="Heist Ping"):
            await interaction.user.add_roles(discord.utils.get(interaction.guild.roles, name="Heist Ping"))
            await interaction.response.send_message("<:DVB_True:887589686808309791> The <@&758174643814793276> role has been added to you!", ephemeral=True)
        else:
            await interaction.response.send_message("<:DVB_True:887589686808309791> You already have the <@&758174643814793276> role.", ephemeral=True)

class PublicVoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="See if you can join the heist later!", style=discord.ButtonStyle.green)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if discord.utils.get(interaction.user.roles, name="DV Voter"):
            await interaction.response.send_message("<:DVB_True:887589686808309791> **You currently have the <@&683884762997587998> role** and can join the heist!\nIf the heist hasn't started, get <@&758174643814793276> to be notified when it starts!", ephemeral=True, view=GetHeistPing())
        else:
            await interaction.response.send_message("<:DVB_False:887589731515392000> **You do not have the <@&683884762997587998> role.**\n` - ` Vote for Dank Vibes at https://top.gg/servers/595457764935991326/vote, and click on the button again to see if you can join the heist!\n` - ` If you have voted for Dank Vibes but still do not have the role, open a ticket in <#870880772985344010> and inform a Mod there.", ephemeral=True)

class ModlogPagination:
    def __init__(self, entries, user, per_page, client):
        self.user = user
        self.entries = entries
        self.pages = []
        self.client = client
        self.per_page = per_page

    def get_pages(self):
        while len(self.entries) > self.per_page:
            self.pages.append(self.format_page(self.entries[:self.per_page]))
            self.entries = self.entries[self.per_page:]
        self.pages.append(self.format_page(self.entries))
        return self.pages

    def format_page(self, page):
        embed = discord.Embed(color=self.client.embed_color, title="Mod Log", timestamp=discord.utils.utcnow()).set_author(icon_url=self.user.display_avatar.url, name=f"{self.user} ({self.user.id}")
        for entry in page:
            if entry.get('action') == 'timeout':
                mod_id = entry.get('moderator_id')
                moderator = self.client.get_user(mod_id) or mod_id
                if (duration := entry.get('duration')) is not None:
                    duration = humanize_timedelta(seconds=duration)
                else:
                    duration = "4 weeks"
                value = f"Mod: {moderator}\nDuration: **{duration}**\nReason: {entry.get('reason')}"
                embed.add_field(name=f"#{entry.get('case_id')}: {entry.get('action').capitalize()} (<t:{entry.get('start_time')}:d>)", value=value, inline=False)
            elif entry.get('action') == 'ban':
                mod_id = entry.get('moderator_id')
                moderator = self.client.get_user(mod_id) or mod_id
                value = f"Mod: {moderator}\nReason: {entry.get('reason')}"
                embed.add_field(name=f"#{entry.get('case_id')}: {entry.get('action').capitalize()} (<t:{entry.get('start_time')}:d>)", value=value, inline=False)
        return embed

class Mod(ModSlash, Role, Sticky, censor, BrowserScreenshot, lockdown, commands.Cog, name='mod'):
    """
    Mod commands
    """
    def __init__(self, client):
        PROXY = "161.35.235.103:8889"
        self.queue = []
        self.op = webdriver.ChromeOptions() # selenium options for chrome
        self.op.add_argument('--no-sandbox')
        self.op.add_argument('--disable-gpu')
        self.op.add_argument('--headless')
        self.op.add_argument("--window-size=1920,1080")
        self.op.add_argument('--allow-running-insecure-content')
        self.op.add_argument('--ignore-certificate-errors')
        self.op.add_argument('--disable-dev-shm-usage')
        #self.op.add_argument(' --user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"')
        self.op.add_argument('--proxy-server=%s' % PROXY)
        self.client: dvvt = client
        prefs = {"download_restrictions": 3}
        self.op.add_experimental_option("prefs", prefs)

    class RoleFlags(commands.FlagConverter, case_insensitive=True, delimiter=' ', prefix='--'):
        roles: Optional[str]

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        CatId = 608506105835814933 if channel.guild.id == 595457764935991326 else 925352977890410557
        if channel.category.id == CatId:
            try:
                ticketmessage = await self.client.wait_for('message', check=lambda m: m.channel.id == channel.id and len(m.mentions) > 0, timeout=60)
            except asyncio.TimeoutError:
                if isinstance(self.client.get_channel(channel.id), discord.TextChannel):
                    return
            else:
                member_who_opened = ticketmessage.mentions[0]
                try:
                    usrmsg = await self.client.wait_for('message', check=lambda m: m.channel.id == channel.id and m.author.id == member_who_opened.id, timeout=180)
                except:
                    if isinstance(self.client.get_channel(channel.id), discord.TextChannel):
                        await channel.send(f"Hey {member_who_opened.name}, ask your question here and a Moderator will be here to assist you as soon as possible! {member_who_opened.mention}")
                else:
                    cont = usrmsg.content
                    if cont.lower().startswith("hi") or cont.lower().startswith("hello") or cont.lower().startswith("hey"):
                        splitted = cont.split(" ")
                        if len(splitted) <= 3:
                            return await channel.send(f"Hey {member_who_opened.mention}, please describe your issue or question here, and not just simply say Hi/Hello. This allows our Mods to deal with your issue quickly.\nhttps://nohello.net/en/")










    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="self", aliases=["selfroles"], usage="--roles (role names separated by commas) (optional)")
    async def selfroles(self, ctx, channel:Optional[discord.TextChannel] = None, *, flags:RoleFlags):
        """
        Sends a message showing the 5 self roles which can be obtained via buttons.
        To highlight a role in green, use `--roles the **full names** of the roles` separated in commas. They are not case sensitive.
        """
        roleids = [895815546292035625, 895815588289581096, 895815773208051763, 895815799812521994, 895815832465190933, 923885874662502451] if os.getenv('state') == '1' else [859493857061503008, 758174135276142593, 758174643814793276, 680131933778346011, 713477937130766396, 846254068434206740]#[895815546292035625, 895815588289581096, 895815773208051763, 895815799812521994, 895815832465190933]
        role1 = ctx.guild.get_role(roleids[0])
        role2 = ctx.guild.get_role(roleids[1])
        role3 = ctx.guild.get_role(roleids[2])
        role4 = ctx.guild.get_role(roleids[3])
        role5 = ctx.guild.get_role(roleids[4])
        role6 = ctx.guild.get_role(roleids[5])
        if role1 == None or role2 == None or role3 == None or role4 == None or role5 == None or role6 == None:
            return await ctx.send("1 or more roles in this command is/are declared as invalid, hence the command cannot proceed.")
        roles = [role1, role2, role3, role4, role5, role6]
        hlroles = None
        if channel is None:
            channel = ctx.channel
            if flags is not None and flags.roles is not None and len(flags.roles) is not None:
                hlroles = flags.roles.split(',')
                for index, role_name in enumerate(hlroles):
                    hlroles[index] = role_name.lower().strip()
        class selfroles(discord.ui.View):
            def __init__(self, ctx: DVVTcontext, client, timeout):
                self.context = ctx
                self.response = None
                self.result = None
                self.client = client
                super().__init__(timeout=timeout)
                emojis = ["<a:dv_wStarOwO:837787067303198750>", "<a:dv_wHeartsOwO:837787079320666138>", "<a:dv_wSparklesOwO:837782054782632006>", "<a:dv_wpinkHeartOwO:837781949337960467>", "<:dv_wFlowerOwO:837700860511256627>", "<:dv_wRainbowOwO:837700739836674078>"]
                rolenames = []
                for role in roles:
                    rolenames.append(role.name)

                class somebutton(discord.ui.Button):
                    async def callback(self, interaction: discord.Interaction):
                        target_role = roles[emojis.index(str(self.emoji))]
                        if target_role in interaction.user.roles:
                            await interaction.response.send_message(f"You already have the role **{target_role.name}**!", ephemeral=True)
                        else:
                            await interaction.user.add_roles(target_role, reason="Selfrole")
                            await interaction.response.send_message(f"The role **{target_role.name}** has been added to you.", ephemeral=True)
                        #await update_roles(self.emoji)
                for emoji in emojis:
                    style = discord.ButtonStyle.grey
                    if hlroles is not None:
                        if rolenames[emojis.index(emoji)].lower() in hlroles:

                            style = discord.ButtonStyle.green
                    self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=rolenames[emojis.index(emoji)], style=style))

            async def on_timeout(self) -> None:
                for b in self.children:
                    b.disabled = True
                await self.response.edit(content="This message is now inactive.", view=self)
        view = selfroles(ctx, self.client, 172800.0)
        message = await channel.send("Press the button to claim your role.", view=view)
        view.response = message

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='selfharm')
    async def selfharm(self, ctx, member: discord.Member = None):
        embed = discord.Embed(title="Suicide and Self-Harm Hotlines \u2764", color=11461317)
        embed.description = "We understand you need someone to talk to and that's alright. You aren't alone. " \
                            "Ever.\nHowever, we aren't an emotional support server. We aren't paid professionals that " \
                            "are trained to handle these types of situations.\n\nThat being said, if you need to open " \
                            "up about serious issues going on in your lives, please don't do that here.\n\nWe know " \
                            "this can be hard to hear, but not only do you impact yourself more, but now, " \
                            "you've brought others into the situation.\n\nPlease seek professional help immediately " \
                            "if you feel you're at risk of inflicting harm upon yourself. Below is a list of " \
                            "resources designed to assist you:\n\nNational Suicide Prevention (United States)\n> " \
                            "Phone Number (24/7): 1-800-273-8255\n\nInternational Suicide Hotlines\n> Look up your " \
                            "country's hotline and call it if you aren't in the US.\n> This list may be out-dated: [" \
                            "International Suicicide Hotline](https://suicidepreventionlifeline.org/)\n\nIf you need " \
                            "a resource within Discord, [click here](" \
                            "https://disboard.org/servers/tag/mental-health?sort=-member_count) for a list of mental " \
                            "health support Discord servers. "
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
        embed.set_thumbnail(url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRqRdSgVuLPG3oLBRlGJay6kKtRjitOxl_ZQTR9T0H8l195daMz&s%22%7D")
        if member is None:
            await ctx.send(embed=embed)
        else:
            try:
                await member.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Could not send Suicide and Self-Harm advice: {e}")
            else:
                with contextlib.suppress(discord.HTTPException):
                    await ctx.message.add_reaction("📩")


    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="getraw", aliases = ['raw', 'rawmessage'])
    async def getrawmessage(self, ctx, message_id=None, channel:discord.TextChannel=None):
        """
        Gets the raw content of a message.
        """
        if not message_id:
            return await ctx.send("`dv.getraw <message_id> <channel>`\nMessage ID is a required argument.")
        if not channel:
            channel = ctx.channel
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send(f"I did not find a message with the ID {message_id} in {channel}. {'DId you forget to include `channel`?' if channel == ctx.channel else ''}")
        else:
            m_content = message.content
            if len(m_content) > 0:
                content_embed_raw = discord.Embed(title="Raw Message Content",
                                                  description=f"```\n{message.content}\n```",
                                                  color=self.client.embed_color)
                if len(message.embeds) > 0:
                    embeds = []
                    for embed in message.embeds:
                        embed_json = json.dumps(embed.to_dict())
                        content_embed = discord.Embed(title="Raw Embed (JSON)", description=f"```\n{embed_json}\n```",
                                                      color=self.client.embed_color)
                        embeds.append(content_embed)
                    await ctx.send(embed=content_embed_raw, view=ViewEmbedJSONs(embeds))
                else:
                    await ctx.send(embed=content_embed_raw)
            elif len(message.embeds) > 0:
                embeds = []
                for embed in message.embeds:
                    embed_json = json.dumps(embed.to_dict())
                    content_embed_raw = discord.Embed(title="Raw Embed (JSON)", description=f"```\n{embed_json}\n```",
                                                      color=self.client.embed_color)
                    embeds.append(content_embed_raw)
                await ctx.send(embeds=embeds)

    @commands.command(name="memberpvc", brief = "Checks the private channels that a member has access to", description = "Checks the private channels that a member has access to", aliases = ["pvcmember"])
    @commands.has_guild_permissions(manage_roles=True)
    async def memberpvc(self, ctx, member:discord.Member = None):
        """
        Checks the private channels that a member has access to
        """
        if member is None:
            await ctx.send("Wanted to check another member, and not yourself? You need to include a member.\nUsage of command: `memberpvc [channel]`")
            member = ctx.author
        # categoryids = [869943348608270446] this is for my server
        categoryids = [802467427208265728, 763457841133912074, 789195494664306688, 783299769580781588, 805052824185733120, 834696686923284510, 847897065081274409] # this is for dv (all the category IDs for the VIP channels)
        categories = []
        for categoryid in categoryids:
            category = discord.utils.find(lambda m: m.id == categoryid, ctx.guild.categories)
            if category is None:
                await ctx.send(f"I could not find a category for the ID {category}")
            else:
                categories.append(category) # gets all the categories for channels
        accessiblechannels = []
        for category in categories:
            for channel in category.channels:
                if channel.id in [820011058629836821, 763458133116059680]:
                    pass
                else:
                    permissions = channel.permissions_for(member)
                    if permissions.view_channel == True:
                        accessiblechannels.append(channel.mention) # gets all the channels that the user can see in private channels
        streeng = "" #ignore the spelling
        for channel in accessiblechannels:
            if len(streeng) < 3900:
                streeng += f"{channel}\n"
            else:
                embed = discord.Embed(title = f"Channels that {member.name}#{member.discriminator} can access", description=streeng, color = self.client.embed_color)
                await ctx.send(embed=embed)
                streeng = f"{channel}\n"
        embed = discord.Embed(title=f"Channels that {member.name}#{member.discriminator} can access",
                            description=streeng, color=self.client.embed_color)
        await ctx.send(embed=embed)

    async def _complex_cleanup_strategy(self, ctx, search):
        prefixes = tuple(await self.client.get_prefix(ctx.message))

        def check(m):
            return m.author == ctx.me or m.content.startswith(prefixes)

        deleted = await ctx.channel.purge(limit=search, check=check, before=ctx.message)
        return Counter(m.author.display_name for m in deleted)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='cleanup', aliases=['cu'])
    async def cleanup(self, ctx, search=100):
        """
        Cleans up the bot's messages and bot's commands.
        Maximum allowed is 100 messages.
        """
        await ctx.message.delete()
        strategy = self._complex_cleanup_strategy
        search = min(max(2, search), 1000)
        spammers = await strategy(ctx, search)
        deleted = sum(spammers.values())
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            messages.append('')
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f'- **{author}**: {count}' for author, count in spammers)
        await ctx.send('\n'.join(messages), delete_after=3.0)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='freezenick', aliases=['fn'])
    async def freezenick(self, ctx, member:discord.Member = None, *, nickname:str = None):
        """
        Freezes a user's nickname, causing their nickname to always display the nickname that you state in the command.
        """
        if member is None:
            return await ctx.send("You need to tell me who you want to freezenick.")
        if nickname is None:
            return await ctx.send("You need to tell me what nickname you want to use.")
        if len(nickname) > 32:
            return await ctx.send("That nickname is too long, just like my-", delete_after=3.0)
        existing = await self.client.db.fetchrow("SELECT * FROM freezenick WHERE user_id = $1 and guild_id = $2", member.id, ctx.guild.id)
        if existing is not None:
            return await ctx.send("A freezenick is already implemented for this user; the user most likely lost a nickbet.")
        try:
            old_nick = member.display_name
            await member.edit(nick=nickname)
        except:
            return await ctx.send(f"I encountered an error while trying to freeze {member}'s nickname. It could be due to role hierachy or missing permissions.")
        else:
            timetounfreeze = 9223372036854775807
            await self.client.db.execute("INSERT INTO freezenick(user_id, guild_id, nickname, old_nickname, time, reason, responsible_moderator) VALUES($1, $2, $3, $4, $5, $6, $7)", member.id, ctx.guild.id, nickname, old_nick, timetounfreeze, f"Invoked via freezenick command", ctx.author.id)
            return await ctx.send(f"{member.mention}'s nickname is now frozen to `{nickname}`.")

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="freezenicks")
    async def active_freezenicks(self, ctx):
        """
        Lists the active blacklists.
        """
        title = "Active frozen nicknames"
        result = await self.client.db.fetch("SELECT * FROM freezenick WHERE guild_id = $1", ctx.guild.id)
        frozennicknames = []
        for entry in result:
            member = self.client.get_user(entry.get('user_id'))
            name = f"{entry.get('id')}. {member} ({member.id})" if member is not None else f"{entry.get('id')}. {entry.get('user_id')}"
            details = f"**Frozen nickname:** {entry.get('nickname')}\n"
            details += f"**Reason:** {entry.get('reason')}\n"
            details += f"**Unfrozen:** <t:{entry.get('time')}:R>\n" if entry.get('time') != 9223372036854775807 else 'Until: Eternity\n'
            responsible_moderator = entry.get('responsible_moderator')
            responsible_moderator = self.client.get_user(responsible_moderator) if responsible_moderator is not None else responsible_moderator
            details += f"**Responsible Moderator:** {responsible_moderator} ({responsible_moderator.mention})" if responsible_moderator is not None else 'Responsible Moderator: None'
            frozennicknames.append((name, details))
        if len(frozennicknames) <= 10:
            embed = discord.Embed(title=title, color=self.client.embed_color, timestamp=discord.utils.utcnow())
            for suggestion in frozennicknames:
                embed.add_field(name=suggestion[0], value=suggestion[1], inline=False)
            return await ctx.send(embed=embed)
        else:
            pages = CustomMenu(source=FrozenNicknames(frozennicknames, title, False), clear_reactions_after=True, timeout=60)
            return await pages.start(ctx)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='unfreezenick', aliases=['ufn'])
    async def unfreezenick(self, ctx: DVVTcontext, member: discord.Member = None):
        """
        Unfreezes a user's nickname.
        """
        if member is None:
            return await ctx.send("You need to tell me who you want to freezenick.")
        existing = await self.client.db.fetchrow("SELECT * FROM freezenick WHERE user_id = $1 and guild_id = $2",
                                                      member.id, ctx.guild.id)
        if existing is None:
            return await ctx.send(f"{member}'s nickname is currently not frozen.")
        moderator = ctx.guild.get_member(existing.get('responsible_moderator'))
        if moderator is not None:
            if moderator != ctx.guild.owner:
                if moderator.top_role >= ctx.author.top_role:
                    return await ctx.send(f"You cannot unfreezenick **{member}**'s nickname, as their nickname was frozen by **{moderator}**, whose highest role is the same as or above your own role.")
        try:
            await member.edit(nick=existing.get('old_nickname'))
        except:
            return await ctx.send(f"I encountered an error while trying to unfreeze {member}'s nickname. It could be due to role hierachy or missing permissions.")
        else:
            await self.client.db.execute("DELETE FROM freezenick WHERE id = $1", existing.get('id'))
            return await ctx.send(f"{member.mention}'s nickname is now unfrozen.")

    class BetterRoles(commands.Converter):
        async def convert(self, ctx, argument):
            try:
                return await commands.RoleConverter().convert(ctx, argument)
            except commands.BadArgument:
                role_to_return = discord.utils.find(lambda x: x.name.lower() == argument.lower(), ctx.guild.roles)
                if role_to_return is not None:
                    return role_to_return
                roles_and_aliases = {}
                for r in ctx.guild.roles:
                    roles_and_aliases[r.name] = r.id
                    # This might be a bad idea, don't care
                name, ratio = process.extractOne(argument, [x for x in roles_and_aliases])
                if ratio >= 75:
                    role_to_return = discord.utils.get(ctx.guild.roles, id=roles_and_aliases[name])
                    return role_to_return

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='timeout', aliases=['to'])
    async def timeout(self, ctx, member: discord.Member = None, duration: BetterTimeConverter = None, *, reason: str = None):
        """
        Timeouts a member for a specified amount of time.
        """
        if member is None:
            return await ctx.send("You need to tell me who you want to timeout.")
        if member.top_role >= ctx.me.top_role:
            return await ctx.send(f"I cannot put **{member}** on a time-out as their highest role is higher than or the same as **my** highest role.")
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("You **cannot** timeout a user that has a higher role than you.")
        if duration is None:
            return await ctx.send("You need to tell me how long you want to timeout the user for.")
        duration: int = duration
        if duration <= 0:
            return await ctx.send("You can't timeout someone for less than 1 second.")
        if duration > 2419200:
            return await ctx.send("You can't timeout someone for more than 4 weeks (28 days).")
        now = round(time.time())
        ending = now + duration
        td_obj = timedelta(seconds=duration)
        try:
            if reason is None:
                auditreason = f"Requested by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id}"
            else:
                auditreason = reason + f" | Requested by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id}"
            await member.timeout_for(duration=td_obj, reason=auditreason)
        except discord.Forbidden:
            return await ctx.send(f"I do not have permission to put {member} on a timeout.")
        else:
            case_id = await self.client.db.fetchval("INSERT INTO modlog (guild_id, moderator_id, offender_id, action, reason, start_time, duration, end_time) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING case_id", ctx.guild.id, ctx.author.id, member.id, "timeout", reason, now, duration, ending, column='case_id')
            msg = f"**{ctx.author}** has put **{member}** on a timeout for {humanize_timedelta(seconds=duration)}, until <t:{ending}>."
            if reason is not None:
                msg += f"\nReason: {reason}"
            await ctx.send(msg)
            if (await self.client.fetch_guild_settings(ctx.guild.id)).timeoutlog is True:
                offender = member
                moderator = ctx.author
                reason = reason or "NA"
                duration = humanize_timedelta(seconds=duration)
                embed = discord.Embed(
                    title=f"Timeout (#{case_id})",
                    description=f'**Offender**: {offender} {offender.mention}\n**Reason**: {reason}\n**Duration**: {duration}\n**Responsible Moderator**: {moderator}',
                    color=discord.Color.orange(), timestamp=discord.utils.utcnow())
                try:
                    await self.client.get_channel(modlog_channelID).send(embed=embed)
                except Exception as e:
                    print(e)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='ban', aliases=['b'])
    async def ban(self, ctx: DVVTcontext, member: Union[discord.Member, discord.User] = None, *, reason: str = None):
        if member == ctx.me:
            return await ctx.send("bye im not banning myself")
        if member == ctx.author:
            return await ctx.send("Why on earth would you want to ban yourself?")
        if member is None:
            return await ctx.send("You need to tell me who you want to ban.")
        if isinstance(member, discord.Member):
            if member.top_role >= ctx.author.top_role:
                return await ctx.send("You **cannot** ban a user that has a higher role than you.")
            if member.top_role >= ctx.me.top_role:
                return await ctx.send(f"I cannot ban **{member}** as their highest role is higher than or the same as **my** highest role.")
        if reason is None:
            auditreason = f"Requested by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id}"
        else:
            auditreason = reason + f" | Requested by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id}"
        if isinstance(member, discord.Member):
            embed = discord.Embed(title="You were banned by a Karuta Senpai!", description=f"Reason: **{reason}**\n\n> If you would like to appeal against your ban, submit an appeal [here](https://kable.lol/DankVibesAppeals/). Specify that you were banned by a Karuta Senpai in the `Other` question.", timestamp=discord.utils.utcnow(), color=discord.Color.red()).set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url, url="https://discord.gg/dankmemer")
            try:
                await member.send(embed=embed)
            except Exception as e:
                await ctx.send(f"I couldn't inform {member.mention} on why they were banned.")
        try:
            await ctx.guild.ban(member, reason=auditreason, delete_message_days=0)
        except Exception as e:
            await ctx.send(f"An error occured while trying to ban the user.\n{e}")
        else:
            now = round(time.time())
            await self.client.db.execute("INSERT INTO modlog (guild_id, moderator_id, offender_id, action, reason, start_time) VALUES ($1, $2, $3, $4, $5, $6)", ctx.guild.id, ctx.author.id, member.id, "ban", reason, now)
            msg = f"**{ctx.author}** has banned **{member}**."
            if reason is not None:
                msg += f"\nReason: {reason}"
            await ctx.send(msg)


    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='untimeout', aliases=['ut', 'uto'])
    async def untimeout(self, ctx, member: discord.Member = None, reason: str = None):
        """
        Removes a member's timeout.
        """
        if member is None:
            return await ctx.send("You need to tell me who you want to untimeout.")
        if member.communication_disabled_until is None or member.communication_disabled_until < discord.utils.utcnow():
            return await ctx.send(f"{member} is not currently on a timeout.")
        try:
            if reason is None:
                auditreason = f"Requested by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id}"
            else:
                auditreason = reason + f" | Requested by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id}"
            await member.timeout(until=None, reason=auditreason)
        except discord.Forbidden:
            return await ctx.send(f"I do not have permission to remove {member}'s timeout.")
        else:
            await ctx.send(f"{member.name}'s timeout successfully removed.")

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='modlog', aliases=['ml'])
    async def modlog(self, ctx, user: discord.User = None):
        """
        Shows a user's mod log.
        """
        if user is None:
            return await ctx.send("Whose modlog are you checking??")
        modlog = await self.client.db.fetch("SELECT * FROM modlog WHERE offender_id = $1 ORDER BY case_id DESC", user.id)
        if len(modlog) < 1:
            embed = discord.Embed(title="Mod Log", description="Nothing to see here, move along 👋").set_author(icon_url=user.display_avatar.url, name=f"{user} ({user.id}")
            return await ctx.send(embed=embed)
        else:
            pag = pages.Paginator(pages=ModlogPagination(modlog, user, 10, self.client).get_pages(), disable_on_timeout=True, use_default_buttons=True)
            await pag.send(ctx)




    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='slowmode', aliases=['sm'])
    async def slowmode(self, ctx, channel: Optional[discord.TextChannel] = None, duration: BetterTimeConverter = None):
        if duration is None:
            duration = 0
        if channel is None:
            channel = ctx.channel
        if duration > 21600:
            return await ctx.send("A channel's slowmode cannot be longer than 6 hours.")
        try:
            await channel.edit(slowmode_delay=duration)
        except discord.Forbidden:
            return await ctx.send(f"I don't have permission to change {channel.mention}'s slowmode.")
        if duration > 0:
            await ctx.send(f"{channel.mention}'s slowmode has been set to **{humanize_timedelta(seconds=duration)}.**")
        else:
            await ctx.send(f"{channel.mention}'s slowmode has been removed.")

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name='dhvt')
    async def dhvt(self, ctx):
        await ctx.send("The requirement to join today's heist is to **vote for Dank Vibes**. Click on the button below to see if you have fulfilled the requirement!", view=PublicVoteView())
        await ctx.message.delete()


    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="roleinfo", aliases=['ri'])
    async def roleinfo(self, ctx, *, role: BetterRoles = None):
        """
        Provides information about a role, including its position, number of members, color, and its role icon.
        """
        if role is None:
            return await ctx.send("What role do you want to know about?")
        role: discord.Role = role
        rolename = role.name
        members = len(role.members)
        color = format(role.color.value, 'x')
        color = str(color)
        while len(color) < 6:
            color = f"0{color}"
        color = f"#{color}"
        hoisted = role.hoist
        mentionable = role.mentionable
        created = role.created_at
        created = created.strftime("%d/%m/%Y %H:%M:%S")
        desc = [f"Color: **{color}**", f"Hoisted: **{hoisted}**", f"Members with this role: **{members}**",
                f"Mentionable: **{'<:DVB_True:887589686808309791>' if mentionable else '<:DVB_False:887589731515392000>'}**",
                f"Created on: **{created}**", '']
        icon = role.icon.url if role.icon else None
        if role.is_default():
            desc.append("⚠️This is a guild-default role.")
        elif role.is_bot_managed():
            bot_id = role.tags.bot_id
            desc.append(f"⚠️This role is an integration role for the bot {ctx.guild.get_member(bot_id)}.")
        elif role.is_premium_subscriber():
            desc.append("<a:DVB_Boost:906198274770346015> This role is the server's Booster role.")
        elif role.managed or role.is_integration():
            integration_id = role.tags.integration_id
            integrations = await ctx.guild.integrations()
            discIntegration = discord.utils.get(integrations, id=integration_id)
            if discIntegration is None:
                desc.append('⚠️This role is managed by an unknown integration.')
            else:
                desc.append(f"⚠️This role is managed by the integration {discIntegration.name} ({discIntegration.id}.")
        if desc[-1] != '':
            desc.append('')
        position = ctx.guild.roles.index(role)
        strposition = f"{ordinal(len(ctx.guild.roles) - position)} of {len(ctx.guild.roles)} roles"
        if role == ctx.guild.roles[0]:
            str_position=f"{ctx.guild.roles[2].name}\n{ctx.guild.roles[1].name}\nLowest role: **{role.name}**"
        elif role == ctx.guild.roles[-1]:
            str_position=f"Highest role: **{role.name}**\n{ctx.guild.roles[-2].name}\n{ctx.guild.roles[-3].name}"
        else:
            str_position=f"{ctx.guild.roles[position+1].name}\n**{role.name}**\n{ctx.guild.roles[position-1].name}"
        embed = discord.Embed(title=f"Role Info for {rolename}", description='\n'.join(desc), color=role.color)
        embed.add_field(name=f"Positon ({strposition})", value=str_position, inline=False)
        embed.set_footer(text=f"Role ID: {role.id}")
        if icon:
            embed.set_thumbnail(url=icon)
        await ctx.send(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="names")
    async def names(self, ctx, *, member: discord.User = None):
        """
        Shows a user's past tracked usernames. Username changes are only recorded from 9 January 22 onwards.
        """
        if member is None:
            return await ctx.send("You need to specify a user.")
        names = await self.client.db.fetch("SELECT * FROM name_changes WHERE user_id = $1", member.id)
        if len(names) == 0:
            return await ctx.send(f"There has been no name changes recorded for {member}.\nName changes are only recorded starting from 9 Jan 2022.")
        buffer = []
        for nameentry in names:
            name = nameentry.get('name')
            time = f"<:Reply:871808167011549244> <t:{nameentry.get('time')}>"
            buffer.append((name, time))
        pages = CustomMenu(source=FrozenNicknames(buffer, f"{member.name}'s past names", True), clear_reactions_after=True, timeout=60)
        return await pages.start(ctx)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="nicknames")
    async def nicknames(self, ctx, *, member: discord.Member = None):
        """
        Shows a user's past (tracked) nicknames. Nickname changes are only recorded from 9 January 22 onwards.
        """
        if member is None:
            return await ctx.send("You need to specify a user.")
        nicknames = await self.client.db.fetch("SELECT * FROM nickname_changes WHERE member_id = $1", member.id)
        if len(nicknames) == 0:
            return await ctx.send(f"There has been no nickname changes recorded for {member}.\nNickname changes are only recorded starting from 9 Jan 2022.")
        buffer = []
        for nicknameentry in nicknames:
            nickname = nicknameentry.get('nickname')
            time = f"<:Reply:871808167011549244> <t:{nicknameentry.get('time')}>"
            buffer.append((nickname, time))
        pages = CustomMenu(source=FrozenNicknames(buffer, f"{member.name}'s past nicknames", True), clear_reactions_after=True, timeout=60)
        return await pages.start(ctx)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="list")
    async def list(self, ctx, list_type: str = None, *, things_to_list: str = None):
        """
        List roles, users or channels using this command! This command won't ping any users or roles.
        list_type can be `member/user`, `role`, or `channel`.
        things_to_list should be user, role or channel IDs separated by spaces.
        """
        if list_type is None:
            list_type = 'member'
        if list_type not in ['role', 'roles', 'member', 'members', 'user', 'users', 'channel', 'channels', 'm', 'u', 'r', 'chan', 'c']:
            return await ctx.send("You need to specify a list type to list. list_type can be `member/user`, `role`, or `channel`.")
        if things_to_list is None:
            return await ctx.send("You need to specify what to list.")
        things_to_list = things_to_list.replace(' ', 'sep').replace('\n', 'sep').strip()
        things_to_list = things_to_list.split('sep')
        sending = []
        for obj_id in things_to_list:
            if len(obj_id) > 0:
                if list_type.lower() in ['member', 'user', 'members', 'users', 'm', 'u']:
                    sending.append(f"<@!{obj_id}>")
                elif list_type.lower() in ['role', 'roles', 'r']:
                    sending.append(f"<@&{obj_id}>")
                elif list_type.lower() in ['channel', 'channels', 'c', 'chan']:
                    sending.append(f"<#{obj_id}>")
                else:
                    return await ctx.send("`list_type` can be `member/user`, `role`, or `channel`.")
        hm = ''
        for obj in sending:
            if len(hm) < 1900:
                hm += f"{obj}\n"
            else:
                await ctx.send(hm)
                hm = f"{obj}\n"
        await ctx.send(hm, allowed_mentions=discord.AllowedMentions(users=False, roles=False, replied_user = False, everyone=False))

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name='watchlist', invoke_without_command=True)
    async def watchlist(self, ctx):
        """
        Watchlists are a new feature on Dank Vibes Bot. It will notify you if someone on your watchlist joins the server.
        This command will show all users who are on your watchlist, and toggle how/if you want to be notified when a user joins.
        """
        watchlist = await self.client.db.fetch("SELECT * FROM watchlist WHERE guild_id = $1 and user_id = $2", ctx.guild.id, ctx.author.id)
        user_notify_method = await self.client.db.fetchval("SELECT watchlist_notify FROM userconfig WHERE user_id = $1", ctx.author.id)
        if len(watchlist) == 0:
            return await ctx.send("You don't have any users on your watchlist.")
        buffer = []
        for watchlist_entry in watchlist:
            target_id = watchlist_entry.get('target_id')
            target = self.client.get_user(watchlist_entry.get('target_id'))
            if target is None:
                target_disp = str(target_id)
            else:
                target_disp = f"{target} ({target_id})"
                if watchlist_entry.get('remarks'):
                    target_disp += f": {watchlist_entry.get('remarks')}"
            buffer.append(target_disp)
        embed = discord.Embed(title=f"{ctx.author.name}'s watchlist", description = "", color = self.client.embed_color)
        for user in buffer:
            if len(embed.description) < 3900:
                embed.description += f"{user}\n"
            else:
                va = len(buffer) - len(embed.description.split("\n"))
                embed.description += f"{user}\n**and {va} more users...**"
                break
        embed.set_footer(text=f"There are {len(buffer)} users on your watchlist.")
        ChangeNotifyView = ChangeWatchlistNotify(self.client, user_notify_method if user_notify_method is not None else 0, ctx.author)
        ChangeNotifyView.response = await ctx.send(embed=embed, view=ChangeNotifyView)



    @checks.has_permissions_or_role(manage_roles=True)
    @watchlist.command(name='add', aliases=['+'])
    async def watchlist_add(self, ctx, target: MemberUserConverter = None, *, remarks: str = None):
        """
        Add a user to your watchlist.
        """
        if target is None:
            return await ctx.send("You need to specify a user to add to your watchlist.")
        target: Union[discord.Member, discord.User] = target
        if remarks is not None:
            if len(remarks) > 1000:
                return await ctx.send("Remarks cannot be longer than 1000 characters.")
        if await self.client.db.fetchrow("SELECT * FROM watchlist WHERE guild_id = $1 and user_id = $2 and target_id = $3", ctx.guild.id, ctx.author.id, target.id) is not None:
            return await ctx.send(f"**{target}** is already on your watchlist.")
        await self.client.db.execute("INSERT INTO watchlist (guild_id, user_id, target_id, remarks) VALUES ($1, $2, $3, $4)", ctx.guild.id, ctx.author.id, target.id, remarks)
        await ctx.send(f"<:DVB_True:887589686808309791> Added **{target}** to your watchlist.")

    @checks.has_permissions_or_role(manage_roles=True)
    @watchlist.command(name='remove', aliases=['-'])
    async def watchlist_remove(self, ctx, target: MemberUserConverter = None):
        """
        Removes a user from your watchlist.
        """
        if target is None:
            return await ctx.send("You need to specify a user to remove from your watchlist.")
        target: Union[discord.Member, discord.User] = target
        if await self.client.db.fetchrow("SELECT * FROM watchlist WHERE guild_id = $1 and user_id = $2 and target_id = $3", ctx.guild.id, ctx.author.id, target.id) is None:
            return await ctx.send(f"**{target}** is not on your watchlist.")
        await self.client.db.execute("DELETE FROM watchlist WHERE guild_id = $1 and user_id = $2 and target_id = $3", ctx.guild.id, ctx.author.id, target.id)
        await ctx.send(f"<:DVB_True:887589686808309791> Removed **{target}** from your watchlist.")

    @checks.has_permissions_or_role(manage_roles=True)
    @watchlist.command(name='clear', aliases=['c'])
    async def watchlist_clear(self, ctx:DVVTcontext ):
        """
        Removes all users from your watchlist.
        """
        if len(existing_watchlist := await self.client.db.fetch("SELECT * FROM watchlist WHERE guild_id = $1 and user_id = $2", ctx.guild.id, ctx.author.id)) < 1:
            return await ctx.send("You don't have any users on your watchlist.")
        confirmview = confirm(ctx, self.client, 30.0)
        embed = discord.Embed(title="Dangerous action!", description=f"Are you sure you want to clear and remove {len(existing_watchlist)} users from your watchlist?\n\nThis action cannot be undone.", color=discord.Color.orange())
        confirmview.response = await ctx.reply(embed=embed, view=confirmview)
        await confirmview.wait()
        if confirmview.returning_value is None:
            embed.description = "Timed out, your watchlist wasn't cleared."
            embed.color = discord.Color.red()
        elif confirmview.returning_value is not True:
            embed.description = "Your watchlist wasn't cleared."
            embed.color = discord.Color.red()
        elif confirmview.returning_value is True:
            await self.client.db.execute("DELETE FROM watchlist WHERE guild_id = $1 and user_id = $2", ctx.guild.id, ctx.author.id)
            embed.description = "Your watchlist was cleared."
            embed.color = discord.Color.green()
        await confirmview.response.edit(embed=embed)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name="messagecleanup", aliases=['mc'], invoke_without_command=True)
    async def messagecleanup(self, ctx: DVVTcontext):
        """
        Message Cleanup is a feature that allows messages from bots to be deleted in certain channels. This is a way to prevent people from using bots in the wrong channel.
        This command shows the current settings for this feature.
        """
        result = await self.client.db.fetch("SELECT * FROM usercleanup WHERE guild_id = $1", ctx.guild.id)
        if len(result) == 0:
            return await ctx.send("There are no channels set for messages to be deleted from.")
        txt = []
        categorised_bots = {}
        for row in result:
            if (target := ctx.guild.get_member(row.get('target_id'))) is not None:
                if (chan := ctx.guild.get_channel(row.get('channel_id'))) is not None:
                    if target in categorised_bots:
                        categorised_bots[target].append(chan)
                    else:
                        categorised_bots[target] = [chan]
        for bot, channels in categorised_bots.items():
            if len(channels) > 0:
                txt.append(f"{bot.mention} **{bot}**: {', '.join([channel.mention for channel in channels])}")
        embed = discord.Embed(title="Message Cleanup", color=self.client.embed_color)
        page = []
        while len(txt) > 0:
            to_send = txt.pop(0)
            embed.add_field(name='\u200b', value=to_send, inline=False)
            if len(embed) > 6000:
                embed.remove_field(-1)
                page.append(embed)
                embed = discord.Embed(title="Message Cleanup", color=self.client.embed_color)
                embed.add_field(name='\u200b', value=to_send, inline=False)
        if embed not in page:
            page.append(embed)
        paginator = pages.Paginator(pages=page, author_check=True)
        await paginator.send(ctx)

    @checks.has_permissions_or_role(manage_roles=True)
    @messagecleanup.command(name='add', aliases=['a'])
    async def messagecleanup_add(self, ctx: DVVTcontext, target: commands.Greedy[discord.Member], channel: commands.Greedy[discord.TextChannel]):
        """
        Adds users to the channels to prevent their messages from showing in that channel.
        You can add as many targets and channels as you would want.
        If you used `dv.mc add @OwO @Dank Memer @Karuta #chan-1 #chan-2 #chan-3, the restrictions for those 3 bots will be applied to all channels.
        """
        if len(target) == 0:
            return await ctx.send("You need to specify at least one user/target.")
        if len(channel) == 0:
            return await ctx.send("You need to specify at least one channel.")
        targets = list(dict.fromkeys(target))
        channels = list(dict.fromkeys(channel))
        to_insert = []
        existing = tuple(await self.client.db.fetch("SELECT target_id, channel_id FROM usercleanup WHERE guild_id = $1", ctx.guild.id))
        for target, channel in itertools.product(targets, channels):
            if (target.id, channel.id) not in existing:
                to_insert.append((ctx.guild.id, target.id, channel.id))
        await self.client.db.executemany("INSERT INTO usercleanup (guild_id, target_id, channel_id) VALUES ($1, $2, $3)", to_insert)

        target_str = human_join([target.mention for target in targets], final='and')
        channel_str = human_join([channel.mention for channel in channels], final='and')
        await ctx.send(f"{target_str} will be prevented from sending messages in {channel_str}. You'll need to set the cleanup message again for any newly added channels with `dv.messagecleanup message [target] [message]`.")

    @checks.has_permissions_or_role(manage_roles=True)
    @messagecleanup.command(name='remove', aliases=['r'])
    async def messagecleanup_remove(self, ctx: DVVTcontext, target: discord.Member, channel: commands.Greedy[discord.TextChannel]):
        """
        Remove users from the channels, alllowing their messages to show up again.
        You can input as many channels as you want, **but only one user**.
        """
        if target is None:
            return await ctx.send("You need to specify a target.")
        if len(channel) == 0:
            return await ctx.send(f"You need to specify at least one channel to **remove** for **{target}**.")
        existing = await self.client.db.fetch("SELECT channel_id FROM usercleanup WHERE guild_id = $1 AND target_id = $2", ctx.guild.id, target.id)
        if len(existing) == 0:
            return await ctx.send(f"{target} is not in the list of users to be prevented from sending messages in any channel.")
        existing = [row.get('channel_id') for row in existing]
        to_push = []
        failed = []
        for _channel in channel:
            if _channel.id not in existing:
                failed.append(f"{_channel.mention} not in list of channels for {target}")
            else:
                to_push.append((ctx.guild.id, target.id, _channel.id))
        if len(failed) > 0:
            await ctx.send("\n".join(failed))
        if len(to_push) > 0:
            await self.client.db.executemany("DELETE FROM usercleanup WHERE guild_id = $1 AND target_id = $2 AND channel_id = $3", to_push)
            await ctx.send(f"{target} will no longer be prevented from sending messages in {human_join([channel.mention for channel in channel], final='and')}.")

    @checks.has_permissions_or_role(manage_roles=True)
    @messagecleanup.command(name="message", aliases=['m'])
    async def messagecleanup_message(self, ctx: DVVTcontext, target: discord.Member = None, *, message: str = None):
        """
        Sets a message to be shown when a message is deleted with the messagecleanup feature.
        """
        if target is None:
            return await ctx.send("You need to specify a target to edit or display its messages.")
        current_msg = await self.client.db.fetchval("SELECT message FROM usercleanup WHERE guild_id = $1 AND target_id = $2 AND message is not null", ctx.guild.id, target.id)
        if message is None:
            if current_msg == "":
                current_msg = None
            return await ctx.send(f"{target}'s message is currently set to: {current_msg}")
        else:
            if message.lower() == 'none':
                await self.client.db.execute("UPDATE usercleanup SET message = $1 WHERE guild_id = $2 AND target_id = $3", None, ctx.guild.id, target.id)
                return await ctx.send(f"{target}'s message has been removed.")
            if len(message) > 1500:
                return await ctx.send(f"Your message is {len(message)} characters long, which is too long. Please keep it under 1500 characters.")
            await self.client.db.execute("UPDATE usercleanup SET message = $1 WHERE guild_id = $2 AND target_id = $3", message, ctx.guild.id, target.id)
            await ctx.send(f"{target}'s message has been set to: {message}")






