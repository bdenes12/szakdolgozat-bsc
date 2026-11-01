CREATE EXTENSION IF NOT EXISTS anon;

ALTER DATABASE staging SET anon.transparent_dynamic_masking TO true;
ALTER DATABASE staging SET anon.masking_policies TO 'support';

SELECT anon.init();

CREATE ROLE support_user LOGIN PASSWORD 'support_user';
CREATE ROLE analyst_user LOGIN PASSWORD 'analyst_user';

GRANT USAGE ON SCHEMA public TO support_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO support_user;

GRANT USAGE ON SCHEMA anon TO support_user;
GRANT SELECT ON ALL TABLES IN SCHEMA anon TO support_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA anon TO support_user;

SECURITY LABEL FOR support ON ROLE support_user IS 'MASKED';

CREATE SCHEMA dev_export;
CREATE SCHEMA analytics;

GRANT USAGE ON SCHEMA analytics TO analyst_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO analyst_user;



