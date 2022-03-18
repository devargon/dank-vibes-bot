import imghdr
import re
from symbol import argument

import aiohttp
import discord
from discord.ext import commands

from utils import checks
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import numpy as np
import random
import os

url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #normal urls
        r'localhost|)' #localhoar
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class ImgenSlash(commands.Cog):
    def __init__(self, client):
        self.client = client

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="goeatpoop", description="Image generation | Get someone to eat poop")
    async def goeatpoop_slash(self, ctx,
                              member: discord.Option(discord.Member, "The member who you want to eat poop")):
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
    async def stank_slash(self, ctx,
                          member: discord.Option(discord.Member, "The member who is stinky")):
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
    async def audacity_slash(self, ctx, member: discord.Option(discord.Member, "The member who is being a b-")):
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
    @commands.slash_command(name='annoy', description="Image generation | Generate an image of someone being annoying in your DMs.")
    async def annoy_slash(self, ctx, member: discord.Option(discord.Member, "The member who is annoying you")):
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
    async def captcha_slash(self, ctx, *, text: discord.Option(str, "The text to show beside the recaptcha button.")):
        recaptchaimage = await self.alex_api.captcha(text)
        image_bytes = await recaptchaimage.read()
        await ctx.respond(file=discord.File(fp=image_bytes, filename="reCAPTCHA.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="didyoumean", aliases=['dym', 'google'], description="Image generation | When you search for `text1` on Google, but they ask you if you meant `text2`...")
    async def didyoumean_slash(self, ctx, *,
                               search_bar_text: discord.Option(str, "The phrase that you were searching on Google"),
                               did_you_mean_text: discord.Option(str, "What Google thought you meant")
                               ):
        text = [search_bar_text[:50], did_you_mean_text[:50]]
        didyoumeanimage = await self.alex_api.didyoumean(text[0], text[1])
        image_bytes = await didyoumeanimage.read()
        await ctx.respond(file=discord.File(fp=image_bytes, filename="didyoumean.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="drake", description="Image generation | I don't really know how to explain this meme... It's just the drake meme thing")
    async def drake_slash(self, ctx, top_text: discord.Option(str, "The top text that Drake doesn't like"), bottom_text: discord.Option(str, "The bottom text that Drake likes")):
        text = [top_text[:50], bottom_text[:50]]
        image = await self.alex_api.drake(text[0], text[1])
        image_bytes = await image.read()
        await ctx.respond(file=discord.File(fp=image_bytes, filename="drake.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="fact", description="Image generation | IT IS A FACT!!!")
    async def fact_slash(self, ctx, *, text: discord.Option(str, "The text that is a fact.")):
        text = text[:50]
        image = await self.alex_api.facts(text)
        image_bytes = await image.read()
        await ctx.respond(file=discord.File(fp=image_bytes, filename="fact.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="bad", description="Image generation | you bad bad but a man is scolding you instead")
    async def bad_slash(self, ctx, member: discord.Option(discord.Member, "The member who is misbehaving")):
        avatar = member.display_avatar.with_format("png").url
        image = await self.alex_api.bad(avatar)
        image_bytes = await image.read()
        await ctx.respond(file=discord.File(fp=image_bytes, filename="bad.png"))

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="what", description="Image generation | *sanctuary guardian music plays*")
    async def what_slash(self, ctx, member: discord.Option(discord.Member, "WHAT")):
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

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="spoiler", description="Image generation| Generates an image with a fake spoiler filter.", guild_ids = [871734809154707467])
    async def spoiler_tag(self, ctx,
                      member: discord.Option(discord.Member, "Spoiler someone's avatar!") = None,
                      link: discord.Option(str, "Spoiler an image via a link!") = None,
                      attachment: discord.Option(discord.Attachment, "Spoiler an image provided as an attachment!") = None):
        """
        Generates an image with a fake spoiler filter.
        """
        base_argument = None
        if member:
            base_argument = member
        if link:
            if base_argument is not None:
                return await ctx.respond("Do not provide more than one argument. Only enter a **member**, **link** or **attachment**.", ephemeral=True)
            base_argument = link
        if attachment:
            if base_argument is not None:
                return await ctx.respond("Do not provide more than one argument. Only enter a **member**, **link** or **attachment**.", ephemeral=True)
            base_argument = attachment
        if isinstance(base_argument, str):
            if re.match(url_regex, base_argument):
                async with aiohttp.ClientSession() as session:
                    async with session.get(base_argument) as resp:
                        if resp.status != 200:
                            return await ctx.send("The URL you provided is not valid.")
                        imagebytes = await resp.read()
                imagetype = imghdr.what(None, imagebytes)
                if imagetype is None:
                    return await ctx.send("The URL you provided is not an image.")
                return imagebytes
            else:
                return await ctx.send("You need to provide an image URL.")
        elif isinstance(base_argument, discord.Member):
            imagebytes = await argument.avatar.with_format("png").read()
        elif isinstance(base_argument, discord.Attachment):
            imagebytes = await base_argument.read()
            imagetype = imghdr.what(None, imagebytes)
            if imagetype is None:
                return await ctx.send("The image you provided is not valid.")
        else:
            return await ctx.send("An error occured, please try again.")
        im = Image.open(BytesIO(imagebytes)).convert('RGBA')
        im = im.filter(ImageFilter.GaussianBlur(radius=30))
        spoilerimage = Image.open('assets/spoilertag.png').convert('RGBA')
        s_width, s_height = spoilerimage.size
        width, height = im.size
        base_multiplier = 3.0
        multiplier = base_multiplier + ((width - 250) / 100 * 0.10)
        tag_width = int(width / multiplier)
        supposed_height = int(tag_width / s_width * s_height)
        if supposed_height > height:
            im.close()
            spoilerimage.close()
            return await ctx.send("The dimentions of this image make it impossible to add the spoiler tag.")
        else:
            center_x = width / 2
            center_y = height / 2
            spoilerimage = spoilerimage.resize((int(tag_width), int(supposed_height)))
            tag_position = (int(center_x - spoilerimage.size[0] / 2), int(center_y - spoilerimage.size[1] / 2))
            print(tag_position)
            im.paste(spoilerimage, tag_position, spoilerimage)
            b = BytesIO()
            im.save(b, 'png')
            b.seek(0)
            await ctx.respond(file=discord.File(fp=b, filename="spoiler.png"))
            im.close()
            spoilerimage.close()