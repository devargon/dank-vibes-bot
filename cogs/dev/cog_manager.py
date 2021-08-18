import discord
from discord.ext import commands
from utils import checks
from utils.converters import TrueFalse

class CogManager(commands.Cog):
    """
    This module allows you to manage cogs directly from discord.
    """
    def __init__(self, client):
        self.client = client

    @checks.admoon()
    @commands.command(name='cogs', hidden=True)
    async def cogs(self, ctx, silence: TrueFalse = False):
        """
        Lists all loaded and available cogs.
        """
        loaded = set(self.client.extensions)
        all_cogs = set(self.client.available_extensions)
        unloaded = all_cogs - loaded
        loaded = sorted(list(loaded), key=str.lower)
        unloaded = sorted(list(unloaded), key=str.lower)
        embed = discord.Embed(color=self.client.embed_color).set_author(name=ctx.me, icon_url=ctx.me.avatar_url)
        embed.set_author(name="{} extensions loaded".format(len(loaded)))
        loaded_extensions = "\n".join(loaded)
        embed.add_field(name='**Loaded extensions**', value=f"```css\n{loaded_extensions}\n```")
        if len(unloaded) != 0:
            unloaded_extensions = "\n".join(unloaded)
            embed.add_field(name="**Unloaded extensions**", value=f"```ldif\n{unloaded_extensions}\n```")
        if silence:
            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete(delay=10)
        else:
            await ctx.send(embed=embed)

    @checks.admoon()
    @commands.command(name='load', hidden=True, usage="<extensions...>", invoke_without_command=True)
    async def load(self, ctx, *, cogs: str = None):
        """
        Loads an available extension.

        Use `.load *` or `.load all` to load all the extensions.
        """
        if cogs is None:
            await ctx.send("Specify an extension to load.", delete_after=3)
            return await ctx.message.delete(delay=3)
        cogs_to_load = []
        output = []
        error = []
        exception_log = []
        if cogs == 'all' or cogs == '*':
            cogs_to_load = self.client.available_extensions
        else:
            names = [cog.strip() for cog in cogs.rsplit(',' if ',' in cogs else ' ')]
            for name in names:
                name = name if name.startswith('cogs') else 'cogs.' + name
                cogs_to_load.append(name)
        for cog in cogs_to_load:
            try:
                self.client.load_extension(cog)
                output.append(f'{cog} is loaded.')
            except commands.ExtensionAlreadyLoaded:
                output.append(f'{cog} is already loaded.')
            except commands.ExtensionNotFound:
                output.append(f'{cog} is not a valid extension.')
                error.append(cog)
            except Exception as e:
                error.append(cog)
                output.append(f'{cog} has not been loaded.')
                exception_log.append(f'```py\n{e}\n```')
        embed = discord.Embed(color=self.client.embed_color)
        await ctx.checkmark() if len(error) == 0 else await ctx.crossmark()
        if len(output) == 1:
            if len(exception_log) == 1:
                message = message = f"{output[0][:-1]}, Check your DMs for more details."
            else:
                message = output[0]
            await ctx.send(message, delete_after=5)
            if exception_log:
                await ctx.author.send(''.join(exception_log))
            return await ctx.message.delete(delay=5)
        else:
            embed.description = '\n'.join(output)
            if len(exception_log) != 0:
                embed.set_footer(text='Check your DMs for more details.')
            await ctx.send(embed=embed, delete_after=10)
            if len(exception_log) != 0:
                await ctx.author.send('\n'.join(exception_log))
            return await ctx.message.delete(delay=10)

    @checks.admoon()
    @commands.command(name='unload', hidden=True, usage="<extensions...>", invoke_without_command=True)
    async def unload(self, ctx, *, cogs: str = None):
        """
        Unloads a previously loaded extension.

        Use `.unload *` or `.unload all` to unload all the extensions.
        """
        if cogs is None:
            await ctx.send("Specify an extension to load.", delete_after=3)
            return await ctx.message.delete(delay=3)
        cogs_to_unload = []
        output = []
        error = []
        exception_log = []
        if cogs == 'all' or cogs == '*':
            cogs_to_unload = self.client.available_extensions
            cogs_to_unload.remove('cogs.dev')
            cogs_to_unload.remove('cogs.help')
        else:
            names = [cog.strip() for cog in cogs.rsplit(',' if ',' in cogs else ' ')]
            for name in names:
                name = name if name.startswith('cogs') else 'cogs.' + name
                cogs_to_unload.append(name)
        for cog in cogs_to_unload:
            try:
                self.client.unload_extension(cog)
                output.append(f'{cog} is unloaded.')
            except commands.ExtensionNotLoaded:
                output.append(f'{cog} is already unloaded.')
            except commands.ExtensionNotFound:
                output.append(f'{cog} is not a valid extension.')
                error.append(cog)
            except Exception as e:
                error.append(cog)
                output.append(f'{cog} has not been unloaded.')
                exception_log.append(f'```py\n{e}\n```')
        embed = discord.Embed(color=self.client.embed_color)
        await ctx.checkmark() if len(error) == 0 else await ctx.crossmark()
        if len(output) == 1:
            if len(exception_log) == 1:
                message = message = f"{output[0][:-1]}, Check your DMs for more details."
            else:
                message = output[0]
            await ctx.send(message, delete_after=5)
            if exception_log:
                await ctx.author.send(''.join(exception_log))
            return await ctx.message.delete(delay=5)
        else:
            embed.description = '\n'.join(output)
            if len(exception_log) != 0:
                embed.set_footer(text='Check your DMs for more details.')
            await ctx.send(embed=embed, delete_after=10)
            if len(exception_log) != 0:
                await ctx.author.send('\n'.join(exception_log))
            return await ctx.message.delete(delay=10)

    @checks.admoon()
    @commands.command(name='reload', hidden=True, usage="<extensions...>", invoke_without_command=True)
    async def reload(self, ctx, *, cogs: str = None):
        """
        Reloads an extension.

        Use `.reload *` or `.reload all` to reload all the extensions.
        """
        if cogs is None:
            await ctx.send("Specify an extension to load.", delete_after=3)
            return await ctx.message.delete(delay=3)
        cogs_to_load = []
        output = []
        error = []
        exception_log = []
        if cogs == 'all' or cogs == '*':
            cogs_to_load = self.client.available_extensions
        else:
            names = [cog.strip() for cog in cogs.rsplit(',' if ',' in cogs else ' ')]
            for name in names:
                name = name if name.startswith('cogs') else 'cogs.' + name
                cogs_to_load.append(name)
        for cog in cogs_to_load:
            try:
                self.client.reload_extension(cog)
                output.append(f'{cog} is reloaded.')
            except commands.ExtensionNotFound:
                output.append(f'{cog} is not a valid extension.')
                error.append(cog)
            except commands.ExtensionNotLoaded:
                output.append(f"{cog} isn't loaded.")
                error.append(cog)
            except Exception as e:
                error.append(cog)
                output.append(f'{cog} has not been loaded.')
                exception_message = f"```py\n{e}```"
                exception_log.append(exception_message)
        embed = discord.Embed(color=self.client.embed_color)
        await ctx.checkmark() if len(error) == 0 else await ctx.crossmark()
        if len(output) == 1:
            if len(exception_log) == 1:
                message = message = f"{output[0][:-1]}, Check your DMs for more details."
            else:
                message = output[0]
            await ctx.send(message, delete_after=5)
            if exception_log:
                await ctx.author.send(''.join(exception_log))
            return await ctx.message.delete(delay=5)
        else:
            embed.description = '\n'.join(output)
            if len(exception_log) != 0:
                embed.set_footer(text='Check your DMs for more details.')
            await ctx.send(embed=embed, delete_after=10)
            if len(exception_log) != 0:
                await ctx.author.send('\n'.join(exception_log))
            return await ctx.message.delete(delay=10)