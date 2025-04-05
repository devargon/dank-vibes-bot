create table if not exists lockdownprofiles
(
    guild_id     bigint,
    profile_name text,
    channel_id   bigint
);