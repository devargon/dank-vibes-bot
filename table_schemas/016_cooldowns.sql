create table if not exists cooldowns
(
    command_name text,
    member_id    bigint,
    time         bigint
);