import random

import discord
from discord.ext import commands
from utils import checks
import asyncio
from PIL import Image, ImageFilter, ImageFont, ImageDraw
from io import BytesIO
import numpy as np
import os
import alexflipnote

alexflipnoteAPI = os.getenv('alexflipnoteAPI')

class Imgen(commands.Cog, name='imgen'):
    """
    Image Generation commands
    """
    def __init__(self, client):
        self.client = client
        self.alex_api = alexflipnote.Client()

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="goeatpoop")
    async def goeatpoop(self, ctx, member :discord.Member = None):
        """
        Get someone to eat poop
        """
        if member is None:
            return await ctx.send("mention someone lol")
        loop = asyncio.get_event_loop()
        ctxavatar = await ctx.author.display_avatar.with_format('png').read()
        member_avatar = await member.display_avatar.with_format('png').read()
        def generate():
            main = Image.open("assets/poop.png")
            ima = Image.open(BytesIO(ctxavatar), formats=['png']).convert('RGBA')
            ima = ima.resize((220 ,220))
            backg = main.copy()
            backg.paste(ima, (107, 218), ima)
            ima2 = Image.open(BytesIO(member_avatar)).convert('RGBA')
            ima2 = ima2.resize((227 ,227))
            backg.paste(ima2, (555 ,112), ima2)
            b = BytesIO()
            backg.save(b, format="png", optimize=True, quality=50)
            b.seek(0)
            file = discord.File(fp=b, filename="goeatpoop.jpg")
            return file
        file = await loop.run_in_executor(None, generate)
        await ctx.send(file=file)

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="stank")
    async def stank(self, ctx, member: discord.Member = None):
        """
        Someone's too stanky in here.
        """
        if member is None:
            return await ctx.send("mention someone lol")
        loop = asyncio.get_event_loop()
        member_avatar = await member.display_avatar.with_format('png').read()
        def generate():
            main = Image.open("assets/stankbase.png")
            backg = main.copy()
            ima2 = Image.open(BytesIO(member_avatar)).convert('RGBA')
            ima2 = ima2.resize((500,500))
            backg.paste(ima2, (535,575), ima2)
            main2 = Image.open("assets/stankbase_finger.png").convert('RGBA')
            backg.paste(main2, (556,281), main2)
            backg = backg.resize((500,500))
            b = BytesIO()
            backg.save(b, format="png", optimize=True, quality=25)
            b.seek(0)
            file = discord.File(fp=b, filename="stank.png")
            return file

        file = await loop.run_in_executor(None, generate)
        msg = await ctx.send(file=file)
        await msg.edit(f"To steal this emoji, go to your server and paste this in: `!steal {member.display_name}stank {msg.attachments[0].proxy_url}`")

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="audacity")
    async def audacity(self, ctx, member: discord.Member = None):
        """
        The Lion, The Witch, and the Audacity of-
        """
        if member is None:
            return await ctx.send("mention someone lol")
        loop = asyncio.get_event_loop()
        member_avatar = await member.display_avatar.with_format('png').read()
        def generate():
            main = Image.open("assets/audacity_cover.jpg")
            backg = main.copy()
            ima2 = Image.open(BytesIO(member_avatar)).convert('RGBA')
            ima2 = ima2.resize((184, 184))
            backg.paste(ima2, (1015, 117), ima2)
            font = ImageFont.truetype("assets/whitneysemibold.otf", size=60)
            image_editable = ImageDraw.Draw(backg)
            image_editable.text((657,573), member.display_name, (0,0,0), font=font)

            b = BytesIO()
            backg.save(b, format="png", optimize=True, quality=25)
            b.seek(0)
            file = discord.File(fp=b, filename="audacity.png")
            return file

        file = await loop.run_in_executor(None, generate)
        await ctx.send(file=file)

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name='annoy')
    async def annoy(self, ctx, member: discord.Member = None):
        """
        PLS STOP DMING ME
        """
        if member is None:
            return await ctx.send("mention someone lol")
        loop = asyncio.get_event_loop()
        member_avatar = await member.display_avatar.with_format('png').read()
        def generate():
            base = Image.open("assets/annoybase.jpg")
            avatar = Image.open(BytesIO(member_avatar)).convert('RGB')
            avatar = avatar.resize((96, 96))
            lum_img = Image.new('L', [96, 96], 0)
            draw = ImageDraw.Draw(lum_img)
            draw.pieslice([(0, 0), (96, 96)], 0, 360, fill=255, outline="white")
            img_arr = np.array(avatar)
            lum_img_arr = np.array(lum_img)
            final_img_arr = np.dstack((img_arr, lum_img_arr))
            new_ava = Image.fromarray(final_img_arr)
            base.paste(new_ava, (24, 164), new_ava)
            ping = Image.open('assets/ping.png')
            base.paste(ping, (52, 220), ping)
            b = BytesIO()
            base.save(b, format="png", optimize=True, quality=25)
            b.seek(0)
            file = discord.File(fp=b, filename="STOPDMINGME.png")
            return file
        file = await loop.run_in_executor(None, generate)
        await ctx.send(f"{member.display_name} STOP DMING 🤬🤬🤬", file=file)

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="captcha")
    async def captcha(self, ctx, *, text: str = None):
        """
        Generate a reCAPTCHA button with the specified text.
        """
        if text is None:
            additional_message = "You can specify what text to show in the reCAPTCHA button!"
            text = "I'm not a robot"
        else:
            additional_message = None
        recaptchaimage = await self.alex_api.captcha(text)
        image_bytes = await recaptchaimage.read()
        await ctx.send(additional_message, file=discord.File(fp=image_bytes, filename="reCAPTCHA.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="didyoumean", aliases=['dym', 'google'], usage="<2 texts separated by a comma>")
    async def didyoumean(self, ctx, *, text: str = None):
        """
        When you search for `text1` on Google, but they ask you if you meant `text2`...
        """
        if text is None or len(text.split(',')) < 2:
            return await ctx.send("You need to specify two texts that are separated by a comma.")
        text = text.split(',')
        text = [text[0][:50], ','.join(text[1:][:50])]
        didyoumeanimage = await self.alex_api.didyoumean(text[0], text[1])
        image_bytes = await didyoumeanimage.read()
        await ctx.send(file=discord.File(fp=image_bytes, filename="didyoumean.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="drake", usage="<2 texts separated by a comma>")
    async def drake(self, ctx, *, text: str = None):
        """
        I don't really know how to explain this meme... It's just the drake meme thing
        """
        if text is None or len(text.split(',')) < 2:
            return await ctx.send("You need to specify two texts that are separated by a comma.")
        text = text.split(',')
        text = [text[0][:50], ','.join(text[1:][:50])]
        image = await self.alex_api.drake(text[0], text[1])
        image_bytes = await image.read()
        await ctx.send(file=discord.File(fp=image_bytes, filename="drake.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="fact")
    async def fact(self, ctx, *, text: str = None):
        """
        IT IS A FACT!!!
        """
        if text is None:
            return await ctx.send("You need to specify a fact.")
        text = text[:50]
        image = await self.alex_api.facts(text)
        image_bytes = await image.read()
        await ctx.send(file=discord.File(fp=image_bytes, filename="fact.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="bad")
    async def bad(self, ctx, member: discord.Member = None):
        """
        you bad bad but a man is scolding you instead
        """
        if member == None:
            member = ctx.author
        avatar = member.display_avatar.with_format("png").url
        image = await self.alex_api.bad(avatar)
        image_bytes = await image.read()
        await ctx.send(file=discord.File(fp=image_bytes, filename="bad.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="what")
    async def what(self, ctx, member: discord.Member = None):
        """
        *sanctuary guardian music plays*
        """
        if member == None:
            member = ctx.author
        avatar = member.display_avatar.with_format("png").url
        image = await self.alex_api.what(avatar)
        image_bytes = await image.read()
        await ctx.send(file=discord.File(fp=image_bytes, filename="WHAT.png"))

    @checks.perm_insensitive_roles()
    @commands.command(name="spam")
    async def spam(self, ctx):
        """
        Bless yourself with these sacred images of spam. 🙏
        """
        imageint = random.randint(1, 74)
        allspams = os.listdir(f'assets/spams')
        image = None
        for file in allspams:
            if str(imageint) in file:
                image = file
        await ctx.send(file=discord.File(f"assets/spams/{image}"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="goeatpoop", description="Image generation | Get someone to eat poop")
    async def goeatpoop_slash(self, ctx, member: discord.Member):
        loop = asyncio.get_event_loop()
        ctxavatar = await ctx.author.display_avatar.with_format('png').read()
        member_avatar = await member.display_avatar.with_format('png').read()
        def generate():
            main = Image.open("assets/poop.png")
            ima = Image.open(BytesIO(ctxavatar), formats=['png']).convert('RGBA')
            ima = ima.resize((220, 220))
            backg = main.copy()
            backg.paste(ima, (107, 218), ima)
            ima2 = Image.open(BytesIO(member_avatar)).convert('RGBA')
            ima2 = ima2.resize((227, 227))
            backg.paste(ima2, (555, 112), ima2)
            b = BytesIO()
            backg.save(b, format="png", optimize=True, quality=50)
            b.seek(0)
            file = discord.File(fp=b, filename="goeatpoop.jpg")
            return file
        file = await loop.run_in_executor(None, generate)
        await ctx.respond(file=file)

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="stank", description="Image generation | Someone's too stanky in here.")
    async def stank_slash(self, ctx, member: discord.Member):
        loop = asyncio.get_event_loop()
        member_avatar = await member.display_avatar.with_format('png').read()

        def generate():
            main = Image.open("assets/stankbase.png")
            backg = main.copy()
            ima2 = Image.open(BytesIO(member_avatar)).convert('RGBA')
            ima2 = ima2.resize((500, 500))
            backg.paste(ima2, (535, 575), ima2)
            main2 = Image.open("assets/stankbase_finger.png").convert('RGBA')
            backg.paste(main2, (556, 281), main2)
            backg = backg.resize((500, 500))
            b = BytesIO()
            backg.save(b, format="png", optimize=True, quality=25)
            b.seek(0)
            file = discord.File(fp=b, filename="stank.png")
            return file

        file = await loop.run_in_executor(None, generate)
        await ctx.respond(file=file)

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="audacity", description="Image generation | The Lion, The Witch, and the Audacity of-")
    async def audacity_slash(self, ctx, member: discord.Member):
        loop = asyncio.get_event_loop()
        member_avatar = await member.display_avatar.with_format('png').read()

        def generate():
            main = Image.open("assets/audacity_cover.jpg")
            backg = main.copy()
            ima2 = Image.open(BytesIO(member_avatar)).convert('RGBA')
            ima2 = ima2.resize((184, 184))
            backg.paste(ima2, (1015, 117), ima2)
            font = ImageFont.truetype("assets/whitneysemibold.otf", size=60)
            image_editable = ImageDraw.Draw(backg)
            image_editable.text((657, 573), member.display_name, (0, 0, 0), font=font)

            b = BytesIO()
            backg.save(b, format="png", optimize=True, quality=25)
            b.seek(0)
            file = discord.File(fp=b, filename="audacity.png")
            return file

        file = await loop.run_in_executor(None, generate)
        await ctx.respond(file=file)

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name='annoy', description="Image generation | PLS STOP DMING ME")
    async def annoy_slash(self, ctx, member: discord.Member):
        loop = asyncio.get_event_loop()
        member_avatar = await member.display_avatar.with_format('png').read()

        def generate():
            base = Image.open("assets/annoybase.jpg")
            avatar = Image.open(BytesIO(member_avatar)).convert('RGB')
            avatar = avatar.resize((96, 96))
            lum_img = Image.new('L', [96, 96], 0)
            draw = ImageDraw.Draw(lum_img)
            draw.pieslice([(0, 0), (96, 96)], 0, 360, fill=255, outline="white")
            img_arr = np.array(avatar)
            lum_img_arr = np.array(lum_img)
            final_img_arr = np.dstack((img_arr, lum_img_arr))
            new_ava = Image.fromarray(final_img_arr)
            base.paste(new_ava, (24, 164), new_ava)
            ping = Image.open('assets/ping.png')
            base.paste(ping, (52, 220), ping)
            b = BytesIO()
            base.save(b, format="png", optimize=True, quality=25)
            b.seek(0)
            file = discord.File(fp=b, filename="STOPDMINGME.png")
            return file

        file = await loop.run_in_executor(None, generate)
        await ctx.respond(f"{member.display_name} STOP DMING 🤬🤬🤬", file=file)

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="captcha", description="Image generation | Generate a reCAPTCHA button with the specified text.")
    async def captcha_slash(self, ctx, *, text: str):
        recaptchaimage = await self.alex_api.captcha(text)
        image_bytes = await recaptchaimage.read()
        await ctx.respond(file=discord.File(fp=image_bytes, filename="reCAPTCHA.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="didyoumean", aliases=['dym', 'google'], description="Image generation | When you search for `text1` on Google, but they ask you if you meant `text2`...")
    async def didyoumean_slash(self, ctx, *, search_bar_text: str, did_you_mean_text: str):
        text = [search_bar_text[:50], did_you_mean_text[:50]]
        didyoumeanimage = await self.alex_api.didyoumean(text[0], text[1])
        image_bytes = await didyoumeanimage.read()
        await ctx.respond(file=discord.File(fp=image_bytes, filename="didyoumean.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="drake", description="Image generation | I don't really know how to explain this meme... It's just the drake meme thing")
    async def drake_slash(self, ctx, top_text: str, bottom_text: str):
        text = [top_text[:50], bottom_text[:50]]
        image = await self.alex_api.drake(text[0], text[1])
        image_bytes = await image.read()
        await ctx.respond(file=discord.File(fp=image_bytes, filename="drake.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="fact", description="Image generation | IT IS A FACT!!!")
    async def fact_slash(self, ctx, *, text: str):
        text = text[:50]
        image = await self.alex_api.facts(text)
        image_bytes = await image.read()
        await ctx.respond(file=discord.File(fp=image_bytes, filename="fact.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="bad", description="Image generation | you bad bad but a man is scolding you instead")
    async def bad_slash(self, ctx, member: discord.Member):
        avatar = member.display_avatar.with_format("png").url
        image = await self.alex_api.bad(avatar)
        image_bytes = await image.read()
        await ctx.respond(file=discord.File(fp=image_bytes, filename="bad.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="what", description="Image generation | *sanctuary guardian music plays*")
    async def what_slash(self, ctx, member: discord.Member):
        avatar = member.display_avatar.with_format("png").url
        image = await self.alex_api.what(avatar)
        image_bytes = await image.read()
        await ctx.respond(file=discord.File(fp=image_bytes, filename="WHAT.png"))

    @commands.slash_command(name="spam", description="Bless yourself with these sacred images of spam. 🙏")
    async def spam_slash(self, ctx):
        imageint = random.randint(1, 74)
        allspams = os.listdir(f'assets/spams')
        image = None
        for file in allspams:
            if str(imageint) in file:
                image = file
        await ctx.respond(file=discord.File(f"assets/spams/{image}"))