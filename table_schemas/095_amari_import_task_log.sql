CREATE TABLE IF NOT EXISTS amari_import_task_log
(
    id SERIAL,
    task_id INT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_before TEXT NOT NULL,
    status_after TEXT NOT NULL,
    event TEXT NOT NULL,
    event_user_id BIGINT NOT NULL,
    details TEXT
);