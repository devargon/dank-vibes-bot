import discord

from discord.ext import pages


class SingleMenuPaginator(pages.Paginator):
    def __init__(self, pages, author_check=True, timeout=30.0):
        super().__init__(
            pages=pages,
            show_disabled=True,
            show_indicator=True,
            show_menu=False,
            author_check=author_check,
            disable_on_timeout=True,
            use_default_buttons=True,
            loop_pages=False,
            timeout=timeout)


class MultiMenuPaginator(pages.Paginator):
    def __init__(self, pages, menu_placeholder="View all options...", author_check=True, timeout=60.0):
        super().__init__(
            pages=pages,
            menu_placeholder=menu_placeholder,
            show_menu=True,
            show_disabled=True,
            show_indicator=True,
            author_check=author_check,
            disable_on_timeout=True,
            use_default_buttons=True,
            loop_pages=False,
            timeout=timeout)