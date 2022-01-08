import asyncio

import discord
from utils import checks
from discord.ext import commands
from utils.format import get_command_name
from utils.converters import BetterRoles, AllowDeny
import json
from utils.format import ordinal
from utils.buttons import confirm

class age(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [668151486060036117, 668151479663853570]
        labels = ["-18", "18+"]
        emojis = ["<:under18:898490697827614740>", "<:18plus:898490829088378891>"]
        ids = ["sr:-18",  "sr:18+"]
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])

                if role not in interaction.user.roles:
                    otherroleindex = 0 if index == 1 else 1
                    role2 = interaction.guild.get_role(catroles[otherroleindex])
                    if role2 in interaction.user.roles:
                        await interaction.user.remove_roles(role2, reason="Selfrole")
                    await interaction.user.add_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                else:
                    await interaction.user.remove_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[emojis.index(emoji)], style=discord.ButtonStyle.grey, custom_id=ids[emojis.index(emoji)]))


class gender(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [758174046365679686, 624308588336250890, 703290809595854928]
        labels = ["Male", "Female", "Non-binary"]
        emojis = ["<:Male:898490868971995156>", "<:Female:898490901511434240>", "<:nonbinary:898490958772068383>"]
        ids = ["sr:male", "sr:female", "sr:non-binary"]
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if index == 0:
                    if interaction.guild.get_role(catroles[1]) in interaction.user.roles:
                        await interaction.user.remove_roles(interaction.guild.get_role(catroles[0]), reason="Selfrole")
                    if interaction.guild.get_role(catroles[2]) in interaction.user.roles:
                        await interaction.user.remove_roles(interaction.guild.get_role(catroles[0]), reason="Selfrole")
                if index == 1:
                    if interaction.guild.get_role(catroles[0]) in interaction.user.roles:
                        await interaction.user.remove_roles(interaction.guild.get_role(catroles[0]), reason="Selfrole")
                    if interaction.guild.get_role(catroles[2]) in interaction.user.roles:
                        await interaction.user.remove_roles(interaction.guild.get_role(catroles[0]), reason="Selfrole")
                if index == 2:
                    if interaction.guild.get_role(catroles[1]) in interaction.user.roles:
                        await interaction.user.remove_roles(interaction.guild.get_role(catroles[0]), reason="Selfrole")
                    if interaction.guild.get_role(catroles[0]) in interaction.user.roles:
                        await interaction.user.remove_roles(interaction.guild.get_role(catroles[0]), reason="Selfrole")
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been added to you.",
                                                            ephemeral=True)
                else:
                    await interaction.user.remove_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been removed from you.",
                                                            ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[emojis.index(emoji)],
                                     style=discord.ButtonStyle.grey, custom_id=ids[emojis.index(emoji)]))

class location(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [665765320644100116, 665765314251980813, 665765307973107723, 665765326482571274, 665766596689526804, 665765388059017217]
        labels = ["North America", "South America", "Oceania", "Europe", "Africa", "Asia"]
        emojis = ["<:NorthAmerica:898491000136290304>", "<:SouthAmerica:898491037100675072>", "<:Oceania:898491069942095872>", "<:Europe:898491102213079050>", "<:Africa:898491126363869214>", "<:Asia:898491160409047051>"]
        ids = ["sr: north", "sr:south", "sr:oceania", "sr:europe", "sr:africa", "sr:asia"]
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                for count, item in enumerate(catroles):
                    if count == index:
                        pass
                    else:
                        targetremove = interaction.guild.get_role(item)
                        if targetremove in interaction.user.roles:
                            await interaction.user.remove_roles(targetremove, reason="Selfrole")
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                else:
                    await interaction.user.remove_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[emojis.index(emoji)], style=discord.ButtonStyle.grey, custom_id=ids[emojis.index(emoji)]))


class minigames(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [740921339832959069, 740921804083691621, 656968113585258498, 740922021453496383]
        labels = ["Bingo Ping", "Mafia Ping", "UNO Ping", "Tea Games Ping"]
        emojis = ["<:bingoball:898491198153568256>", "<:mafiahead:898491254264954880>", "<:uno:898491224246333500>", "<:DVB_tea:898730353584386058>"]
        ids = ["sr:bingoping", "sr:mafiaping", "sr:unoping", "sr:teagamesping"]
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                else:
                    await interaction.user.remove_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[emojis.index(emoji)], style=discord.ButtonStyle.grey, custom_id=ids[emojis.index(emoji)]))


class event_pings(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [758174224208363560, 782606174624940062, 758180976282173470, 846254068434206740, 782606155188666374, 822537296158261268]
        labels = ["Events Ping", "Tea Events Ping", "Mafia Events Ping", "Special Events Ping", "Bingo Events Ping", "Gartic Events Piing"]
        emojis = ["<:pepeEvent:898501043338502174>", "<:pepeTea:898493318177095690>",
                  "<:Mafia:898493349521145866>", "<:SpecialEvent:898501437074571314>", "<:pepe8ball:898493385743147028>", "<:garticio:898493421189226496>"]
        ids = ["sr:eventsping", "sr:teaeventsping", "sr:mafiaeventsping", "sr:specialeventspingeventsping", "sr:bingoeventspingeventsping", "sr:garticeventsping"]
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                else:
                    await interaction.user.remove_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[emojis.index(emoji)], style=discord.ButtonStyle.grey, custom_id=ids[emojis.index(emoji)]))


class dank_pings(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [758174643814793276, 757907479190306826, 680131933778346011, 859493857061503008, 758175760909074432, 758174135276142593]
        labels = ["Heist Ping", "Shop Sale Ping", "Lottery Ping", "Partnered Heist Ping", "Giveaway Ping", "Elite Giveaway Ping"]
        emojis = ["<:heistpepe:898493464684142663>", "<:ShopSale:898493500545433650>", "<:pepelotto:898493525031792690>", "<:heistpartner:898493577376710677>", "<:Pepeliftmeme:898493625950949426>", "<:pepepec:898493664920227850>"]
        ids = ["sr:heistping", "sr:shopsaleping", "sr:lotteryping", "sr:partneredheistping", "sr:giveawayping", "sr:elitegiveawayping"]
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                else:
                    await interaction.user.remove_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[emojis.index(emoji)], style=discord.ButtonStyle.grey, custom_id=ids[emojis.index(emoji)]))


class server_pings(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [630485302854811679, 685233344136609812, 631699309540147230, 713477937130766396, 685237146415792128, 859494195706200104]
        labels = ["Announcements Ping", "Nitro Giveaways", "Vote Ping", "Partner Ping", "Media Events Ping", "No Partnership Ping"]
        emojis = ["<:DVpepe:898493715075706890>", "<:nitro:898493741667586049>", "<:Vote:898493770180481024>",
                  "<:Partner:898493813323096074>", "<:media:898494087647330324>", "<:nopartner:898494125769371669>"]
        ids = ["sr:announcementsping", "sr:nitrogiveawaysping", "sr:voteping", "sr:partnerping", "sr:mediaeventsping", "sr:nopartnershipping"]
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                else:
                    await interaction.user.remove_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[emojis.index(emoji)], style=discord.ButtonStyle.grey, custom_id=ids[emojis.index(emoji)]))


class bot_roles(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [837594909917708298, 837616413929504778, 837595491096199179, 837595397349179402, 837595433349152768, 837594929974870047]
        labels = ["Dank Memer Player", "Karuta Player", "Pokemon Player", "Mudae Player", "Anigame Player", "OwO Player"]
        emojis = ["<:DankMemer:898501160992911380>", "<:Karuta:898501294396964874>",
                  "<:Pokemon:898501263849816064>", "<:currency:898494174557515826>", "<:Anigame:898501235404079114>", "<:OwO:898501205360271380>"]
        ids = ["sr:dankmemerplayer", "sr:karutaplayer", "sr:pokemonplayer", "sr:mudaeplayer", "sr:anigameplayer", "sr:owoplayer"]
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                else:
                    await interaction.user.remove_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[emojis.index(emoji)], style=discord.ButtonStyle.grey, custom_id=ids[emojis.index(emoji)]))


class random_color(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [758176387806396456]
        labels = ["Random Color"]
        emojis = ["<:prism:898494225874833428>"]
        ids = ['sr:randomcolor']
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                else:
                    await interaction.user.remove_roles(role, reason="Selfrole")
                    await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label=labels[emojis.index(emoji)], style=discord.ButtonStyle.grey, custom_id = ids[emojis.index(emoji)]))

class colors(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [677658283732893701, 740717141782954105, 758172198769917993, 627934465959919656, 631228082728075264, 758171919349710859, 694795449273548813, 631227617651195904, 758172003814866944, 758172076082987028]
        emojis = ["<:SpookyGhost:898494594889682976>", "<:SilverFox:898494627227762698>", "<:SourLemon:898494660576686111>", "<:ElectricGreen:898494712233730059>", "<:BabyBlue:898494748078268417>", "<:Blurple:898494776469504021>", "<:PurpleAF:898494809197641738>", "<:StrawberryMilk:898494844396265502>", "<:BloodRed:898494876868575252>", "<:Dreamsicle:898494905398206485>"]
        ids = ['sr:spookyghost', 'sr:silverfox', 'sr:sourlemon', 'sr:electricgreen', 'sr:babyblue', 'sr:blurple', 'sr:purpleaf', 'sr:strawberrymilk', 'sr:bloodred', 'sr:dreamsicle']
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                for count, item in enumerate(catroles):
                    if count == index:
                        pass
                    else:
                        targetremove = interaction.guild.get_role(item)
                        if targetremove in interaction.user.roles:
                            await interaction.user.remove_roles(targetremove, reason="Selfrole")
                if discord.utils.get(interaction.user.roles, id = 645934789160992768) or discord.utils.get(interaction.user.roles, id = 739199912377319427) or discord.utils.get(interaction.user.roles, id = 769491608189927434) or discord.utils.get(interaction.user.roles, id=847461071643607091) or discord.utils.get(interaction.user.roles, id = 758172293133762591) or discord.utils.get(interaction.user.roles, id = 758172863580209203) or discord.utils.get(interaction.user.roles, id = 872685125471727656):
                    if role not in interaction.user.roles:
                        await interaction.user.add_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                    else:
                        await interaction.user.remove_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)
                else:
                    await interaction.response.send_message("To get any of these roles, you need to be a __Booster__, __Investor__, __100M Donator (Dank Memer)__ or __1M Donator (OwO)__.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), style=discord.ButtonStyle.grey, custom_id = ids[emojis.index(emoji)]))

class BoostPing(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [662876587687018507]
        emojis = ["<:BoosterGwPing:898495751372554261>"]
        ids = ['sr:boostergwping']
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if discord.utils.get(interaction.user.roles, id = 645934789160992768):
                    if role not in interaction.user.roles:
                        await interaction.user.add_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                    else:
                        await interaction.user.remove_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)
                else:
                    await interaction.response.send_message("To get this role, you need to be a __Booster__.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label = "Booster Giveaway Ping", style=discord.ButtonStyle.grey, custom_id = ids[emojis.index(emoji)]))

class VIPHeist(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [817459252913635438]
        emojis = ["<:heistpepe:898493464684142663>"]
        ids = ['sr:vipheistping']
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                if discord.utils.get(interaction.user.roles, id = 758173667682287616):
                    if role not in interaction.user.roles:
                        await interaction.user.add_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                    else:
                        await interaction.user.remove_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)
                else:
                    await interaction.response.send_message("To get any of these roles, you need to be a __750M Donator (Dank Memer)__.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), label="VIP Heist Ping", style=discord.ButtonStyle.grey, custom_id = ids[emojis.index(emoji)]))

class specialcolors(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        catroles = [758170964340506675, 767031737673842708, 782945052770697256, 758176346139918396, 758176352901529601, 782945398431023104, 782944967516618762, 758171089095360533, 782945231985311745, 631225364496121866]
        emojis = ['<:EmoBoiBlacc:898495383662121041>', '<:Mysterious:898495420471336961>', '<:Sunshine:898495451903447091>', '<:Caribbean:898495483616583710>', '<:MermaidTaffy:898495521872826388>', '<:Azure:898495548678631434>', '<:DustyRose:898495582006554624>', '<:Lilac:898495608103518208>', '<:PinkLemonade:898495644178718720>', '<:Starburst:898495679477973032>']
        ids = ['sr:emoboiblacc', 'sr:mysterious', 'sr:sunshine', 'sr:caribbean', 'sr:mermaidtaffy', 'sr:azure', 'sr:dustyrose', 'sr:lilac', 'sr:pinklemonade', 'sr:starburst']
        class somebutton(discord.ui.Button):
            async def callback(self, interaction: discord.Interaction):
                index = emojis.index(str(self.emoji))
                role = interaction.guild.get_role(catroles[index])
                for count, item in enumerate(catroles):
                    if count == index:
                        pass
                    else:
                        targetremove = interaction.guild.get_role(item)
                        if targetremove in interaction.user.roles:
                            await interaction.user.remove_roles(targetremove, reason="Selfrole")
                if discord.utils.get(interaction.user.roles, id = 758173974348824576) or discord.utils.get(interaction.user.roles, id = 739199912377319427) or discord.utils.get(interaction.user.roles, id = 756226612261027961) or discord.utils.get(interaction.user.roles, id=847461249935343626) or discord.utils.get(interaction.user.roles, id = 892266027495350333):
                    if role not in interaction.user.roles:
                        await interaction.user.add_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.name}** has been added to you.", ephemeral=True)
                    else:
                        await interaction.user.remove_roles(role, reason="Selfrole")
                        await interaction.response.send_message(f"The role **{role.name}** has been removed from you.", ephemeral=True)
                else:
                    await interaction.response.send_message("To get any of these roles, you need to be a __Double Booster__, __Vibing Investor__, __300M Donator (Dank Memer)__ or __5M Donator (OwO)__.", ephemeral=True)

        for emoji in emojis:
            self.add_item(somebutton(emoji=discord.PartialEmoji.from_str(emoji), style=discord.ButtonStyle.grey, custom_id = ids[emojis.index(emoji)]))

class BetterSelfroles(commands.Cog):
    def __init__(self, client):
        self.client= client
        self.persistent_views_added = False

    @commands.Cog.listener()
    async def on_ready(self):
        print('um')
        if not self.selfroleviews_added:
            print('noooo')
            self.client.add_view(age())
            self.client.add_view(gender())
            self.client.add_view(location())
            self.client.add_view(minigames())
            self.client.add_view(event_pings())
            self.client.add_view(dank_pings())
            self.client.add_view(server_pings())
            self.client.add_view(bot_roles())
            self.client.add_view(random_color())
            self.client.add_view(colors())
            self.client.add_view(specialcolors())
            self.client.add_view(BoostPing())
            self.client.add_view(VIPHeist())
            self.selfroleviews_added = True

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="initselfroles", aliases=["isr"])
    async def selfroles(self, ctx):
        channel = ctx.guild.get_channel(782586550486695936)
        if channel is None:
            return await ctx.send("There is no such channel with the ID 782586550486695936.")
        selfrolemessages = await self.client.pool_pg.fetchrow(
            "SELECT age, gender, location, minigames, event_pings, dank_pings, server_pings, bot_roles, random_color FROM selfrolemessages WHERE guild_id = $1",
            595457764935991326)
        categories = ['age', 'gender', 'location', 'minigames', 'event_pings', 'dank_pings', 'server_pings',
                      'bot_roles', 'random_color']
        if selfrolemessages is not None:
            if selfrolemessages.get('age'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('age')).delete()
                except:
                    pass
            if selfrolemessages.get('gender'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('gender')).delete()
                except:
                    pass
            if selfrolemessages.get('location'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('location')).delete()
                except:
                    pass
            if selfrolemessages.get('minigames'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('minigames')).delete()
                except:
                    pass
            if selfrolemessages.get('event_pings'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('event_pings')).delete()
                except:
                    pass
            if selfrolemessages.get('dank_pings'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('dank_pings')).delete()
                except:
                    pass
            if selfrolemessages.get('server_pings'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('server_pings')).delete()
                except:
                    pass
            if selfrolemessages.get('bot_roles'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('bot_roles')).delete()
                except:
                    pass
            if selfrolemessages.get('random_color'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('random_color')).delete()
                except:
                    pass
            await ctx.send("Deleted (or attempted to delete) previous instances of selfroles.")
        titles = ["Age", "Gender", "Location", "Minigames", "Event Pings", "Dank Pings", "Server Pings", "Bot Roles", "Random Color"]
        selfroleViews = [age(), gender(), location(), minigames(), event_pings(), dank_pings(), server_pings(), bot_roles(), random_color()]
        msgids = [ctx.guild.id]
        for oneview in selfroleViews:
            msg = await channel.send(embed = discord.Embed(title=titles[selfroleViews.index(oneview)], color=self.client.embed_color), view=oneview)
            msgids.append(msg.id)
        if selfrolemessages is not None:
            msgids.append(ctx.guild.id)
            await self.client.pool_pg.execute("UPDATE selfrolemessages SET guild_id = $1, age = $2, gender = $3, location = $4, minigames = $5, event_pings = $6, dank_pings = $7, server_pings = $8, bot_roles = $9, random_color = $10 WHERE guild_id = $11", *msgids)
        else:
            await self.client.pool_pg.execute("INSERT INTO selfrolemessages VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)", *msgids)
        await ctx.send("Done!")

    @checks.has_permissions_or_role(administrator=True)
    @commands.command(name="initviproles", aliases=['ivr'])
    async def initviproles(self, ctx):
        channel = ctx.guild.get_channel(641497978112180235)
        if channel is None:
            return await ctx.send("There is no such channel with the ID 641497978112180235.")
        selfrolemessages = await self.client.pool_pg.fetchrow(
            "SELECT colors, vipcolors, boostgaw, vipheistping FROM viprolemessages WHERE guild_id = $1",
            595457764935991326)
        if selfrolemessages is not None:
            if selfrolemessages.get('colors'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('colors')).delete()
                except:
                    pass
            if selfrolemessages.get('vipcolors'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('vipcoors')).delete()
                except:
                    pass
            if selfrolemessages.get('boostgaw'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('boostgaw')).delete()
                except:
                    pass
            if selfrolemessages.get('vipheistping'):
                try:
                    await channel.get_partial_message(selfrolemessages.get('vipheistping')).delete()
                except:
                    pass
            await ctx.send("Deleted (or attempted to delete) previous instances of VIP roles.")
        titles = ["Colors!", "Special Colors!", "Booster Giveaway Ping!", "VIP Heist Ping!"]
        descriptions = ["You need to be a __Booster__, __Investor__, __100M Donator (Dank Memer)__ or __1M Donator (OwO)__ to claim any of these roles.", "You need to be a __Double Booster__, __Vibing Investor__, __300M Donator (Dank Memer)__ or __5M Donator (OwO)__ to claim any of these roles.", "You need to be a __Booster__ to claim this role.", "You need to be a __750M Donator (Dank Memer)__ to claim this role."]
        selfroleViews = [colors(), specialcolors(), BoostPing(), VIPHeist()]
        msgids = [ctx.guild.id]
        for oneview in selfroleViews:
            msg = await channel.send(
                embed=discord.Embed(title=titles[selfroleViews.index(oneview)], description = descriptions[selfroleViews.index(oneview)], color=self.client.embed_color),
                view=oneview)
            msgids.append(msg.id)
        if selfrolemessages is not None:
            msgids.append(ctx.guild.id)
            await self.client.pool_pg.execute(
                "UPDATE selfrolemessages SET guild_id = $1, colors = $2, specialcolors = $3, boostping = $4, vipheist = $5 WHERE guild_id = $6", *msgids)
        else:
            await self.client.pool_pg.execute(
                "INSERT INTO selfrolemessages(guild_id, colors, specialcolors, boostping, vipheist) VALUES($1, $2, $3, $4, $5)", *msgids)
        await ctx.send("Done!")
