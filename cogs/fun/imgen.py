import discord
from discord.ext import commands
from utils import checks
import asyncio
from PIL import Image, ImageFilter, ImageFont, ImageDraw
from io import BytesIO
import numpy as np

class imgen(commands.Cog):
    def __init__(self, client):
        self.client = client

    @checks.requires_roles()
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

    @checks.requires_roles()
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

    @checks.requires_roles()
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

    @checks.requires_roles()
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