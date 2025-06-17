create table if not exists maintenance
(
    cog_name text not null
        primary key,
    message  text,
    enabled  boolean
);