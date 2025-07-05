CREATE TABLE IF NOT EXISTS messagecount_logs(
    user_id      BIGINT NOT NULL,
    performed_by_user_id    BIGINT NOT NULL,
    change       INT NOT NULL,
    before       BIGINT NOT NULL,
    after        BIGINT NOT NULL,
    guild_id     BIGINT NOT NULL,
    channel_id   BIGINT NOT NULL,
    message_id   BIGINT NOT NULL,
    reason      VARCHAR(255) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
)