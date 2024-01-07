import time

import asyncpg
import discord
from typing import Optional, Union, List


class Voter:
    def __init__(self, record: asyncpg.Record, member: Optional[discord.Member] = None):
        self.member_id: int = record.get('member_id')
        self.count: int = record.get('count')
        self.rmtype: int = record.get('rmtype')
        self.rmtime: int = record.get('rmtime')
        self.member: discord.Member = member


class VoteDB:
    def __init__(self, db):
        self.db: asyncpg.Pool = db

    async def get_voter(self, member: discord.Member) -> Voter:
        result = await self.db.fetchrow("SELECT * FROM voters WHERE member_id = $1 LIMIT 1", member.id)
        if result is None:
            await self.db.execute("INSERT INTO voters(member_id) VALUES($1)", member.id)
            result = {'member_id': member.id, 'rmtype': 1, 'count': 0, 'rmtime': None}
        return Voter(result, member)

    async def get_voters(self, expiring=True, limit: Optional[int] = 10) -> List[Voter]:
        if expiring:
            raw = await self.db.fetch("SELECT * FROM voters WHERE voters.rmtime < $1", round(time.time()))
        else:
            if limit is not None and type(limit) == int:
                raw = await self.db.fetch("SELECT * FROM voters ORDER BY count DESC LIMIT $1", limit)
            else:
                raw = await self.db.fetch("SELECT * FROM voters WHERE count > 0 ORDER BY count DESC")
        arr = []
        for i in raw:
            arr.append(Voter(i))
        return arr

    async def update_voter(self, voter: Voter):
        await self.db.execute("UPDATE voters SET count = $1, rmtype = $2, rmtime = $3 WHERE member_id = $4", voter.count, voter.rmtype, voter.rmtime, voter.member.id if voter.member is not None else voter.member_id)
        return voter

    async def add_one_votecount(self, member: discord.Member) -> Union[bool, Voter]:
        voter: Voter = await self.get_voter(member)
        voter.count = voter.count + 1
        updated_voter = await self.update_voter(voter)
        return updated_voter
