import discord
from discord.ext import commands, menus
from utils.menus import CustomMenu
from utils import checks
from datetime import datetime
from utils.buttons import *

class MessageLog(commands.Cog):
    def __init(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.webhook_id:
            return
        if message.is_system():
            return
        if message.author.bot:
            return
        if message.channel.id != 871734809653833740:#
            return
        result = await self.client.pool_pg.fetchrow("SELECT * FROM messagelog WHERE user_id = $1", message.author.id)
        if result is None:
            await self.client.pool_pg.execute("INSERT INTO messagelog VALUES($1, $2)", message.author.id, 1)
        else:
            existing_count = result.get('messagecount')
            await self.client.pool_pg.execute("UPDATE messagelog SET messagecount = $1 WHERE user_id = $2", existing_count + 1, message.author.id)


    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="messagereset", aliases=["mreset"], invoke_without_command=True)
    async def messagelog(self, ctx):
        """
        Resets the database for counting messages sent.
        """
        confirm_view = confirm(ctx, self.client, 30.0)
        messagecount = await self.client.pool_pg.fetch("SELECT * FROM messagelog")
        if len(messagecount) == 0:  # if there's nothing to be deleted
            return await ctx.send("There's no message count to be removed.")
        totalvote = sum(userentry.get('messagecount') for userentry in messagecount)
        embed = discord.Embed(title="Action awaiting confirmation", description=f"There are {len(messagecount)} who have chatted, amounting to a total of {totalvote} messages. Are you sure you want to reset the message count?", color=self.client.embed_color, timestamp=datetime.utcnow())
        msg = await ctx.reply(embed=embed, view=confirm_view)
        confirm_view.response = msg
        await confirm_view.wait()
        if confirm_view.returning_value is None:
            embed.color, embed.description = discord.Color.red(), "You didn't respond."
            return await msg.edit(embed=embed)
        if confirm_view.returning_value == False:
            embed.color, embed.description = discord.Color.red(), "Action cancelled."
            return await msg.edit(embed=embed)
        if confirm_view.returning_value == True:
            await self.client.pool_pg.execute("DELETE FROM messagelog")
            embed.color, embed.description = discord.Color.green(), "The message count has been cleared."
            await msg.edit(embed=embed)