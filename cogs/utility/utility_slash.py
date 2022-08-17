import json

import discord
from discord.ext import commands

class ViewEmbedJSONs(discord.ui.View):
    def __init__(self, embeds):
        self.embeds = embeds
        super().__init__(timeout=None)

    @discord.ui.button(label="View raw JSON embeds", style=discord.ButtonStyle.primary, emoji=discord.PartialEmoji.from_str("<:DVB_Embed:976499722070151258>"))
    async def view_raw_json(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        await interaction.response.edit_message(embeds=self.embeds, view=self)


class UtilitySlash(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.has_permissions(manage_messages=True)
    @commands.message_command(name="View raw")
    async def view_raw(self, ctx: discord.ApplicationContext, message: discord.Message):
        """View the raw content of a message."""
        m_content = message.content
        if len(m_content) > 0:
            content_embed_raw = discord.Embed(title="Raw Message Content", description=f"```\n{message.content}\n```", color=self.client.embed_color)
            if len(message.embeds) > 0:
                embeds = []
                for embed in message.embeds:
                    embed_json = json.dumps(embed.to_dict())
                    content_embed = discord.Embed(title="Raw Embed (JSON)", description=f"```\n{embed_json}\n```", color=self.client.embed_color)
                    embeds.append(content_embed)
                await ctx.respond(embed=content_embed_raw, view=ViewEmbedJSONs(embeds), ephemeral=True)
            else:
                await ctx.respond(embed=content_embed_raw, ephemeral=True)
        elif len(message.embeds) > 0:
            embeds = []
            for embed in message.embeds:
                embed_json = json.dumps(embed.to_dict())
                content_embed_raw = discord.Embed(title="Raw Embed (JSON)", description=f"```\n{embed_json}\n```", color=self.client.embed_color)
                embeds.append(content_embed_raw)
            await ctx.respond(embeds=embeds, ephemeral=True)
