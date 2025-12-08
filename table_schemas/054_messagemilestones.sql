create table if not exists messagemilestones
(
    guild_id bigint not null,
    role_id bigint not null,
    messagecount integer not null
);