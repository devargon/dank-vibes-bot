import asyncio

import discord
from utils import checks
from discord.ext import commands
from utils.format import get_command_name
from utils.converters import BetterRoles, AllowDeny
import json
from utils.format import ordinal
from utils.buttons import confirm

def format_custom(text: str, member: discord.Member):
    text = text.replace('{member}', f"{member.name}#{member.discriminator}")
    text = text.replace('{member_mention}', member.mention)
    text = text.replace('{count}', ordinal(member.guild.member_count))
    return text

class Joining(commands.Cog):
    def __init__(self, client):
        self.client= client


    @commands.Cog.listener()
    async def on_member_join(self, member):
        join_message = await self.client.pool_pg.fetchrow("SELECT * FROM joinmessages WHERE guild_id = $1", member.guild.id)
        if join_message is None:
            return
        message_text = join_message.get('plain_text')
        if type(message_text) is str:
            message_text = format_custom(message_text, member)
        json_data = join_message.get('embed_details')
        if json_data is not None:
            json_data = format_custom(json_data, member)
            try:
                json_data = json.loads(json_data)
            except json.decoder.JSONDecodeError:
                json_data = None
        if join_message is None and json_data is None:
            return
        channel = self.client.get_channel(join_message.get('channel_id'))
        if channel is None:
            return
        try:
            await channel.send(message_text, embed=discord.Embed.from_dict(json_data) if json_data is not None else None, delete_after=join_message.get('delete_after'))
        except Exception as e:
            if "Missing Permissions" in str(e):
                return
            message_text += f"\n{e}"
            await channel.send(message_text, delete_after=join_message.get('delete_after'))
        else:
            return

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="joinmessage")
    async def joinmessage(self, ctx, channel: discord.TextChannel = None):
        """
        Interactive command to set the message set when members are joining. Do dv.help joinmessage for more information.
        Just specify a channel for the message to be sent, and the bot will guide you through.
        To remove the join message, do not include a channel in the command.
        This are the optional tags you can use when setting the text:
        `-` `{member}` shows the Username#Discriminator. Example: Argon#0002
        `-` `{member_mention}` shows the user but in a mention. Example: <@650647680837484556>
        `-` `{count}` shows the number of members after the user has joined. Example: 36121st
        """
        config = await self.client.pool_pg.fetchrow("SELECT * FROM joinmessages WHERE guild_id = $1", ctx.guild.id)
        confirmview = confirm(ctx, self.client, 30.0)
        if channel is None:
            if config is None:
                return await ctx.send("You don't have a message set when members join.")
            embed = discord.Embed(title="Action awaiting confirmation", description=f"Are you sure you want to **delete** the existing message configuration? To set a new configuration, use `dv.joinmessage <channel>` instead.", color=self.client.embed_color, timestamp=discord.utils.utcnow())
            message = await ctx.send(embed=embed, view=confirmview)
            confirmview.response = message
            await confirmview.wait()
            if confirmview.returning_value == True:
                embed.color, embed.description = discord.Color.green(), "The configuration has been deleted."
                await self.client.pool_pg.execute("DELETE FROM joinmessages WHERE guild_id = $1 and channel_id = $2", config.get('guild_id'), config.get('channel_id'))
            elif confirmview.returning_value == False:
                embed.color, embed.description = discord.Color.red(), "Action cancelled."
            elif confirmview.returning_value == None:
                embed.color, embed.description = discord.Color.red(), "You didn't respond."
            return await message.edit(embed=embed)
        if config is not None:
            embed = discord.Embed(title="Action awaiting confirmation", description=f"You already have an existing configuration set. Proceeding will overwrite the configuration at the end. Are you sure you want to proceed?", color=self.client.embed_color, timestamp=discord.utils.utcnow())
            message = await ctx.send(embed=embed, view=confirmview)
            confirmview.response = message
            await confirmview.wait()
            if confirmview.returning_value == True:
                embed.color, embed.description = discord.Color.green(), None
                await message.edit(embed=embed)
            elif confirmview.returning_value == False:
                embed.color, embed.description = discord.Color.red(), "Action cancelled."
                return await message.edit(embed=embed)
            elif confirmview.returning_value == None:
                embed.color, embed.description = discord.Color.red(), "You didn't respond."
                return await message.edit(embed=embed)
        templatemessage = await ctx.send("This message will be used to show the template. **Do not delete this message.**")
        questionmessage = await ctx.send("""Send the **text** message that will be sent when a member joins the server. If you do not want to specify a message, type 'none' instead. A text message can only have up to 2000 characters.
        This are the optional tags you can use when setting the text:
        `-` `{member}` shows the Username#Discriminator. Example: Argon#0002
        `-` `{member_mention}` shows the user but in a mention. Example: `<@650647680837484556>`
        `-` `{count}` shows the number of members after the user has joined. Example: 36121st""")
        def check(payload):
            return payload.author == ctx.author and payload.channel == ctx.channel
        try:
            response = await self.client.wait_for('message', check=check, timeout = 10.0*60.0)
        except asyncio.TimeoutError:
            return await ctx.send("Session stopped. If you had an existing configuration, it is still in place.")
        else:
            if len(response.content) > 2000:
                return await ctx.send("You sent a message that has more than 2000 characters. Please start again.")
            if 'none' in response.content.lower():
                await ctx.send("There will be no text message sent.")
                message_text = None
            else:
                message_text = response.content
                sample_text = format_custom(response.content, ctx.author)
                await templatemessage.edit(content=sample_text)
        await questionmessage.delete()
        questionmessage = await ctx.send("""Send the **embed** message in the form of a JSON that will be sent when a member joins the server. If you do not want to specify an embed, type 'none' instead.
                This are the optional tags you can use when setting the text:
                `-` `{member}` shows the Username#Discriminator. Example: Argon#0002
                `-` `{member_mention}` shows the user but in a mention. Example: `<@650647680837484556>`
                `-` `{count}` shows the number of members after the user has joined. Example: 36121st""")
        try:
            response = await self.client.wait_for('message', check=check, timeout=10.0 * 60.0)
        except asyncio.TimeoutError:
            return await ctx.send("Session stopped. If you had an existing configuration, it is still in place.")
        else:
            if 'none' in response.content.lower():
                await ctx.send("There will be no embed sent.")
                json_text = None
            else:
                if not (response.content.startswith('{') and response.content.endswith('}')):
                    return await ctx.send("Hmm... I don't think you sent a proper JSON for an embed. Please start again.")
                json_text = response.content
                try:
                    json.loads(json_text)
                except json.decoder.JSONDecodeError:
                    return await ctx.send("Hmm... I don't think you sent a proper JSON for an embed. Please start again. Ensure that there are brackets where you should've put them.")
                else:
                    try:
                        sample_json = response.content
                        sample_json = format_custom(sample_json, ctx.author)
                        sample_json = json.loads(sample_json)
                        await templatemessage.edit(embed=discord.Embed.from_dict(sample_json))
                    except Exception as e:
                        return await ctx.send(f"I got an error while trying to send. To prevent any further errors, please start again.\nError: {e}")
        await questionmessage.delete()
        questionmessage = await ctx.send("How long after (in seconds) do you want the message to be deleted? If you don't want the message to be deleted, send 0.")
        try:
            response = await self.client.wait_for('message', check=check, timeout=10.0 * 60.0)
        except asyncio.TimeoutError:
            return await ctx.send("Session stopped. If you had an existing configuration, it is still in place.")
        else:
            try:
                duration = int(response.content)
            except ValueError:
                return await ctx.send("You didn't enter a correct number. Please try again.")
            else:
                if duration == 0:
                    duration = None
        confirmview = confirm(ctx, self.client, 30.0)
        if json_text is None and message_text is None:
            return await ctx.send("You can't have both the message text and JSON be None.")
        embed = discord.Embed(title="Action awaiting confirmation",
                              description=f"Please check if this is how you want the message to be presented. If everything is in order, select Yes.",
                              color=self.client.embed_color, timestamp=discord.utils.utcnow())
        message = await templatemessage.reply(embed=embed, view=confirmview)
        confirmview.response = message
        await confirmview.wait()
        if confirmview.returning_value == True:
            embed.color, embed.description = discord.Color.green(), "The configuration has been successfully added!"
            if config is not None:
                await self.client.pool_pg.execute("UPDATE joinmessages SET channel_id = $1, plain_text = $2, embed_details = $3, delete_after = $4 WHERE guild_id = $5", channel.id, message_text, json_text, duration, ctx.guild.id)
            else:
                await self.client.pool_pg.execute("INSERT INTO joinmessages VALUES($1, $2, $3, $4, $5)", ctx.guild.id, channel.id, message_text, json_text, duration)
        elif confirmview.returning_value == False:
            embed.color, embed.description = discord.Color.red(), "Action cancelled. Please start over."
        elif confirmview.returning_value == None:
            embed.color, embed.description = discord.Color.red(), "You didn't respond. Please start over."
        return await message.edit(embed=embed)


