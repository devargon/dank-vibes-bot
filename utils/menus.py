from collections import namedtuple
from typing import Iterable, Any, Dict

import discord
from discord.ext import menus
from discord.ui import View, Button
from discord.ext.menus import First, Last, Button


class MenuBase(menus.MenuPages):
    """
    This is a MenuPages class that is used every single paginator menus. All it does is replace the default emoji
    with a custom emoji, and keep the functionality.
    """
    def __init__(self, source, dict_emoji = None, **kwargs):
        super().__init__(source, delete_message_after=kwargs.pop('delete_message_after', True), **kwargs)
        self.info = False

        EmojiB = namedtuple("EmojiB", "emoji position explain")
        def_dict_emoji = {'\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f':
                          EmojiB("<:DVB_first_check:955345524519759903>", First(0),
                                 "Goes to the first page."),

                          '\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f':
                          EmojiB("<:DVB_prev_check:955345544623038484>", First(1),
                                 "Goes to the previous page."),

                          '\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f':
                          EmojiB("<:DVB_next_check:955345527610945536>", Last(1),
                                 "Goes to the next page."),

                          '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f':
                          EmojiB("<:DVB_last_check:955345526302318622>", Last(2),
                                 "Goes to the last page."),

                          '\N{BLACK SQUARE FOR STOP}\ufe0f':
                          EmojiB("<:DVB_stop_check:955345546103631902>", Last(0),
                                 "Removes this message.")
                          }
        self.dict_emoji = dict_emoji or def_dict_emoji
        for emoji in self.buttons:
            callback = self.buttons[emoji].action
            if emoji.name not in self.dict_emoji:
                continue
            new_but = self.dict_emoji[emoji.name]
            new_button = Button(new_but.emoji, callback, position=new_but.position)
            del self.dict_emoji[emoji.name]
            self.dict_emoji[new_but.emoji] = new_but
            self.add_button(new_button)
            self.remove_button(emoji)

    async def _get_kwargs_from_page(self, page):
        value = await discord.utils.maybe_coroutine(self._source.format_page, self, page)
        no_ping = {'allowed_mentions': discord.AllowedMentions(replied_user=False)}
        if isinstance(value, dict):
            value.update(no_ping)
        elif isinstance(value, str):
            no_ping.update({'content': value})
        elif isinstance(value, discord.Embed):
            no_ping.update({'embed': value, 'content': None})
        return no_ping

    def generate_page(self, content, maximum):
        if maximum > 1:
            page = f"Page {self.current_page + 1}/{maximum}"
            if isinstance(content, discord.Embed):
                content.color = 0x57F0F0
                if embed_dict := getattr(content, "_footer", None):
                    embed_dict["text"] += f" • {page}"
                    return content
                return content.set_footer(text=page)
            elif isinstance(content, str):
                return f"{page}\n{content}"
        return content

    async def send_initial_message(self, ctx, channel):
        page = await self._source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        return await ctx.reply(**kwargs)


class HelpMenuBase(MenuBase):
    """
    This is a MenuPages class that is used every single paginator menus. All it does is replace the default emoji
    with a custom emoji, and keep the functionality.
    """
    def __init__(self, source, **kwargs):
        EmojiB = namedtuple("EmojiB", "emoji position explain")
        help_dict_emoji = {'\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f':
                           EmojiB("<:DVB_first_check:955345524519759903>", First(0),
                                  "Goes to the first page."),

                           '\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f':
                           EmojiB("<:DVB_prev_check:955345544623038484>", First(1),
                                  "Goes to the previous page."),

                           '\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f':
                           EmojiB("<:DVB_next_check:955345527610945536>", Last(1),
                                  "Goes to the next page."),

                           '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f':
                           EmojiB("<:DVB_last_check:955345526302318622>", Last(2),
                                  "Goes to the last page."),

                           '\N{BLACK SQUARE FOR STOP}\ufe0f':
                           EmojiB("<:DVB_stop_check:955345546103631902>", Last(0),
                                  "Removes this message."),

                           '<:DVB_information_check:955345547542294559>':
                           EmojiB("<:DVB_information_check:955345547542294559>", Last(4),
                                  "Shows this infomation message.")
                            }
        super().__init__(source, dict_emoji=help_dict_emoji, **kwargs)

    async def show_page(self, page_number):
        self.info = False
        await super().show_page(page_number)

    @menus.button('<:DVB_information_check:955345547542294559>', position=Last(4))
    async def on_information(self, payload):
        if info := not self.info:
            await self.on_information_show(payload)
        else:
            self.current_page = max(self.current_page, 0)
            await self.show_page(self.current_page)
        self.info = info

    async def on_information_show(self, payload):
        raise NotImplementedError("Information is not implemented.")

class HelpMenu(HelpMenuBase):
    """
    This is a MenuPages class that is used only in help command. All it has is custom information and
    custom initial message.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.help_command = None

    async def on_information_show(self, payload):
        exists = [str(emoji) for emoji in super().buttons]
        embed = discord.Embed(title="Information", description="This shows each commands in this bot. Each page is a category that shows\nwhat commands that the category have.")
        embed.color = 0x57F0F0
        curr = self.current_page + 1 if (p := self.current_page > -1) else "cover page"
        pa = "page" if p else "the"
        embed.set_footer(text=f"You were on {pa} {curr}")
        nav = '\n'.join(f'{self.dict_emoji[e].emoji} {self.dict_emoji[e].explain}' for e in exists)
        embed.add_field(name='Navigation', value=nav)
        await self.message.edit(embed=embed)

    async def start(self, ctx, **kwargs):
        self.help_command = ctx.bot.help_command
        self.help_command.context = ctx
        await super().start(ctx, **kwargs)

class CogMenu(HelpMenu):
    """
    This is a MenuPages class that is used only in Cog help command. All it has is custom information and
    custom initial message.
    """
    async def on_information_show(self, payload):
        exists = [str(emoji) for emoji in super().buttons]
        embed = discord.Embed(title="Information", description="This shows available commands in this category. \nEach line shows what the command is about and how to use it.")
        embed.color = 0x57F0F0
        curr = self.current_page + 1 if (p := self.current_page > -1) else "cover page"
        pa = "page" if p else "the"
        embed.set_footer(text=f"You were on {pa} {curr}")
        nav = '\n'.join(f'{self.dict_emoji[e].emoji} {self.dict_emoji[e].explain}' for e in exists)
        embed.add_field(name='Navigation', value=nav)
        await self.message.edit(embed=embed)

class GroupMenu(HelpMenu):
    """
    This is a MenuPages class that is used only in Group help command. All it has is custom information and
    custom initial message
    """
    async def on_information_show(self, payload):
        exists = [str(emoji) for emoji in super().buttons]
        embed = discord.Embed(title="Information", description="This shows available subcommands in this command. \nEach line shows what the subcommand is about and how to use it.")
        embed.color = 0x57F0F0
        curr = self.current_page + 1 if (p := self.current_page > -1) else "cover page"
        pa = "page" if p else "the"
        embed.set_footer(text=f"You were on {pa} {curr}")
        nav = '\n'.join(f'{self.dict_emoji[e].emoji} {self.dict_emoji[e].explain}' for e in exists)
        embed.add_field(name='Navigation', value=nav)
        await self.message.edit(embed=embed)

class CustomMenu(HelpMenu):
    """
    This is a MenuPages class that is used only in Emoji command. All it has it custom information and
    custom initial message
    """
    async def on_information_show(self, payload):
        exists = [str(emoji) for emoji in super().buttons]
        embed = discord.Embed(color=self.ctx.bot.help_color)
        curr = self.current_page + 1 if (p := self.current_page > -1) else "cover page"
        pa = "page" if p else "the"
        embed.set_footer(text=f"You were on {pa} {curr}")
        nav = '\n'.join(f'{self.dict_emoji[e].emoji} {self.dict_emoji[e].explain}' for e in exists)
        embed.add_field(name='Navigation', value=nav)
        await self.message.edit(embed=embed)

class MenuViewInteractionBase(HelpMenuBase):
    """MenuPages class that is specifically for the help command."""
    def __init__(self, view: View, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.view = view

    def stop(self) -> None:
        self.view.stop()
        super().stop()

    async def _get_kwargs_from_page(self, page: Any) -> Dict[str, Any]:
        kwargs = await super()._get_kwargs_from_page(page)
        kwargs.update({"view": await self._source.format_view(self, page)})
        return kwargs

class ListPageInteractionBase(menus.ListPageSource):
    """A ListPageSource base that is involved with Interaction. It takes button and interaction object
        to correctly operate and require format_view to be overriden"""
    def __init__(self, button: Button, entries: Iterable[Any], **kwargs: Any):
        super().__init__(entries, **kwargs)
        self.button = button

    async def format_view(self, menu: menus.MenuPages, entry: Any) -> None:
        """Method that handles views, it must return a View"""
        raise NotImplementedError