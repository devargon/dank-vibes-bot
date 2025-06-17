create table if not exists forcetimeout
(
    log_id       serial,
    guild_id     bigint not null,
    offender_id  bigint not null,
    moderator_id bigint not null,
    start_time   bigint not null,
    duration     bigint not null,
    end_time     bigint not null,
    reason       text
);