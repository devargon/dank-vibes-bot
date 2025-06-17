create table if not exists nicknames
(
    id        serial
        primary key,
    member_id bigint,
    nickname  text,
    messageid bigint
);