CREATE TABLE departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL UNIQUE,
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
    dept_id INTEGER CONSTRAINT fk_practitioners_departments REFERENCES departments(dept_id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    license_number VARCHAR(10) UNIQUE,
    email VARCHAR(100),
    phone_number VARCHAR(32),
    specialty VARCHAR(100),
    hired_at DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    national_health_id VARCHAR(16) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    mother_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('Férfi', 'Nő', 'Egyéb')),
    email VARCHAR(100),
    phone_number VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE patient_addresses (
    address_id SERIAL PRIMARY KEY,
    patient_id INTEGER CONSTRAINT fk_patient_addresses_patients REFERENCES patients(patient_id),
    postal_code VARCHAR(10),
    city VARCHAR(100),
    street_address VARCHAR(150),
    country VARCHAR(100),
    valid_from DATE
);

CREATE TABLE insurance_policies (
    policy_id SERIAL PRIMARY KEY,
    patient_id INTEGER CONSTRAINT fk_insurance_policies_patients REFERENCES patients(patient_id),
    insurer_name VARCHAR(100),
    policy_number VARCHAR(32) UNIQUE,
    coverage_type VARCHAR(32),
    valid_from DATE,
    valid_to DATE,
    monthly_premium NUMERIC(10,2)
);

CREATE TABLE encounters (
    encounter_id BIGSERIAL PRIMARY KEY,
    patient_id INTEGER CONSTRAINT fk_encounters_patients REFERENCES patients(patient_id),
    practitioner_id INTEGER CONSTRAINT fk_encounters_practitioners REFERENCES practitioners(practitioner_id),
    dept_id INTEGER CONSTRAINT fk_encounters_departments REFERENCES departments(dept_id),
    encounter_type VARCHAR(20) NOT NULL CHECK (encounter_type IN ('fekvőbeteg', 'járóbeteg', 'sürgősségi')),
    admitted_at TIMESTAMP NOT NULL,
    discharged_at TIMESTAMP,
    length_of_stay_days SMALLINT,
    triage_level SMALLINT NOT NULL CHECK (triage_level BETWEEN 1 AND 5)
);

CREATE TABLE diagnoses (
    diagnosis_id BIGSERIAL PRIMARY KEY,
    encounter_id BIGINT CONSTRAINT fk_diagnoses_encounters REFERENCES encounters(encounter_id),
    icd_code VARCHAR(10) CONSTRAINT fk_diagnoses_icd_codes REFERENCES icd_codes(icd_code),
    diagnosed_at TIMESTAMP,
    severity VARCHAR(20),
    notes TEXT
);

CREATE TABLE lab_results (
    result_id BIGSERIAL PRIMARY KEY,
    encounter_id BIGINT CONSTRAINT fk_lab_results_encounters REFERENCES encounters(encounter_id),
    test_name VARCHAR(100),
    unit VARCHAR(20),
    value_numeric NUMERIC(10,3),
    measured_at TIMESTAMP
);

CREATE TABLE invoices (
    invoice_id BIGSERIAL PRIMARY KEY,
    encounter_id BIGINT CONSTRAINT fk_invoices_encounters REFERENCES encounters(encounter_id),
    total_amount NUMERIC(12,2),
    paid_amount NUMERIC(12,2),
    issued_at DATE,
    payment_status VARCHAR(32),
    bank_account_number VARCHAR(32)
);