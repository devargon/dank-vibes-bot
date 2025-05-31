CREATE TABLE IF NOT EXISTS amari_import_workers
(
    id SERIAL,
    host TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    worker_user_id BIGINT NOT NULL,
    creator_user_id BIGINT NOT NULL
);