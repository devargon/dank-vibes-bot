import imghdr
import math
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

from utils.format import proper_userf
from utils.errors import ArgumentBaseError

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
    @commands.slash_command(name="spoiler", description="Image generation| Generates an image with a fake spoiler filter.")
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
                            return await ctx.respond("The URL you provided is not valid.", ephemeral=True)
                        imagebytes = await resp.read()
                imagetype = imghdr.what(None, imagebytes)
                if imagetype is None:
                    return await ctx.respond("The URL you provided is not an image.", ephemeral=True)
            else:
                return await ctx.respond("You need to provide an image URL.", ephemeral=True)
        elif isinstance(base_argument, discord.Member):
            imagebytes = await base_argument.display_avatar.with_format("png").read()
        elif isinstance(base_argument, discord.Attachment):
            imagebytes = await base_argument.read()
            imagetype = imghdr.what(None, imagebytes)
            if imagetype is None:
                return await ctx.respond("The image you provided is not valid.", ephemeral=True)
        else:
            return await ctx.respond("An error occured, please try again.", ephemeral=True)
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
                raise ArgumentBaseError(message="The dimensions of the image you provided make it impossible to add the spoiler tag.")
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
        return await ctx.respond(file=file, ephemeral=False)

    @checks.perm_insensitive_roles()
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.slash_command(name="ebay", description="Image generation | Sell someone - a random stranger, or a friend - on eBay.")
    async def spoiler_tag(self, ctx, member: discord.Option(discord.Member, "The user you want to sell on eBay")):
        """
        Sell someone - a random stranger, or a friend - on eBay.
        """
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
            name = f"{proper_userf(member)} {brackets}"
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
        return await ctx.respond(file=file, ephemeral=False)