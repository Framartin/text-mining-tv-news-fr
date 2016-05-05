drop table if exists subject;
create table subject (
  id integer primary key autoincrement,
  url text not null unique,
  title text,
  channel text not null,
  topic text,
  duration integer,
  speaker text,
  type text not null,
  date date,
  description text,
  date_scraping datetime not null
);
