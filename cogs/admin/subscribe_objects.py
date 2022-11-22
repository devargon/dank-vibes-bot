import datetime

import asyncpg
from typing import Union, Optional

import discord

import time

from main import dvvt


class NewsletterAutopost:
    __slots__ = ("newsletter", "content_type", "content", "post_time")

    def __init__(self, record: asyncpg.Record, newsletter):
        self.newsletter = newsletter
        self.content_type = record.get("content_type")
        self.content = record.get("content")
        self.post_time = record.get("post_time")


class Newsletter:
    __slots__ = ("nsl_id", "name", "description", "author", "content_type", "autopost_interval", "subscribers", "client", "icon_url")

    def __init__(self, record: asyncpg.Record, client: dvvt):
        self.client = client
        self.nsl_id = record.get("nsl_id")
        self.name = record.get("name")
        self.description = record.get('description')
        self.author = self.client.get_user(record.get('author_id'))
        self.content_type = record.get("content_type")
        self.autopost_interval = record.get("autopost_interval")
        self.icon_url = record.get("icon_url")
        self.subscribers = []

    async def add_subscriber(self, user: Union[discord.User, discord.Member]):
        if user not in self.subscribers:
            await self.client.db.execute("INSERT INTO newsletter_subscribers (nsl_id, user_id, since) VALUES ($1, $2, $3)", self.nsl_id, user.id, round(time.time()))
            self.subscribers.append(user)

    async def remove_subscriber(self, user: Union[discord.User, discord.Member]):
        if user in self.subscribers:
            await self.client.db.execute("DELETE FROM newsletter_subscribers WHERE nsl_id = $1 AND user_id = $2", self.nsl_id, user.id)
            self.subscribers.remove(user)

    async def embed(self, member: Optional[Union[discord.User, discord.Member]] = None):
        embed = discord.Embed(title=self.name, description=self.description, color=discord.Color.blurple())
        embed.set_author(name=f"Editor: {self.author.name}#{self.author.discriminator}", icon_url=self.author.avatar.with_size(64).url)
        if member is None or member not in self.subscribers:
            embed.set_footer(text=f"ID: {self.nsl_id}")
        else:
            since = await self.client.db.fetchval("SELECT since FROM newsletter_subscribers WHERE nsl_id = $1 AND user_id = $2", self.nsl_id, member.id)
            embed.set_footer(text=f"You're subscribed since")
            embed.timestamp = datetime.datetime.fromtimestamp(since)
        if self.icon_url is not None:
            embed.set_thumbnail(url=self.icon_url)
        return embed

    def detailed_embed(self):
        embed = discord.Embed(title=self.name, description=self.description, color=discord.Color.blurple())
        embed.set_author(name=self.author.name, icon_url=self.author.avatar.with_size(64).url)
        embed.set_footer(text=f"ID: {self.nsl_id}")
        embed.add_field(name="Content Type", value=self.content_type)
        embed.add_field(name="Autopost Interval", value=self.autopost_interval)
        embed.add_field(name="Subscribers", value=str(len(self.subscribers)))
        return embed


class NewsletterManager:
    def __init__(self, client: dvvt):
        self.client = client

    async def get_newsletter(self, newsletter_id: str):
        newsl_raw = await self.client.db.fetchrow("SELECT * FROM newsletter WHERE nsl_id = $1", newsletter_id)
        if newsl_raw is not None:
            newsl = Newsletter(newsl_raw, self.client)
            await self.update_newsletter_subscribers(newsl)
            return newsl
        else:
            return None

    async def update_newsletter_subscribers(self, newsletter: Newsletter):
        subscribers = await self.client.db.fetch("SELECT * FROM newsletter_subscribers WHERE nsl_id = $1", newsletter.nsl_id)
        sub_list = []
        for subscriber in subscribers:
            if sub_user := self.client.get_user(subscriber.get("user_id")) is not None:
                sub_list.append(sub_user)
        newsletter.subscribers = sub_list
