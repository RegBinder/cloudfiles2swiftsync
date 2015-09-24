create table if not exists synced_objects (
  container_name text,
  object_name text,
  inserted timestamp not null default now()
);

create table if not exists error_objects (
  container_name text,
  object_name text,
  error_message text,
  inserted timestamp not null default now()
);

