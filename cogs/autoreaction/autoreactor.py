import re
import random
import discord
import asyncio
import contextlib
from utils import checks
from typing import Union
from utils.menus import CustomMenu
from discord.ext import commands
from utils.format import plural
from utils.errors import ArgumentBaseError
from cogs.autoreaction.ar_utils import get_ars

EMOJI_RE = re.compile(r"<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>")
UNICODE_RE = re.compile(r"(?:\U0001f1e6[\U0001f1e8-\U0001f1ec\U0001f1ee\U0001f1f1\U0001f1f2\U0001f1f4\U0001f1f6-\U0001f1fa\U0001f1fc\U0001f1fd\U0001f1ff])|(?:\U0001f1e7[\U0001f1e6\U0001f1e7\U0001f1e9-\U0001f1ef\U0001f1f1-\U0001f1f4\U0001f1f6-\U0001f1f9\U0001f1fb\U0001f1fc\U0001f1fe\U0001f1ff])|(?:\U0001f1e8[\U0001f1e6\U0001f1e8\U0001f1e9\U0001f1eb-\U0001f1ee\U0001f1f0-\U0001f1f5\U0001f1f7\U0001f1fa-\U0001f1ff])|(?:\U0001f1e9[\U0001f1ea\U0001f1ec\U0001f1ef\U0001f1f0\U0001f1f2\U0001f1f4\U0001f1ff])|(?:\U0001f1ea[\U0001f1e6\U0001f1e8\U0001f1ea\U0001f1ec\U0001f1ed\U0001f1f7-\U0001f1fa])|(?:\U0001f1eb[\U0001f1ee-\U0001f1f0\U0001f1f2\U0001f1f4\U0001f1f7])|(?:\U0001f1ec[\U0001f1e6\U0001f1e7\U0001f1e9-\U0001f1ee\U0001f1f1-\U0001f1f3\U0001f1f5-\U0001f1fa\U0001f1fc\U0001f1fe])|(?:\U0001f1ed[\U0001f1f0\U0001f1f2\U0001f1f3\U0001f1f7\U0001f1f9\U0001f1fa])|(?:\U0001f1ee[\U0001f1e8-\U0001f1ea\U0001f1f1-\U0001f1f4\U0001f1f6-\U0001f1f9])|(?:\U0001f1ef[\U0001f1ea\U0001f1f2\U0001f1f4\U0001f1f5])|(?:\U0001f1f0[\U0001f1ea\U0001f1ec-\U0001f1ee\U0001f1f2\U0001f1f3\U0001f1f5\U0001f1f7\U0001f1fc\U0001f1fe\U0001f1ff])|(?:\U0001f1f1[\U0001f1e6-\U0001f1e8\U0001f1ee\U0001f1f0\U0001f1f7-\U0001f1fb\U0001f1fe])|(?:\U0001f1f2[\U0001f1e6\U0001f1e8-\U0001f1ed\U0001f1f0-\U0001f1ff])|(?:\U0001f1f3[\U0001f1e6\U0001f1e8\U0001f1ea-\U0001f1ec\U0001f1ee\U0001f1f1\U0001f1f4\U0001f1f5\U0001f1f7\U0001f1fa\U0001f1ff])|\U0001f1f4\U0001f1f2|(?:\U0001f1f4[\U0001f1f2])|(?:\U0001f1f5[\U0001f1e6\U0001f1ea-\U0001f1ed\U0001f1f0-\U0001f1f3\U0001f1f7-\U0001f1f9\U0001f1fc\U0001f1fe])|\U0001f1f6\U0001f1e6|(?:\U0001f1f6[\U0001f1e6])|(?:\U0001f1f7[\U0001f1ea\U0001f1f4\U0001f1f8\U0001f1fa\U0001f1fc])|(?:\U0001f1f8[\U0001f1e6-\U0001f1ea\U0001f1ec-\U0001f1f4\U0001f1f7-\U0001f1f9\U0001f1fb\U0001f1fd-\U0001f1ff])|(?:\U0001f1f9[\U0001f1e6\U0001f1e8\U0001f1e9\U0001f1eb-\U0001f1ed\U0001f1ef-\U0001f1f4\U0001f1f7\U0001f1f9\U0001f1fb\U0001f1fc\U0001f1ff])|(?:\U0001f1fa[\U0001f1e6\U0001f1ec\U0001f1f2\U0001f1f8\U0001f1fe\U0001f1ff])|(?:\U0001f1fb[\U0001f1e6\U0001f1e8\U0001f1ea\U0001f1ec\U0001f1ee\U0001f1f3\U0001f1fa])|(?:\U0001f1fc[\U0001f1eb\U0001f1f8])|\U0001f1fd\U0001f1f0|(?:\U0001f1fd[\U0001f1f0])|(?:\U0001f1fe[\U0001f1ea\U0001f1f9])|(?:\U0001f1ff[\U0001f1e6\U0001f1f2\U0001f1fc])|(?:\U0001f3f3\ufe0f\u200d\U0001f308)|(?:\U0001f441\u200d\U0001f5e8)|(?:[\U0001f468\U0001f469]\u200d\u2764\ufe0f\u200d(?:\U0001f48b\u200d)?[\U0001f468\U0001f469])|(?:(?:(?:\U0001f468\u200d[\U0001f468\U0001f469])|(?:\U0001f469\u200d\U0001f469))(?:(?:\u200d\U0001f467(?:\u200d[\U0001f467\U0001f466])?)|(?:\u200d\U0001f466\u200d\U0001f466)))|(?:(?:(?:\U0001f468\u200d\U0001f468)|(?:\U0001f469\u200d\U0001f469))\u200d\U0001f466)|[\u2194-\u2199]|[\u23e9-\u23f3]|[\u23f8-\u23fa]|[\u25fb-\u25fe]|[\u2600-\u2604]|[\u2638-\u263a]|[\u2648-\u2653]|[\u2692-\u2694]|[\u26f0-\u26f5]|[\u26f7-\u26fa]|[\u2708-\u270d]|[\u2753-\u2755]|[\u2795-\u2797]|[\u2b05-\u2b07]|[\U0001f191-\U0001f19a]|[\U0001f1e6-\U0001f1ff]|[\U0001f232-\U0001f23a]|[\U0001f300-\U0001f321]|[\U0001f324-\U0001f393]|[\U0001f399-\U0001f39b]|[\U0001f39e-\U0001f3f0]|[\U0001f3f3-\U0001f3f5]|[\U0001f3f7-\U0001f3fa]|[\U0001f400-\U0001f4fd]|[\U0001f4ff-\U0001f53d]|[\U0001f549-\U0001f54e]|[\U0001f550-\U0001f567]|[\U0001f573-\U0001f57a]|[\U0001f58a-\U0001f58d]|[\U0001f5c2-\U0001f5c4]|[\U0001f5d1-\U0001f5d3]|[\U0001f5dc-\U0001f5de]|[\U0001f5fa-\U0001f64f]|[\U0001f680-\U0001f6c5]|[\U0001f6cb-\U0001f6d2]|[\U0001f6e0-\U0001f6e5]|[\U0001f6f3-\U0001f6f6]|[\U0001f910-\U0001f91e]|[\U0001f920-\U0001f927]|[\U0001f933-\U0001f93a]|[\U0001f93c-\U0001f93e]|[\U0001f940-\U0001f945]|[\U0001f947-\U0001f94b]|[\U0001f950-\U0001f95e]|[\U0001f980-\U0001f991]|\u00a9|\u00ae|\u203c|\u2049|\u2122|\u2139|\u21a9|\u21aa|\u231a|\u231b|\u2328|\u23cf|\u24c2|\u25aa|\u25ab|\u25b6|\u25c0|\u260e|\u2611|\u2614|\u2615|\u2618|\u261d|\u2620|\u2622|\u2623|\u2626|\u262a|\u262e|\u262f|\u2660|\u2663|\u2665|\u2666|\u2668|\u267b|\u267f|\u2696|\u2697|\u2699|\u269b|\u269c|\u26a0|\u26a1|\u26aa|\u26ab|\u26b0|\u26b1|\u26bd|\u26be|\u26c4|\u26c5|\u26c8|\u26ce|\u26cf|\u26d1|\u26d3|\u26d4|\u26e9|\u26ea|\u26fd|\u2702|\u2705|\u270f|\u2712|\u2714|\u2716|\u271d|\u2721|\u2728|\u2733|\u2734|\u2744|\u2747|\u274c|\u274e|\u2757|\u2763|\u2764|\u27a1|\u27b0|\u27bf|\u2934|\u2935|\u2b1b|\u2b1c|\u2b50|\u2b55|\u3030|\u303d|\u3297|\u3299|\U0001f004|\U0001f0cf|\U0001f170|\U0001f171|\U0001f17e|\U0001f17f|\U0001f18e|\U0001f201|\U0001f202|\U0001f21a|\U0001f22f|\U0001f250|\U0001f251|\U0001f396|\U0001f397|\U0001f56f|\U0001f570|\U0001f587|\U0001f590|\U0001f595|\U0001f596|\U0001f5a4|\U0001f5a5|\U0001f5a8|\U0001f5b1|\U0001f5b2|\U0001f5bc|\U0001f5e1|\U0001f5e3|\U0001f5e8|\U0001f5ef|\U0001f5f3|\U0001f6e9|\U0001f6eb|\U0001f6ec|\U0001f6f0|\U0001f930|\U0001f9c0|[#|0-9]\u20e3")
MENTION_RE = re.compile(r"<@(!?)([0-9]*)>")

class EmojiOrString(commands.Converter):
    async def convert(self, ctx, argument):
        args = argument.split()
        reactions = []
        if EMOJI_RE.match(args[0]) is not None or UNICODE_RE.match(args[0]) is not None:
            for arg in args:
                try:
                    emoji = await commands.EmojiConverter().convert(ctx, arg)
                    reaction = str(emoji)
                except commands.BadArgument:
                    emoji = UNICODE_RE.match(arg)
                    if emoji is not None:
                        reaction = emoji.group()
                    else:
                        emoji = EMOJI_RE.match(arg)
                        if emoji is not None:
                            raise ArgumentBaseError(message=f"I couldn't find {argument} in the server")
                        else:
                            continue
                reactions.append(reaction)
            return reactions
        else:
            return argument

class Autoreaction(commands.Cog, name='autoreaction'):
    """
    Auto Reaction commands
    """
    def __init__(self, client):
        self.client = client

    def cancerous_name(self, text: str):
        for word in text.split():
            for char in word:
                if not (char.isascii() and char.isalnum()):
                    return False
        return False

    @commands.group(aliases=['ar'], invoke_without_command=True)
    async def autoreact(self, ctx):
        """
        Base command for managing autoreactions.
        """
        return await ctx.help()

    @checks.has_permissions_or_role(administrator=True)
    @autoreact.command(name='add', aliases=['create', '+'], usage='<trigger> <response>')
    async def autoreact_add(self, ctx, trigger: str = None, *, responses: EmojiOrString = None):
        """
        Add an auto reaction for a mention or username.
        
        Required role: <@&608495204399448066> 
        """
        if trigger is None:
            return await ctx.send("Trigger is a required argument.")
        if responses is None:
            return await ctx.send("Response is a required argument.")
        trigger = trigger.lower()
        if (len(await self.client.pool_pg.fetch("SELECT response FROM autoreactions WHERE trigger=$1 AND guild_id=$2", *(trigger, ctx.guild.id))) != 0 ):
            return await ctx.send("I already have an autoreaction for that trigger.")
        query = "INSERT INTO autoreactions VALUES ($1, $2, $3)"
        if isinstance(responses, list):
            if len(responses) > 1:
                params = [(ctx.guild.id, trigger, response) for response in responses]
                await self.client.pool_pg.executemany(query, params)
            else:
                params = (ctx.guild.id, trigger, responses[0])
                await self.client.pool_pg.execute(query, *params)
        else:
            params = (ctx.guild.id, trigger, responses,)
            await self.client.pool_pg.execute(query, *params)
        return await ctx.send("Autoreaction added.")

    @autoreact.command(name='remove', aliases=['delete', '-'], usage='<trigger>')
    @checks.has_permissions_or_role(administrator=True)
    async def autoreact_remove(self, ctx, trigger: str = None):
        """
        Remove an auto reaction.
        
        Required role: <@&608495204399448066>
        """
        if trigger is None:
            return await ctx.send("Trigger is a required argument.")
        ar = await self.client.pool_pg.fetchrow("SELECT response FROM autoreactions WHERE trigger=$1 AND guild_id=$2", *(trigger, ctx.guild.id))
        if not ar:
            return await ctx.send("Looks like I don't have any reactions for that trigger.")
        await self.client.pool_pg.execute("DELETE FROM autoreactions WHERE trigger=$1 AND guild_id=$2", *(trigger, ctx.guild.id))
        await ctx.send('Autoreaction removed.')

    @commands.guild_only()
    @autoreact.command(name='claim', usage='<response>')
    @commands.cooldown(1, 1800, commands.BucketType.user)
    @checks.has_permissions_or_role(manage_messages=True)
    async def autoreact_claim(self, ctx, response: Union[discord.Emoji, str] = None):
        """
        Set your personal auto reaction.
        
        Cooldown: 30 minutes
        Required roles: <@&819998671742959636>, <@&645934789160992768>, <@&739199912377319427> or <@&847461305774243890>
        """
        if response is None:
            return await ctx.send("Response is a required argument.")
        if isinstance(response, discord.Emoji):
            reaction = str(response)
        else:
            emoji = UNICODE_RE.match(response)
            if emoji is not None:
                reaction = emoji.group()
            else:
                emoji = EMOJI_RE.match(response)
                if emoji is not None:
                    ctx.command.reset_cooldown(ctx)
                    return await ctx.send("I couldn't find that emoji in the server.")
                else:
                    ctx.command.reset_cooldown(ctx)
                    return await ctx.send(f"{response} is not a valid emoji", allowed_mentions=discord.AllowedMentions(roles=False, users=False))
        mention = True
        msg = None
        if (donor5b := ctx.guild.get_role(819998800382132265)) is not None and donor5b in ctx.author.roles:
            msg = await ctx.send(f"Which ar do you wanna change?\nReact with <:mention:870679716779163659> for mention or <:name:870679739524874312> for name.")
            for emoji in ['<:mention:870679716779163659>','<:name:870679739524874312>']:
                await msg.add_reaction(emoji)
            def check(payload):
                return payload.user_id == ctx.message.author.id and payload.channel_id == ctx.channel.id and payload.message_id == msg.id and str(payload.emoji) in ['<:mention:870679716779163659>','<:name:870679739524874312>']
            try:
                response = await self.client.wait_for('raw_reaction_add', timeout=15, check=check)
                if str(response.emoji) == '<:mention:870679716779163659>':
                    check_values = (f"<@!{ctx.author.id}>", ctx.guild.id) # Ar for mention
                elif str(response.emoji) == '<:name:870679739524874312>':
                    if self.cancerous_name(ctx.author.name):
                        ctx.command.reset_cooldown(ctx)
                        await msg.clear_reactions()
                        return await msg.edit(content="I can't set an autoreaction for that username.")
                    check_values = (f"{ctx.author.name.lower()}", ctx.guild.id)
                    mention = False # Ar for name
            except asyncio.TimeoutError:
                ctx.command.reset_cooldown(ctx)
                await msg.clear_reactions()
                return await msg.edit(content="You didn't react on time.")
        else:
            check_values = (f"<@!{ctx.author.id}>", ctx.guild.id)
        ar = await self.client.pool_pg.fetch("SELECT response FROM autoreactions WHERE trigger=$1 AND guild_id=$2", *check_values)
        query = "INSERT INTO autoreactions VALUES ($1, $2, $3)"
        value = (ctx.guild.id, f"<@!{ctx.author.id}>", reaction,) if mention else (ctx.guild.id, f"{ctx.author.name.lower()}", reaction)
        if len(ar) != 0:
            if ar[0].get('response') == reaction:
                if msg is not None:
                    await msg.clear_reactions()
                    ctx.command.reset_cooldown(ctx)
                    return await msg.edit(content=f"You already have that autoreaction for your {'mention' if mention else 'name'}.")
                ctx.command.reset_cooldown(ctx)
                return await ctx.send(f"You already have that autoreaction for your {'mention' if mention else 'name'}.")
            query = "UPDATE autoreactions SET response=$1 WHERE trigger=$2 AND guild_id=$3"
            value = (reaction, f"<@!{ctx.author.id}>", ctx.guild.id,) if mention else (reaction, f"{ctx.author.name.lower()}", ctx.guild.id)
        await self.client.pool_pg.execute(query, *value)
        if msg is not None:
            await msg.clear_reactions()
            return await msg.edit(content="Autoreaction added.")
        return await ctx.send("Autoreaction added.")

    @autoreact.command(name='clear')
    @commands.has_guild_permissions(administrator=True)
    async def autoreact_clear(self, ctx):
        """
        Clear all auto reactions from the server
        
        Required role: <@&663502776952815626>
        """
        ars = await self.client.pool_pg.fetch('SELECT DISTINCT trigger FROM autoreactions WHERE guild_id=$1', ctx.guild.id)
        if len(ars) == 0:
            return await ctx.send("This server does not have any autoreaction.")
        if ctx.channel.permissions_for(ctx.me).add_reactions:
            msg = await ctx.send(embed=discord.Embed(title="Confirmation",color=discord.Color.orange(), description=f"Are you sure you want to remove **ALL** autoreactions?\nThis will remove **{plural(len(ars)):autoreaction}**."))
            for emoji in ['✅','❌']:
                await msg.add_reaction(emoji)
            def check(payload):
                return payload.user_id == ctx.message.author.id and payload.channel_id == ctx.channel.id and payload.message_id == msg.id and str(payload.emoji) in ['✅','❌']
            try:
                reaction = await self.client.wait_for('raw_reaction_add', timeout=15, check=check)
                if str(reaction.emoji) == '✅':
                    await self.client.pool_pg.execute("DELETE FROM autoreactions WHERE guild_id=$1", ctx.guild.id)
                    embed = discord.Embed(title='Deleted', color=discord.Color.green(), description=f"Successfully removed **{plural(len(ars)):autoreaction}**.")
                    try:
                        await msg.edit(embed=embed)
                    except discord.NotFound:
                        await ctx.send(embed=embed)
                    except Exception as e:
                        await ctx.send_error(e)
                    return await msg.clear_reactions()
                elif str(reaction.emoji) == '❌':
                    embed = discord.Embed(title='Cancelled', color=discord.Color.red(), description=f"Autoreactions will not be deleted.")
                    try:
                        await msg.edit(embed=embed)
                    except discord.NotFound:
                        await ctx.send(embed=embed)
                    return await msg.clear_reactions()
            except asyncio.TimeoutError:
                embed = msg.embeds[0]
                embed.color = discord.Color.red()
                await msg.edit(embed=embed)
                return await msg.clear_reactions()
        else:
            return await ctx.send("I need `Add Reactions` perms to do that.")

    @autoreact.command(name='list')
    @checks.has_permissions_or_role(administrator=True)
    async def autoreact_list(self, ctx):
        """
        View a full list of all auto reactions in the server
        
        Required role: <@&608495204399448066>
        """
        ars = await self.client.pool_pg.fetch("SELECT DISTINCT trigger FROM autoreactions WHERE guild_id=$1", ctx.guild.id)
        if len(ars) == 0:
            return await ctx.send("This server does not have any autoreaction.")
        pages = CustomMenu(source=get_ars(ars, ctx.guild, self.client.embed_color), clear_reactions_after=True, timeout=60)
        await pages.start(ctx)
        return await ctx.checkmark()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        if message.author.bot:
            return
        triggers = await self.client.pool_pg.fetch("SELECT DISTINCT trigger FROM autoreactions WHERE guild_id=$1", message.guild.id)
        if len(triggers) == 0:
            return
        if not message.channel.permissions_for(message.guild.me).add_reactions:
            return
        for trigger in triggers:
            msgcontent = message.content.lower()
            if trigger.get('trigger') in msgcontent:
                responses = await self.client.pool_pg.fetch("SELECT response FROM autoreactions WHERE guild_id=$1 AND trigger=$2", *(message.guild.id, trigger[0]))
                if len(responses) > 1:
                    response = random.choice(responses)
                else:
                    response = responses[0]
                response = response.get('response')
                if EMOJI_RE.match(response) or UNICODE_RE.match(response):
                    try:
                        return await message.add_reaction(response)
                    except discord.HTTPException as error:
                        if error.status == 400:
                            await self.client.pool_pg.execute("DELETE FROM autoreactions WHERE guild_id=$1 AND trigger=$2 AND response=$3", *(message.guild.id, trigger.get('trigger'), response))
                        return
                else:
                    with contextlib.suppress(discord.HTTPException):
                        return await message.channel.send(response)