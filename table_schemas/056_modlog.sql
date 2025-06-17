create table if not exists modlog
(
    case_id      serial,
    guild_id     bigint not null,
    moderator_id bigint not null,
    offender_id  bigint not null,
    action       text   not null,
    reason       text,
    start_time   bigint,
    duration     bigint,
    end_time     bigint
);