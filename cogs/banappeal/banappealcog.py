import os
import re
from datetime import timedelta

import discord
import asyncio
import contextlib

import typing

import server
from aiohttp import ClientSession

from .banappeal_views import BanAppealView
from .banappealdb import BanAppealDB, BanAppeal
from main import dvvt
from utils.format import proper_userf, print_exception
from utils import checks
from utils.buttons import *
from discord.ext import commands, tasks
from .banappeal_discord import BanAppealDiscord
from .banappeal_server import BanAppealServer

server_id = 871734809154707467
banappeal_chn_id = 1194673636196491396

class BanAppealCog(BanAppealServer, BanAppealDiscord, commands.Cog, name='banappeal'):
    """
    Banappeal commands
    """
    def __init__(self, client):
        self.client: dvvt = client
        self.server = server.HTTPServer(
            bot=self.client,
            host="0.0.0.0",
            port=5003,
        )
        self.client.loop.create_task(self._start_server())
        self.discordBanAppealPostQueue: typing.List[BanAppeal] = []
        self.discordBanAppealUpdateQueue: typing.List[BanAppeal] = []
        self.notifyUpdateQueueStarted = False
        self.notifyPostQueueStarted = False
        self.notifyDeadlineAppealsStarted = False

    async def _start_server(self):
        await self.client.wait_until_ready()
        print("Starting custom Web Server for port 5003")
        await self.server.start()

    async def generate_embed(self, appeal: BanAppeal):
        embed = discord.Embed(title=f"Ban Appeal #{appeal.appeal_id}", color=discord.Color.green() if appeal.appeal_status == 2 else discord.Color.red() if appeal.appeal_status == 1 else discord.Color.light_gray());
        appealing_user = await self.client.get_or_fetch_user(appeal.user_id)
        if appealing_user:
            ap_user_disp = f"@{appealing_user.name}" if appealing_user.discriminator == "0" else f"{appealing_user.name}#{appealing_user.discriminator}"
        else:
            ap_user_disp = str(appeal.user_id)
        embed.set_author(name=ap_user_disp, icon_url=appealing_user.display_avatar.with_size(32).url)
        descriptions = []
        descriptions.append("Banned for: " + appeal.ban_reason if appeal.ban_reason is not None else "Not specified")
        descriptions.append("")
        if appeal.appeal_status == 0:
            descriptions.append("Pending, **awaiting review**")
            embed.set_footer(text="Pending, review this appeal BEFORE") # Add a loading graphic?
            embed.timestamp = appeal.appeal_timestamp + timedelta(days=7)
        elif appeal.appeal_status in [1, 2]:
            status_str = "Denied" if appeal.appeal_status == 1 else "Approved"
            embed.set_footer(text=status_str)
            embed.timestamp = appeal.reviewed_timestamp
            if appeal.reviewer_id:
                reviewer_moderator = await self.client.get_or_fetch_user(appeal.reviewer_id)
                if reviewer_moderator:
                    embed.set_footer(text=embed.footer.text, icon_url=reviewer_moderator.display_avatar.with_size(32).url)
                reviewer_disp = f"{reviewer_moderator.mention} ({reviewer_moderator.id})" if reviewer_moderator else f"{appeal.user_id}"
                status_str += f" by {reviewer_disp}"
            if appeal.reviewed_timestamp:
                status_str += f" on <t:{round(appeal.reviewed_timestamp.timestamp())}:F>"
            descriptions.append(status_str)
            if appeal.reviewer_response:
                embed.set_footer(text=embed.footer.text + " with remarks", icon_url=embed.footer.icon_url)
                descriptions.append(f"Reviewer remarks: {appeal.reviewer_response}")
            embed.set_footer(text=embed.footer.text + " on ", icon_url=embed.footer.icon_url)
        else:
            descriptions.append("Status unknown")
        descriptions.append("** **")
        descriptions.append(f"Appeal responses")
        embed.description = "\n".join(descriptions)

        def add_prefix_to_lines(multiline_string):
            lines = multiline_string.split('\n')
            lines_with_prefix = [f"> {line}" for line in lines]
            return '\n'.join(lines_with_prefix)

        if appeal.version == 1:
            qn_1 = "Do you understand why you were banned/what do you think led to your ban?"
            ans_1 = appeal.appeal_answer1.strip()
            ans_1 = add_prefix_to_lines(ans_1) if type(ans_1) == str and len(ans_1.strip()) > 0 else "_ _"
            ans_2 = appeal.appeal_answer2.strip()
            ans_2 = add_prefix_to_lines(ans_2) if type(ans_2) == str and len(ans_2.strip()) > 0 else "_ _"
            ans_3 = appeal.appeal_answer3.strip()
            ans_3 = add_prefix_to_lines(ans_3) if type(ans_3) == str and len(ans_3.strip()) > 0 else "_ _"

            qn_2 = "How will you change to be a positive member of the community?"
            qn_3 = "Is there any other information you would like to provide?"
            qn_id = 1
            embed.add_field(name=f"_{qn_id}. {qn_1}_", value=ans_1, inline=False)
            qn_id += 1
            embed.add_field(name=f"_{qn_id}. {qn_2}_", value=ans_2, inline=False)
            qn_id += 1
            embed.add_field(name=f"_{qn_id}. {qn_3}_", value=ans_3, inline=False)
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.wait_until_ready()
        banappealdb = BanAppealDB(self.client.db)
        self.discordBanAppealPostQueue = await banappealdb.get_ban_appeals_awaiting_post()
        self.discordBanAppealUpdateQueue = await banappealdb.get_ban_appeals_awaiting_update()
        self.check_unposted_appeals.start()
        self.check_unupdated_appeals.start()
        self.check_appeal_deadlines.start()
        self.client.add_view(view=BanAppealView())

    @tasks.loop(seconds=5)
    async def check_unposted_appeals(self):
        if not self.notifyPostQueueStarted:
            self.notifyPostQueueStarted = True
            print("Appeal Post Queue Check started")
        try:
            if len(self.discordBanAppealPostQueue) > 0:
                banappealdb = BanAppealDB(self.client.db)
                print(f"There are {len(self.discordBanAppealPostQueue)} items in the post queue.")
                banappeal_channel = self.client.get_guild(server_id).get_channel(banappeal_chn_id)
                if banappeal_channel is None:
                    raise (ValueError(f"Appeal Post Queue: Hardcoded Channel not found for {server_id}/{banappeal_chn_id}"))
                for appeal in self.discordBanAppealPostQueue:
                    e = await self.generate_embed(appeal)
                    m = await banappeal_channel.send(embed=e, view=BanAppealView(appeal))
                    self.discordBanAppealPostQueue.remove(appeal)
                    appeal.posted = True
                    appeal.guild_id = m.guild.id
                    appeal.channel_id = m.channel.id
                    appeal.message_id = m.id
                    await banappealdb.update_ban_appeal(appeal)
        except Exception as e:
            a = print_exception("Error in Appeal Post Queue", e)
            await self.client.error_channel.send(embed=discord.Embed(title="Error in Appeal Post Queue", description=a))

    @tasks.loop(seconds=5)
    async def check_unupdated_appeals(self):
        await self.client.wait_until_ready()
        if not self.notifyUpdateQueueStarted:
            self.notifyUpdateQueueStarted = True
            print("Appeal Update Queue Check started")
        print("Task for checking unupdated appeals started.")
        try:
            if len(self.discordBanAppealUpdateQueue) > 0:
                banappealdb = BanAppealDB(self.client.db)
                print(f"There are {len(self.discordBanAppealUpdateQueue)} items in the update queue.")
                for appeal in self.discordBanAppealUpdateQueue:
                    channel = self.client.get_channel(appeal.channel_id)
                    embed = await self.generate_embed(appeal)
                    if channel is None:
                        raise ValueError(f"Appeal update queue: Channel not found for {appeal.channel_id}")
                    try:
                        m = await channel.fetch_message(appeal.message_id)
                    except discord.Forbidden:
                        appeal.updated = True
                        await banappealdb.update_ban_appeal(appeal)
                        print(f"Warning: Forbidden permissions for Appeal #{appeal.appeal_id} ({appeal.guild_id}/{appeal.channel_id}/{appeal.message_id})")
                        continue
                    except discord.NotFound: # Send a new message
                        await channel.send(embed=embed, view=BanAppealView(appeal))
                        appeal.updated = True
                        await banappealdb.update_ban_appeal(appeal)
                    else:
                        await m.edit(embed=embed, view=BanAppealView(appeal))
                        appeal.updated = True
                        await banappealdb.update_ban_appeal(appeal)
                    self.discordBanAppealUpdateQueue.remove(appeal)

        except Exception as e:
            a = print_exception("Error in Appeal Update Queue", e)
            await self.client.error_channel.send(embed=discord.Embed(title="Error in Appeal Update Queue", description=a))

    @tasks.loop(seconds=10)
    async def check_appeal_deadlines(self):
        await self.client.wait_until_ready()
        if not self.notifyDeadlineAppealsStarted:
            self.notifyDeadlineAppealsStarted = True
            print("Appeal Deadlines Check started")
        try:
            banappealdb = BanAppealDB(self.client.db)
            appeals = await banappealdb.get_all_awaiting_ban_appeals()
            print(f"There are {len(appeals)} appeals awaiting response.")
            for appeal in appeals:
                day_6 = appeal.appeal_timestamp + timedelta(days=6)
                day_7 = appeal.appeal_timestamp + timedelta(days=7)
                channel = self.client.get_channel(appeal.channel_id)

                if discord.utils.utcnow() >= day_6 and appeal.last_reminder is not True:  # Time to remind
                    if channel is not None:
                        pmessage = channel.get_partial_message(appeal.message_id)
                        msg = f"<@&> <@&> Appeal #{appeal.appeal_id} has not been responded to yet.\nPlease make a decision <t:{round(day_7.timestamp())}:R>, otherwise it'll be automatically denied.\nhttps://discord.com/channels/{appeal.guild_id}/{appeal.channel_id}/{appeal.message_id}"
                        try:
                            await pmessage.reply(msg)
                            appeal.last_reminder = True
                        except discord.Forbidden:  # no permission to send messages in ban appeal channel
                            appeal.last_reminder = True
                        except discord.HTTPException:
                            try:
                                await channel.send(msg)
                                appeal.last_reminder = True
                            except discord.Forbidden:  # no permission to send messages in ban appeal channel
                                appeal.last_reminder = True
                            except discord.HTTPException:
                                continue

                        appeal.updated = False
                        await banappealdb.update_ban_appeal(appeal)
                        self.discordBanAppealUpdateQueue.append(appeal)
                elif discord.utils.utcnow() >= day_7: # automatically deny appeal
                    appeal.reviewer_id = self.client.user.id
                    appeal.appeal_status = 1
                    appeal.reviewed_timestamp = discord.utils.utcnow()
                    appeal.updated = False
                    appealer = await self.client.get_or_fetch_user(appeal.user_id)
                    await banappealdb.update_ban_appeal(appeal)
                    self.discordBanAppealUpdateQueue.append(appeal)
                    if appeal.email is not None:
                        print(
                            f"Appeal #{appeal.appeal_id} has an email associated, will attempt to request the server to send an email.")
                        middleman_server = os.getenv("APPEALS_SERVER_HOST")
                        if not middleman_server:
                            print(f"Middleman server env, APPEALS_SERVER_HOST has not been set.")
                        else:
                            try:
                                async with ClientSession(headers={"authorization": os.getenv("APPEALS_SHARED_SECRET")}) as session:
                                    print(f"Sending Appeal #{appeal.appeal_id} data to notify endpoint")
                                    data = appeal.to_public_dict()
                                    if appealer:
                                        data['username'] = appealer.display_name
                                    a = await session.post(f"{middleman_server}/api/notify-update", json=data)
                                    print(f"#{appeal.appeal_id} data has been sent. Response: {a.status}")
                                    await session.close()
                            except Exception as e:
                                print_exception(f"Error while sending appeal #{appeal.appeal_id} data to endpoint:", e)


        except Exception as e:
            a = print_exception("Error in Appeal Update Queue", e)
            await self.client.error_channel.send(
                embed=discord.Embed(title="Error in Appeal Update Queue", description=a))


    @checks.dev()
    @commands.command(name="updateappealqueue", aliases=["uaq"])
    async def update_appeal_queue(self, ctx):
        banappealdb = BanAppealDB(self.client.db)
        self.discordBanAppealPostQueue = await banappealdb.get_ban_appeals_awaiting_post()
        self.discordBanAppealUpdateQueue = await banappealdb.get_ban_appeals_awaiting_update()
        await ctx.message.add_reaction("👍")
