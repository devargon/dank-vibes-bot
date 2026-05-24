CREATE TABLE IF NOT EXISTS dumbfight_suggestions(
    id           SERIAL PRIMARY KEY,
    user_id      BIGINT NOT NULL,
    fight_type   VARCHAR(50) NOT NULL,
    message      TEXT NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending_approval',
    actioned_by BIGINT,
    action_reason VARCHAR(255),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
)