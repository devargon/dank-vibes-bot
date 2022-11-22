import discord
from discord.ext import commands
from discord import SlashCommandGroup
from .subscribe_objects import *
from main import dvvt
from utils.buttons import confirm


class Subscribe(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
        self.nsl_manager: NewsletterManager = NewsletterManager(self.client)

    async def users_newsletters_autocomplete(self, ctx: discord.AutocompleteContext):
        nsl_ids = await self.client.db.fetch("SELECT nsl_id FROM newsletter WHERE author_id = $1", ctx.interaction.user.id)
        nsl_id_list = []
        for nsl_id in nsl_ids:
            nsl_id_list.append(nsl_id.get("nsl_id"))
        return nsl_id_list

    async def subscribed_newsletters_autocomplete(self, ctx: discord.AutocompleteContext):
        nsl_ids = await self.client.db.fetch("SELECT DISTINCT nsl_id FROM newsletter_subscribers WHERE user_id = $1", ctx.interaction.user.id)
        nsl_id_list = []
        for nsl_id in nsl_ids:
            nsl_id_list.append(nsl_id.get("nsl_id"))
        return nsl_id_list


    Subscribe_cmd = SlashCommandGroup("subscription", "Manage your newsletter subscriptions")
    Newsletter_cmd = SlashCommandGroup("newsletter", "Manage your newsletter", default_member_permissions=discord.Permissions(manage_roles=True))

    @Subscribe_cmd.command(name="subscribe", description="Subscribe to a newsletter")
    async def subscribe(self, ctx: discord.ApplicationContext, newsletter_id: discord.Option(str, "The newsletter ID", required=True)):
        newsletter = await self.nsl_manager.get_newsletter(newsletter_id)
        if newsletter is None:
            return await ctx.respond("This newsletter does not exist.")
        await newsletter.add_subscriber(ctx.author)
        await ctx.respond(f"You have subscribed to **{newsletter.name}**.")

    @Subscribe_cmd.command(name="unsubscribe", description="Unsubscribe from a newsletter")
    async def unsubscribe(self, ctx: discord.ApplicationContext, newsletter_id: discord.Option(str, "The newsletter ID", required=True)):
        newsletter = await self.nsl_manager.get_newsletter(newsletter_id)
        if newsletter is None:
            return await ctx.respond("This newsletter does not exist.")
        if ctx.author not in newsletter.subscribers:
            return await ctx.respond(f"You are not subscribed to the **{newsletter.name}** newsletter.")
        else:
            await newsletter.remove_subscriber(ctx.author)
            await ctx.respond(f"You have unsubscribed from **{newsletter.name}**.")

    @Subscribe_cmd.command(name="info", description="Get newsletter information")
    async def info(self, ctx: discord.ApplicationContext, newsletter_id: discord.Option(str, "The newsletter ID", required=True)):
        newsletter = await self.nsl_manager.get_newsletter(newsletter_id)
        if newsletter is None:
            return await ctx.respond("This newsletter does not exist.")
        embed = discord.Embed(title=newsletter.name, description=newsletter.description, color=discord.Color.blurple())
        embed.add_field(name="Newsletter ID", value=newsletter.nsl_id)
        if newsletter.author is not None:
            embed.set_author(name=newsletter.author.name, icon_url=newsletter.author.avatar.with_size(64).url)
        if ctx.author in newsletter.subscribers:
            embed.set_footer(text="You're subscribed to this newsletter.", icon_url="https://cdn.discordapp.com/attachments/871737314831908974/1044261855432036482/unknown.png")
        else:
            embed.set_footer(text="You're not subscribed to this newsletter.")
        await ctx.respond(embed=embed)

    @Newsletter_cmd.command(name="create", description="Create a newsletter")
    async def create(self, ctx: discord.ApplicationContext,
                     name: discord.Option(str, "The newsletter name", required=True, max_length=100),
                     nsl_id: discord.Option(str, "The ID of your newsletter (used for identification). It should be as short as possible.", required=True, name="id", max_length=10),
                     description: discord.Option(str, "The newsletter description", required=True),
                     content_type: discord.Option(str, "How the content will be posted (as normal text or as an embed)", choices=["text", "embed"], required=True),
                     icon_url: discord.Option(str, "The thumbnail for your newsletter", required=False) = "",
                     ):
        if await self.nsl_manager.get_newsletter(nsl_id) is not None:
            return await ctx.respond(f"A newsletter with the ID `{nsl_id}` already exists.")
        await self.client.db.execute("INSERT INTO newsletter(nsl_id, name, description, author_id, content_type, autopost_interval, icon_url) VALUES ($1, $2, $3, $4, $5, $6, $7)", nsl_id, name, description, ctx.author.id, content_type, 0, icon_url)
        nsl = await self.nsl_manager.get_newsletter(nsl_id)
        await nsl.add_subscriber(ctx.author)
        embed = await nsl.embed(ctx.author)
        await ctx.respond(f"Newsletter **{nsl.name}** created. You're automatically subscribed to it.", embed=embed)

    @Newsletter_cmd.command(name="force-subscribe", description="Force subscribe a user to a newsletter")
    async def force_subscribe(self, ctx: discord.ApplicationContext, user: discord.Option(discord.Member, "The user to subscribe", required=True), newsletter_id: discord.Option(str, "The newsletter ID", required=True, autocomplete=users_newsletters_autocomplete)):
        newsletter = await self.nsl_manager.get_newsletter(newsletter_id)
        if newsletter is None:
            return await ctx.respond("This newsletter does not exist.")
        await newsletter.add_subscriber(user)
        await ctx.respond(f"{user.mention} has been subscribed to **{newsletter.name}**.")
        nsl_embed = await newsletter.embed(user)
        await user.send(f"You have been automatically subscribed to the newsletter **{newsletter.name}** by **{ctx.author}**.", embed=nsl_embed)

    @Newsletter_cmd.command(name="force-unsubscribe", description="Force unsubscribe a user from a newsletter")
    async def force_unsubscribe(self, ctx: discord.ApplicationContext,
                                user: discord.Option(discord.Member, "The user to unsubscribe", required=True),
                                newsletter_id: discord.Option(str, "The newsletter ID", required=True, autocomplete=users_newsletters_autocomplete)
                                ):
        newsletter = await self.nsl_manager.get_newsletter(newsletter_id)
        if newsletter is None:
            return await ctx.respond("This newsletter does not exist.")
        if user not in newsletter.subscribers:
            return await ctx.respond(f"{user.mention} is not subscribed to the **{newsletter.name}** newsletter.")
        else:
            await newsletter.remove_subscriber(user)
            await ctx.respond(f"{user.mention} has been unsubscribed from **{newsletter.name}**.")
            nsl_embed = await newsletter.embed()
            await user.send(f"You have been automatically unsubscribed from the newsletter **{newsletter.name}** by **{ctx.author}**.", embed=nsl_embed)

    @Newsletter_cmd.command(name="delete", description="Delete a newsletter")
    async def delete(self, ctx: discord.ApplicationContext, newsletter_id: discord.Option(str, "The newsletter ID", required=True, autocomplete=users_newsletters_autocomplete)):
        newsletter = await self.nsl_manager.get_newsletter(newsletter_id)
        if newsletter is None:
            return await ctx.respond("This newsletter does not exist.")
        if newsletter.author != ctx.author:
            return await ctx.respond("You are not the author of this newsletter.")
        c = confirm(ctx, self.client, 30.0)
        if len(newsletter.subscribers) <= 30:
            a = f"\n    • **{newsletter.name}**'s subscribers will be notified of the deletion."
        else:
            a = f"\n    • Since **{newsletter.name}** has more than 30 subscribers, its subscribers will not be notified of the deletion."
        embed = discord.Embed(title="Are you sure you want to delete your newsletter?", description=f"Your newsletter, **{newsletter.name}** will be permanently removed.\n    • All subscribers to **{newsletter.name}** will be removed.\n    • Any existing auto-posts for **{newsletter.name}** will be removed.\n    •Anyone can use your Newsletter ID (`{newsletter.nsl_id}`) to create their own newsletter." + a, color=discord.Color.orange())
        c.response = await ctx.respond(embed=embed, view=c)
        await c.wait()
        if c.returning_value is not True:
            embed.color = discord.Color.red()
            embed.description = "Newsletter deletion cancelled."
        else:
            embed.description += "\n"
            if len(newsletter.subscribers) <= 30:
                embed.description += f"\nNotifying subscribers of **{newsletter.name}**..."
                await c.response.edit_original_message(embed=embed)
                for member in newsletter.subscribers:
                    try:
                        await member.send(f"You have been unsubscribed from the newsletter **{newsletter.name}** as it is being removed by the author.")
                    except:
                        pass
            embed.description += f"\nDeleting newsletter **{newsletter.name}**..."
            await c.response.edit_original_message(embed=embed)
            await self.client.db.execute("DELETE FROM newsletter WHERE nsl_id = $1", newsletter.nsl_id)
            await self.client.db.execute("DELETE FROM newsletter_subscribers WHERE nsl_id = $1", newsletter.nsl_id)
            await self.client.db.execute("DELETE FROM newsletter_autoposts WHERE nsl_id = $1", newsletter.nsl_id)
            embed.color = discord.Color.green()
            embed.description += f"\n\n**Newsletter deleted.**"
        await c.response.edit_original_message(embed=embed)









