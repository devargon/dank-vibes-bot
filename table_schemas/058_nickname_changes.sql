create table if not exists nickname_changes
(
    guild_id  bigint,
    member_id bigint,
    nickname  text,
    time      bigint
);