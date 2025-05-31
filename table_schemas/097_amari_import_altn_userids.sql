CREATE TABLE IF NOT EXISTS amari_import_altn_userids
(
    id SERIAL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    creator_user_id BIGINT NOT NULL,
    target_user_id BIGINT NOT NULL,
    alternate_user_id BIGINT NOT NULL
);