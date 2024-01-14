import time
from datetime import datetime
import asyncpg
import discord
from typing import Optional, Union, List


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

    @staticmethod
    def datetime_to_iso(dt: datetime) -> str:
        """Convert a datetime object to an ISO 8601 formatted string."""
        return dt.isoformat() if dt else None

    def to_presentable_format(self):
        if self.version == 1:
            questions = [
                {
                    "q": "Do you understand why you were banned/what do you think led to your ban?",
                    "d": "Lorem Ipsum",
                    "a": self.appeal_answer1
                },
                {
                    "q": "How will you change to be a positive member of the community?",
                    "d": "Lorem Ipsum",
                    "a": self.appeal_answer2
                },
                {
                    "q": "Is there any other information you would like to provide?",
                    "d": "Lorem Ipsum",
                    "a": self.appeal_answer3
                },
            ]
        return {
            'appeal_id': self.appeal_id,
            'user_id': self.user_id,
            'appeal_timestamp': self.datetime_to_iso(self.appeal_timestamp),
            'ban_reason': self.ban_reason,
            'email': self.email,
            'appeal_status': self.appeal_status,
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
            'version': self.version
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

    async def update_ban_appeal(self, appeal: BanAppeal):
        await self.db.execute(
            "UPDATE BanAppeals SET appeal_answer1 = $1, appeal_answer2 = $2, appeal_answer3 = $3, email = $4, appeal_status = $5, reviewed_timestamp = $6, reviewer_id = $7, reviewer_response = $8 WHERE appeal_id = $9",
            appeal.appeal_answer1, appeal.appeal_answer2, appeal.appeal_answer3, appeal.email, appeal.appeal_status,
            appeal.reviewed_timestamp, appeal.reviewer_id, appeal.reviewer_response, appeal.appeal_id)

    async def add_new_ban_appeal(self, user_id: int, ban_reason: str, appeal_answer1: str,
                                 appeal_answer2: str, appeal_answer3: str) -> bool:
        try:
            await self.db.execute(
                "INSERT INTO BanAppeals (user_id, appeal_timestamp, ban_reason, appeal_answer1, appeal_answer2, appeal_answer3) VALUES ($1, $2, $3, $4, $5, $6)",
                user_id, discord.utils.utcnow(), ban_reason, appeal_answer1, appeal_answer2, appeal_answer3)
            return True
        except Exception as e:
            print(f"Failed to add new ban appeal: {e}")
            return False
