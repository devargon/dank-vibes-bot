create table autorole
(
    member_id bigint,
    guild_id  bigint,
    role_id   bigint,
    time      bigint,
    constraint autorole_unique
        unique (member_id, role_id)
);