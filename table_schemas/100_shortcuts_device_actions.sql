CREATE TABLE IF NOT EXISTS shortcuts_device_actions(
    id SERIAL PRIMARY KEY,
    device_id BIGINT NOT NULL REFERENCES shortcuts_devices(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    action_name VARCHAR(255),
    simple_value VARCHAR(255),
    extra_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);