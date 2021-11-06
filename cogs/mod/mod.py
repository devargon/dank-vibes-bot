import time
import discord
import datetime
import asyncio
from discord.ext import commands
from utils import checks
from utils.format import text_to_file, stringtime_duration
from .lockdown import lockdown
from .censor import censor
from utils.buttons import *
from .browser_screenshot import BrowserScreenshot
from selenium import webdriver
from collections import Counter
import os
from utils.time import humanize_timedelta
import time
from utils.converters import BetterRoles
from fuzzywuzzy import process

class Mod(censor, BrowserScreenshot, lockdown, commands.Cog, name='mod'):
    """
    Mod commands
    """
    def __init__(self, client):
        PROXY = "161.35.235.103:8889"
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
        self.client = client
        prefs = {"download_restrictions": 3}
        self.op.add_experimental_option("prefs", prefs)

    class RoleFlags(commands.FlagConverter, case_insensitive=True, delimiter=' ', prefix='--'):
        roles: Optional[str]

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="self", aliases=["selfroles"], usage="--roles (role names separated by commas) (optional)")
    async def selfroles(self, ctx, channel:Optional[discord.TextChannel] = None, *, flags:RoleFlags):
        """
        Sends a message showing the 5 self roles which can be gotten via buttons.
        To highlight a role in green, use `--roles the **full names** of the roles` separated in commas. They are not case sensitive.
        """
        roleids = [895815546292035625, 895815588289581096, 895815773208051763, 895815799812521994, 895815832465190933] if os.name == "nt" else [859493857061503008, 758174135276142593, 758174643814793276, 680131933778346011, 713477937130766396]#[895815546292035625, 895815588289581096, 895815773208051763, 895815799812521994, 895815832465190933]
        role1 = ctx.guild.get_role(roleids[0])
        role2 = ctx.guild.get_role(roleids[1])
        role3 = ctx.guild.get_role(roleids[2])
        role4 = ctx.guild.get_role(roleids[3])
        role5 = ctx.guild.get_role(roleids[4])
        if role1 == None or role2 == None or role3 == None or role4 == None or role5 == None:
            return await ctx.send("1 or more roles in this command is/are declared as invalid, hence the command cannot proceed.")
        roles = [role1, role2, role3, role4, role5]
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
                emojis = ["<a:dv_wStarOwO:837787067303198750>", "<a:dv_wHeartsOwO:837787079320666138>", "<a:dv_wSparklesOwO:837782054782632006>", "<a:dv_wpinkHeartOwO:837781949337960467>", "<:dv_wFlowerOwO:837700860511256627>"]
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


    @checks.has_permissions_or_role(administrator=True)
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
            content = message.content
            if "‍" in content or "​" in content:
                return await ctx.send("Nice try, but you won't be able to get the raw text for hiding pings.")
            if len(content) > 4096:
                await ctx.send(f"Raw content of message with ID {message_id} in {channel}", file=text_to_file(content, "file.txt", "utf8"))
            else:
                await ctx.send(embed=discord.Embed(title=f"Raw content of message with ID {message_id} in {channel}", description=f"```\n{content}\n```", color = self.client.embed_color))

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name='karutaeventinfo', aliases=['kei'])
    async def karutaeventinfo(self, ctx):
        embed = discord.Embed(title="Dank Vibes Bot's Karuta Halloween Event!", description="From **__24/10, 0.00 EST to 31/10, 0.00 EST__**, zombies will be spawned by me in these channels:\n> <#823597687940841482>\n> <#881149732628623390>\n> <#847375281399791616>\nYour **goal** is to collect as many skulls 💀 as possible by **defeating the zombie hordes**. \n\nThe top 3 players with the **most skulls collected 💀** will win certain prizes!\n\nMore information is in <#901402571862843392>.", color=self.client.embed_color)
        embed.set_author(name=f"{ctx.guild.name}'s Karuta Zombie Halloween Event", url=ctx.guild.icon.url)
        embed.add_field(name="How do I kill the zombies?", value="I'll tell you which button/emoji to click'. The button that **matches** <:DVB_True:887589686808309791> the emoji shown on the message is the correct button.\n\n**Every time** you press the button, you'll kill a zombie! The buttons wll shuffle once in a while, so be careful not to press the wrong button.", inline=False)
        embed.add_field(name="How can I die?", value="If you press the wrong button, the zombies will kill you instead.", inline=True)
        embed.add_field(name="What happens if I die?", value="If you die, you **can't** fight the zombies. You will **not receive** any skulls as you aren't alive to collect them, even had killed some zombies.", inline=True)
        embed.set_thumbnail(url="https://cdn.nogra.me/core/zombie.gif")
        embed.set_image(url="https://cdn.nogra.me/dankvibes/karuta_win.gif")
        if ctx.message.reference:
            partial = ctx.channel.get_partial_message(ctx.message.reference.message_id)
            try:
                await partial.reply(embed=embed)
            except:
                pass
            else:
                return
        await ctx.send(embed=embed)


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
                embed = discord.Embed(title = f"Channels that {member.name}#{member.discriminator} can access", description=streeng, color = 0x57f0f0)
                await ctx.send(embed=embed)
                streeng = f"{channel}\n"
        embed = discord.Embed(title=f"Channels that {member.name}#{member.discriminator} can access",
                            description=streeng, color=0x57f0f0)
        await ctx.send(embed=embed)

    async def _complex_cleanup_strategy(self, ctx, search):
        prefixes = tuple(await self.client.get_prefix(ctx.message))

        def check(m):
            return m.author == ctx.me or m.content.startswith(prefixes)

        deleted = await ctx.channel.purge(limit=search, check=check, before=ctx.message)
        return Counter(m.author.display_name for m in deleted)

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name='cleanup', aliases=['cu'])
    async def cleanup(self, ctx, search=100):
        """
        Cleans up the bot's messages and bot's commands.
        Maximum allowed is 100 messages.
        """

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

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name='freezenick', aliases=['fn'])
    async def freezenick(self, ctx, member:discord.Member = None, *, nickname:str = None):
        """
        Freezes a user's nickname, causing their nickname to always display the nickname that you state in the command.
        To specify a duration, add --duration [duration] at the end.
        """
        if member is None:
            return await ctx.send("You need to tell me who you want to freezenick.")
        if nickname is None:
            return await ctx.send("You need to tell me what nickname you want to use.")
        if len(nickname) > 32:
            return await ctx.send("That nickname is too long, just like my-", delete_after=3.0)
        existing = await self.client.pool_pg.fetchrow("SELECT * FROM freezenick WHERE user_id = $1 and guild_id = $2", member.id, ctx.guild.id)
        if existing is not None:
            return await ctx.send("A freezenick is already implemented for this user; the user most likely lost a nickbet.")
        try:
            old_nick = member.display_name
            await member.edit(nick=nickname)
        except:
            return await ctx.send(f"I encountered an error while trying to freeze {member}'s nickname. It could be due to role hierachy or missing permissions.")
        else:
            timetounfreeze = 9223372036854775807
            await self.client.pool_pg.execute("INSERT INTO freezenick(user_id, guild_id, nickname, old_nickname, time, reason) VALUES($1, $2, $3, $4, $5, $6)", member.id, ctx.guild.id, nickname, old_nick, timetounfreeze, f"Freezenick command invoked by {ctx.author}")
            return await ctx.send(f"{member.mention}'s nickname is now frozen to `{nickname}`.")

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name='unfreezenick', aliases=['ufn'])
    async def unfreezenick(self, ctx, member: discord.Member = None):
        """
        Unfreezes a user's nickname.
        """
        intduration = None
        if member is None:
            return await ctx.send("You need to tell me who you want to freezenick.")
        existing = await self.client.pool_pg.fetchrow("SELECT * FROM freezenick WHERE user_id = $1 and guild_id = $2",
                                                      member.id, ctx.guild.id)
        if existing is None:
            return await ctx.send(f"{member}'s nickname is currently not frozen.")
        try:
            await member.edit(nick=existing.get('old_nickname'))
        except:
            return await ctx.send(f"I encountered an error while trying to unfreeze {member}'s nickname. It could be due to role hierachy or missing permissions.")
        else:
            await self.client.pool_pg.execute("DELETE FROM freezenick WHERE id = $1", existing.get('id'))
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

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="roleinfo", aliases=['ri'])
    async def roleinfo(self, ctx, *, role: BetterRoles = None):
        if role is None:
            return await ctx.send("What role do you want to know about?")
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
        position = role.position
        if position == 0:
            str_position=f"{ctx.guild.roles[2].name}\n{ctx.guild.roles[1].name}\nLowest role: **{role.name}**"
        elif position+1 == len(ctx.guild.roles):
            str_position=f"Highest role: **{role.name}**\n{ctx.guild.roles[-2].name}\n{ctx.guild.roles[-3].name}"
        else:
            str_position=f"{ctx.guild.roles[position-1].name}\n**{role.name}**\n{ctx.guild.roles[position+1].name}"
        embed = discord.Embed(title=f"Role Info for {rolename}", description='\n'.join(desc), color=role.color)
        embed.add_field(name="Positon", value=str_position, inline=False)
        embed.set_footer(text=f"Role ID: {role.id}")
        await ctx.send(embed=embed)
