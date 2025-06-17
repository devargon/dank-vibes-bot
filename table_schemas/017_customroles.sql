create table if not exists customroles
(
    guild_id bigint not null,
    user_id  bigint not null,
    role_id  bigint not null
);