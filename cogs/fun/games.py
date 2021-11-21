import random
from utils.context import DVVTcontext
import discord
from discord.ext import commands
from utils import checks
import asyncio
from utils.buttons import confirm
from utils.format import stringtime_duration
from utils.time import humanize_timedelta
from time import time
from utils.errors import NicknameIsManaged
import contextlib


class games(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.nickbets = []

    @checks.requires_roles()
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name='guessthenumber', aliases=['gtn', 'numberevent'])
    async def guessthenumber(self, ctx):
        """
        Sets up an interactiive guess the number game. This command can only be run in <#735477033949462578>, by the event host or sponsor.
        """
        if ctx.channel.id != 735477033949462578:
            return await ctx.send("This command can only be run in <#735477033949462578>, by the event host or sponsor.")
        channel = ctx.channel
        confirmview = confirm(ctx, self.client, 30.0)
        if ctx.author.id in self.planning_numberevent:
            return await ctx.send("You're already planning a Guess the Number game. Please check your DMs.")
        if channel.id in self.numberevent_channels:
            return await ctx.send("A Guess the Number game is already taking place in the specified channel. Tell the host to `cancel` the game.")
        embed = discord.Embed(title="Action awaiting confirmation", description=f"Are you ready to start a Guess the Number game in {channel.mention}?", color=self.client.embed_color, timestamp=discord.utils.utcnow())
        confirmmsg = await ctx.send(embed=embed, view=confirmview)
        confirmview.response = confirmmsg
        await confirmview.wait()
        if confirmview.returning_value == None:
            embed.description, embed.color = "I did not get a repsonse, so I cancelled the game. To proceed with setting up the game, press the green button 'Yes'.", discord.Color.red()
            return await confirmmsg.edit(embed=embed)
        elif confirmview.returning_value == False:
            embed.description, embed.color = "I cancelled the game. To proceed with setting up the game, press the green button 'Yes'.", discord.Color.red()
            return await confirmmsg.edit(embed=embed)
        elif confirmview.returning_value == True:
            small = None
            big = None
            chosen = None
            error = None
            try:
                await ctx.author.send(embed=discord.Embed(title="Setting up a Guess the Number game...", description="You can say `cancel` anytime during the setup to cancel the Guess the Number game.", color=self.client.embed_color))
            except discord.Forbidden:
                return await ctx.send("To set up the game, I need your DMs open for me. Please open your DMs and run the command again!")
            self.planning_numberevent.append(ctx.author.id)
            embed.description, embed.color = "Please check your DMs!", discord.Color.green()
            await confirmmsg.edit(embed=embed)
            while small == None or big == None:
                sending = "State the range of numbers that the number you chose is within, with two numbers separated by a dash (`-`).\nFor example, if the number you have in mind is `5`, you should input a range of `0-10`.\nNegative numbers aren't allowed."
                if error is not None:
                    sending = error + '\n\n' + sending
                await ctx.author.send(embed=discord.Embed(title="Guess the Number game setup: Step 1 of 2", description=sending, color=self.client.embed_color))
                def check(payload):
                    return payload.author == ctx.author and isinstance(payload.channel, discord.DMChannel)
                try:
                    inputmessage = await self.client.wait_for('message', check=check, timeout=30.0)
                except asyncio.TimeoutError:
                    try:
                        await ctx.author.send("I didn't get a response from you, hence the game is cancelled.")
                    except:
                        self.planning_numberevent.remove(ctx.author.id)
                        return await ctx.send(f"The game was cancelled as I can't DM {ctx.author}.")
                    else:
                        self.planning_numberevent.remove(ctx.author.id)
                        return await ctx.send(f"I didn't get a response from {ctx.author.mention}, hence the game is cancelled.")
                else:
                    if inputmessage.content.lower() == 'cancel':
                        self.planning_numberevent.remove(ctx.author.id)
                        await ctx.author.send("I have cancelled your Guess the Number game.")
                        return await ctx.send(f"{ctx.author} has cancelled the Guess the Number game.")
                    content = inputmessage.content.replace(' ', '')
                    content = content.replace(',', '')
                    content = content.split('-')
                    if len(content) != 2:
                        error = "You didn't provide a valid range."
                    else:
                        nums = []
                        for i in content:
                            try:
                                intval = int(i)
                            except:
                                error = "You didn't provide a proper number."
                            else:
                                nums.append(intval)
                        nums = sorted(nums)
                        if nums[1] - nums[0] > 10000000:
                            error = "The range should not be bigger than 10,000,000."
                        elif nums[1] == nums[0]:
                            error = "You didn't provide a valid range."
                        else:
                            small = nums[0]
                            big = nums[1]
            error = None
            while chosen == None:
                sending = f"What is the correct number that should be guessed? The number should be between {small} and {big} (both inclusive)."
                if error is not None:
                    sending = error + '\n\n' + sending
                await ctx.author.send(embed=discord.Embed(title="Guess the Number game setup: Step 2 of 2", description=sending, color=self.client.embed_color))
                def check(payload):
                    return payload.author == ctx.author and isinstance(payload.channel, discord.DMChannel)
                try:
                    inputmessage = await self.client.wait_for('message', check=check, timeout=30.0)
                except asyncio.TimeoutError:
                    try:
                        await ctx.author.send("I didn't get a response from you, hence the game is cancelled.")
                    except:
                        self.planning_numberevent.remove(ctx.author.id)
                        return await ctx.send(f"The game was cancelled as I can't DM {ctx.author}.")
                    else:
                        self.planning_numberevent.remove(ctx.author.id)
                        return await ctx.send(f"I didn't get a response from {ctx.author.mention}, hence the game is cancelled.")
                else:
                    if inputmessage.content.lower() == 'cancel':
                        self.planning_numberevent.remove(ctx.author.id)
                        await ctx.author.send("I have cancelled your Guess the Number game.")
                        return await ctx.send(f"{ctx.author} has cancelled the Guess the Number game.")
                    content = inputmessage.content
                    content = content.replace(',', '')
                    try:
                        intval = int(content)
                    except:
                        error = "You didn't provide a proper number."
                    else:
                        if intval > big or intval < small:
                            error = f"The number you choose should be between {small} and {big} (both inclusive)."
                        else:
                            chosen = intval
            summary = f"**Summary**\nThe correct number is **{chosen}**, and I will tell people that the number is **between {small} and {big} (both inclusive)**.\n\nNow head to {channel.mention}, and say `start` to initialize the game!"
            await ctx.author.send(summary)
            self.planning_numberevent.remove(ctx.author.id)
            embed = discord.Embed(title="Guess the Number game!", description=f"**{ctx.author}** is starting a Guess the Number game!\nYou have to guess a number that is **between {small} and {big}** (both inclusive).", color=self.client.embed_color)
            self.numberevent_channels.append(channel.id)
            await channel.send(f"{ctx.author.mention}, say `start` to start this game or `cancel` to cancel it!", embed=embed)
            try:
                def check(message):
                    return message.content.lower() in ['start', 'cancel'] and message.author.id == ctx.author.id and message.channel.id == channel.id
                msg = await self.client.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                self.numberevent_channels.remove(channel.id)
                return await channel.send(f"{ctx.author.mention} did not tell me to start or cancel the Guess the Number game. I've automatically cancelled the game.")
            else:
                if msg.content.lower() == 'cancel':
                    self.numberevent_channels.remove(channel.id)
                    return await channel.send("The Guess the Number game has been cancelled.")
                pinmsg = await channel.send(f"The game has started! Remember, **{ctx.author.display_name}**'s chosen number is between {small} and {big}.\nHave fun guessing the number!")
                await pinmsg.pin(reason="Guess the Number game information")
                times_guessed = 0
                has_guessed = False
                while not has_guessed:
                    def check(payload):
                        return payload.channel.id == channel.id
                    try:
                        guessingmsg = await self.client.wait_for('message', check=check, timeout = 600.0)
                    except asyncio.TimeoutError:
                        self.numberevent_channels.remove(channel.id)
                        await pinmsg.unpin(reason="Guess the Number game information")
                        return await ctx.send("No one guessed within the last 10 minutes. Therefore, the Guess the Number game has been cancelled.")
                    else:
                        if guessingmsg.author.id == ctx.author.id:
                            if guessingmsg.content.lower() == 'cancel':
                                self.numberevent_channels.remove(channel.id)
                                await pinmsg.unpin(reason="Guess the Number game information")
                                return await channel.send(f"After `{times_guessed}` times of guessing, {ctx.author.mention} has cancelled the Guess the Number game. The correct number was `{chosen}`.")
                        else:
                            try:
                                guessednum = int(guessingmsg.content)
                            except ValueError:
                                pass
                            else:
                                if guessednum != chosen:
                                    times_guessed += 1
                                else:
                                    self.numberevent_channels.remove(channel.id)
                                    has_guessed = True
                                    embed = discord.Embed(title="<a:dv_aConfettiOwO:837712162079244318> CONGRATULATIONS!", description=f"You got the correct number: `{chosen}`!\nThank you for playing **{ctx.author.display_name}**'s Guess the Number Game!", color=self.client.embed_color).set_footer(text=f'Guessing attempts: `{times_guessed}`')
                                    await pinmsg.unpin(reason="Guess the Number game information")
                                    return await guessingmsg.reply(f"{guessingmsg.author.mention}", embed=embed)

    @checks.requires_roles()
    @checks.is_not_blacklisted()
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.command(name="nickbet", aliases = ['nb'])
    async def nickbet(self, ctx, member: discord.Member = None, duration: str = None):
        """
        Challenge your friend to a nick bet! Both of you will choose a nickname for one another, and one of you will choose a side of the coin.
        If the coin flips onto the side that you choose, you will win! The loser will have their nickname changed.
        """
        if await self.client.pool_pg.fetchval("SELECT user_id FROM freezenick WHERE user_id = $1", ctx.author.id):
            return await ctx.send("Your nickname is currently frozen. Wait until your nickname is unfrozen before placing a nick bet with someone else.")
        if member is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You need to specify who you want to nick bet with.")
        if member == ctx.author:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Don't be shy, go nick bet with other people instead!")
        if member.id in self.nickbets:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("That person is currently nickbetting with someone else.")
        if await self.client.pool_pg.fetchval("SELECT user_id FROM freezenick WHERE user_id = $1", member.id):
            ctx.command.reset_cooldown(ctx)
            raise NicknameIsManaged()
        if await self.client.check_blacklisted_user(member):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"{member} is currently blacklisted from using the bot. You cannot have a nick bet with them.")
        if member.bot:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"🤖 **{member}**: `I'll rather have a nick bet with {random.choice([botacc for botacc in ctx.guild.members if botacc.bot])}.`")
        if duration is not None:
            duration = stringtime_duration(duration)
            if duration is None:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("You need to specify a valid duration. I can only read timings with `y`, `d`, `h`, `m` or `s`.")
            if duration > 86400:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("You can't have a nick bet for longer than 24 hours.")
        class consent(discord.ui.View):
            def __init__(self, target):
                self.response = None
                self.returning_value = None
                self.target = target
                super().__init__(timeout=30.0)

            @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
            async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.returning_value = True
                for b in self.children:
                    b.disabled = True
                await self.response.edit(view=self)
                self.stop()

            @discord.ui.button(label="No", style=discord.ButtonStyle.red)
            async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.returning_value = False
                for b in self.children:
                    b.disabled = True
                await self.response.edit(view=self)
                self.stop()

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user.id != self.target.id:
                    await interaction.response.send_message("These buttons aren't for you!", ephemeral=True)
                    return False
                return True

            async def on_timeout(self) -> None:
                self.returning_value = None
                for b in self.children:
                    b.disabled = True
                await self.response.edit(view=self)
                self.stop()
        view = consent(member)
        self.nickbets.append(member.id)
        self.nickbets.append(ctx.author.id)
        embed = discord.Embed(title=f"Hey {member.name}!", description=f"Would you like to have a nick bet with {ctx.author.name}? {f'The loser will have their nickname frozen for **{humanize_timedelta(seconds=duration)} **.' if duration is not None else ''}", color=self.client.embed_color)
        msg = await ctx.send(member.mention, embed=embed, view=view)
        view.response = msg
        await view.wait()
        if view.returning_value is None:
            ctx.command.reset_cooldown(ctx)
            embed.color, embed.title = discord.Color.red(), "You didn't respond in time."
            with contextlib.suppress(ValueError):
                self.nickbets.remove(member.id)
                self.nickbets.remove(ctx.author.id)
            return await msg.edit(embed=embed)
        elif view.returning_value == False:
            ctx.command.reset_cooldown(ctx)
            with contextlib.suppress(ValueError):
                self.nickbets.remove(member.id)
                self.nickbets.remove(ctx.author.id)
            embed.color, embed.title = discord.Color.red(), "You declined the nick bet :("
            try:
                return await msg.edit(embed=embed)
            except:
                return await ctx.send(embed=embed)
        embed.color, embed.title, embed.description = discord.Color.green(), "You accepted the nick bet. Yay!", "Nicknames **must follow server rules**. That includes the **NSFW rule**.\nFailure to follow these rules will result in a blacklist from the bot, or getting the \"No Tags\" role."
        await msg.edit(embed=embed)
        membernick = None
        authornick = None
        error = None
        while membernick == None:
            msg = f"{ctx.author.mention}, what nickname do you want to give to {member.name}?"
            if error is not None:
                msg = f"{ctx.author.mention}, {error}\nWhat nickname do you want to give to {member.name}?"
            await ctx.send(msg)
            try:
                membernickmsg = await self.client.wait_for('message', check=lambda
                    m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id, timeout=30.0)
            except asyncio.TimeoutError:
                ctx.command.reset_cooldown(ctx)
                with contextlib.suppress(ValueError):
                    self.nickbets.remove(member.id)
                    self.nickbets.remove(ctx.author.id)
                return await ctx.send(f"{ctx.author.name} didn't respond in time, hence this nick bet is cancelled.")
            else:
                if membernickmsg.content.lower() == 'cancel':
                    ctx.command.reset_cooldown(ctx)
                    with contextlib.suppress(ValueError):
                        self.nickbets.remove(member.id)
                        self.nickbets.remove(ctx.author.id)
                    return await ctx.send("This nick bet is cancelled.")
                if await self.client.check_blacklisted_content(membernickmsg.content):
                    error = "you can't use blacklisted words."
                elif len(membernickmsg.content) > 32:
                    error = "a nickname can only be 32 characters long."
                else:
                    membernick = membernickmsg.content
        error = None
        while authornick == None:
            msg = f"{member.mention}, what nickname do you want to give to {ctx.author.name}?"
            if error is not None:
                msg = f"{member.mention}, {error}\nWhat nickname do you want to give to {ctx.author.name}?"
            await ctx.send(msg)
            try:
                authornickmsg = await self.client.wait_for('message', check=lambda
                    m: m.author.id == member.id and m.channel.id == ctx.channel.id, timeout=30.0)
            except asyncio.TimeoutError:
                ctx.command.reset_cooldown(ctx)
                with contextlib.suppress(ValueError):
                    self.nickbets.remove(member.id)
                    self.nickbets.remove(ctx.author.id)
                return await ctx.send(f"{member.mention} didn't respond in time, hence this nick bet is cancelled.")
            else:
                if authornickmsg.content.lower() == 'cancel':
                    ctx.command.reset_cooldown(ctx)
                    with contextlib.suppress(ValueError):
                        self.nickbets.remove(member.id)
                        self.nickbets.remove(ctx.author.id)
                    return await ctx.send("This nick bet is cancelled.")
                if await self.client.check_blacklisted_content(authornickmsg.content):
                    error = "you can't use blacklisted words."
                elif len(authornickmsg.content) > 32:
                    error = "a nickname can only be 32 characters long."
                else:
                    authornick = authornickmsg.content

        class pickACoin(discord.ui.View):
            def __init__(self, ctx: DVVTcontext, target):
                self.response = None
                self.returning_value = None
                self.target = target
                super().__init__(timeout=30.0)

            @discord.ui.button(label="Heads", emoji=discord.PartialEmoji.from_str("<:DVB_CoinHead:905400213785690172>"))
            async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.returning_value = True
                for b in self.children:
                    b.disabled = True
                await self.response.edit(view=self)
                self.stop()

            @discord.ui.button(label="Tails", emoji=discord.PartialEmoji.from_str("<:DVB_CoinTail:905400213676638279>"))
            async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.returning_value = False
                for b in self.children:
                    b.disabled = True
                await self.response.edit(view=self)
                self.stop()

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user.id != self.target.id:
                    await interaction.response.send_message("These buttons aren't for you!", ephemeral=True)
                    return False
                return True

            async def on_timeout(self) -> None:
                self.returning_value = None
                for b in self.children:
                    b.disabled = True
                await self.response.edit(view=self)

        coinpickview = pickACoin(ctx, member)
        embed = discord.Embed(description=f"The nickname chosen for {ctx.author.name} is `{authornick}`.\nThe nickname chosen for {member.name} is `{membernick}`.\n\n{member.name}, please pick a side of the coin, and I'll flip the coin to see who's the winner!", color=self.client.embed_color)
        coinpickmsg = await ctx.send(member.mention, embed=embed, view=coinpickview)
        coinpickview.response = coinpickmsg
        await coinpickview.wait()
        if coinpickview.returning_value is None:
            embed.color, embed.description = discord.Color.red(), "You didn't respond in time."
            ctx.command.reset_cooldown(ctx)
            with contextlib.suppress(ValueError):
                self.nickbets.remove(member.id)
                self.nickbets.remove(ctx.author.id)
            return await coinpickmsg.edit(embed=embed)
        embed.title = f"{member.name} chose {'Heads! <:DVB_CoinHead:905400213785690172>' if coinpickview.returning_value == True else 'Tails! <:DVB_CoinTail:905400213676638279>'}"
        olddesc = f"{embed.description.splitlines()[0]}\n{embed.description.splitlines()[1]}\n"
        embed.description = f"{olddesc}\nI'm flipping the coin..."
        embed.set_thumbnail(url="https://cdn.nogra.me/core/coin_spin.gif")
        try:
            await coinpickmsg.edit(embed=embed)
        except:
            coinpickmsg = await coinpickmsg.send(embed=embed)
        heads_or_tails = random.choice([True, True, True, True, True, True, False, False, False, False, False, False, None])
        await asyncio.sleep(3.0)
        coinflipembed = embed
        if heads_or_tails == None:
            try:
                old_nick = ctx.author.display_name
                await ctx.author.edit(nick=authornick)
                if duration and duration > 0:
                    await self.client.pool_pg.execute("INSERT INTO freezenick(user_id, guild_id, nickname, old_nickname, time, reason) VALUES($1, $2, $3, $4, $5, $6)", ctx.author.id, ctx.guild.id, authornick, old_nick, round(time()) + duration, f"[Nick bet]({ctx.message.jump_url})")
            except discord.HTTPException:
                return await ctx.send(f"I couldn't change some nicknames due to permission issues.")
            try:
                old_nick = member.display_name
                await member.edit(nick=membernick)
                if duration and duration > 0:
                    await self.client.pool_pg.execute("INSERT INTO freezenick(user_id, guild_id, nickname, old_nickname, time, reason) VALUES($1, $2, $3, $4, $5, $6)", member.id, ctx.guild.id, membernick, old_nick, round(time()) + duration, f"[Nick bet]({ctx.message.jump_url})")
            except discord.HTTPException:
                return await ctx.send(f"I couldn't change some nicknames due to permission issues.")
            coinflipembed.description = f"{olddesc}\nOh what just happened...\nLooks like the coin landed on its edge! I guess both of you lost ¯\_(ツ)_/¯"
            coinflipembed.set_thumbnail(url="https://preview.redd.it/x4eb8v0dvsv31.png?auto=webp&s=849a80f279ac59060e2f0bdc35b9c30723bdb745")
            try:
                await coinpickmsg.edit(embed=coinflipembed)
            except:
                await ctx.send(embed=coinflipembed)
            if duration and duration > 0:
                await ctx.send(f"Both {ctx.author.name} and {member.name}'s nicknames have been frozen to their respective chosen nicknames for **{humanize_timedelta(seconds=duration)}**. Their nicknames will be unfrozen <t:{round(time())+duration}:R>.")
            return
        if heads_or_tails == True:
            coinflipembed.description = f"{olddesc}\nThe coin landed on Heads!! <:DVB_CoinHead:905400213785690172>"
            coinflipembed.set_thumbnail(url="https://cdn.discordapp.com/emojis/905400213785690172.png?size=96")
            if coinpickview.returning_value == True:
                coinflipembed.color, coinflipembed.description = discord.Color.green(), coinflipembed.description + f"\n\n{member.name} won the bet! 🎊"
                loser = ctx.author
                nick = authornick
                old_nick = ctx.author.display_name
            else:
                coinflipembed.color, coinflipembed.description = discord.Color.red(), coinflipembed.description + f"\n\n{ctx.author.name} won the bet, and {member.name} lost 🪦"
                loser = member
                nick = membernick
                old_nick = member.display_name
        else:
            coinflipembed.description = f"{olddesc}\nThe coin landed on Tails!! <:DVB_CoinTail:905400213676638279>"
            coinflipembed.set_thumbnail(url="https://cdn.discordapp.com/emojis/905400213676638279.png?size=96")
            if coinpickview.returning_value == True:
                coinflipembed.color, coinflipembed.description = discord.Color.red(), coinflipembed.description + f"\n\n{ctx.author.name} won the bet, and {member.name} lost 🪦"
                loser = member
                nick = membernick
                old_nick = member.display_name
            else:
                coinflipembed.color, coinflipembed.description = discord.Color.green(), coinflipembed.description + f"\n\n{member.name} won the bet! 🎊"
                loser = ctx.author
                nick = authornick
                old_nick = ctx.author.display_name
        try:
            await coinpickmsg.edit(embed=coinflipembed)
        except:
            await ctx.send(embed=coinflipembed)
        with contextlib.suppress(ValueError):
            self.nickbets.remove(member.id)
            self.nickbets.remove(ctx.author.id)
        try:
            await loser.edit(nick=nick)
        except discord.HTTPException:
            await ctx.send(f"I couldn't change the loser's nickname, probably due to role hierachy or missing permissions. Sorry :c\nAsk them to change their nickname to `{authornick}`.")
        else:
            if duration and duration > 0:
                await self.client.pool_pg.execute("INSERT INTO freezenick(user_id, guild_id, nickname, old_nickname, time, reason) VALUES($1, $2, $3, $4, $5, $6)", loser.id, ctx.guild.id, nick, old_nick, round(time()) + duration, f"[Nick bet]({ctx.message.jump_url})")
                await ctx.send(f"{loser.name}'s name has been changed to **{nick}** for **{humanize_timedelta(seconds=duration)}**. Their nickname will be unfrozen <t:{round(time())+duration}:R>.")
            else:
                await ctx.send(f"{loser.name}'s name has been changed to **{nick}**.")