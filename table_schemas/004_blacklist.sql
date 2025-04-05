create table if not exists blacklist
(
    incident_id      serial,
    user_id          bigint,
    moderator_id     bigint,
    blacklist_active boolean,
    time_until       bigint,
    reason           text
);