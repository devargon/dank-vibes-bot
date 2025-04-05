create table if not exists suggestion_response
(
    suggestion_id integer,
    user_id       bigint,
    response_id   bigint,
    message_id    bigint,
    message       text
);