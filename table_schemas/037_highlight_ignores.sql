create table if not exists highlight_ignores
(
    guild_id    bigint,
    user_id     bigint,
    ignore_type text,
    ignore_id   bigint
);