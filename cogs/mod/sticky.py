import discord
from utils import checks
from discord.ext import commands, menus
from utils.menus import CustomMenu
import json

class betcheck_pagination(menus.ListPageSource):
    def __init__(self, entries, title):
        self.title = title
        super().__init__(entries, per_page=20)

    async def format_page(self, menu, page):
        embed = discord.Embed(color=menu.ctx.bot.embed_color, title=self.title)
        embed.description = "\n".join(page)
        return embed

class Sticky(commands.Cog):
    def __init__(self, client):
        self.client= client


    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.client.guilds:
            result = await self.client.db.fetch("SELECT * FROM stickymessages WHERE guild_id = $1", guild.id)
            if len(result) == 0:
                pass
            for entry in result:
                channel = guild.get_channel(entry.get('channel_id'))
                if channel is not None and channel.last_message_id != entry.get('message_id'):
                    self.queue.append(channel)
                    try:
                        old_bot_message = await channel.fetch_message(entry.get('message_id'))
                    except discord.NotFound:
                        pass
                    else:
                        await old_bot_message.delete()
                    if entry.get('type') == 0:
                        embedjson = json.loads(entry.get('message'))
                        newmessage = await channel.send(embed=discord.Embed.from_dict(embedjson))
                    else:
                        newmessage = await channel.send(entry.get('message'))
                    await self.client.db.execute("UPDATE stickymessages SET message_id = $1 WHERE guild_id = $2 and channel_id = $3", newmessage.id, guild.id, channel.id)
                    self.queue.remove(channel)


    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if message.channel in self.queue:
                return
            if message.author == self.client.user:
                return
            if not message.guild:
                return
            result = await self.client.db.fetchrow("SELECT * FROM stickymessages WHERE guild_id = $1 and channel_id = $2", message.guild.id, message.channel.id)
            if result is None:
                return
            try:
                old_bot_message = await message.channel.fetch_message(result.get('message_id'))
            except discord.NotFound:
                self.queue.append(message.channel)
            else:
                self.queue.append(message.channel)
                await old_bot_message.delete()
            if result.get('type') == 0:
                embedjson = json.loads(result.get('message'))
                newmessage = await message.channel.send(embed=discord.Embed.from_dict(embedjson))
            else:
                newmessage = await message.channel.send(result.get('message'))
            await self.client.db.execute("UPDATE stickymessages SET message_id = $1 WHERE guild_id = $2 and channel_id = $3", newmessage.id, message.guild.id, message.channel.id)
            self.queue.remove(message.channel)
        except Exception as e:
            self.queue.remove(message.channel)

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name="sticky", invoke_without_command=True, aliases = ["stickymessage"])
    async def sticky(self, ctx):
        """
        Base command for managing sticky messages.
        """
        return await ctx.help()

    @checks.admoon()
    @sticky.command(name="resetlist")
    async def sticky_reset(self, ctx):
        """
        Resets the queue that contains channels for sticky messages.
        """
        await ctx.send(f"```py\n{self.queue}\n```")
        self.queue = []
        await ctx.send(f"The queue has been reset.")

    @checks.has_permissions_or_role(manage_roles=True)
    @sticky.command(name="create", alises=["add"])
    async def sticky_create(self, ctx, channel:discord.TextChannel=None, *, content=None):
        """
        Creates a sticky message for the specified channel. Only one sticky message can be created for one channel.
        To add an embed as a message, add it in the form of a JSON code which you can get from https://carl.gg/dashboard/595457764935991326/embeds.
        """
        if channel is None:
            return await ctx.send("`channel` is a required argument. `sticky create [channel] [content]`")
        if content is None:
            return await ctx.send(f"`content` is a required argument. `sticky create [channel] [content]`")
        existing = await self.client.db.fetch("SELECT * FROM stickymessages WHERE guild_id = $1 and channel_id = $2", ctx.guild.id, channel.id)
        if len(existing) > 0:
            return await ctx.send(f"You already have a sticky message set for {channel.mention}. Remove that sticky message with `` before adding a new sticky message.")
        if content.startswith('{') and content.endswith('}'):
            message_type = "embed"
        else:
            message_type = "text"
        if message_type == "text" and len(content) > 2000:
            return await ctx.send(f"Your message is currently {len(content)} characters long. It can only be 2000 characters long. Consider using a embed instead, as its description supports up to 4096 characters.")
        all = await self.client.db.fetch("SELECT * FROM stickymessages WHERE guild_id = $1", ctx.guild.id)
        if len(all) > 1:
            await ctx.send("You have already created **2** sticky messages with Dank Vibes Bot. To create more sticky messages, purchase Premium for Dank Vibes Bot. <http://premium.dvbot.nogra.me/>", delete_after = 3.0)
        if message_type == "embed":
            try:
                embedjson = json.loads(content)
            except json.decoder.JSONDecodeError:
                return await ctx.send(f"<:DVB_eyeroll:878146268277374976> You did not give me a proper JSON code. Get the JSON code directly from Carlbot's embed generator: https://cdn.nogra.me/core/embed.gif")
            else:
                try:
                    message = await channel.send(embed=discord.Embed.from_dict(embedjson))
                except discord.HTTPException as e:
                    return await ctx.send(
                        f"<:DVB_eyeroll:878146268277374976> You entered a JSON code, but Discord was not able to decode it. More details: `{e}`.\nGet the JSON code directly from Carlbot's embed generator: https://cdn.nogra.me/core/embed.gif")
                else:
                    await self.client.db.execute("INSERT INTO stickymessages VALUES($1, $2, $3, $4, $5)", ctx.guild.id, channel.id, message.id, 0, content)
                    return await ctx.send(f"<:DVB_checkmark:955345523139805214> I am now sending a sticky embed message in {channel.mention}.")
        elif message_type == "text":
            try:
                message = await channel.send(content)
            except discord.HTTPException as e:
                return await ctx.send(f"I was not able to add this sticky message. Details: `{e}`")
            else:
                await self.client.db.execute("INSERT INTO stickymessages VALUES($1, $2, $3, $4, $5)", ctx.guild.id, channel.id, message.id, 1, content)
                return await ctx.send(f"<:DVB_checkmark:955345523139805214> I am now sending a sticky message in {channel.mention}.")

    @checks.has_permissions_or_role(manage_roles=True)
    @sticky.command(name="remove", aliases=["delete"])
    async def sticky_remove(self, ctx, channel:discord.TextChannel=None):
        """
        Removes a sticky message that was set for the specified channel.
        """
        if channel is None:
            return await ctx.send(f"`channel` is a required argument. `sticky create [channel] [message_type] [content]`")
        existing = await self.client.db.fetch("SELECT * FROM stickymessages WHERE guild_id = $1 and channel_id = $2", ctx.guild.id, channel.id)
        if len(existing) == 0:
            return await ctx.send(f"You do not have a sticky message set for {channel.mention}.")
        await self.client.db.fetch("DELETE FROM stickymessages WHERE guild_id = $1 and channel_id = $2", ctx.guild.id, channel.id)
        return await ctx.send(f"<:DVB_checkmark:955345523139805214> The sticky message for {channel.mention} has been removed.")

    @checks.has_permissions_or_role(manage_roles=True)
    @sticky.command(name="view")
    async def sticky_view(self, ctx, channel:discord.TextChannel=None):
        """
        Shows you all the sticky messages set in this server.
        """
        if channel is not None:
            return await ctx.send(f"Lazy {ctx.author.display_name}, just go to the channel to see the message? {channel.mention}")
        result = await self.client.db.fetch("SELECT * FROM stickymessages WHERE guild_id = $1", ctx.guild.id)
        entries = []
        for row in result:
            channel = ctx.guild.get_channel(row.get('channel_id'))
            if channel is None:
                channel = f"**{row.get('channel_id')}**"
            type = "embed" if row.get('type') == 0 else "text"
            content = row.get('message').split("\n")[0]
            content = content[:32] + '...' if len(content) > 32 or len(row.get('message').split("\n")) > 1 else content
            if row.get('type') == 0:
                content = "<:DVB_embed:882268583571357736>"
            entries.append(f"• {channel} `({type})`: {content}")
        title = f"Sticky Messages in {ctx.guild.name}"
        pages = CustomMenu(source=betcheck_pagination(entries, title), clear_reactions_after=True, timeout=30)
        await pages.start(ctx)
