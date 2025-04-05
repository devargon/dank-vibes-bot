create table if not exists suggestions
(
    suggestion_id serial,
    user_id       bigint,
    finish        boolean,
    response_id   bigint,
    suggestion    text
);