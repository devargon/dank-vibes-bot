import discord
from discord.ext import menus
from collections import namedtuple
from discord.ext.menus import First, Last, Button

def pages(per_page=1, show_page=True):
    """Compact ListPageSource that was originally made teru but was modified"""
    def page_source(coro):
        async def create_page_header(self, menu, entry):
            result = await discord.utils.maybe_coroutine(coro, self, menu, entry)
            return menu.generate_page(result, self._max_pages)

        def __init__(self, list_pages):
            super(self.__class__, self).__init__(list_pages, per_page=per_page)
        kwargs = {
            '__init__': __init__,
            'format_page': (coro, create_page_header)[show_page]
        }
        return type(coro.__name__, (menus.ListPageSource,), kwargs)
    return page_source

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
                          EmojiB("<:first_check:843858924100517968>", First(0),
                                 "Goes to the first page."),

                          '\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f':
                          EmojiB("<:prev_check:843859502843035688>", First(1),
                                 "Goes to the previous page."),

                          '\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f':
                          EmojiB("<:next_check:843859461683544074>", Last(1),
                                 "Goes to the next page."),

                          '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f':
                          EmojiB("<:last_check:843859408488628304>", Last(2),
                                 "Goes to the last page."),

                          '\N{BLACK SQUARE FOR STOP}\ufe0f':
                          EmojiB("<:stop_check:843859572741111859>", Last(0),
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
                           EmojiB("<:first_check:843858924100517968>", First(0),
                                  "Goes to the first page."),

                           '\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f':
                           EmojiB("<:prev_check:843859502843035688>", First(1),
                                  "Goes to the previous page."),

                           '\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f':
                           EmojiB("<:next_check:843859461683544074>", Last(1),
                                  "Goes to the next page."),

                           '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f':
                           EmojiB("<:last_check:843859408488628304>", Last(2),
                                  "Goes to the last page."),

                           '\N{BLACK SQUARE FOR STOP}\ufe0f':
                           EmojiB("<:stop_check:843859572741111859>", Last(0),
                                  "Removes this message."),

                           '<:information_check:843859623874396232>':
                           EmojiB("<:information_check:843859623874396232>", Last(4),
                                  "Shows this infomation message.")
                            }
        super().__init__(source, dict_emoji=help_dict_emoji, **kwargs)

    async def show_page(self, page_number):
        self.info = False
        await super().show_page(page_number)

    @menus.button('<:information_check:843859623874396232>', position=Last(4))
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