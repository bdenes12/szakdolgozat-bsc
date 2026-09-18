create extension if not exists anon;

alter database staging set anon.transparent_dynamic_masking to true;

select anon.init();

create role support_user login password 'support_user';

GRANT USAGE ON SCHEMA public TO support_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO support_user;

security label for anon on column patients.first_name
	is 'masked with function anon.fake_first_name()';

security label for anon on column patients.email
	is 'masked with function anon.partial_email(email)';

SECURITY LABEL FOR anon ON ROLE support_user IS 'MASKED';

create schema dev_export;

create view dev_export.departments AS
SELECT * FROM public.departments;

create view dev_export.patients AS
SELECT     
	patient_id,
    national_health_id,
    anon.fake_first_name() AS first_name,
    last_name,
    mother_name,
    birth_date,
    gender,
    anon.partial_email(email) AS email,
    phone_number,
    created_at 
FROM public.patients;