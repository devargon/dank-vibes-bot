import time
from datetime import datetime
import asyncpg
import discord
from typing import Optional, Union, List

from utils.format import print_exception


class BanAppeal:
    def __init__(self, record: asyncpg.Record):
        self.appeal_id: int = record.get('appeal_id')
        self.user_id: int = record.get('user_id')
        self.appeal_timestamp: datetime = record.get('appeal_timestamp')
        self.ban_reason: str = record.get('ban_reason')
        self.appeal_answer1: str = record.get('appeal_answer1')
        self.appeal_answer2: str = record.get('appeal_answer2')
        self.appeal_answer3: str = record.get('appeal_answer3')
        self.email: str = record.get('email')
        self.appeal_status: int = record.get('appeal_status')
        self.reviewed_timestamp: datetime = record.get('reviewed_timestamp')
        self.reviewer_id: int = record.get('reviewer_id')
        self.reviewer_response: str = record.get('reviewer_response')
        self.version: int = record.get('version')
        self.guild_id: int = record.get('guild_id')
        self.channel_id: int = record.get('channel_id')
        self.updated: bool = record.get('updated')
        self.posted: bool = record.get('posted')
        self.message_id: int = record.get('message_id')
        self.last_reminder: bool = record.get('last_reminder')

    def __repr__(self):
        return f"BanAppeal(appeal_id={self.appeal_id}, user_id={self.user_id}, appeal_timestamp={self.appeal_timestamp}, ban_reason='{self.ban_reason}', appeal_answer1='{self.appeal_answer1}', appeal_answer2='{self.appeal_answer2}', appeal_answer3='{self.appeal_answer3}', email='{self.email}', appeal_status={self.appeal_status}, reviewed_timestamp={self.reviewed_timestamp}, reviewer_id={self.reviewer_id}, reviewer_response='{self.reviewer_response}', version={self.version}, guild_id={self.guild_id}, channel_id={self.channel_id}, message_id={self.message_id}, updated={self.updated}, posted={self.posted}, last_reminder={self.last_reminder})"

    @staticmethod
    def datetime_to_iso(dt: datetime) -> str:
        """Convert a datetime object to an ISO 8601 formatted string."""
        return dt.isoformat() if dt else None

    def to_full_format(self):
        if self.version == 1:
            questions = [
                {
                    "q": "Do you understand why you were banned/what do you think led to your ban?",
                    "d": "Explain your understanding of the ban reasons and your actions leading up to it.",
                    "a": self.appeal_answer1
                },
                {
                    "q": "How will you change to be a positive member of the community?",
                    "d": "Detail your plan to improve and positively engage with the community.",
                    "a": self.appeal_answer2
                },
                {
                                    "q": "Is there any other information you would like to provide?",
                    "d": "Add any extra information or context about your ban and appeal that you think might be useful for us to know.",
                    "a": self.appeal_answer3
                },
            ]
        else:
            questions = []
        return {
            "appeal_id": self.appeal_id,
            "user_id": self.user_id,
            "appeal_timestamp": self.datetime_to_iso(self.appeal_timestamp),
            "ban_reason": self.ban_reason,
            "questions": questions,
            "email": self.email,
            "appeal_status": self.appeal_status,
            "reviewed_timestamp": self.datetime_to_iso(self.reviewed_timestamp),
            "reviewer_id": self.reviewer_id,
            "reviewer_response": self.reviewer_response,
            "version": self.version,
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "updated": self.updated,
            "posted": self.posted,
            "message_id": self.message_id
        }

    def to_presentable_format(self):
        if self.version == 1:
            questions = [
                {
                    "q": "Do you understand why you were banned/what do you think led to your ban?",
                    "d": "Explain your understanding of the ban reasons and your actions leading up to it.",
                    "a": self.appeal_answer1
                },
                {
                    "q": "How will you change to be a positive member of the community?",
                    "d": "Detail your plan to improve and positively engage with the community.",
                    "a": self.appeal_answer2
                },
                {
                                    "q": "Is there any other information you would like to provide?",
                    "d": "Add any extra information or context about your ban and appeal that you think might be useful for us to know.",
                    "a": self.appeal_answer3
                },
            ]
        else:
            questions = []
        return {
            'appeal_id': self.appeal_id,
            'user_id': self.user_id,
            'appeal_timestamp': self.datetime_to_iso(self.appeal_timestamp),
            'ban_reason': self.ban_reason,
            'email': self.email,
            'appeal_status': self.appeal_status,
            'reviewed_timestamp': self.datetime_to_iso(self.reviewed_timestamp),
            'reviewer_response': self.reviewer_response,
            'version': self.version,
            'questions': questions
        }

    def to_public_dict(self) -> dict:
        """Converts to a dictionary for public view, excluding some fields."""
        print(self.appeal_timestamp.tzinfo)
        return {
            'appeal_id': self.appeal_id,
            'user_id': self.user_id,
            'appeal_timestamp': self.datetime_to_iso(self.appeal_timestamp),
            'ban_reason': self.ban_reason,
            'appeal_answer1': self.appeal_answer1,
            'appeal_answer2': self.appeal_answer2,
            'appeal_answer3': self.appeal_answer3,
            'email': self.email,
            'appeal_status': self.appeal_status,
            "reviewed_timestamp": self.datetime_to_iso(self.reviewed_timestamp),
            'reviewer_response': self.reviewer_response,
            'version': self.version,
        }

    def to_moderator_dict(self) -> dict:
        """Converts to a dictionary for moderator view, including all fields."""
        return {
            'appeal_id': self.appeal_id,
            'user_id': self.user_id,
            'appeal_timestamp': self.datetime_to_iso(self.appeal_timestamp),
            'ban_reason': self.ban_reason,
            'appeal_answer1': self.appeal_answer1,
            'appeal_answer2': self.appeal_answer2,
            'appeal_answer3': self.appeal_answer3,
            'email': self.email,
            'appeal_status': self.appeal_status,
            'reviewed_timestamp': self.datetime_to_iso(self.reviewed_timestamp),
            'reviewer_id': self.reviewer_id,
            'reviewer_response': self.reviewer_response,
            'version': self.version,
            'guild_id': self.guild_id,
            'channel_id': self.channel_id,
            'message_id': self.message_id
        }


class BanAppealDB:
    def __init__(self, db):
        self.db: asyncpg.Pool = db

    async def get_ban_appeal_by_appeal_id(self, appeal_id: int) -> BanAppeal:
        result = await self.db.fetchrow(
            "SELECT * FROM BanAppeals WHERE appeal_id = $1 ORDER BY appeal_timestamp DESC LIMIT 1", appeal_id)
        if result is not None:
            return BanAppeal(result)
        return None

    async def get_user_latest_ban_appeal(self, user_id: int) -> BanAppeal:
        result = await self.db.fetchrow("SELECT * FROM BanAppeals WHERE user_id = $1 ORDER BY appeal_timestamp DESC LIMIT 1", user_id)
        if result is not None:
            return BanAppeal(result)
        return None

    async def get_all_awaiting_ban_appeals(self) -> List[BanAppeal]:
        result = await self.db.fetch("SELECT * FROM banappeals WHERE appeal_status = 0 ORDER BY appeal_timestamp")
        results = []
        for i in result:
            results.append(BanAppeal(i))
        return results

    async def get_user_all_ban_appeals(self, user_id: int) -> List[BanAppeal]:
        result = await self.db.fetch("SELECT * FROM BanAppeals WHERE user_id = $1 ORDER BY appeal_id DESC", user_id)
        results = []
        for i in result:
            results.append(BanAppeal(i))
        return results

    async def get_all_ban_appeals(self, limit: Optional[int] = 10) -> List[BanAppeal]:
        if limit is not None and isinstance(limit, int):
            raw = await self.db.fetch("SELECT * FROM BanAppeals ORDER BY appeal_timestamp DESC LIMIT $1", limit)
        else:
            raw = await self.db.fetch("SELECT * FROM BanAppeals ORDER BY appeal_timestamp DESC")
        return [BanAppeal(record) for record in raw]

    async def get_ban_appeals_awaiting_update(self) -> List[BanAppeal]:
        raw = await self.db.fetch("SELECT * FROM BanAppeals WHERE updated = FALSE")
        return [BanAppeal(record) for record in raw]

    async def get_ban_appeals_awaiting_post(self) -> List[BanAppeal]:
        raw = await self.db.fetch("SELECT * FROM BanAppeals WHERE posted = FALSE")
        return [BanAppeal(record) for record in raw]


    async def update_ban_appeal(self, appeal: BanAppeal):
        await self.db.execute(
            "UPDATE BanAppeals SET appeal_answer1 = $1, appeal_answer2 = $2, appeal_answer3 = $3, email = $4, appeal_status = $5, reviewed_timestamp = $6, reviewer_id = $7, reviewer_response = $8, guild_id = $9, channel_id = $10, message_id = $11, updated = $12, posted = $13, last_reminder = $14 WHERE appeal_id = $15",
            appeal.appeal_answer1, appeal.appeal_answer2, appeal.appeal_answer3, appeal.email, appeal.appeal_status,
            appeal.reviewed_timestamp, appeal.reviewer_id, appeal.reviewer_response, appeal.guild_id, appeal.channel_id, appeal.message_id, appeal.updated, appeal.posted, appeal.last_reminder, appeal.appeal_id)

    async def add_new_ban_appeal(self, user_id: int, ban_reason: str, appeal_answer1: str,
                                 appeal_answer2: str, appeal_answer3: str) -> Optional[int]:
        try:
            appeal_id = await self.db.fetchval(
                "INSERT INTO BanAppeals (user_id, appeal_timestamp, ban_reason, appeal_answer1, appeal_answer2, appeal_answer3) "
                "VALUES ($1, $2, $3, $4, $5, $6) RETURNING appeal_id",
                user_id, discord.utils.utcnow(), ban_reason, appeal_answer1, appeal_answer2, appeal_answer3)
            return appeal_id
        except Exception as e:
            print_exception(f"Failed to add new ban appeal: {e}")
            return None
