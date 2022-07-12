import imghdr
import math
import random
import re
from typing import Optional, Union

import aiohttp
import discord
from discord.ext import commands
from emoji import UNICODE_EMOJI

from utils import checks
import asyncio
from PIL import Image, ImageFilter, ImageFont, ImageDraw
from io import BytesIO
import numpy as np
import os
import alexflipnote

from utils.errors import ArgumentBaseError
from .imgen_slash import ImgenSlash
url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #normal urls
        r'localhost|)' #localhoar
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


alexflipnoteAPI = os.getenv('alexflipnoteAPI')

class Imgen(ImgenSlash, commands.Cog, name='imgen'):
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
    @commands.command(name="spoiler")
    async def spoiler(self, ctx, argument: Union[discord.Emoji, discord.PartialEmoji, discord.Member, str] = None):
        """
        Generates an image with a fake spoiler filter.
        """
        if argument is None:
            if len(ctx.message.attachments) > 0:
                imagebytes = await ctx.message.attachments[0].read()
            else:
                return await ctx.send("You need to provide an attachment, emoji, image URL or mention a user.")
        elif isinstance(argument, str):
            if re.match(url_regex, argument):
                async with aiohttp.ClientSession() as session:
                    async with session.get(argument) as resp:
                        if resp.status != 200:
                            return await ctx.send("The URL you provided is not valid.")
                        imagebytes = await resp.read()
                imagetype = imghdr.what(None, imagebytes)
                if imagetype is None:
                    return await ctx.send("The URL you provided is not an image.")
            else:
                return await ctx.send("You need to provide an custom emoji, image (as an attachment or URL), or mention someone.")
        elif isinstance(argument, discord.Emoji) or isinstance(argument, discord.PartialEmoji):
            imagebytes = await argument.read()
        else:
            imagebytes = await argument.display_avatar.with_format("png").read()
        imagetype = imghdr.what(None, imagebytes)
        if imagetype is None:
            return await ctx.send("The image you provided is not valid.")
        def generate():
            im = Image.open(BytesIO(imagebytes)).convert('RGBA')
            im = im.filter(ImageFilter.GaussianBlur(radius=30))
            spoilerimage = Image.open('assets/spoilertag.png').convert('RGBA')
            s_width, s_height = spoilerimage.size
            width, height = im.size
            base_multiplier = 3.0
            multiplier = base_multiplier + ((width - 250)/100*0.10)
            tag_width = int(width / multiplier)
            supposed_height = int(tag_width/s_width * s_height)
            if supposed_height > height:
                im.close()
                spoilerimage.close()
                raise ArgumentBaseError(message="the dimensions of the image you provided make it impossible to add the spoiler tag.")
            else:
                center_x = width / 2
                center_y = height / 2
                spoilerimage = spoilerimage.resize((int(tag_width), int(supposed_height)))
                tag_position = (int(center_x - spoilerimage.size[0] / 2), int(center_y - spoilerimage.size[1] / 2))
                im.paste(spoilerimage, tag_position, spoilerimage)
                b = BytesIO()
                im.save(b, 'png')
                b.seek(0)
                im.close()
                spoilerimage.close()
                file = discord.File(b, filename="spoiler.png")
                return file
        loop = asyncio.get_event_loop()
        file = await loop.run_in_executor(None, generate)
        await ctx.send(file=file)

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="ebay")
    async def ebay(self, ctx, member: discord.Member = None):
        """
        Sell someone - a random stranger, or a friend - on eBay.
        """
        if member is None:
            return await ctx.send("mention someone lol")
        loop = asyncio.get_event_loop()
        member_avatar = await member.display_avatar.with_format('png').read()

        def generate():
            def comma_number(number: int):
                return "{:,}".format(number)

            def short_time(duration: int):
                if duration is None or duration < 1:
                    return ''
                duration_in_mins = duration / 60
                if duration_in_mins < 1:
                    return '< 1m'
                if duration_in_mins < 60:
                    return f'{math.ceil(duration_in_mins)}m'
                duration_in_hours = duration_in_mins / 60
                if duration_in_hours < 1.017:
                    return '1h'
                if duration_in_hours < 24:
                    return f'{math.ceil(duration_in_hours)}h'
                duration_in_days = duration_in_hours / 24
                if duration_in_days < 1.05:
                    return '1d'
                else:
                    return f'{math.ceil(duration_in_days)}d'

            template = 'assets/ebay_app.png'

            username = member.display_name
            brackets = random.choice(["(LIMITED)", "(SUSSY)", "(SUPER SUSSY)"])
            name = f"{member} {brackets}"
            proper_name = name if len(name) < 28 else name[:25] + '...'
            description = 'Pre-Owned · Sussy · Amogus · Baka'
            number_of_bids = random.choice([0, 0, 0, random.randint(1, 1000000)])
            duration = random.randint(1, 31536000)
            bid_and_duration = f"{comma_number(number_of_bids)} bids · {short_time(duration)}"
            shipping_random = random.uniform(0, 100)
            shipping = random.choice(["Free shipping", "+${:,.2f} shipping estimate".format(shipping_random)])
            all_countries = ['United States', 'Afghanistan', 'Albania', 'Algeria', 'American Samoa', 'Andorra',
                             'Angola',
                             'Anguilla', 'Antarctica', 'Antigua And Barbuda', 'Argentina', 'Armenia', 'Aruba',
                             'Australia',
                             'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belarus',
                             'Belgium',
                             'Belize', 'Benin', 'Bermuda', 'Bhutan', 'Bolivia', 'Bosnia And Herzegowina', 'Botswana',
                             'Bouvet Island', 'Brazil', 'Brunei Darussalam', 'Bulgaria', 'Burkina Faso', 'Burundi',
                             'Cambodia', 'Cameroon', 'Canada', 'Cape Verde', 'Cayman Islands', 'Central African Rep',
                             'Chad', 'Chile', 'China', 'Christmas Island', 'Cocos Islands', 'Colombia', 'Comoros',
                             'Congo',
                             'Cook Islands', 'Costa Rica', 'Cote D`ivoire', 'Croatia', 'Cuba', 'Cyprus',
                             'Czech Republic',
                             'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic', 'East Timor', 'Ecuador', 'Egypt',
                             'El Salvador', 'Equatorial Guinea', 'Eritrea', 'Estonia', 'Ethiopia',
                             'Falkland Islands (Malvinas)', 'Faroe Islands', 'Fiji', 'Finland', 'France',
                             'French Guiana',
                             'French Polynesia', 'French S. Territories', 'Gabon', 'Gambia', 'Georgia', 'Germany',
                             'Ghana',
                             'Gibraltar', 'Greece', 'Greenland', 'Grenada', 'Guadeloupe', 'Guam', 'Guatemala', 'Guinea',
                             'Guinea-bissau', 'Guyana', 'Haiti', 'Honduras', 'Hong Kong', 'Hungary', 'Iceland', 'India',
                             'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel', 'Italy', 'Jamaica', 'Japan', 'Jordan',
                             'Kazakhstan', 'Kenya', 'Kiribati', 'Korea (North)', 'Korea (South)', 'Kuwait',
                             'Kyrgyzstan',
                             'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania',
                             'Luxembourg', 'Macau', 'Macedonia', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali',
                             'Malta', 'Marshall Islands', 'Martinique', 'Mauritania', 'Mauritius', 'Mayotte', 'Mexico',
                             'Micronesia', 'Moldova', 'Monaco', 'Mongolia', 'Montserrat', 'Morocco', 'Mozambique',
                             'Myanmar', 'Namibia', 'Nauru', 'Nepal', 'Netherlands', 'Netherlands Antilles',
                             'New Caledonia',
                             'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'Niue', 'Norfolk Island',
                             'Northern Mariana Islands', 'Norway', 'Oman', 'Pakistan', 'Palau', 'Panama',
                             'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Pitcairn', 'Poland', 'Portugal',
                             'Puerto Rico', 'Qatar', 'Reunion', 'Romania', 'Russian Federation', 'Rwanda',
                             'Saint Kitts And Nevis', 'Saint Lucia', 'St Vincent/Grenadines', 'Samoa', 'San Marino',
                             'Sao Tome', 'Saudi Arabia', 'Senegal', 'Seychelles', 'Sierra Leone', 'Singapore',
                             'Slovakia',
                             'Slovenia', 'Solomon Islands', 'Somalia', 'South Africa', 'Spain', 'Sri Lanka',
                             'St. Helena',
                             'St.Pierre', 'Sudan', 'Suriname', 'Swaziland', 'Sweden', 'Switzerland',
                             'Syrian Arab Republic',
                             'Taiwan', 'Tajikistan', 'Tanzania', 'Thailand', 'Togo', 'Tokelau', 'Tonga',
                             'Trinidad And Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda', 'Ukraine',
                             'United Arab Emirates', 'United Kingdom', 'Uruguay', 'Uzbekistan', 'Vanuatu',
                             'Vatican City State', 'Venezuela', 'Viet Nam', 'Virgin Islands (British)',
                             'Virgin Islands (U.S.)', 'Western Sahara', 'Yemen', 'Yugoslavia', 'Zaire', 'Zambia',
                             'Zimbabwe']

            location = f"from {random.choice(all_countries)}"
            price_random = random.uniform(0, 500)
            price = random.choice(["$0.00", "$0.00", "$0.99", "${:,.2f}".format(price_random)])

            template = Image.open(template).convert('RGBA')
            profile_picture = Image.open(BytesIO(member_avatar)).convert('RGBA')

            background = template.copy()
            profile_picture_resized = profile_picture.resize((287, 287))
            background.paste(profile_picture_resized, (50, 1134), profile_picture_resized)

            image_editable = ImageDraw.Draw(background)
            helvetica_search = ImageFont.truetype("assets/Helvetica.ttf", size=44)
            helvetica_description = ImageFont.truetype("assets/Helvetica.ttf", size=36)
            marketsans_name = ImageFont.truetype("assets/MarketSans.ttf", size=39)
            marketsans_price = ImageFont.truetype("assets/MarketSans.ttf", size=43)
            helvetica_details = ImageFont.truetype("assets/Helvetica.ttf", size=32)

            image_editable.point((95, 498), fill="#ff0000")
            image_editable.text((95, 498), username, fill="black", anchor="ls", font=helvetica_search)
            image_editable.text((425, 1122), proper_name, fill="black", anchor="ls", font=marketsans_name)
            image_editable.text((425, 1179), description, fill="#707070", anchor="ls", font=helvetica_description)
            image_editable.text((425, 1282), price, fill="black", anchor="ls", font=marketsans_price)
            image_editable.text((425, 1343), bid_and_duration, fill="#707070", anchor="ls", font=helvetica_details)
            image_editable.text((425, 1391), shipping, fill="#707070", anchor="ls", font=helvetica_details)
            image_editable.text((425, 1439), location, fill="#707070", anchor="ls", font=helvetica_details)
            b = BytesIO()
            background.save(b, format="png", optimize=True, quality=25)
            b.seek(0)
            file = discord.File(fp=b, filename="stank.png")
            return file
        file = await loop.run_in_executor(None, generate)
        await ctx.send(file=file)
