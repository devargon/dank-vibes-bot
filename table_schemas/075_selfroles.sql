create table if not exists selfroles
(
    guild_id               bigint,
    channel_id             bigint,
    message_id             bigint not null
        primary key,
    type                   text,
    title                  text,
    placeholder_for_select text,
    role_ids               text,
    emojis                 text,
    descriptions           text,
    required_role          text,
    max_gettable_role      integer,
    single_role            boolean
);