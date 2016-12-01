drop table if exists subject;
create table subject (
  id integer primary key autoincrement,
  url text not null unique,
  id_emission integer not null references emission(id),
  title text,
  subtitle text,
--  channel text not null,
  topic text,
  duration integer,
--  speaker text,
--  type text not null,
--  date date,
  description text,
  date_scraping datetime not null
);

drop table if exists emission;
create table emission (
  id integer primary key autoincrement,
  url text unique,
  title text,
  channel text not null,
  speaker text,
  type text not null,
  date date not null,
  date_scraping datetime not null,
  unique (channel, type, date) -- avoid duplicated emissions
);