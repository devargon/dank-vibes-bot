import json
import discord
import selenium
from selenium import webdriver
import os
import ssl, socket
from urllib.parse import urlparse
import re
from discord.ext import commands
from io import BytesIO
import asyncio
import time
from utils import checks

#Checking if provided link is indeed a link
regex = re.compile(
        r'^https?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|)'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class BrowserScreenshot(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.cooldown(1, 30.0, commands.BucketType.guild)
    @checks.has_permissions_or_role(manage_roles=True)
    @commands.command(name="browser", aliases=["screenshot", "ss"])
    async def screenshot(self, ctx, link):
        """
        Gets the screenshot of a website. Any website can be specified.
        You are not allowed to use this command to get private information about the bot, such as IP addresses, locations, and the bot's server's specifications. Doing so will result in a command blacklist.
        """
        loop = asyncio.get_event_loop()
        self.is_processing = True
        check = re.match(regex, link) is not None
        if not check:
            return await ctx.send("You did not give a proper link. Links should start with `http://` or `https://`.")
        if "dQw4w9WgXcQ" in link and "youtu" in link:
            return await ctx.send("You should just open this website yourself lol")
        domain = urlparse(link).netloc
        filename = (f'screenshot_{domain}_{time.time()}.png')
        if os.path.exists(filename):
            return await ctx.send("Apparently, a website screenshot is currently being processed by another command. Please wait until that screenshot has been processed. If it has been a long time, and this is still showing up, please notify the developer.")
        message = await ctx.send(embed = discord.Embed(title=f"Website details for {domain}", description=f"__**Status**__\n<:DVB_start_complete:895172800627769447> Start Google Chrome\n<:DVB_middle_incomplete:895172800430620742> **Connecting to linked website**\n<:DVB_middle_incomplete:895172800430620742> **Getting screenshot of website**\n<:DVB_end_incomplete:895172799923109919> Getting SSL Certificate information of {domain}", timestamp=discord.utils.utcnow(), color=self.client.embed_color).set_footer(icon_url="https://camo.githubusercontent.com/74ed64243ba05754329bc527cd4240ebd1c087a1/68747470733a2f2f73656c656e69756d2e6465762f696d616765732f73656c656e69756d5f6c6f676f5f7371756172655f677265656e2e706e67", text="Powered by Selenium | This process could take up to 30 seconds."))
        async with ctx.typing():
            def open_browser():
                try:
                    #asyncio.run(msgsend(ctx, "Starting web browser..."))
                    #WGET THE CHROME DRIVER OR IT WILL NOT WORK
                    if os.getenv('state') == '1':
                        browser = webdriver.Chrome(r"C:\Users\laiye\Downloads\chromedriver.exe", options=self.op)
                    else:
                        browser = webdriver.Chrome(options=self.op)
                except selenium.common.exceptions.SessionNotCreatedException as e:
                    if "This version of ChromeDriver only supports" in str(e):
                        return "The version of Chrome used on this device is not matched with ChromeDriver. Please notify the developer about this."
                else:
                    return browser
            browser = await loop.run_in_executor(None, open_browser)
            if type(browser) == str:
                return await message.edit(embed=discord.Embed(title=message.embeds[0].title, description=browser, color=self.client.embed_color, timestamp=discord.utils.utcnow()))
            await message.edit(embed = discord.Embed(title=f"Website details for {domain}", description=f"__**Status**__\n<:DVB_start_complete:895172800627769447> Start Google Chrome\n<:DVB_middle_complete:895172800627769444> **Connecting to linked website**\n<:DVB_middle_incomplete:895172800430620742> **Getting screenshot of website**\n<:DVB_end_incomplete:895172799923109919> Getting SSL Certificate information of {domain}", timestamp=discord.utils.utcnow(), color=self.client.embed_color).set_footer(icon_url="https://camo.githubusercontent.com/74ed64243ba05754329bc527cd4240ebd1c087a1/68747470733a2f2f73656c656e69756d2e6465762f696d616765732f73656c656e69756d5f6c6f676f5f7371756172655f677265656e2e706e67", text="Powered by Selenium | This process could take up to 30 seconds."))
            def get_to_website():
                    try:
                        browser.get(link)
                    except Exception as e:
                        if "ERR_CONNECTION_TIMED_OUT" in str(e):
                            return f"**This site can't be reached**;\n`{domain}` took too long to respond.\n`ERR_CONNECTION_TIMED_OUT`"
                        elif "ERR_CERT_DATE_INVALID" in str(e):
                            return "**Please inform the developer about this.**\n`ERR_CERT_DATE_INVALID`"
                        elif "ERR_CERT_AUTHORITY_INVALID" in str(e) or "ERR_CERT_COMMON_NAME_INVALID" in str(e) or "ERR_CERT_WEAK_SIGNATURE_ALGORITHM" in str(e) or "ERR_CERTIFICATE_TRANSPARENCY_REQUIRED" in str(e):
                            return f"**Your connection to this website is not private.**\nClick `Advanced` for more information."
                        elif "ERR_TOO_MANY_REDIRECTS" in str(e):
                            return f"**This page isn't working**\n{domain} redirected you too many times. "
                        elif "ERR_NAME_NOT_RESOLVED" in str(e):
                            return f"**This site can't be reached**\n{domain}'s server DNS address could not be found. *This may mean that the website does not exist.*"
                        else:
                            return f"**Error encountered!** <@650647680837484556>\m{e}"
                    else:
                        return None
            result = await loop.run_in_executor(None, get_to_website)
            if result is not None:
                if "CERT" in result:
                    class View(discord.ui.View):
                        def __init__(self, ctx):
                            super().__init__(timeout=60)
                        @discord.ui.button(label='Advanced', style=discord.ButtonStyle.blurple)
                        async def freecoins(self, button: discord.ui.Button, interaction: discord.Interaction):
                            await interaction.response.send_message(f"{domain} normally uses encryption to protect your information. When Google Chrome tried to connect to {domain} this time, the website sent back unusual and incorrect credentials. This may happen when an attacker is trying to pretend to be {domain}, or a Wi-Fi sign-in screen has interrupted the connection. Your information is still secure because Google Chrome stopped the connection before any data was exchanged.\n\nYou cannot visit {domain} at the moment because the website sent scrambled credentials that Google Chrome cannot process. Network errors and attacks are usually temporary, so this page will probably work later.", ephemeral=True)
                else:
                    View = None
                return await message.edit(embed=discord.Embed(title=message.embeds[0].title, description=result, color=self.client.embed_color, timestamp=discord.utils.utcnow()), view=View)
            await message.edit(embed=discord.Embed(title=f"Website details for {domain}", description=f"__**Status**__\n<:DVB_start_complete:895172800627769447> Start Google Chrome\n<:DVB_middle_complete:895172800627769444> **Connecting to linked website**\n<:DVB_middle_complete:895172800627769444> **Getting screenshot of website**\n<:DVB_end_incomplete:895172799923109919> Getting SSL Certificate information of {domain}", timestamp=discord.utils.utcnow(),color=self.client.embed_color).set_footer(icon_url="https://camo.githubusercontent.com/74ed64243ba05754329bc527cd4240ebd1c087a1/68747470733a2f2f73656c656e69756d2e6465762f696d616765732f73656c656e69756d5f6c6f676f5f7371756172655f677265656e2e706e67", text="Powered by Selenium | This process could take up to 30 seconds."))
            def generate_screenshot():
                try:
                    req_height = browser.execute_script('return document.body.parentNode.scrollHeight')
                    browser.set_window_size(1920, req_height if req_height < 10000 else 10000)
                    el = browser.find_element_by_tag_name('body')
                    try:
                        el.screenshot(f'temp/{filename}')
                    except:
                        browser.get_screenshot_as_file(f'temp/{filename}')
                    #browser.set_window_size(1920, 1080)
                    #browser.get_screenshot_as_file("testscreenshot.png")
                    browser.quit()
                    file = discord.File(fp=f'temp/{filename}', filename=filename)
                    return file
                except Exception as e:
                    return e

            screenshot = await loop.run_in_executor(None, generate_screenshot)
            if not type(screenshot) == discord.File:
                return await message.edit(
                    embed=discord.Embed(title=message.embeds[0].title, description=screenshot, color=self.client.embed_color,
                                        timestamp=discord.utils.utcnow()))
            await message.edit(embed=discord.Embed(title=f"Website details for {domain}",
                                                   description=f"__**Status**__\n<:DVB_start_complete:895172800627769447> Start Google Chrome\n<:DVB_middle_complete:895172800627769444> **Connecting to linked website**\n<:DVB_middle_complete:895172800627769444> **Getting screenshot of website**\n<:DVB_end_complete:895172800082509846> Getting SSL Certificate information of {domain}",
                                                   timestamp=discord.utils.utcnow(),
                                                   color=self.client.embed_color).set_footer(
                icon_url="https://camo.githubusercontent.com/74ed64243ba05754329bc527cd4240ebd1c087a1/68747470733a2f2f73656c656e69756d2e6465762f696d616765732f73656c656e69756d5f6c6f676f5f7371756172655f677265656e2e706e67",
                text="Powered by Selenium | This process could take up to 30 seconds."))
            def get_ssl_information():
                ssl_context = ssl.create_default_context()
                try:
                    with ssl_context.wrap_socket(socket.socket(), server_hostname=domain) as s:
                        s.connect((domain, 443))
                        cert = s.getpeercert()
                except Exception as e:
                    result = f"The SSL Certificate for this website could not be verified. Tip: All websites with an invalid/unkown SSL Certificate are less trusted.\nMore details: `{e}`"
                else:
                    subject = dict(x[0] for x in cert['subject'])
                    issued_to = subject['commonName']
                    if 'organizationName' in subject:
                        if 'countryName' in subject:
                            owner = f"{subject['organizationName']} [{subject['countryName']}]"
                        else:
                            owner = f"{subject['organizationName']}"
                    else:
                        owner = None
                    issuer = dict(x[0] for x in cert['issuer'])
                    issued_by = issuer['commonName']
                    result = f"**__Certificate Information for {domain}__**\n`-` Issued by: **{issued_by}**\n`-` Issued to the domain: **{issued_to}** \n"
                    if owner:
                        result += f"'`-` <:DVB_secure:894962850110509056> Owned by: **{owner}**"
                    return result
            async with ctx.typing():
                ssldetails = await loop.run_in_executor(None, get_ssl_information) or f"**__Certificate Information for {domain}__\nNo information is available.**"
            embed = discord.Embed(title=f"Website details for {domain}", description=ssldetails+"\n\nScreenshot: ", timestamp=discord.utils.utcnow(), color=self.client.embed_color)
            embed.set_image(url=f"attachment://{filename}")
            with open('assets/linkinfo.json', 'r', encoding='utf8') as f:
                linkdata = json.load(f)
            for i in linkdata:
                if i in link:
                    embed.add_field(name="Additional information about link", value=linkdata[i], inline=False)
                    break
                else:
                    continue
            embed.set_footer(icon_url="https://camo.githubusercontent.com/74ed64243ba05754329bc527cd4240ebd1c087a1/68747470733a2f2f73656c656e69756d2e6465762f696d616765732f73656c656e69756d5f6c6f676f5f7371756172655f677265656e2e706e67", text="Powered by Selenium | Try opening the screenshot in a browser if it's too blur.")
            await message.delete()
        await ctx.send(file=screenshot, embed=embed)
        try:
            os.remove(filename)
        except FileNotFoundError:
            return