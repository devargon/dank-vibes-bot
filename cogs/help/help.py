import copy
import re
from utils.context import DVVTcontext
from utils.errors import ArgumentBaseError
import discord
import itertools
import contextlib
import more_itertools
from datetime import datetime
from discord.ext import commands
from utils.menus import CogMenu, GroupMenu, ListPageInteractionBase, HelpMenu, HelpMenuBase, MenuViewInteractionBase
from utils.buttons import BaseButton, ViewButtonIteration, MenuViewBase
from utils.helper import unpack, empty_page_format
from collections import namedtuple
from utils.format import get_command_name
from typing import Optional, Any, List, Union, Tuple

CommandGroup = Union[commands.Command, commands.Group]
CogHelp = namedtuple("CogAmount", 'name commands description')
GroupHelp = namedtuple("GroupHelp", 'name brief usage group_obj')
CommandHelp = namedtuple("CommandHelp", 'command brief command_obj')
SubcommandHelp = namedtuple("SubcommandHelp", 'name brief command_obj')

class HelpMenuView(MenuViewBase):
    """This class is responsible for starting the view + menus activity for the help command.
       This accepts embed, help_command, context, page_source, dataset and optionally Menu.
       """
    def __init__(self, *data: Any, embed: discord.Embed, help_object, context: DVVTcontext, **kwargs: Any):
        super().__init__(context, HelpSource, *data,
                         button=HelpButton,
                         menu=HelpMenu,
                         style=discord.ButtonStyle.primary,
                         **kwargs)
        self.original_embed = embed
        self.help_command = help_object

class HomeButton(BaseButton):
    async def callback(self, interaction: discord.Interaction):
        self.view.clear_items()
        for b in self.view.old_items:
            self.view.add_item(b)
        await interaction.message.edit(view=self.view, embed=self.view.original_embed)

class HelpButton(BaseButton):
    """This Button update the menu, and shows a list of commands for the cog.
       This saves the category buttons as old_items and adds relevant buttons that
       consist of HomeButton, and HelpSearchButton."""

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        bot = view.help_command.context.bot
        select = self.selected or "No Category"
        cog = bot.get_cog(select.lower())
        data = [(cog, commands_list) for commands_list in view.mapper.get(cog)]
        self.view.old_items = copy.copy(self.view.children)
        await view.update(self, interaction, data)

class HelpSearchButton(BaseButton):
    """This class is used inside a help command that shows a help for a specific command.
       This is also used inside help search command."""

    async def callback(self, interaction: discord.Interaction) -> None:
        help_obj = self.view.help_command
        bot = help_obj.context.bot
        command = bot.get_command(self.selected)
        embed = help_obj.get_command_help(command)
        await interaction.response.send_message(content=f"Help for **{self.selected}**", embed=embed, ephemeral=True)

class Information(HelpMenuBase):
    async def on_information_show(self, payload: discord.RawReactionActionEvent) -> None:
        ctx = self.ctx
        embed = discord.Embed(title="Information", description=self.description, color=0x5464B4)
        curr = self.current_page + 1 if (p := self.current_page > -1) else "cover page"
        pa = ("page", "the")[not p]
        embed.set_author(icon_url=ctx.bot.user.avatar, name=f"You were on {pa} {curr}")
        nav = '\n'.join(f"{e} {b.action.__doc__}" for e, b in super().buttons.items())
        embed.add_field(name="Navigation:", value=nav)
        await self.message.edit(embed=embed, allowed_mentions=discord.AllowedMentions(replied_user=False))


class HelpMenu(MenuViewInteractionBase, Information):
    """MenuPages class that is specifically for the help command."""
    def __init__(self, *args: Any, description: Optional[str] = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.description = description or """This shows each commands in this bot. Each page is a category that shows 
                                             what commands that the category have."""

class CogMenu(Information):
    def __init__(self, *args: Any, description: Optional[str] = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.description = description

class GroupMenu(Information):
    def __init__(self, *args: Any, description: Optional[str] = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.description = description

class HelpSearchView(ViewButtonIteration):
    """This view class is specifically for command_callback method"""

    def __init__(self, help_object, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.help_command = help_object
        self.ctx = help_object.context
        self.bot = help_object.context.bot

class HelpSource(ListPageInteractionBase):
    """This ListPageSource is meant to be used with view, format_page method is called first
       after that would be the format_view method which must return a View, or None to remove."""

    async def format_page(self, menu: HelpMenu, entry: Tuple[commands.Cog, List[CommandHelp]]) -> discord.Embed:
        """This is for the help command ListPageSource"""
        cog, list_commands = entry
        embed = discord.Embed(title=f"{getattr(cog, 'qualified_name', 'No').capitalize()} Category", color=0x5464B4)
        for command in list_commands:
            embed.add_field(name=command.command, value=command.brief, inline=False)
        author = menu.ctx.author
        return embed.set_footer(text=f"Requested by {author}", icon_url=author.display_avatar.url)

    async def format_view(self, menu: HelpMenu, entry: Tuple[Optional[commands.Cog], List[CommandHelp]]) -> HelpMenuView:
        if not menu._running:
            return
        _, list_commands = entry
        commands = [c.command_obj.name for c in list_commands]
        menu.view.clear_items()
        menu.view.add_item(HomeButton(style=discord.ButtonStyle.success, selected="Home", row=None))
        for c in commands:
            menu.view.add_item(HelpSearchButton(style=discord.ButtonStyle.secondary, selected=c, row=None))
        return menu.view

class DVBotHelp(commands.DefaultHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)

    def get_command_name(self, command, ctx = None):
        """
        Method to return a command's name and signature.
        """
        if not ctx:
            prefix = self.context.clean_prefix
            if not command.parent:
                return f"{prefix}{command.name}"
            else:
                return f"{prefix}{command.parent} {command.name}"
        else:
            def get_invoke_with():
                msg = ctx.message.content
                prefixmax = re.match(f'{re.escape(ctx.prefix)}', ctx.message.content).regs[0][1]
                return msg[prefixmax:msg.rindex(ctx.invoked_with)]
            if not command.signature and not command.parent:
                return f'{ctx.prefix}{ctx.invoked_with}'
            if command.signature and not command.parent:
                return f'{ctx.prefix}{ctx.invoked_with} {command.signature}'
            if not command.signature and command.parent:
                return f'{ctx.prefix}{get_invoke_with()}{ctx.invoked_with}'
            else:
                return f'{ctx.prefix}{get_invoke_with()}{ctx.invoked_with} {command.signature}'

    def get_command_usage(self, command, ctx = None):
        """
        Method to return a command's name and it's usage.
        """
        if not ctx:
            prefix = self.context.clean_prefix
            if not command.signature and not command.parent:
                return f'`{prefix}{command.name}`'
            if command.signature and not command.parent:
                return f"`{prefix}{command.name}` `{command.signature}`"
            if not command.signature and command.parent:
                return f"`{prefix}{command.parent}` `{command.name}`"
            else:
                return f"`{prefix}{command.parent}` `{command.name}` `{command.signature}`"
        else:
            prefix = ctx.clean_prefix
            if not command.signature and not command.parent:
                return f'`{prefix}{command.name}`'
            if command.signature and not command.parent:
                return f"`{prefix}{command.name}` `{command.signature}`"
            if not command.signature and command.parent:
                return f"`{prefix}{command.parent}` `{command.name}`"
            else:
                return f"`{prefix}{command.parent}` `{command.name}` `{command.signature}`"

    def get_help(self, command, brief = True):
        """
        Gets the command short_doc if brief is True while getting the longer help if it is false
        """
        real_help = command.help or "This command is not documented."
        return real_help if not brief else command.short_doc or real_help

    def get_aliases(self, command):
        """
        LMFAO it isn't even needed, but for some reasons it exists
        """
        return command.aliases

    async def send_bot_help(self, mapping):
        """
        Gets called when `uwu help` is invoked.
        """
        def get_command_help(com: CommandGroup) -> CommandHelp:
            signature = self.get_command_name(com)
            desc = self.get_help(com)
            return CommandHelp(signature, desc, com)
        
        def get_cog_help(cog, cog_commands) -> CogHelp:
            cog_name_none = getattr(cog, "qualified_name", "No Category")
            cog_name = cog_name_none.capitalize() if cog_name_none != 'owo' else 'OwO'
            cog_description = getattr(cog, 'description', "Not documented")
            cog_amount = len([*unpack(cog_commands)])
            return CogHelp(cog_name, cog_amount, cog_description)
        
        ctx = self.context
        bot = ctx.bot
        EACH_PAGE = 5
        command_data = {}
        for cog, unfiltered in mapping.items():
            if list_commands := await self.filter_commands(unfiltered, sort=True):
                lists = command_data.setdefault(cog, [])
                for chunks in discord.utils.as_chunks(list_commands, EACH_PAGE):
                    lists.append([*map(get_command_help, chunks)])
        mapped = itertools.starmap(get_cog_help, command_data.items())
        sort_cog = [*sorted(mapped, key=lambda c: c.commands, reverse=True)]
        embed = discord.Embed(description=f"{bot.description}\n\n**Select a Category**", color=0x5464B4)
        embed.set_author(name=f"{self.context.me.name}'s Help Command", icon_url=self.context.me.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        sort_cog = sorted(sort_cog, key=lambda x: x.name)
        for abc in sort_cog:
            embed.add_field(name=abc.name, value=abc.description)
        embed.set_footer(text=f"Requested by {self.context.author}", icon_url=self.context.author.display_avatar.url)
        loads = {
            "embed": embed,
            "help_object": self,
            "context": ctx,
            "mapper": command_data
        }
        cog_names = [{"selected": ch.name} for ch in sort_cog]
        buttons = discord.utils.as_chunks(cog_names, 5)
        menu_view = HelpMenuView(*buttons, **loads)
        await ctx.reply(embed=embed, view=menu_view)

    def get_command_help(self, command):
        """
        Returns an Embed version of the command object given.
        """
        if not self.context.guild:
            raise commands.NoPrivateMessage
        embed = discord.Embed(title=self.get_command_name(command))
        embed.description = self.get_help(command, brief=False)
        embed.color = 0x57F0F0
        embed.timestamp = datetime.utcnow()
        if alias := self.get_aliases(command):
            embed.add_field(name="Aliases", value=f'[{" | ".join(f"`{x}`" for x in alias)}]', inline=True)
        embed.add_field(name='Usage', value=self.get_command_usage(command), inline=True)
        embed.set_footer(text=f"Requested by {self.context.author}", icon_url=self.context.author.display_avatar.url)
        if isinstance(command, commands.Group):
            subcommand = command.commands
            value = "\n".join(self.get_command_signature(c) for c in subcommand)
            embed.add_field(name="Subcommands", value=value)
        return embed

    async def get_cog_help(self, cog):
        if not self.context.guild:
            raise commands.NoPrivateMessage
        self.show_hidden = True
        unfiltered_commands = cog.get_commands()
        list_commands = await self.filter_commands(unfiltered_commands, sort=True)
        if not list_commands:
            raise ArgumentBaseError(message="You don't have enough permission to see this help.") from None
        embeds = []
        for chunks in more_itertools.chunked(list_commands, 5):
            embed = discord.Embed(title=f"{getattr(cog, 'qualified_name', 'No').capitalize()} Category", color=0x57F0F0)
            embed.set_footer(text=f"Requested by {self.context.author}", icon_url=self.context.author.display_avatar.url)
            for command in chunks:
                embed.add_field(name=self.get_command_name(command), value=self.get_help(command, brief=True), inline=False)
            embeds.append(embed)
        return embeds

    async def get_group_help(self, group):
        if not self.context.guild:
            raise commands.NoPrivateMessage
        self.show_hidden = True
        list_commands = await self.filter_commands(group.commands, sort=True)
        if not list_commands:
            return await self.handle_help(group)
        embeds = []
        for chunks in more_itertools.chunked(list_commands, 4):
            embed = discord.Embed(title=self.get_command_name(group), color=0x57F0F0)
            embed.description = f"{self.get_help(group, brief=False)}\nUsage: {self.get_command_usage(group)}"
            embed.set_footer(text=f"Requested by {self.context.author}", icon_url=self.context.author.display_avatar.url)
            for command in chunks:
                embed.add_field(name=self.get_command_name(command), value=self.get_help(command, brief=True), inline=False)
            embeds.append(embed)
        return embeds

    async def handle_help(self, command):
        with contextlib.suppress(commands.CommandError):
            await command.can_run(self.context)
            return await self.context.reply(embed=self.get_command_help(command), mention_author=False)
        raise ArgumentBaseError(message="You don't have enough permission to see this help.") from None

    async def send_command_help(self, command):
        """
        Gets called when `uwu help <command>` is invoked.
        """
        await self.handle_help(command)

    async def send_group_help(self, group):
        """
        Gets called when `uwu help <group>` is invoked.
        """
        # await self.handle_help(group)
        from discord import ui
        if not self.context.guild:
            raise commands.NoPrivateMessage
        self.show_hidden = True
        list_commands = await self.filter_commands(group.commands, sort=True)
        if not list_commands:
            return await self.handle_help(group)
        command_data = {}
        lists = command_data.setdefault(group, list_commands)
        embed = self.get_command_help(group)
        # view = MenuViewBase(self.context, HelpSource)
        view = HelpMenuView(embed=embed, help_object=self, context=self.context)
        # view.help_command = self
        for subcommand in list_commands:
            name = get_command_name(subcommand)
            view.add_item(HelpSearchButton(style=discord.ButtonStyle.secondary, label=subcommand.name, selected=name, row=None))
        await self.context.reply(embed=embed, view=view)

    async def send_cog_help(self, cog):
        """
        Gets called when `uwu help <cog>` is invoked.
        """
        cog_commands = await self.get_cog_help(cog)
        description = """This shows available commands in this category 
                         Each line shows what the command is about."""
        pages = CogMenu(source=empty_page_format(cog_commands), description=description)
        with contextlib.suppress(discord.NotFound, discord.Forbidden):
            await pages.start(self.context, wait=True)
            await self.context.checkmark()

    def subcommand_not_found(self, command, string):
        """
        Replaces default error message.
        """
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            return f'Oops, looks like command "{command.qualified_name}" doesn\'t have a subcommand named "{string}"!'
        return f'Oops, looks like command "{command.qualified_name}" doesn\'t have a subcommand!'

    def command_not_found(self, string):
        """
        Replaces default error message.
        """
        return f'Oops, looks like command "{string}" doesn\'t exist!'

    async def send_error_message(self, error):
        return await self.context.reply(error, delete_after=10, mention_author=False)

class Help(commands.Cog, name='help'):
    def __init__(self, client):
        self.client = client
        self.default_help_command = client.help_command
        client.help_command = DVBotHelp()
        self.current_help_command = client.help_command
        client.get_command('help').hidden = True
        client.help_command.cog = self

    @commands.is_owner()
    @commands.command(name='mayday!!!', invoke_without_command=True, hidden=True)
    async def mayday(self, ctx):
        """
        A command for my dumb owner, just in case he unloaded dev extension.
        """
        dev = 'cogs.dev'
        try:
            self.client.load_extension(dev)
        except commands.ExtensionAlreadyLoaded:
            await ctx.checkmark()
            await ctx.send('Extensions was already loaded', delete_after=5)
        except Exception as e:
            await ctx.crossmark()
            await ctx.send('An unexpected error has occured.', delete_after=5)
            await ctx.author.send(f'```\n{e}\n```')
        else:
            await ctx.checkmark()
            await ctx.send("Extension was successfully loaded.", delete_after=5)
        await ctx.message.delete(delay=5)

    def cog_unload(self):
        self.client.help_command = self.default_help_command