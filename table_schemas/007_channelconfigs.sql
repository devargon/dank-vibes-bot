create table if not exists channelconfigs
(
    guild_id           bigint not null
        primary key,
    nicknamechannel_id bigint,
    dmchannel_id       bigint
);