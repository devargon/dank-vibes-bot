create table if not exists dankitems
(
    name                  text,
    idcode                text                 not null
        primary key,
    type                  text,
    image_url             text,
    trade_value           bigint,
    last_updated          bigint  default 0,
    overwrite             boolean default false,
    celeb_donation        boolean default true not null,
    celeb_overwrite_value integer,
    plural_name           text
);