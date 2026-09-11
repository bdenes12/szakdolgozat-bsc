CREATE TABLE departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    building VARCHAR(100),
    floor_number SMALLINT,
    phone_extension VARCHAR(10)
);

CREATE TABLE icd_codes (
    icd_code VARCHAR(10) PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    is_chronic BOOLEAN DEFAULT FALSE
);

CREATE TABLE practitioners (
    practitioner_id SERIAL PRIMARY KEY,
    dept_id INTEGER,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    license_number VARCHAR(10),
    email VARCHAR(100),
    phone_number VARCHAR(32),
    specialty VARCHAR(100),
    hired_at DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    national_health_id VARCHAR(16) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    mother_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    gender VARCHAR(10) NOT NULL,
    email VARCHAR(100),
    phone_number VARCHAR(32),
    created_at TIMESTAMP 
);

CREATE TABLE patient_addresses (
    address_id SERIAL PRIMARY KEY,
    patient_id INTEGER,
    postal_code VARCHAR(10),
    city VARCHAR(100),
    street_address VARCHAR(150),
    country VARCHAR(100),
    valid_from DATE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE insurance_policies (
    policy_id SERIAL PRIMARY KEY,
    patient_id INTEGER,
    insurer_name VARCHAR(100),
    policy_number VARCHAR(32),
    coverage_type VARCHAR(32),
    valid_from DATE,
    valid_to DATE,
    monthly_premium NUMERIC(10,2)
);

CREATE TABLE encounters (
    encounter_id BIGSERIAL PRIMARY KEY,
    patient_id INTEGER,
    practitioner_id INTEGER,
    dept_id INTEGER,
    encounter_type VARCHAR(20) NOT NULL,
    admitted_at TIMESTAMP NOT NULL,
    discharged_at TIMESTAMP,
    length_of_stay_days SMALLINT,
    triage_level SMALLINT NOT NULL
);

CREATE TABLE diagnoses (
    diagnosis_id BIGSERIAL PRIMARY KEY,
    encounter_id BIGINT,
    icd_code VARCHAR(10),
    diagnosed_at TIMESTAMP,
    severity VARCHAR(20),
    notes TEXT
);

CREATE TABLE lab_results (
    result_id BIGSERIAL PRIMARY KEY,
    encounter_id BIGINT,
    test_name VARCHAR(100),
    unit VARCHAR(20),
    value_numeric NUMERIC(10,3),
    measured_at TIMESTAMP
);

CREATE TABLE invoices (
    invoice_id BIGSERIAL PRIMARY KEY,
    encounter_id BIGINT,
    total_amount NUMERIC(12,2),
    paid_amount NUMERIC(12,2),
    issued_at DATE,
    payment_status VARCHAR(32),
    bank_account_number VARCHAR(32)
);