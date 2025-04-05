create table if not exists rules
(
    guild_id  bigint,
    command   text,
    role_id   bigint,
    whitelist boolean
);