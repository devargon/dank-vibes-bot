create table if not exists claimed_messageids
(
    message_id bigint,
    claimer_id bigint,
    user_id    bigint,
    time       bigint
);