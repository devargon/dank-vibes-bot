import discord
from discord.ext import menus

class get_ars(menus.ListPageSource):
    def __init__(self, data, guild, color):
        self.data = data
        self.guild = guild
        self.color = color
        super().__init__(data, per_page=20)
    
    async def format_page(self, menu, entries):
        embed = discord.Embed(color=self.color, title="Autoreactions")
        embed.description = "\n".join(f"• {entry.get('trigger')}" for entry in entries)
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()} | Total ARs: {len(entries)}", icon_url=self.guild.icon.url)
        return embed