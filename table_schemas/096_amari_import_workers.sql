CREATE TABLE IF NOT EXISTS amari_import_workers
(
    id SERIAL,
    host TEXT,
    token TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    worker_user_id BIGINT NOT NULL,
    creator_user_id BIGINT NOT NULL
);