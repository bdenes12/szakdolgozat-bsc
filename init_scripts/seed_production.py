import os
import string
import psycopg2
import random
import psycopg2.extras as extras
from datetime import timedelta
from faker import Faker
from psycopg2 import sql
from dotenv import load_dotenv
from reference_data import departments_data, icd_codes_data, PRACTITIONERS_PER_DEPARTMENT, SPECIALTIES_BY_DEPARTMENT, COVERAGE_TYPES, INSURERS, PREMIUM_RANGES, POLICY_DURATIONS_YEARS, ENCOUNTER_TYPES, STAY_DAYS_BY_TYPE, TRIAGE_LEVELS, LAB_TESTS, PAYMENT_STATUSES


load_dotenv()

faker = Faker('hu_HU')
patient_number = 500

PRODUCTION_DSN = os.getenv("PRODUCTION_DSN")

#faker.seed_instance(12)
#random.seed(12)

def truncate_prod_database_data():
    try:
        conn = psycopg2.connect(PRODUCTION_DSN)
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables t WHERE t.table_schema = 'public';")

        result = cur.fetchall()

        prod_tables = [_[0] for _ in result]

        for table in prod_tables:
            cur.execute(sql.SQL("TRUNCATE TABLE public.{table_name} CASCADE").format(
                table_name=sql.Identifier(table)
            ))

        conn.commit()

        cur.close()
        conn.close()

    except psycopg2.OperationalError as e:
        print(f"The error '{e}' occurred!")

def generate_taj_number():
    first_eight_digits = str(random.randint(10000000, 99999999))

    sum_odd_index = 0
    sum_even_index = 0

    for index, digit in enumerate(first_eight_digits):

        if index % 2 != 0:
            sum_odd_index += int(digit)*7
        if index % 2 == 0:
            sum_even_index += int(digit)*3

    ninth_digit =  str((sum_odd_index + sum_even_index) % 10)

    taj_number = int(first_eight_digits + ninth_digit)

    return taj_number

def fill_prod_database():
    try:
        conn = psycopg2.connect(PRODUCTION_DSN)
        cur = conn.cursor()

        patient_data = []
        for _ in range(patient_number):
            national_health_id = generate_taj_number()
            patient_data.append(
                (
                    national_health_id,
                    faker.first_name(),
                    faker.last_name(),
                    faker.name_female(),
                    faker.date_of_birth(),
                    faker.random_element(elements=('Férfi', 'Nő', 'Egyéb')),
                    faker.email(),
                    faker.phone_number()
                )
            )

        #patients table
        patient_ids = extras.execute_values(cur, "INSERT INTO patients (national_health_id, first_name, last_name, mother_name, birth_date, gender, email, phone_number) VALUES %s RETURNING patient_id", patient_data, fetch=True)

        #departments table
        extras.execute_values(cur, "INSERT INTO departments (dept_name, building, floor_number, phone_extension) VALUES %s", departments_data)

        cur.execute("SELECT d.dept_id, d.dept_name FROM public.departments d")
        result_dep = cur.fetchall()

        practitioners_data = []
        for id, dept_name in result_dep:
            for _ in range(PRACTITIONERS_PER_DEPARTMENT):
                practitioners_data.append(
                    (
                        id,
                        faker.first_name(),
                        faker.last_name(),
                        random.randint(100000, 999999),
                        faker.email(),
                        faker.phone_number(),
                        random.choice(SPECIALTIES_BY_DEPARTMENT[dept_name])
                    )
                )

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
                        faker.date() 
                    )
                )

        insurance_policies_data = []
        for id in patient_ids:
            valid_from = faker.date_between(start_date='-6y', end_date='today')

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
                    random.randint(PREMIUM_RANGES[coverage_type][0], PREMIUM_RANGES[coverage_type][1])
                )
            )

        #practitioners table
        practioner_id_and_dept_id = extras.execute_values(cur, "INSERT INTO practitioners (dept_id, first_name, last_name, license_number, email, phone_number, specialty) VALUES %s RETURNING practitioner_id, dept_id", practitioners_data, fetch=True)

        encounters_data = []
        for _ in range(random.randint(1, 4) * len(patient_ids)):
            practitioner_id_and_dept_id = random.choice(practioner_id_and_dept_id)

            types, weights = zip(*ENCOUNTER_TYPES)
            encounter_type = random.choices(types, weights=weights)[0] # a [0] azért kell, hogy ne listát adjon vissza

            admitted_at = faker.date_time_between(start_date='-2y', end_date='now') 
            discharged_at = faker.date_time_between(start_date=admitted_at, end_date=admitted_at + timedelta(days=random.randint(STAY_DAYS_BY_TYPE[encounter_type][0], STAY_DAYS_BY_TYPE[encounter_type][1])))
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
                    triage_level
                )
            )

        #encounters table 
        encounter_ids = extras.execute_values(cur, "INSERT INTO encounters (patient_id, practitioner_id, dept_id, encounter_type, admitted_at, discharged_at, length_of_stay_days, triage_level) VALUES %s RETURNING encounter_id", encounters_data, fetch=True)

        diagnoses_data = []
        for _ in encounter_ids:
            diagnoses_data.append(
                (
                    random.choice(encounter_ids),
                    random.choice(icd_codes_data)[0],
                    faker.date_time_between(start_date="-2y", end_date="now"),
                    random.choice(["enyhe", "közepes", "súlyos"]),
                    faker.sentence()
                )
            )

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
                        faker.date_time_between(start_date="-2y", end_date="now")
                    )
                )

        invoices_data = []
        for id in encounter_ids:
            payment_status = random.choice(PAYMENT_STATUSES)
            total_amount = random.gauss(80000, 25000)
            paid_amount = total_amount if payment_status=="kifizetett" else (total_amount / 2 if payment_status=="részben fizetett" else 0)
            invoices_data.append(
                (
                    id,
                    random.gauss(80000, 25000),
                    paid_amount,
                    faker.date_between(start_date="-2y", end_date="today"),
                    payment_status,
                    faker.iban()
                )
            )

        #insurance_policies table
        extras.execute_values(cur, "INSERT INTO insurance_policies (patient_id, insurer_name, policy_number, coverage_type, valid_from, valid_to, monthly_premium) VALUES %s", insurance_policies_data)

        #patient_addresses table    
        extras.execute_values(cur, "INSERT INTO patient_addresses (patient_id, postal_code, city, street_address, country, valid_from) VALUES %s", patient_addresses_data)

        #icd_codes table
        extras.execute_values(cur, "INSERT INTO icd_codes (icd_code, description, category, is_chronic) VALUES %s", icd_codes_data)

        #diagnoses table
        extras.execute_values(cur, "INSERT INTO diagnoses (encounter_id, icd_code, diagnosed_at, severity, notes) VALUES %s", diagnoses_data)

        #lab_results table
        extras.execute_values(cur, "INSERT INTO lab_results (encounter_id, test_name, unit, value_numeric, measured_at) VALUES %s", lab_results_data)

        #invoices table
        extras.execute_values(cur, "INSERT INTO invoices (encounter_id, total_amount, paid_amount, issued_at, payment_status, bank_account_number) VALUES %s", invoices_data)

        conn.commit()
        cur.close()
        conn.close()

    except psycopg2.OperationalError as e:
        print(f"The error '{e}' occurred!")

truncate_prod_database_data()

fill_prod_database()