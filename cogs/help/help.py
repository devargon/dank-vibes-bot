import re
from utils.errors import ArgumentBaseError
import discord
import contextlib
import more_itertools
from datetime import datetime
from discord.ext import commands
from utils.menus import pages, CogMenu, GroupMenu


@pages()
async def group_help_source_format(self, menu: GroupMenu, entry):
    """
    This is for the group help command ListPageSource
    """
    group, list_commands = entry
    embed = discord.Embed(title=DVBotHelp.get_command_name(self, group))
    embed.color = 0x57F0F0
    embed.description = f"{DVBotHelp.get_help(self, group, False, ctx=menu.ctx)}\nUsage: {DVBotHelp.get_command_usage(self, group, ctx=menu.ctx)}"
    embed.set_footer(text=f"Requested by {menu.ctx.author}", icon_url=menu.ctx.author.avatar_url)
    for command in list_commands:
        value = f"{DVBotHelp.get_help(self, command, ctx=menu.ctx)}\nUsage: {DVBotHelp.get_command_usage(self, command, ctx=menu.ctx)}"
        embed.add_field(name=f"{DVBotHelp.get_command_name(self, command)}", value=value, inline=False)
    return embed

@pages()
async def cog_help_source_format(self, menu: CogMenu, entry):
    """
    This is for the cog help command ListPageSource
    """
    cog, list_commands = entry
    embed = discord.Embed(title=f"{getattr(cog, 'qualified_name', 'No').capitalize()} Category")
    embed.color = 0x57F0F0
    embed.set_footer(text=f"Requested by {menu.ctx.author}", icon_url=menu.ctx.author.avatar_url)
    for command in list_commands:
        value = f"{DVBotHelp.get_help(self, command, ctx=menu.ctx)}\nUsage: {DVBotHelp.get_command_usage(self, command, ctx=menu.ctx)}"
        if isinstance(command, commands.Group):
            value += f"\n`{menu.ctx.clean_prefix}help {DVBotHelp.get_command_name(self, command)}` for subcommands."
        embed.add_field(name=f"{DVBotHelp.get_command_name(self, command)}", value=value, inline=False)
    return embed

@pages()
def empty_page_format(_, __, entry):
    """This is for Code Block ListPageSource and for help Cog ListPageSource"""
    return entry

class DVBotHelp(commands.DefaultHelpCommand):
    def __init__(self, **options):
        super().__init__(**options)

    def get_command_name(self, command, ctx = None):
        """
        Method to return a command's name and signature.
        """
        if not ctx:
            if not command.parent:
                return f"{command.name}"
            else:
                return f"{command.parent} {command.name}"
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

    def get_help(self, command, brief = True, ctx = None):
        """
        Gets the command short_doc if brief is True while getting the longer help if it is false
        """
        context = ctx if ctx else self.context
        if not command.description:
            db_desc = context.bot.cur.execute("SELECT description FROM config WHERE command=?", (command.name,)).fetchone()
            if not db_desc:
                real_help = command.help or "This command is not documented."
                command.description = command.help or "This command is not documented."
            else:
                real_help = db_desc[0]
                command.help = db_desc[0]
                command.description = db_desc[0]
        real_help = command.help or "This command is not documented."
        return real_help if not brief else command.short_doc or real_help

    def get_aliases(self, command):
        """
        LMFAO it isn't even needed
        """
        return command.aliases

    async def send_bot_help(self, mapping):
        """
        Gets called when `.help` is invoked.
        """
        if not self.context.guild:
            raise commands.NoPrivateMessage
        embed = discord.Embed(color=0x57F0F0)
        embed.timestamp = datetime.utcnow()
        embed.set_author(name=f"{self.context.me.name}'s Command List", icon_url=self.context.me.avatar_url)
        embed.set_footer(text=f"Requested by {self.context.author}", icon_url=self.context.author.avatar_url)
        for cog, unfiltered_commands in mapping.items():
            filtered = await self.filter_commands(unfiltered_commands, sort=True)
            if not cog:
                continue
            if filtered:
                name = cog.qualified_name.capitalize()
                description = cog.description if cog.description else "Not documented."
                value = f"{description}\n `{self.context.clean_prefix}help {cog.qualified_name}` for more info"
                embed.add_field(name=name, value=value)
        await self.context.reply(embed=embed, mention_author=False)

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
        embed.set_footer(text=f"Requested by {self.context.author}", icon_url=self.context.author.avatar_url)
        return embed

    async def handle_help(self, command):
        with contextlib.suppress(commands.CommandError):
            await command.can_run(self.context)
            return await self.context.reply(embed=self.get_command_help(command), mention_author=False)
        raise ArgumentBaseError(message="You don't have enough permission to see this help.") from None

    async def send_command_help(self, command):
        """
        Gets called when `.help <command>` is invoked.
        """
        await self.handle_help(command)

    async def send_group_help(self, group):
        """
        Gets called when `.help <group>` is invoked.
        """
        if not self.context.guild:
            raise commands.NoPrivateMessage
        data = []
        self.show_hidden = True
        list_commands = await self.filter_commands(group.commands, sort=True)
        if not list_commands:
            return await self.handle_help(group)
        for chunks in more_itertools.chunked(list_commands, 4):
            data.append((group, [sub for sub in chunks]))
        pages = GroupMenu(source=group_help_source_format(data), timeout=60)
        with contextlib.suppress(discord.NotFound, discord.Forbidden):
            await pages.start(self.context, wait=True)
            return await self.context.checkmark()

    async def send_cog_help(self, cog):
        """
        Gets called when `.help <cog>` is invoked.
        """
        if not self.context.guild:
            raise commands.NoPrivateMessage
        command_data = []
        self.show_hidden = True
        unfiltered_commands = cog.get_commands()
        list_commands = await self.filter_commands(unfiltered_commands, sort=True)
        if not list_commands:
            raise commands.CommandError("You don't have enough permission to see this help.") from None
        for chunks in more_itertools.chunked(list_commands, 5):
            command_data.append((cog, [command for command in chunks]))
        pages = CogMenu(source=cog_help_source_format(command_data), timeout=60)
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

class Help(commands.Cog):
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