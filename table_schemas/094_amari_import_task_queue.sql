DO $$ BEGIN
    CREATE TYPE task_status AS ENUM (
        'PENDING',
        'IN_PROGRESS',
        'COMPLETED',
        'FAILED',
        'ADMIN_SKIPPED',
        'ADMIN_CANCELLED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


create table if not exists amari_import_task_queue
(
    id                      SERIAL,
    user_id                 BIGINT      NOT NULL,
    status                  task_status NOT NULL DEFAULT 'PENDING',
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    enqueued_at             TIMESTAMPTZ,
    updated_at              TIMESTAMPTZ,
    stopped_at              TIMESTAMPTZ,
    ticket_guild_id         BIGINT      NOT NULL,
    ticket_channel_id       BIGINT      NOT NULL,
    ticket_message_id       BIGINT      NOT NULL,
    notified_near_front     BOOLEAN     NOT NULL DEFAULT FALSE,
    error_message           TEXT,
    ticket_message          TEXT,
    amari_xp_to_add         BIGINT      NOT NULL,
    expected_amari_level    INT         NOT NULL,
    expected_total_amari_xp BIGINT      NOT NULL
);

CREATE OR REPLACE VIEW amari_import_task_queue_with_position AS
SELECT
    *,
    ROW_NUMBER() OVER (
        ORDER BY COALESCE(enqueued_at, created_at), id
    ) -1 AS position
FROM amari_import_task_queue
WHERE stopped_at IS NULL OR status = 'FAILED';
