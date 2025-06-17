create table if not exists watchlist
(
    guild_id  bigint,
    user_id   bigint,
    target_id bigint,
    remarks   text
);