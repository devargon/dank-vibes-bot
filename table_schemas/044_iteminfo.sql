create table if not exists iteminfo
(
    name        text not null
        primary key,
    fullname    text,
    description text,
    emoji       text,
    image       text,
    hidden      boolean,
    usable      boolean
);