import discord
from discord.ext import commands
import json
import asyncio

class MessageTracking(commands.Cog, name='MessageTracking'):
    def __init__(self, client):
        self.client = client
        self.queue = []

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author in self.queue:
            return
        if message.author == self.client.user:
            return
        if not message.guild:
            return
        if message.author.bot:
            return
        if message.webhook_id:
            return
        if message.channel.id != 608498967474601995:
            return
        if len(str(message.content)) == 1:
            return
        self.queue.append(message.author)
        result = await self.client.pool_pg.fetchrow("SELECT * FROM messagelog WHERE user_id = $1", message.author.id)
        if result is None:
            await self.client.pool_pg.execute("INSERT INTO messagelog VALUES($1, $2)", message.author.id, 1)
            existing_count = 1
        else:
            existing_count = result.get('messagecount')
            await self.client.pool_pg.execute("UPDATE messagelog SET messagecount = $1 WHERE user_id = $2", existing_count+1, message.author.id)
        milestones = await self.client.pool_pg.fetch("SELECT * FROM messagemilestones")
        if len(milestones) != 0:  # there are settings for milestones
            rolesummary = ""
            for milestone in milestones:
                role = message.guild.get_role(milestone.get('roleid'))  # gets the milestone role
                if (
                        role is not None
                        and existing_count+1 >= milestone.get('messagecount')
                        and role not in message.author.roles  # the user doesn't have the role yet
                ):
                    try:
                        await message.author.add_roles(role, reason=f"Message milestone reached for user")  # adds the role

                        rolesummary += f"\nYou've gotten the role **{role.name}** for sending {milestone.get('messagecount')} messages! 🥳"  # adds on to the summary of roles added
                    except discord.Forbidden:
                        pass
            if rolesummary:
                await message.reply(rolesummary)
        await asyncio.sleep(8)
        self.queue.remove(message.author)