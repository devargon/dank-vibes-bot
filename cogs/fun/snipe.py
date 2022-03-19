import discord
from discord.ext import commands
from utils import checks
import asyncio
from time import time
from typing import Optional
from utils.time import humanize_timedelta

blacklisted = ['discordnltro.com', 'discordairdrop.com', 'n1g@', 'http://discordnitro.click/gift/steam', 'nïgga',
               'https://steamdiscordnitro.ru/gift', 'https://dlscorcl.gift', '░', 'discord.qg', 'retard',
               'https://discordnitro.link/steam/gifts', 'send this to all servers you are in.', 'discordapp.click',
               'negga', '⠿', 'niqqer', 'nixgger', 're.tard', 'kyś', 'nibbas', 'nig||g||a', 'nergga', 'n.i.g.g.a',
               '||n||||i||||g||||g||||a||', 'neeger', 'n!gger', 'nigger', 'discond.ru.com', 'furfag', '⣿', 'nag gers',
               'frigger', 'nygga', 'r3tar d', 'discordsgift.com', 'discrodup', 'f||i||ggot', 'discordapp.me', 'neega',
               'noiga', 'steamsourcegame', 'r3tard', 'negro', 'dlcsorcl', 'steamcommunytu', 'n!g3r', 'tranny',
               '.ni.gga.', 'n|ggers', 'discordgifts.com', 'nigas', 'n1 66 er', 'n||oice ca||r', 'dlscordapp.info',
               'etard', 'phaggot', 'n1gər', 'n igger', 'send this to all the servers you are in', 'niglet', 'fagot',
               'niogger', 'n06g4s', 'dlscord.org', 'steamcomumunty', 'steamcommnuitry', 'kyfs', 'n1gga',
               'https://discordgift.ru.com/gift', '𓂺', 'https://discordnltro.com/steam/gift', 'ni||gg||a', 'пидарас',
               'n1ggä', 'https://discorcl.click/gift/b5xkymkdgtacxja', 'gleam.io', 'n!gga', 'discord.qq', 'nig gas',
               'https://dlscocrdapp.com/airdrop/nitro', 'http://discordglft.ru/gift', 'n1gger', 'dlscord', 'ñïbbä',
               'N1QQ3R', 'discordrgift.com', 'リ╎⊣⊣ᒷ∷', 'nirrger', 'nig||ht||', 'discorcl.click', 'n i g a', 'nidgga',
               'n¡gga', 'n1gg@', 'higgers', 'n||1g||||64||', 're tar d', 'giveawaynitro.com', 'discocrd.gift',
               'nitrogift', 'https://discordapp.click/settings/premium', 'migga', 'nighha', 'nìģêŕ', 'discordgive.com',
               'n||ig||ga', 'fa.g', 'nippa', 'nig a', 'kill yourself', 'n||a||gger', 'ni99er', 'retrded', 'n3bb4s',
               'n||a||ggers', 'fucktard', 'ni||ce', 'ni||ceca||r', 'steamsource',
               'hey, free discord gifted nitro for 1 month:', 'n I g g a', 'rxtarded', 'car||s', 'n!gg3r', 'nigg',
               'nigba', 'nebbas', 'nigfa', 'no664s', 'https://discordnitro.link/stearncommunity', 'ching chong',
               'nibba', 'steamdlscord', 'n||igg||4', 'https://dlscocrdapp.com', 'fags', 'nigga', 'discordc.gift',
               'n.i.g.g.e.r', 'n||ice ca||r', 'faggot', 'n!6g3r', 'n8gga', 'ni gger', 'niuggers', 'n1gg3rs', 'n iggers',
               'n||iceca||r', 'retarted', 'n!ggas', 'discordsteams.com', 'nltro', 'kýs', 'n!gg@', 'nlgga', 'nêģŕö',
               'nugga', 'f@g', '卐', 'nlgger', 'dlcsorcl.com']

class snipe(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.deleted_messages = {}
        self.edited_messages = {}
        self.removed_reactions = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id == 837627114659905566:
            return
        if message.author.bot:
            return
        if message.webhook_id:
            return
        data = {
            'author': message.author,
            'time': round(time()),
            'content': message.content,
            'image': message.attachments[0].proxy_url if message.attachments and message.attachments[0].content_type in ["image/apng", "image/gif", "image/jpeg", "image/png", "image/webp"] else None
        }
        self.deleted_messages[message.channel.id] = data


    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.channel.id == 837627114659905566:
            return
        if before.author.bot:
            return
        if before.webhook_id:
            return
        if before.content == after.content:
            return
        data = {
            'author': before.author,
            'time': round(time()),
            'content': before.content,
        }
        self.edited_messages[before.channel.id] = data

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        data = {
            'author': self.client.get_user(payload.user_id),
            'time': round(time()),
            'emoji': payload.emoji,
            'url': payload.emoji.url,
            'message': f"https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}"
        }
        self.removed_reactions[payload.channel_id] = data

    @checks.perm_insensitive_roles()
    @commands.command(name='snipe', aliases=['s'])
    async def snipe(self, ctx, channel: Optional[discord.TextChannel]):
        """
        "snipes" a deleted message, showing its content. Does not support `snipe <num>`.
        """
        if channel is None:
            channel = ctx.channel
        if channel.id not in self.deleted_messages:
            return await ctx.send("There's nothing to snipe here!")
        if not channel.permissions_for(ctx.author).view_channel:
            return await ctx.send("You can't view this channel.")
        snipedata = self.deleted_messages[channel.id]
        async def desc():
            blacklisted_words = await self.client.pool_pg.fetch("SELECT * FROM blacklisted_words")
            if any([i.get('string') in snipedata['content'] for i in blacklisted_words]):
                return "This message has a blacklisted word and cannot be shown."
            if snipedata['content'].lower().startswith('dv.hp') or snipedata['content'].lower().startswith('dv.hideping'):
                return "Ha, you got hidepinged!"
            else:
                content = snipedata['content']
                splitlines = content.split('\n')
                if len(splitlines) <= 1:
                    return content if len(content) < 2000 else content[:2000] + "..."
                else:
                    return '\n'.join(splitlines[:len(splitlines)]) if len(splitlines) < 20 else '\n'.join(splitlines[:20]) + "\n" + f"**... and another {len(splitlines) - 20} lines**"
        desc = await desc()
        embed = discord.Embed(title=f"Sniped message from {snipedata['author'].name} 🔫", description=desc, color=self.client.embed_color)
        if snipedata['content'].lower().startswith('dv.hp') or snipedata['content'].lower().startswith('dv.hideping'):
            embed.title = "Sniped message from someone..."
            embed.set_author(name='Someone...')
        else:
            embed.set_author(name=f"{snipedata['author']}", icon_url=snipedata['author'].display_avatar.url)
        embed.set_footer(text=f"Sniped in {humanize_timedelta(seconds=round(time())-snipedata['time'])}")
        if snipedata['image'] is not None:
            if ctx.guild.get_role(608495204399448066) in ctx.author.roles or ctx.guild.get_role(684591962094829569) in ctx.author.roles or ctx.author.guild_permissions.administrator==True:
                embed.set_image(url=snipedata['image'])
            else:
                embed.description += "\n\n[Image sent with message](https://www.youtube.com/watch?v=dQw4w9WgXcQ)"
        await ctx.send("Tip: To quickly snipe a message before they counter the snipe, use `dv.s` instead!" if 'snipe' in ctx.message.content else None, embed=embed)


    @checks.perm_insensitive_roles()
    @commands.command(name='editsnipe', aliases=['esnipe', 'es'])
    async def editsnipe(self, ctx, channel: Optional[discord.TextChannel]):
        """
        "snipes" an edited message, showing its unedited content. Does not support `snipe <num>`.
        """
        if channel is None:
            channel = ctx.channel
        if channel.id not in self.edited_messages:
            return await ctx.send("There's nothing to snipe here!")
        snipedata = self.edited_messages[channel.id]

        async def desc():
            blacklisted_words = await self.client.pool_pg.fetch("SELECT * FROM blacklisted_words")
            if any([i.get('string') in snipedata['content'] for i in blacklisted_words]):
                return "This message has a blacklisted word and cannot be shown."
            if 'dv.hp' in snipedata['content'].lower() or 'dv.hideping' in snipedata['content'].lower() or 'uwu hideping' in snipedata['content'].lower() or 'uwu hp' in snipedata['content'].lower():
                return "Ha, you got hidepinged!"
            else:
                content = snipedata['content']
                splitlines = content.split('\n')
                if len(splitlines) <= 1:
                    return content if len(content) < 2000 else content[:2000] + "..."
                else:
                    return '\n'.join(splitlines[:len(splitlines)]) if len(splitlines) < 20 else '\n'.join(splitlines[:20]) + "\n" + f"**... and another {len(splitlines) - 20} lines**"
        desc = await desc()
        embed = discord.Embed(title=f"Message edited by {snipedata['author'].name}", description=desc, color=self.client.embed_color)
        embed.set_author(name=f"{snipedata['author']}", icon_url=snipedata['author'].display_avatar.url)
        embed.set_footer(text=f"Edited {humanize_timedelta(seconds=round(time()) - snipedata['time'])} ago")
        await ctx.send(embed=embed)

    @checks.perm_insensitive_roles()
    @commands.command(name='reactionsnipe', aliases=['rsnipe', 'rs'])
    async def reactionsnipe(self, ctx, channel: Optional[discord.TextChannel]):
        """
        "snipes" a removed reaction. Does not support `snipe <num>`.
        """
        if channel is None:
            channel = ctx.channel
        if channel.id not in self.removed_reactions:
            return await ctx.send("No one has removed a reaction here.")
        snipedata = self.removed_reactions[channel.id]
        def emoji():
            for string in blacklisted:
                if string in str(snipedata['emoji']):
                    return "This emoji has a blacklisted name and cannot be shown.", "https://cdn.discordapp.com/attachments/616007729718231161/905702687566336013/DVB_False.png"
            return f"{snipedata['emoji'].name} (Emoji ID: {snipedata['emoji'].id})", snipedata['url']

        emoji = emoji()
        embed = discord.Embed(title=f"Sniped {snipedata['author'].name}'s reaction:", description=f"Emoji: {emoji[0]}\n\nThe message they reacted to: [Jump to message!]({snipedata['message']})", color=self.client.embed_color)
        embed.set_author(name=f"{snipedata['author']}", icon_url=snipedata['author'].display_avatar.url)
        embed.set_thumbnail(url=emoji[1])
        embed.set_footer(text=f"Reaction removed {humanize_timedelta(seconds=round(time()) - snipedata['time'])} ago")
        await ctx.send(embed=embed)