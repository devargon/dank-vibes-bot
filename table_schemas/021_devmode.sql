create table if not exists devmode
(
    user_id bigint not null
        primary key,
    enabled boolean
);
