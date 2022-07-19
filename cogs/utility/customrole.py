import discord
from discord.ext import commands
from utils.converters import BetterBetterRoles, BetterColor
from utils.buttons import confirm
from utils.paginator import SingleMenuPaginator
from typing import Union, Optional
from utils.context import DVVTcontext
from utils import checks
from main import dvvt


class RoleList(discord.Embed):
    def __init__(self, client, guild, description=discord.Embed.Empty):
        super().__init__(title=f"Custom Roles for {guild.name}", color=client.embed_color, description=description)

class CustomRoleManagement(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @checks.has_permissions_or_role(manage_roles=True)
    @commands.group(name="customrole", aliases=["crole", "cr"], invoke_without_command=True)
    async def customrole(self, ctx: DVVTcontext, *, member_or_role: Optional[Union[discord.Member, BetterBetterRoles]] = None):
        """
        View all custom roles in the server. You can also see the users who own a single role, or the role that a user owns.
        One user can only have one custom role, but one custom role can be assigned to many users.
        """
        if member_or_role is None:
            roles_db = await self.client.db.fetch("SELECT * FROM customroles WHERE guild_id = $1", ctx.guild.id)
            if len(roles_db) == 0:
                page_embeds = [RoleList(self.client, ctx.guild, "No custom roles found.")]
            else:
                page_embeds = []
                embed = RoleList(self.client, ctx.guild)
                for role_db in roles_db:
                    role = ctx.guild.get_role(role_db.get('role_id'))
                    if role is not None:
                        member = self.client.get_user(role_db.get('user_id'))
                        member_disp = f"{member} {member.mention}" if member is not None else f"{role_db.get('user_id')} (unknown)"
                        embed.add_field(name=role.name, value=member_disp, inline=True)
                        if len(embed) > 6000:
                            embed.remove_field(-1)
                            page_embeds.append(embed)
                            embed = RoleList(self.client, ctx.guild)
                            embed.add_field(name=role.name, value=member_disp, inline=True)
                    else:
                        continue
                if len(page_embeds) == 0:
                    if len(embed.fields) == 0:
                        embed.description = "No custom roles found."
                    page_embeds.append(embed)
                else:
                    if page_embeds[-1] != embed:
                        page_embeds.append(embed)
            paginator = SingleMenuPaginator(pages=page_embeds)
            await paginator.send(ctx)
        else:
            if isinstance(member_or_role, discord.Member):
                member = member_or_role
                role_db = await self.client.db.fetchrow("SELECT role_id FROM customroles WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
                if role_db is None:
                    await ctx.send(f"**{member}** does not own a custom role.")
                else:
                    role = ctx.guild.get_role(role_db.get('role_id'))
                    if role is None:
                        await ctx.send(f"**{member}** does not own a custom role.")
                    else:
                        embed = discord.Embed(title=f"{member} owns the custom role", description=role.mention, color=self.client.embed_color)
                        await ctx.send(embed=embed)
            elif isinstance(member_or_role, discord.Role) or isinstance(member_or_role, BetterBetterRoles):
                role = member_or_role
                roles_db = await self.client.db.fetch("SELECT user_id FROM customroles WHERE guild_id = $1 AND role_id = $2", ctx.guild.id, role.id)
                if len(roles_db) == 0:
                    await ctx.send(f"**{role}** is not owned by any member.")
                else:
                    roles_disp = []
                    for role_db in roles_db:
                        user = self.client.get_user(role_db.get('user_id'))
                        if user is not None:
                            roles_disp.append(f"• **{user}** ({user.mention})")
                    embed = discord.Embed(title=f"{role} is owned by these users:", description="\n".join(roles_disp), color=self.client.embed_color)
                    await ctx.send(embed=embed)
            else:
                await ctx.send("Invalid argument.")

    @checks.has_permissions_or_role(manage_roles=True)
    @customrole.command(name="list", aliases=['view'])
    async def customrole_list(self, ctx: DVVTcontext, *, member_or_role: Optional[Union[discord.Member, BetterBetterRoles]] = None):
        """
        View all custom roles in the server. You can also see the users who own a single role, or the role that a user owns.
        One user can only have one custom role, but one custom role can be assigned to many users.
        """
        await ctx.invoke(ctx.command.parent, member_or_role=member_or_role)

    @checks.has_permissions_or_role(manage_roles=True)
    @customrole.command(name="set", aliases=['give'])
    async def customrole_set(self, ctx: DVVTcontext, member: discord.Member, *, role: BetterBetterRoles):
        """
        Set a role to be owned by a user, making it their custom role.
        The role will automatically be added to the user.
        One user can only have one custom role, but one custom role can be assigned to many users.
        """
        existing = await self.client.db.fetchrow("SELECT * FROM customroles WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
        if existing is not None:
            confirmview = confirm(ctx, self.client, 30)
            embed = discord.Embed(title=f"Are you sure you want to change {member}'s custom role?", description=f"**{member}** currently owns the custom role <@&{existing.get('role_id')}>.", color=discord.Color.yellow())
            confirmview.response = await ctx.send(embed=embed, view=confirmview)
            await confirmview.wait()
            if confirmview.returning_value is not True:
                embed.description += "\n\nNo action was taken."
                await confirmview.response.edit(embed=embed)
                return
            else:
                await self.client.db.execute("DELETE FROM customroles WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
        existing_owners = await self.client.db.fetch("SELECT * FROM customroles WHERE guild_id = $1 AND role_id = $2", ctx.guild.id, role.id)
        await self.client.db.execute("INSERT INTO customroles (guild_id, user_id, role_id) VALUES ($1, $2, $3)", ctx.guild.id, member.id, role.id)
        added_role = False
        if role >= ctx.me.top_role:
            can_handle = False
        else:
            can_handle = True
            if role not in member.roles:
                await member.add_roles(role, reason=f"Custom Role Added by {ctx.author} ({ctx.author.id})")
                added_role = True


        formatted_existing_owners = []
        if len(existing_owners) > 0:
            for i in existing_owners:
                us = i.get('user_id')
                existing_user = self.client.get_user(us)
                existing_user = existing_user or us
                if len(formatted_existing_owners) > 2 and len(formatted_existing_owners) < 3:
                    formatted_existing_owners.append(f" and {len(existing_owners) - 2} other user(s)")
                    break
                else:
                    formatted_existing_owners.append(f"{existing_user}")

        finalmsg = [f"**{member}** now owns the custom role **{role.name}**."]
        if added_role:
            finalmsg.append(f"It has been automatically added to **{member}**'s roles.")
        if len(formatted_existing_owners) > 0:
            finalmsg.append(f"⚠️ **{', '.join(formatted_existing_owners)} also own this role.**")
        if not can_handle:
            finalmsg.append("⚠️ **This role is higher than my highest role.** I may not be able to manage the role.")


        await ctx.send("\n".join(finalmsg))

    @checks.has_permissions_or_role(manage_roles=True)
    @customrole.command(name="remove", aliases=['delete', 'clear'])
    async def customrole_remove(self, ctx: DVVTcontext, *, member_or_role: Optional[Union[discord.Member, BetterBetterRoles]]):
        """
        Remove a custom role from a user.
        You can also reset a custom role's users by inputting a role instead.
        """
        if isinstance(member_or_role, discord.Member):
            member = member_or_role
            existing = await self.client.db.fetchrow("SELECT * FROM customroles WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
            if existing is None:
                await ctx.send(f"**{member}** does not own a custom role.")
            else:
                role_id = existing.get('role_id')
                role = ctx.guild.get_role(role_id)
                if role is not None and role < ctx.me.top_role:
                    await member.remove_roles(role, reason=f"Custom Role Removed by {ctx.author} ({ctx.author.id})")
                await self.client.db.execute("DELETE FROM customroles WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, member.id)
                await ctx.send(f"**{member}** no longer owns the custom role **{role.name if role is not None else role_id}**.")
        else:
            role: discord.Role = member_or_role
            existing = await self.client.db.fetch("SELECT * FROM customroles WHERE guild_id = $1 AND role_id = $2", ctx.guild.id, role.id)
            if len(existing) == 0:
                await ctx.send(f"**{role}** is not owned by any member.")
            else:
                async with ctx.typing():
                    members_disp = []
                    for i in existing:
                        member = ctx.guild.get_member(i.get('user_id'))
                        if member is not None and role < ctx.me.top_role:
                            await member.remove_roles(role, reason=f"Custom Role Removed by {ctx.author} ({ctx.author.id})")
                        if len(members_disp) < 10:
                            members_disp.append(f"• {member.name}" if member is not None else f"• {i.get('user_id')}")
                        else:
                            if len(members_disp) < 11:
                                members_disp.append(f"and {len(existing) - len(members_disp)} other member(s)")
                            else:
                                pass
                    await self.client.db.execute("DELETE FROM customroles WHERE guild_id = $1 AND role_id = $2", ctx.guild.id, role.id)
                    final_summary = [f"**{role.name}** is no longer owned by any member."]
                    if len(members_disp) > 0:
                        final_summary.append("\n\nThe following members no longer own this role:\n")
                        final_summary.append("\n".join(members_disp))
                    await ctx.send("\n".join(final_summary))


    @customrole.command(name="color", aliases=['colour'])
    async def customrole_color(self, ctx: DVVTcontext, color: BetterColor):
        """
        If you have a custom role, use this command to change the color of it.
        """
        if color is None:
            return await ctx.send("Please provide a valid color in the format of:\n`#FFFFFF`\n`FFFFFF`\n`0xFFFFFF`\n`0x#FFFFFF`\n`rgb(255, 255, 255)`\nA colour name")
        failembed = discord.Embed(title="Role Edit Failed", color=discord.Color.red())
        users_role = await self.client.db.fetchval("SELECT role_id FROM customroles WHERE guild_id = $1 AND user_id = $2", ctx.guild.id, ctx.author.id)
        if users_role is None:
            failembed.description = "You do not own a custom role."
            return await ctx.send(embed=failembed)
        role = ctx.guild.get_role(users_role)
        if role is None:
            failembed.description = "You do not own a custom role."
            return await ctx.send(embed=failembed)


        if role >= ctx.me.top_role:
            failembed.description = "⚠️ **This role is higher than my highest role.** I cannot edit the color."
            return await ctx.send(embed=failembed)
        old_color = ((hex(role.color.value))[2:]).zfill(6)
        try:
            await role.edit(color=color, reason=f"Requested by role owner {ctx.author} ({ctx.author.id})")
        except discord.Forbidden as e:
            failembed.description = str(e)
            return await ctx.send(embed=failembed)
        except Exception as e:
            failembed.description = f"An unexpected error occured: {e}"
            return await ctx.send(embed=failembed)
        else:
            embed = discord.Embed(
                title="Role Edit Successful",
                description=f"Your custom role, **{role.name}**'s color has been changed from **#{old_color}** to **#{((hex(color.value))[2:]).zfill(6)}**.",
                color=discord.Color.green()
            )
            embed.set_footer(text="What? You think I'm going to call you wonderful like Yui! In your dreams!")
            await ctx.send(embed=embed)






