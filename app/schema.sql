
create table if not exists "users" (
    Id integer primary key,
    Username text not null unique,
    Password text not null,
    GoogleCalenderLink text,
    StartId integer,
    DestId integer,
    MorningTime integer,
    StartWalk integer,
    DestTime integer


);