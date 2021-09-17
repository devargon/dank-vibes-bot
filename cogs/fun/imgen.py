import discord
from discord.ext import commands
from utils import checks
import asyncio
from PIL import Image, ImageFilter
from io import BytesIO

class imgen(commands.Cog):
    def __init__(self, client):
        self.client = client

    @checks.has_permissions_or_role(administrator=True)
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="goeatpoop")
    async def goeatpoop(self, ctx, member :discord.Member = None):
        """
        Get someone to eat poop
        """
        if member is None:
            return await ctx.send("mention someone lol")
        loop = asyncio.get_event_loop()
        ctxavatar = await ctx.author.display_avatar.read()
        member_avatar = await member.display_avatar.read()
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
        await ctx.send("If you don't understand the reference: <https://www.youtube.com/watch?v=M-PvB0NdO2g>",
                       file=file)

    @checks.has_permissions_or_role(administrator=True)
    @commands.cooldown(10, 1, commands.BucketType.user)
    @commands.command(name="goeatpoop")
    async def goeatpoop(self, ctx, member: discord.Member = None):
        """
        Get someone to eat poop
        """
        if member is None:
            return await ctx.send("mention someone lol")
        loop = asyncio.get_event_loop()
        ctxavatar = await ctx.author.display_avatar.read()
        member_avatar = await member.display_avatar.read()

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
        await ctx.send("If you don't understand the reference: <https://www.youtube.com/watch?v=M-PvB0NdO2g>",
                       file=file)

    @checks.dev()
    @commands.command(name="stank")
    async def stank(self, ctx, member: discord.Member = None):
        """
        Someone's too stanky in here.
        """
        if member is None:
            return await ctx.send("mention someone lol")
        loop = asyncio.get_event_loop()
        member_avatar = await member.display_avatar.read()
        def generate():
            main = Image.open("assets/stankbase.png")
            backg = main.copy()
            ima2 = Image.open(BytesIO(member_avatar)).convert('RGBA')
            ima2 = ima2.resize((400,400))
            backg.paste(ima2, (545,586), ima2)
            main2 = Image.open("assets/stankbase_finger.png").convert('RGBA')
            backg.paste(main2, (0,0), main2)
            backg = backg.resize((500,500))
            b = BytesIO()
            backg.save(b, format="png", optimize=True, quality=25)
            b.seek(0)
            file = discord.File(fp=b, filename="stank.png")
            return file

        file = await loop.run_in_executor(None, generate)
        await ctx.send(file=file)