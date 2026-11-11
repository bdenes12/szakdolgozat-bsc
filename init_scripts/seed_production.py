import argparse
import os
import random
import string
from datetime import timedelta

import psycopg2
from dotenv import load_dotenv
from faker import Faker
from psycopg2 import extras, sql
from reference_data import (
    COVERAGE_TYPES,
    DEPARTMENTS_DATA,
    ENCOUNTER_TYPES,
    ICD_CODES_DATA,
    INSURERS,
    LAB_TESTS,
    PAYMENT_STATUSES,
    POLICY_DURATIONS_YEARS,
    PRACTITIONERS_PER_DEPARTMENT,
    PREMIUM_RANGES,
    SPECIALTIES_BY_DEPARTMENT,
    STAY_DAYS_BY_TYPE,
    TRIAGE_LEVELS,
)

load_dotenv()

faker = Faker("hu_HU")

PRODUCTION_DSN = os.getenv("PRODUCTION_DSN")

# faker.seed_instance(12)
# random.seed(12)


def truncate_prod_database_data():
    try:
        conn = psycopg2.connect(PRODUCTION_DSN)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables t WHERE t.table_schema = 'public';")

        result = cur.fetchall()

        prod_tables = [_[0] for _ in result]

        for table in prod_tables:
            cur.execute(sql.SQL("TRUNCATE TABLE public.{table_name} CASCADE").format(table_name=sql.Identifier(table)))

        conn.commit()

        cur.close()
        conn.close()

    except psycopg2.OperationalError as e:
        print(f"Hiba történt: {e}")


def generate_taj_number():
    first_eight_digits = str(random.randint(10000000, 99999999))

    sum_odd_index = 0
    sum_even_index = 0

    for index, digit in enumerate(first_eight_digits):
        if index % 2 != 0:
            sum_odd_index += int(digit) * 7
        if index % 2 == 0:
            sum_even_index += int(digit) * 3

    ninth_digit = str((sum_odd_index + sum_even_index) % 10)

    taj_number = int(first_eight_digits + ninth_digit)

    return taj_number


def insert_patients(cur: psycopg2.extensions.cursor, patient_number):
    taj_numbers = set()
    while len(taj_numbers) < patient_number:
        taj_numbers.add(generate_taj_number())

    patient_data = []
    for national_health_id in taj_numbers:
        patient_data.append(
            (
                national_health_id,
                faker.first_name(),
                faker.last_name(),
                faker.name_female(),
                faker.date_of_birth(),
                faker.random_element(elements=("Férfi", "Nő", "Egyéb")),
                faker.email(),
                faker.phone_number(),
            )
        )
    patient_ids = extras.execute_values(
        cur,
        "INSERT INTO patients (national_health_id, first_name, last_name, mother_name, birth_date, gender, email, phone_number) VALUES %s RETURNING patient_id",
        patient_data,
        fetch=True,
    )

    return patient_ids


def insert_departments(cur: psycopg2.extensions.cursor):
    departments = extras.execute_values(
        cur,
        "INSERT INTO departments (dept_name, building, floor_number, phone_extension) VALUES %s RETURNING dept_id, dept_name",
        DEPARTMENTS_DATA,
        fetch=True,
    )

    return departments


def insert_practitioners(cur: psycopg2.extensions.cursor, departments):
    practitioners_data = []
    for id, dept_name in departments:
        for _ in range(PRACTITIONERS_PER_DEPARTMENT):
            practitioners_data.append(
                (
                    id,
                    faker.first_name(),
                    faker.last_name(),
                    random.randint(100000, 999999),
                    faker.email(),
                    faker.phone_number(),
                    random.choice(SPECIALTIES_BY_DEPARTMENT[dept_name]),
                )
            )
    practitioners = extras.execute_values(
        cur,
        "INSERT INTO practitioners (dept_id, first_name, last_name, license_number, email, phone_number, specialty) VALUES %s RETURNING practitioner_id, dept_id",
        practitioners_data,
        fetch=True,
    )

    return practitioners


def insert_patient_addresses(cur: psycopg2.extensions.cursor, patient_ids):
    patient_addresses_data = []
    for id in patient_ids:
        for _ in range(random.randint(1, 2)):
            patient_addresses_data.append(
                (
                    id,
                    faker.postcode(),
                    faker.city(),
                    faker.street_address(),
                    "Magyarország" if random.random() < 0.95 else faker.country(),
                    faker.date(),
                )
            )
    extras.execute_values(
        cur,
        "INSERT INTO patient_addresses (patient_id, postal_code, city, street_address, country, valid_from) VALUES %s",
        patient_addresses_data,
    )


def insert_insurance_policies(cur: psycopg2.extensions.cursor, patient_ids):
    insurance_policies_data = []
    for id in patient_ids:
        valid_from = faker.date_between(start_date="-6y", end_date="today")

        years = random.choice(POLICY_DURATIONS_YEARS)
        valid_to = valid_from + timedelta(days=365 * years)

        coverage_type = random.choice(COVERAGE_TYPES)

        insurance_policies_data.append(
            (
                id,
                random.choice(INSURERS),
                "".join(random.choices(string.ascii_uppercase, k=3)) + str(random.randint(100000, 999999)),
                coverage_type,
                valid_from,
                valid_to,
                random.randint(PREMIUM_RANGES[coverage_type][0], PREMIUM_RANGES[coverage_type][1]),
            )
        )
    extras.execute_values(
        cur,
        "INSERT INTO insurance_policies (patient_id, insurer_name, policy_number, coverage_type, valid_from, valid_to, monthly_premium) VALUES %s",
        insurance_policies_data,
    )


def insert_icd_codes(cur: psycopg2.extensions.cursor):
    extras.execute_values(
        cur, "INSERT INTO icd_codes (icd_code, description, category, is_chronic) VALUES %s", ICD_CODES_DATA
    )


def insert_encounters(cur: psycopg2.extensions.cursor, patient_ids, practitioners):
    encounters_data = []
    for _ in range(random.randint(1, 4) * len(patient_ids)):
        practitioner_id_and_dept_id = random.choice(practitioners)

        types, weights = zip(*ENCOUNTER_TYPES)
        encounter_type = random.choices(types, weights=weights)[0]

        admitted_at = faker.date_time_between(start_date="-2y", end_date="now")
        discharged_at = faker.date_time_between(
            start_date=admitted_at,
            end_date=admitted_at
            + timedelta(
                days=random.randint(STAY_DAYS_BY_TYPE[encounter_type][0], STAY_DAYS_BY_TYPE[encounter_type][1])
            ),
        )
        length_of_stay_days = (discharged_at - admitted_at).days

        levels, weights = zip(*TRIAGE_LEVELS)
        triage_level = random.choices(levels, weights=weights)[0]

        encounters_data.append(
            (
                random.choice(patient_ids),
                practitioner_id_and_dept_id[0],
                practitioner_id_and_dept_id[1],
                encounter_type,
                admitted_at,
                discharged_at,
                length_of_stay_days,
                triage_level,
            )
        )
    encounter_ids = extras.execute_values(
        cur,
        "INSERT INTO encounters (patient_id, practitioner_id, dept_id, encounter_type, admitted_at, discharged_at, length_of_stay_days, triage_level) VALUES %s RETURNING encounter_id",
        encounters_data,
        fetch=True,
    )

    return encounter_ids


def insert_diagnoses(cur: psycopg2.extensions.cursor, encounter_ids):
    diagnoses_data = []
    for _ in encounter_ids:
        diagnoses_data.append(
            (
                random.choice(encounter_ids),
                random.choice(ICD_CODES_DATA)[0],
                faker.date_time_between(start_date="-2y", end_date="now"),
                random.choice(["enyhe", "közepes", "súlyos"]),
                faker.sentence(),
            )
        )
    extras.execute_values(
        cur, "INSERT INTO diagnoses (encounter_id, icd_code, diagnosed_at, severity, notes) VALUES %s", diagnoses_data
    )


def insert_lab_results(cur: psycopg2.extensions.cursor, encounter_ids):
    lab_results_data = []
    for id in encounter_ids:
        for _ in range(random.randint(1, 4)):
            test_name, unit, mean, stddev = random.choice(LAB_TESTS)
            value_numeric = random.gauss(mean, stddev)
            lab_results_data.append(
                (
                    id,
                    test_name,
                    unit,
                    abs(value_numeric) if value_numeric < 0 else value_numeric,
                    faker.date_time_between(start_date="-2y", end_date="now"),
                )
            )
    extras.execute_values(
        cur,
        "INSERT INTO lab_results (encounter_id, test_name, unit, value_numeric, measured_at) VALUES %s",
        lab_results_data,
    )


def insert_invoices(cur: psycopg2.extensions.cursor, encounter_ids):
    invoices_data = []
    for id in encounter_ids:
        payment_status = random.choice(PAYMENT_STATUSES)
        total_amount = max(0, random.gauss(80000, 25000))
        paid_amount = (
            total_amount
            if payment_status == "kifizetett"
            else (total_amount / 2 if payment_status == "részben fizetett" else 0)
        )
        invoices_data.append(
            (
                id,
                total_amount,
                paid_amount,
                faker.date_between(start_date="-2y", end_date="today"),
                payment_status,
                faker.iban(),
            )
        )
    extras.execute_values(
        cur,
        "INSERT INTO invoices (encounter_id, total_amount, paid_amount, issued_at, payment_status, bank_account_number) VALUES %s",
        invoices_data,
    )


def fill_prod_database(patient_number):
    conn = None

    try:
        conn = psycopg2.connect(PRODUCTION_DSN)
        cur = conn.cursor()
        patient_ids = insert_patients(cur, patient_number)
        departments = insert_departments(cur)
        practitioners = insert_practitioners(cur, departments)
        insert_patient_addresses(cur, patient_ids)
        insert_insurance_policies(cur, patient_ids)
        insert_icd_codes(cur)
        encounter_ids = insert_encounters(cur, patient_ids, practitioners)
        insert_diagnoses(cur, encounter_ids)
        insert_lab_results(cur, encounter_ids)
        insert_invoices(cur, encounter_ids)
        conn.commit()

    except psycopg2.OperationalError as e:
        print(f"Hiba történt: {e}")

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fill PROD database with fake data")
    parser.add_argument("-p", "--patients", type=int, default=5000)
    args = parser.parse_args()
    truncate_prod_database_data()
    fill_prod_database(args.patients)
