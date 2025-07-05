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
        if message.channel.id != 1288032530569625663:
            return
        if len(str(message.content)) == 1:
            return
        self.queue.append(message.author)
        result = await self.client.db.fetchrow("SELECT * FROM messagecount WHERE user_id = $1 AND guild_id = $2", message.author.id, message.guild.id)
        if result is None:
            await self.client.db.execute("INSERT INTO messagecount (guild_id, user_id, mcount) VALUES($1, $2, $3)", message.guild.id, message.author.id, 0)
            existing_count = 0
        else:
            existing_count = result.get('messagecount')
            await self.client.db.execute("UPDATE messagelog SET messagecount = $1 WHERE user_id = $2", existing_count+1, message.author.id)
        milestones = await self.client.db.fetch("SELECT * FROM messagemilestones")
            existing_count = result.get('mcount')
        new_count = existing_count + add_message_count
        await self.client.db.execute("UPDATE messagecount SET mcount = $1 WHERE guild_id = $2 AND user_id = $3", new_count, message.guild.id, message.author.id)
        if len(milestones) != 0:  # there are settings for milestones
            rolesummary = ""
            for milestone in milestones:
                role = message.guild.get_role(milestone.get('role_id'))  # gets the milestone role
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
                try:
                    await message.reply(rolesummary)
                except Exception as e:
                    await message.channel.send(rolesummary)
        await asyncio.sleep(8)
        self.queue.remove(message.author)