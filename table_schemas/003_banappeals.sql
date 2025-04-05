create table if not exists banappeals
(
    appeal_id               serial
        primary key,
    user_id                 bigint                                                                              not null,
    appeal_timestamp        timestamp with time zone                                                            not null,
    ban_reason              text                     default 'None specified'::text                             not null,
    appeal_answer1          varchar(1024)                                                                       not null,
    appeal_answer2          varchar(1024)                                                                       not null,
    appeal_answer3          varchar(1024)                                                                       not null,
    email                   varchar(255),
    appeal_status           integer                  default 0                                                  not null,
    reviewed_timestamp      timestamp with time zone,
    reviewer_id             bigint,
    reviewer_response       text,
    version                 integer                  default 1                                                  not null,
    guild_id                bigint                   default 0                                                  not null,
    channel_id              bigint                   default 0                                                  not null,
    message_id              bigint                   default 0                                                  not null,
    updated                 boolean                  default true                                               not null,
    posted                  boolean                  default false                                              not null,
    last_reminder           boolean                  default false                                              not null,
    dungeon_over_reminder   boolean                  default false                                              not null,
    review_before_timestamp timestamp with time zone default '1970-01-01 00:00:01+00'::timestamp with time zone not null
);

create index idx_appealdate
    on banappeals (appeal_timestamp);

create unique index idx_unique_user_guild_active_appeal
    on banappeals (user_id, guild_id)
    where (appeal_status = 0);

create index idx_userid
    on banappeals (user_id);

