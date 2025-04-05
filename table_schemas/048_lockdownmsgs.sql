create table if not exists lockdownmsgs
(
    guild_id     bigint,
    profile_name text,
    startmsg     text,
    endmsg       text
);