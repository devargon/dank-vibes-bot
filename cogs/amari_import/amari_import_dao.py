import re

from main import dvvt
from utils.specialobjects import AmariImportWorker, AmariImportTask, AmariImportTaskLog


class AmariImportDAO:
    def __init__(self, client: dvvt):
        self.client: dvvt = client

    async def createAmariImportTask(self, user_id: int, ticket_channel_id: int, ticket_message_id: int, amari_xp_to_add: int, expected_amari_level: int, expected_total_amari_xp: int):
        row = await self.client.db.fetchrow(
            """
            INSERT INTO amari_import_task_queue(
                user_id, enqueued_at, ticket_channel_id, ticket_message_id,
                amari_xp_to_add, expected_amari_level, expected_total_amari_xp
            )
            VALUES ($1, CURRENT_TIMESTAMP, $2, $3, $4, $5, $6)
            RETURNING *
            """,
            user_id, ticket_channel_id, ticket_message_id, amari_xp_to_add, expected_amari_level, expected_total_amari_xp
        )
        return AmariImportTask(row)

    async def fetchAllTasksOrderedByCreatedAt(self):
        tasks = []
        task_records = await self.client.db.fetch("SELECT * FROM amari_import_task_queue_with_position ORDER BY created_at")
        for task_record in task_records:
            tasks.append(AmariImportTask(task_record))
        return tasks

    async def fetchAllTasksForUser(self, user_id: int):
        tasks = []
        task_records = await self.client.db.fetch("SELECT * FROM amari_import_task_queue WHERE user_id = $1 ORDER BY created_at", user_id)
        for task_record in task_records:
            tasks.append(AmariImportTask(task_record))
        return tasks

    async def fetchAllTasksInQueue(self):
        tasks = []
        task_records = await self.client.db.fetch("SELECT * FROM amari_import_task_queue_with_position")
        for task_record in task_records:
            tasks.append(AmariImportTask(task_record))
        return tasks

    async def fetchTaskByTicketChannelId(self, channel_id: int) -> AmariImportTask | None:
        task_record = await self.client.db.fetchrow("SELECT * FROM amari_import_task_queue WHERE ticket_channel_id = $1 LIMIT 1", channel_id)
        return AmariImportTask(task_record) if task_record else None

    async def fetchTaskById(self, task_id: int) -> AmariImportTask | None:
        task_record = await self.client.db.fetchrow("SELECT * FROM amari_import_task_queue WHERE id = $1 LIMIT 1", task_id)
        return AmariImportTask(task_record) if task_record else None

    async def deleteTaskById(self, task_id: int) -> int:

        result = await self.client.db.execute("DELETE FROM amari_import_task_queue WHERE id = $1", task_id)
        match = re.search(r'DELETE (\d+)', result)
        if match:
            rows_deleted = int(match.group(1))
            return rows_deleted
        else:
            return 0
