create extension if not exists anon;

alter database staging set anon.transparent_dynamic_masking to true;
ALTER DATABASE staging SET anon.masking_policies TO 'support, analytics';

select anon.init();

create role support_user login password 'support_user';
create role analyst_user login password 'analyst_user';

GRANT USAGE ON SCHEMA public TO support_user, analyst_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO support_user, analyst_user;

GRANT USAGE ON SCHEMA anon TO support_user, analyst_user;
GRANT SELECT ON ALL TABLES IN SCHEMA anon TO support_user, analyst_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA anon TO support_user, analyst_user;

SECURITY LABEL FOR support ON ROLE support_user IS 'MASKED';
SECURITY LABEL FOR analytics ON ROLE analyst_user IS 'MASKED';

create schema dev_export;

