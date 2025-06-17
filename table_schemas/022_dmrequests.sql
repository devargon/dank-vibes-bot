create table if not exists dmrequests
(
    id        serial
        primary key,
    member_id bigint,
    target_id bigint,
    dmcontent text,
    messageid bigint
);