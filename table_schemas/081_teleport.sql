create table if not exists teleport
(
    member_id  bigint,
    checkpoint text,
    channel_id bigint
);