CREATE TABLE IF NOT EXISTS actions(
    id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    target_user_id BIGINT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details JSONB
)