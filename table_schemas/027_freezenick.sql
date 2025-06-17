create table if not exists freezenick
(
    id                    serial,
    user_id               bigint,
    guild_id              bigint,
    nickname              text,
    old_nickname          text,
    time                  bigint,
    reason                text,
    responsible_moderator bigint
);
