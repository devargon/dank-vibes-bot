import asyncio
import math
import re
import discord
from discord.ext import commands
from main import dvvt
from utils.buttons import SingleURLButton
from utils.format import human_join, comma_number, plural
import os

currency = "⏣"
heistannouncements_channel_id = 1018414186516205608 if os.getenv('state') == '1' else 876827800236064808
serverheists_channel_id = 1018414206481084477 if os.getenv('state') == '1' else 690125458272288814
heists_ping_id = 895815773208051763 if os.getenv('state') == '1' else 758174643814793276
vip_heists_ping_id = 895815546292035625 if os.getenv('state') == '1' else 817459252913635438
heist_log_channel_id = 977043022082613320 if os.getenv('state') == '1' else 751031637294186566
dankmemer_id = 270904126974590976


class SafeToDismiss(discord.ui.View):
    @discord.ui.button(label="Safe to dismiss", style=discord.ButtonStyle.grey, disabled=True)
    async def safe_to_dismiss_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass


class HeistUtils(discord.ui.View):
    def __init__(self, heistannouncements_channel, serverheists_channel, thx_embed):
        self.heistannouncements_channel = heistannouncements_channel
        self.serverheists_channel = serverheists_channel
        self.thx_embed = thx_embed
        self.message: discord.Message = None
        super().__init__(timeout=None)

    @discord.ui.button(label="DO NOT DISMISS", style=discord.ButtonStyle.red, disabled=True)
    async def do_not_dismiss(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass


    @discord.ui.button(label="Send Heist Thanks embed (press this AFTER heist is over)", style=discord.ButtonStyle.grey)
    async def send_heist_thanks_embed(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        await self.heistannouncements_channel.send(embed=self.thx_embed)
        await self.serverheists_channel.send(embed=self.thx_embed)
        await interaction.response.edit_message(view=self)

    async def safe_to_dismiss(self):
        self.children[0].style = discord.ButtonStyle.green
        self.children[0].label = "Safe to dismiss"
        await self.message.edit(view=self)





class HeistTags(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    heistGroup = discord.SlashCommandGroup(name="heist", description="Manage heists with this command.", default_member_permissions=discord.Permissions(administrator=True))

    @heistGroup.command(name="start")
    async def start(self, ctx: discord.ApplicationContext,
                    amount: discord.Option(int, "Must be in numbers ONLY"),
                    sponsor1: discord.Option(discord.Member),
                    requirement: discord.Option(discord.Role, "The role requirement for the heist, will be applied.") = None,
                    sponsor2: discord.Option(discord.Member) = None,
                    sponsor3: discord.Option(discord.Member) = None,
                    sponsor4: discord.Option(discord.Member) = None,
                    sponsor5: discord.Option(discord.Member) = None,
                    sponsor6: discord.Option(discord.Member) = None,
                    sponsor7: discord.Option(discord.Member) = None,
                    sponsor8: discord.Option(discord.Member) = None,
                    sponsor9: discord.Option(discord.Member) = None,
                    sponsor10: discord.Option(discord.Member) = None
                    ):
        """
        Start a heist
        """
        serverheists_channel = ctx.guild.get_channel(serverheists_channel_id)
        heistannouncements_channel = ctx.guild.get_channel(heistannouncements_channel_id)
        if serverheists_channel is None:
            return await ctx.respond("**Fatal error**\n<:DVB_False:887589731515392000> The **server heists** channel is not found.", ephemeral=True)
        if heistannouncements_channel is None:
            return await ctx.respond("**Fatal error**\n<:DVB_False:887589731515392000> The **heist announcements** channel is not found.", ephemeral=True)
        await ctx.defer(ephemeral=True)
        # consolidate sponsors into a list if sponsors are not none
        sponsors = [sponsor1, sponsor2, sponsor3, sponsor4, sponsor5, sponsor6, sponsor7, sponsor8, sponsor9, sponsor10]
        sponsors_filtered = []
        for i in sponsors:
            if i is not None and i not in sponsors_filtered:
                sponsors_filtered.append(i)
        if len(sponsors_filtered) == 0:
            return await ctx.respond("**Fatal error**\n<:DVB_False:887589731515392000> You must have specified at least 1 sponsor.", ephemeral=True)
        sponsors_str = human_join([f"{sponsor.mention}" for sponsor in sponsors_filtered], final="and")
        requirement_str = requirement.mention if requirement is not None else None
        server_heists_embed = discord.Embed(title=f"{currency} {comma_number(amount)} Heist", description=f"**Requirement:** {requirement_str}\nSponsors: {sponsors_str}", color=self.client.embed_color)
        server_heists_embed.add_field(name="Make sure to:", value="• Withdraw coins: `/withdraw 2000`\n• Toggle passive: `/settings` >> `Passive` >> `Disable`\n• Press the `JOIN BANKROB` button below")
        server_heists_embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon.with_size(32).url)
        server_heists_embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/969734884039995432.png")
        try:
            await serverheists_channel.send(embed=server_heists_embed)
        except Exception as e:
            return await ctx.respond(f"**Fatal error**\n<:DVB_False:887589731515392000> Failed to send the heist embed in `{serverheists_channel}`.\n```py\n# More details\n{e}```", ephemeral=True)

        info_embed = discord.Embed(title=f"{currency} {comma_number(amount)}", description=f"React with <a:dv_iconOwO:837943874973466664> below\nSponsors: {sponsors_str}\nTimer: □□□□□□□□□□", color=self.client.embed_color)
        info_embed.add_field(name="Requirement", value=f"{requirement_str}", inline=False)
        info_embed.set_footer(text=ctx.guild.name)
        if requirement is not None:
            extra_str = f"• Grab the Requirement role\n"
        else:
            extra_str = ""
        info_embed.add_field(name="Make sure to", value=f"{extra_str}• Head over to {serverheists_channel.mention}", inline=False)
        ping = f"<@&{heists_ping_id}>"
        if amount >= 25000000:
            ping += f"<@&{vip_heists_ping_id}>"
        try:
            info_message = await heistannouncements_channel.send(ping + "\n🎉 **DANK VIBES HEIST** 🎉", embed=info_embed, allowed_mentions=discord.AllowedMentions(everyone=False, roles=True))
        except Exception as e:
            return await ctx.respond(f"**Fatal error**\n<:DVB_False:887589731515392000> Failed to send the heist embed in `{heistannouncements_channel}`.\n```py\n# More details\n{e}```", ephemeral=True, view=SafeToDismiss())
        timer = 0
        thx_embed = discord.Embed(title=f"<a:DVpopper:904267438839959553> {currency} {comma_number(amount)} HEIST <a:DVpopper:904267438839959553>", description=f"<:dv_itPepeCrownOwO:857898556487761951> Thank {sponsors_str} for the heist in <#608498967474601995> <:dv_itPepeCrownOwO:857898556487761951>\n\nIf you wish to host a heist run `/hdonate <amount> [optional level req]` in <#786944439360290826> `[Minimum: 10,000,000]`")
        thx_embed.set_thumbnail(url=ctx.guild.icon.with_size(128).url)
        heistutil_view = HeistUtils(heistannouncements_channel, serverheists_channel, thx_embed)
        heistutil_view.message = await ctx.respond("Heist Started!\n**DO NOT dismiss this message until the heist is over.**", view=heistutil_view, ephemeral=True)
        try:
            await info_message.add_reaction("<a:dv_iconOwO:837943874973466664>")
        except Exception as e:
            await ctx.respond(f"**Non-fatal error**\nFailed to add reaction to the heist embed in `{heistannouncements_channel}`. The heist tag will proceed.\n```py\n#Error details\n{e}```", ephemeral=True)

        if requirement is not None:
            original_everyone_overwrite = serverheists_channel.overwrites_for(ctx.guild.default_role)
            original_requirement_overwrite = serverheists_channel.overwrites_for(requirement)
            try:
                await serverheists_channel.set_permissions(ctx.guild.default_role, view_channel=False, send_messages=False)
                await ctx.respond(f"`@everyone`'s __View Channel__ permissions has been set to **False**.", ephemeral=True, view=SafeToDismiss())
            except Exception as e:
                await ctx.respond(f"**Non-fatal error**\nFailed to set `@everyone`'s __View Channel__ permissions to **False** in `{serverheists_channel}`. The heist tag will proceed.\n```py\n# More details\n{e}```", ephemeral=True, view=SafeToDismiss())
            try:
                await serverheists_channel.set_permissions(requirement, view_channel=True, send_messages=False)
                await ctx.respond(f"{requirement.mention}'s __View Channel__ permissions has been set to **True**.", ephemeral=True, view=SafeToDismiss())
            except Exception as e:
                await ctx.respond(f"**Non-fatal error**\nFailed to set {requirement.mention}'s __View Channel__ permissions to **True** in `{serverheists_channel}`. The heist tag will proceed.\n```py\n# More details\n{e}```", ephemeral=True, view=SafeToDismiss())


        while timer < 10:
            await asyncio.sleep(4)
            timer_str = "■" * timer + "□" * (10 - timer)
            new_timer_str = "■" * (timer + 1) + "□" * (10 - (timer + 1))
            info_embed.description = info_embed.description.replace(timer_str, new_timer_str)
            try:
                await info_message.edit(embed=info_embed)
            except discord.HTTPException:
                try:
                    info_message = info_message.channel.send(embed=info_embed)
                except Exception as e:
                    pass
            timer += 1
        info_embed.description = info_embed.description.replace("Timer: ■■■■■■■■■■", f"**Head to <#{serverheists_channel_id}>!**")
        try:
            await info_message.edit(embed=info_embed)
        except discord.HTTPException:
            info_message.channel.send(embed=info_embed)
        def check(m: discord.Message):
            if m.channel.id != serverheists_channel_id or m.author.id != dankmemer_id:
                return False
            if len(m.embeds) < 0:
                return False
            embed = m.embeds[0]
            if embed.title.endswith("is starting a bank robbery"):
                return True
            return False

        details = await self.client.fetch_user_info(ctx.author.id)
        details.heists += 1
        details.heistamt += amount
        await details.update(self.client)
        total_heistamt = int(await self.client.db.fetchval("SELECT SUM(heistamt) AS total FROM userinfo"))
        total_heists = int(await self.client.db.fetchval("SELECT SUM(heists) AS total FROM userinfo"))
        log_text = f"`{ctx.author} ({ctx.author.id})` started a heist!"
        log_embed = discord.Embed(description=f"**Sponsors**: {sponsors_str}\n**Amount**: `{currency} {comma_number(amount)}`\n`{comma_number(total_heists)}` total heists worth over \n`{currency} {comma_number(total_heistamt)}` in the server!", color=self.client.embed_color)
        log_channel = self.client.get_channel(heist_log_channel_id)
        try:
            await log_channel.send(log_text, embed=log_embed)
        except Exception as e:
            await ctx.respond(f"**Non-fatal error**\nFailed to log heist in `{log_channel}`. The heist tag will proceed.\n```py\n# More details\n{e}```", view=SafeToDismiss(), ephemeral=True)






        wait_for_heist_embed = discord.Embed(description="Waiting for a heist to be started.", color=self.client.embed_color)
        try:
            wait_for_heist_msg = await serverheists_channel.send(embed=wait_for_heist_embed)
        except:
            wait_for_heist_msg = None
        try:
            await self.client.wait_for('message', check=check, timeout=120.0)
        except asyncio.TimeoutError:
            wait_for_heist_embed.color = discord.Color.red()
            wait_for_heist_embed.description = "Timed out waiting for a heist to be started."
            if wait_for_heist_msg is not None:
                try:
                    await wait_for_heist_msg.edit(embed=wait_for_heist_embed)
                except Exception as e:
                    pass
        else:
            wait_for_heist_embed.description, wait_for_heist_embed.color = "Heist detected.", discord.Color.green()
            if wait_for_heist_msg is not None:
                try:
                    await wait_for_heist_msg.edit(embed=wait_for_heist_embed, delete_after=2.0)
                except Exception as e:
                    pass
            await asyncio.sleep(88.0) # dank memer might be too fast
            wait_for_result_embed = discord.Embed(description="Waiting for a heist result to be posted.", color=self.client.embed_color)
            try:
                wait_for_result_msg = await serverheists_channel.send(embed=wait_for_result_embed)
            except:
                wait_for_result_msg = None
            def dank_memer_check(m: discord.Message):
                return len(m.embeds) > 0 and m.channel.id == serverheists_channel_id and m.author.id == dankmemer_id
            try:
                dank_memer_message = await self.client.wait_for('message', check=dank_memer_check, timeout=120.0)
            except asyncio.TimeoutError:
                wait_for_result_embed.color = discord.Color.red()
                wait_for_result_embed.description = "Timed out waiting for a heist result to be posted."
                if wait_for_result_msg is not None:
                    try:
                        await wait_for_result_msg.edit(embed=wait_for_result_embed)
                    except Exception as e:
                        pass
            else:
                await wait_for_result_msg.delete()
                heist_result = dank_memer_message.embeds[0]
                heist_result_format = discord.Embed(title="Heist Result", color=discord.Color.green(), timestamp=discord.utils.utcnow())
                if "Amazing job everybody" in heist_result.description: # proper result
                    payout_regex = r"`(\d+)` users? got the payout"
                    died_regex = r"`(\d+)` users? died"
                    nothing_regex = r"`(\d+)` users? got nothing"
                    fined_regex = r"`(\d+)` users? got fined"
                    payout_regex = re.compile(payout_regex)
                    died_regex = re.compile(died_regex)
                    nothing_regex = re.compile(nothing_regex)
                    fined_regex = re.compile(fined_regex)

                    def find_stat(regex):
                        match = re.findall(regex, heist_result.description)
                        if len(match) > 0:
                            try:
                                result = int(match[0])
                            except ValueError:
                                return None
                            else:
                                return result
                        else:
                            return None

                    payouted = find_stat(payout_regex)
                    died = find_stat(died_regex)
                    nothing = find_stat(nothing_regex)
                    fined = find_stat(fined_regex)
                    if payouted is None or died is None or nothing is None or fined is None:
                        heist_result_format.color = discord.Color.red()
                        heist_result_format.description = "Failed to parse heist result."
                    else:
                        payout_per_user = math.floor(amount / payouted)
                        descriptions = [
                            f"◈ <:DVB_Blank:918464127779876924> **Amount**: `⏣ {comma_number(amount)}`",
                            f"◈ 💰 **Payouts per user**: `⏣ {comma_number(payout_per_user)}`",
                            f"◈ <a:dv_peperobOwO:956769885885726742> **Users successful**: `{comma_number(payouted)}`",
                            f"◈ 🚨 **Users fined**: `{comma_number(fined)}`",
                            f"◈ 🪦 **Users died**: `{comma_number(died)}`",
                        ]
                        heist_result_format.description = "\n".join(descriptions)
                        heist_result_format.set_footer(text=f"{ctx.guild.name}", icon_url=f"{ctx.guild.icon.with_size(32).url}")
                        heist_result_format.set_author(name=f"{comma_number(payouted+died+nothing+fined)} users joined", icon_url=f"https://cdn.discordapp.com/emojis/913426937362391111.webp?size=96&quality=lossless")
                elif "Server is not popular enough" in heist_result.description:
                    heist_result_format.color = discord.Color.red()
                    heist_result_format.description = "None"
                else:
                    heist_result_format.color = discord.Color.red()
                    heist_result_format.description = "Unknown Response"
                try:
                    await heistannouncements_channel.send(embed=heist_result_format, view=SingleURLButton(link=f"{dank_memer_message.jump_url}", text="Jump to results", emoji="💰"))
                except Exception as e:
                    await ctx.respond(f"**Non-fatal error**\nFailed to send summarised results in `{heistannouncements_channel}`. The heist tag will proceed.\n```py\n# More details\n{e}```", ephemeral=True, view=SafeToDismiss())
        if requirement is not None:
            try:
                await serverheists_channel.set_permissions(ctx.guild.default_role, overwrite=original_everyone_overwrite)
                await ctx.respond("`@everyone`'s permissions has been restored.", ephemeral=True, view=SafeToDismiss())
            except Exception as e:
                await ctx.respond(f"**Non-fatal error**\nFailed to restore permissions for `@everyone` in `{serverheists_channel}`.\n```py\n# More details\n{e}```", ephemeral=True, view=SafeToDismiss())
            try:
                await serverheists_channel.set_permissions(requirement, overwrite=original_requirement_overwrite)
                await ctx.respond(f"{requirement.mention}'s permissions has been restored.", ephemeral=True, view=SafeToDismiss())
            except Exception as e:
                await ctx.respond(f"**Non-fatal error**\nFailed to restore permissions for {requirement.mention} in `{serverheists_channel}`.\n```py\n# More details\n{e}```", ephemeral=True, view=SafeToDismiss())
        await heistutil_view.safe_to_dismiss()




