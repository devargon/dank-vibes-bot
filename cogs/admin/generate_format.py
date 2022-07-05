import time

import discord
from discord import default_permissions
from discord.ext import commands
from main import dvvt
from utils import checks
from utils.format import box

events = [
    "4 Pictures 1 Word",
    "Bingo",
    "Mafia",
    "Rumble Royale",
    "Last to Leave VC",
    "Food Kahoot",
    "Dank Vibes Kahoot",
    "Ban Battle",
]

event_timings = {
    "4 Pictures 1 Word": [1656874800, 1656993600, 1657274400],
    "Bingo": [1656738000, 1656889200, 1657036800, 1657177200, 1657335600],
    "Mafia": [1656925200, 1657123200],
    "Rumble Royale": [1656907200, 1657051200, 1657159200, 1657184400, 1657299600],
    "Last to Leave VC": [1656792000, 1657072800],
    "Food Kahoot": [1657011600],
    "Dank Vibes Kahoot": [1657213200],
    "Ban Battle": [1656810000, 1657083600],
}

minimum_time = 1656691200

class GenerateFormat(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    generate = discord.SlashCommandGroup("generate", "Generate text from templates.", default_member_permissions=discord.Permissions(permissions=268435456))

    @checks.has_permissions_or_role(manage_roles=True)
    @default_permissions(manage_roles=True)
    @generate.command(name="winner", description="Generate message for #┆・hall-of-winners.")
    async def generate_winner(self, ctx: discord.ApplicationContext,
                              event: discord.Option(str, choices=events),
                              winner1: discord.Option(discord.Member),
                              winner2: discord.Option(discord.Member) = None,
                              winner3: discord.Option(discord.Member) = None,
                              winner4: discord.Option(discord.Member) = None,
                              winner5: discord.Option(discord.Member) = None,
                              winner6: discord.Option(discord.Member) = None,
                              winner7: discord.Option(discord.Member) = None,
                              winner8: discord.Option(discord.Member) = None,
                              winner9: discord.Option(discord.Member) = None,
                              winner10: discord.Option(discord.Member) = None,
                              winner11: discord.Option(discord.Member) = None,
                              winner12: discord.Option(discord.Member) = None,
                              ):
        selected_event_timings = event_timings.get(event, [])
        if len(selected_event_timings) > 0:
            current_time = round(time.time())
            before_event_timings = [x for x in selected_event_timings if x < current_time]
            closest_time = min(before_event_timings, key=lambda x: abs(x - current_time))


            msg = [f"<a:YMe_IA_PlanetS_NOSTEAL:833789373539418113> __**{event}**__ - <t:{closest_time}:f>"]
            winners = [winner1, winner2, winner3, winner4, winner5, winner6, winner7, winner8, winner9, winner10, winner11, winner12]
            winners = [x for x in winners if x is not None]
            dash_emojis = ["<:aa_limeheart:915532105189056524>", "<:aa_purpleheart:915510313972023306>"]
            heart_emojis = ["<:d_thinpurpledash:933643545909280788>", "<:d_thinlimedash:933643434848313365>"]
            for i, winner in enumerate(winners):
                dash_emoji = dash_emojis[i % 2]
                heart_emoji = heart_emojis[i % 2]
                msg.append(f"{dash_emoji} {heart_emoji}꒰**{i+1}**꒱ **{winner}** ({winner.mention})")
            embed = discord.Embed(title="Result", description=box("\n".join(msg)), color=self.client.embed_color)
            await ctx.respond(embed=embed)

    @generate.command(name="event", description="Generate message for the next event.")
    @default_permissions(manage_roles=True)
    async def generate_event(self, ctx: discord.ApplicationContext,
                             event: discord.Option(str, choices=events)
                             ):
        current_time = round(time.time())
        after_event_timings = [x for x in event_timings.get(event, []) if x > current_time]
        closest_time = min(after_event_timings, key=lambda x: abs(x - current_time))
        text = f"<a:YMe_IA_PlanetS_NOSTEAL:833789373539418113> **{event}** <t:{closest_time}:R>. Stay tuned!\n<:dashgreen_donotsteal:834087005826580490><:aa_purpleheart:915510313972023306>Read the embed above for details.\n<:dash_donotsteal:834086914767323136><:aa_limeheart:915532105189056524>Run `-3yschedule` for the full schedule!\n<:dashgreen_donotsteal:834087005826580490><:aa_purpleheart:915510313972023306>Grab some roles to get notified for our events and more!"
        embed = discord.Embed(title="Template", description=box(text), color=self.client.embed_color)
        await ctx.respond("Also send: ```\ndv.self --roles Special Events Ping\n```", embed=embed)




