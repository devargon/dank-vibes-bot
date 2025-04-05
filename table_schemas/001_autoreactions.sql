create table if not exists autoreactions
(
    guild_id bigint,
    trigger  text,
    response text
);