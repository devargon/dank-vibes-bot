import asyncio
import math
import re
import discord
from discord.ext import commands
from main import dvvt
from utils.buttons import SingleURLButton
from utils.format import human_join, comma_number
import os

currency = "⏣"
heistannouncements_channel_id = 1018414186516205608 if os.getenv('state') == '1' else 876827800236064808
serverheists_channel_id = 1018414206481084477 if os.getenv('state') == '1' else 690125458272288814
heists_ping_id = 895815773208051763 if os.getenv('state') == '1' else 758174643814793276
vip_heists_ping_id = 895815546292035625 if os.getenv('state') == '1' else 817459252913635438
dankmemer_id = 666152603339718667

class HeistUtils(discord.ui.View):
    def __init__(self, heistannouncements_channel, serverheists_channel, thx_embed):
        self.heistannouncements_channel = heistannouncements_channel
        self.serverheists_channel = serverheists_channel
        self.thx_embed = thx_embed
        super().__init__(timeout=None)

    @discord.ui.button(label="Send Heist Thanks embed (press this after heist is over)", style=discord.ButtonStyle.grey)
    async def send_heist_thanks_embed(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.disabled = True
        button.style = discord.ButtonStyle.green
        await self.heistannouncements_channel.send(embed=self.thx_embed)
        await self.serverheists_channel.send(embed=self.thx_embed)
        await interaction.response.edit_message(view=self)



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
            return await ctx.respond("<:DVB_False:887589731515392000> The **server heists** channel is not found.", ephemeral=True)
        if heistannouncements_channel is None:
            return await ctx.respond("<:DVB_False:887589731515392000> The **server heists** channel is not found.", ephemeral=True)
        await ctx.defer(ephemeral=True)
        # consolidate sponsors into a list if sponsors are not none
        sponsors = [sponsor1, sponsor2, sponsor3, sponsor4, sponsor5, sponsor6, sponsor7, sponsor8, sponsor9, sponsor10]
        sponsors_filtered = []
        for i in sponsors:
            if i is not None and i not in sponsors_filtered:
                sponsors_filtered.append(i)
        sponsors_str = human_join([f"{sponsor.mention}" for sponsor in sponsors_filtered], final="and")
        requirement_str = requirement.mention if requirement is not None else None
        server_heists_embed = discord.Embed(title=f"{currency} {comma_number(amount)} Heist", description=f"**Requirement:** {requirement_str}\nSponsors: {sponsors_str}", color=self.client.embed_color)
        server_heists_embed.add_field(name="Make sure to:", value="• Withdraw coins: `/withdraw 2000`\n• Toggle passive: `/settings` >> `Passive` >> `Disable`\n• Press the `JOIN BANKROB` button below")
        server_heists_embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon.with_size(32).url)
        server_heists_embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/969734884039995432.png")
        await serverheists_channel.send(embed=server_heists_embed)
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
        info_message = await heistannouncements_channel.send(ping + "\n🎉 **DANK VIBES HEIST** 🎉", embed=info_embed, allowed_mentions=discord.AllowedMentions(everyone=False, roles=True))
        timer = 0
        thx_embed = discord.Embed(title=f"<a:DVpopper:904267438839959553> {currency} {comma_number(amount)} HEIST <a:DVpopper:904267438839959553>", description=f"<:dv_itPepeCrownOwO:857898556487761951> Thank {sponsors_str} for the heist in <:dv_itPepeCrownOwO:857898556487761951>\n\nIf you wish to host a heist run `/hdonate <amount> [optional level req]` in <#786944439360290826> `[Minimum: 10,000,000]")
        thx_embed.set_thumbnail(url=ctx.guild.icon.with_size(128).url)
        await ctx.respond("Heist Started!\n**DO NOT dismiss this message until the heist is over.**", view=HeistUtils(heistannouncements_channel, serverheists_channel, thx_embed), ephemeral=True)

        if requirement is not None:
            original_everyone_overwrite = serverheists_channel.overwrites_for(ctx.guild.default_role)
            original_requirement_overwrite = serverheists_channel.overwrites_for(requirement)
            await serverheists_channel.set_permissions(ctx.guild.default_role, view_channel=False)
            await ctx.respond(f"`@everyone`'s __View Channel__ permissions has been set to **False**.", ephemeral=True)
            await serverheists_channel.set_permissions(requirement, view_channel=True)
            await ctx.respond(f"{requirement.mention}'s __View Channel__ permissions has been set to **True**.", ephemeral=True)

        while timer < 10:
            await asyncio.sleep(3)
            timer_str = "■" * timer + "□" * (10 - timer)
            new_timer_str = "■" * (timer + 1) + "□" * (10 - (timer + 1))
            print(timer_str, new_timer_str)
            info_embed.description = info_embed.description.replace(timer_str, new_timer_str)
            try:
                await info_message.edit(embed=info_embed)
            except discord.HTTPException:
                info_message = info_message.channel.send(embed=info_embed)
            timer += 1
        info_embed.description = info_embed.description.replace("Timer: ■■■■■■■■■■", f"**Head to <#{serverheists_channel_id}>!**")
        try:
            await info_message.edit(embed=info_embed)
        except discord.HTTPException:
            info_message = info_message.channel.send(embed=info_embed)
        def check(m: discord.Message):
            if m.channel.id != serverheists_channel_id or m.author.id != dankmemer_id:
                return False
            if len(m.embeds) < 0:
                return False
            embed = m.embeds[0]
            if embed.title.endswith("is starting a bank robbery"):
                return True
            return False
        wait_for_heist_embed = discord.Embed(description="Waiting for a heist to be started.", color=self.client.embed_color)
        wait_for_heist_msg = await serverheists_channel.send(embed=wait_for_heist_embed)
        try:
            await self.client.wait_for('message', check=check, timeout=120.0)
        except asyncio.TimeoutError:
            wait_for_heist_embed.color = discord.Color.red()
            wait_for_heist_embed.description = "Timed out waiting for a heist to be started."
            await wait_for_heist_msg.edit(embed=wait_for_heist_embed)
            return
        else:
            wait_for_heist_embed.description, wait_for_heist_embed.color = "Heist detected.", discord.Color.green()
            await wait_for_heist_msg.edit(embed=wait_for_heist_embed, delete_after=2.0)
            await asyncio.sleep(88.0) # dank memer might be too fast
            wait_for_result_embed = discord.Embed(description="Waiting for a heist result to be posted.", color=self.client.embed_color)
            wait_for_result_msg = await serverheists_channel.send(embed=wait_for_result_embed)
            def dank_memer_check(m: discord.Message):
                return len(m.embeds) > 0 and m.channel.id == serverheists_channel_id and m.author.id == dankmemer_id
            try:
                dank_memer_message = await self.client.wait_for('message', check=dank_memer_check, timeout=120.0)
            except asyncio.TimeoutError:
                wait_for_result_embed.color = discord.Color.red()
                wait_for_result_embed.description = "Timed out waiting for a heist result to be posted."
                await wait_for_result_msg.edit(embed=wait_for_result_embed)
                return
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
                            f"◈ **Amount**: `⏣ {comma_number(amount)}`",
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
                await heistannouncements_channel.send(embed=heist_result_format, view=SingleURLButton(link=f"{dank_memer_message.jump_url}", text="Jump to results", emoji="💰"))
        if requirement is not None:
            await serverheists_channel.set_permissions(ctx.guild.default_role, overwrite=original_everyone_overwrite)
            await ctx.respond("`@everyone`'s permissions has been restored.", ephemeral=True)
            await serverheists_channel.set_permissions(requirement, overwrite=original_requirement_overwrite)
            await ctx.respond(f"{requirement.mention}'s permissions has been restored.", ephemeral=True)




