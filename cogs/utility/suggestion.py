import discord
from utils import checks
from datetime import datetime
from discord.ext import commands


class Suggestion(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.group(name='suggest', usage='<suggestion>', invoke_without_command=True)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def suggest(self, ctx, *, message: str = None):
        """
        Suggest something to the developers through the bot.
        """
        if message is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Hey! im not sending a blank message, write something meaningful and try again.")
        if not await ctx.confirmation("Are you sure you wanna send this message to the developers?", cancel_message="Okay, we're not sending that message to the developers", delete_delay=5):
            return ctx.command.reset_cooldown(ctx)
        try:
            embed = discord.Embed(color=0xffcccb,
                                    title="Suggestion sent to the developers",
                                    description=f"**You sent:** {message}",
                                    timestamp=datetime.utcnow())
            embed.set_footer(text=f"Any response from the developers will be through DM.")
            response = await ctx.author.send(embed=embed)
        except:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Please enable your DM, any response from the developers will be through DMs.")
        else:
            query = "INSERT INTO suggestions VALUES (DEFAULT, $1, False, $2, $3) RETURNING suggestion_id"
            values = (ctx.author.id, response.id, message)
            suggestion_id = await self.client.pool_pg.fetchval(query, *values, column='suggestion_id')
            embed.title += f" (ID: {suggestion_id})"
            await response.edit(embed=embed)
            channel = self.client.get_guild(871734809154707467).get_channel(876346196564803614)
            embed = discord.Embed(color=0xffcccb,
                                    description=message,
                                    timestamp=datetime.utcnow())
            embed.set_author(name=f"{ctx.author} made a suggestion", icon_url=ctx.author.avatar.url)
            embed.set_footer(text=f"Suggestion ID: {suggestion_id}")
            msg = await channel.send(embed=embed)
            await ctx.checkmark()
            query = "INSERT INTO suggestion_response VALUES ($1, $2, $3, $4, $5)"
            values = (suggestion_id, ctx.author.id, response.id, msg.id, message)
            await self.client.pool_pg.execute(query, *values)

    @checks.dev()
    @suggest.command(name='close', aliases=['end'], usage='<suggestion_id> <message>', hidden=True)
    async def suggest_close(self, ctx, suggestion_id = None, *, message = None):
        """
        Close an active suggestion.
        """
        if suggestion_id is None:
            return await ctx.send("You forgot to include a suggestion ID")
        if not suggestion_id.isdigit():
            return await ctx.send("That's not a valid suggestion ID")
        if message is None:
            return await ctx.send("Hey, you need to add a message!")
        suggestion_id = int(suggestion_id)
        suggestion = await self.client.pool_pg.fetchrow("SELECT * FROM suggestions WHERE suggestion_id=$1", suggestion_id)
        if not suggestion:
            return await ctx.send("I couldn't find a suggestion with that ID.")
        if suggestion.get('finish'):
            return await ctx.send("That suggestion is already closed.")
        channel = self.client.get_guild(871734809154707467).get_channel(876346196564803614)
        await self.client.pool_pg.execute("UPDATE suggestions SET finish=True WHERE suggestion_id=$1", suggestion_id)
        stats = await self.client.pool_pg.fetchrow("SELECT * FROM suggestion_response WHERE suggestion_id=$1", suggestion_id)
        dm = await self.get_dm(suggestion.get('user_id'))
        dm_msg = dm.get_partial_message(suggestion.get('response_id'))
        dmembed = discord.Embed(color=0xffcccb,
                                title='Suggestion Closed',
                                description=f"{ctx.author} has closed the suggestion.",
                                timestamp=datetime.utcnow())
        dmembed.set_footer(text=f"Suggestion ID: {suggestion_id}")
        dmembed.add_field(name="Reason", value=message)
        msg = await channel.fetch_message(stats.get('message_id'))
        embed = msg.embeds[0]
        embed.timestamp = datetime.utcnow()
        embed.add_field(name=f"Suggestion closed by {ctx.author}", value=message)
        await dm_msg.reply(embed=dmembed)
        await msg.edit(embed=embed)
        await ctx.checkmark()

    @checks.dev()
    @suggest.command(name='respond', aliases=['reply'], usage='<suggestion_id> <message>', hidden=True)
    async def suggest_respond(self, ctx, suggestion_id = None, *, message = None):
        """
        Send a reply to the person who made the suggestion.
        """
        if suggestion_id is None:
            return await ctx.send("You forgot to include a suggestion ID")
        if not suggestion_id.isdigit():
            return await ctx.send("That's not a valid suggestion ID")
        if message is None:
            return await ctx.send("Hey, you need to add a message!")
        suggestion_id = int(suggestion_id)
        suggestion = await self.client.pool_pg.fetchrow("SELECT * FROM suggestions WHERE suggestion_id=$1", suggestion_id)
        if not suggestion:
            return await ctx.send("I couldn't find a suggestion with that ID.")
        if suggestion.get('finish'):
            return await ctx.send("That suggestion is already closed.")
        if not await ctx.confirmation(f"Are you sure you wanna send this message to {self.client.get_user(suggestion.get('user_id'))}?", cancel_message="Aborting...", delete_delay=5):
            return
        stats = await self.client.pool_pg.fetchrow("SELECT * FROM suggestion_response WHERE suggestion_id=$1", suggestion_id)
        dm = await self.get_dm(stats.get('user_id'))
        msg = dm.get_partial_message(stats.get('response_id'))
        embed = discord.Embed(color=0xffcccb,
                                title=f"Response from {ctx.author}",
                                description=message,
                                timestamp=datetime.utcnow())
        response = await msg.reply(embed=embed)
        query = "INSERT INTO suggestion_response VALUES ($1, $2, $3, $4, $5)"
        values = (suggestion_id, stats.get('user_id'), response.id, stats.get('message_id'), message)
        await self.client.pool_pg.execute(query, *values)
        await ctx.checkmark()
    
    async def get_dm(self, user_id):
        user = self.client.get_user(user_id)
        if not (channel := user.dm_channel):
            channel = await user.create_dm()
        return channel