create table if not exists highlight
(
    guild_id   bigint,
    user_id    bigint,
    highlights text
);