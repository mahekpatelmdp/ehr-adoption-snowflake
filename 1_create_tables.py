"""
1_create_tables.py
Creates the Snowflake database, schema, and all dimension/fact tables.
Safe to rerun — drops and recreates all tables.
"""

import snowflake.connector
import configparser

config = configparser.ConfigParser()
config.read("snowflake.cfg")

conn = snowflake.connector.connect(
    user=config["SNOWFLAKE"]["user"],
    password=config["SNOWFLAKE"]["password"],
    account=config["SNOWFLAKE"]["account"],
    warehouse=config["SNOWFLAKE"]["warehouse"],
)
cur = conn.cursor()

DB = config["SNOWFLAKE"]["database"]
SCHEMA = config["SNOWFLAKE"]["schema"]


def run(sql, msg=None):
    cur.execute(sql)
    if msg:
        print(f"  OK: {msg}")


def setup():
    run(f"CREATE DATABASE IF NOT EXISTS {DB}", f"Database {DB}")
    run(f"USE DATABASE {DB}")
    run(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}", f"Schema {SCHEMA}")
    run(f"USE SCHEMA {SCHEMA}")


def drop_tables():
    for t in ["fact_workflow_metrics", "fact_ehr_adoptions", "dim_providers", "dim_program_year", "dim_ehr_vendor"]:
        run(f"DROP TABLE IF EXISTS {t}", f"Dropped {t}")


def create_dim_providers():
    run("""
    CREATE TABLE dim_providers (
        provider_key        INTEGER       NOT NULL,
        provider_id         VARCHAR(20)   NOT NULL,
        provider_name       VARCHAR(200)  NOT NULL,
        hospital_type       VARCHAR(50),
        ownership_type      VARCHAR(50),
        state               VARCHAR(5)    NOT NULL,
        region              VARCHAR(20),
        bed_count           INTEGER,
        rural_urban         VARCHAR(20),
        teaching_hospital   INTEGER
    )
    """, "dim_providers")


def create_dim_program_year():
    run("""
    CREATE TABLE dim_program_year (
        year_key        INTEGER NOT NULL,
        program_year    INTEGER NOT NULL,
        era             VARCHAR(30)
    )
    """, "dim_program_year")


def create_dim_ehr_vendor():
    run("""
    CREATE TABLE dim_ehr_vendor (
        vendor_key      INTEGER      NOT NULL,
        vendor_name     VARCHAR(100) NOT NULL,
        vendor_tier     VARCHAR(20)
    )
    """, "dim_ehr_vendor")


def create_fact_ehr_adoptions():
    run("""
    CREATE TABLE fact_ehr_adoptions (
        adoption_key                INTEGER       NOT NULL,
        adoption_id                 VARCHAR(20)   NOT NULL,
        provider_key                INTEGER       NOT NULL,
        year_key                    INTEGER       NOT NULL,
        vendor_key                  INTEGER       NOT NULL,
        certification_level         VARCHAR(50),
        adoption_score              FLOAT,
        meaningful_use_stage        INTEGER,
        interoperability_enabled    INTEGER,
        patient_portal_enabled      INTEGER,
        telehealth_enabled          INTEGER,
        staff_trained_pct           FLOAT,
        downtime_hours_annual       FLOAT
    )
    """, "fact_ehr_adoptions")


def create_fact_workflow_metrics():
    run("""
    CREATE TABLE fact_workflow_metrics (
        metric_key                      INTEGER     NOT NULL,
        metric_id                       VARCHAR(20) NOT NULL,
        adoption_key                    INTEGER     NOT NULL,
        provider_key                    INTEGER     NOT NULL,
        year_key                        INTEGER     NOT NULL,
        avg_documentation_time_min      FLOAT,
        order_entry_error_rate_pct      FLOAT,
        duplicate_record_rate_pct       FLOAT,
        data_completeness_pct           FLOAT,
        patient_satisfaction_score      FLOAT,
        readmission_rate_pct            FLOAT,
        avg_length_of_stay_days         FLOAT
    )
    """, "fact_workflow_metrics")


if __name__ == "__main__":
    print("Setting up Snowflake database and schema...")
    setup()

    print("\nDropping existing tables...")
    drop_tables()

    print("\nCreating dimension tables...")
    create_dim_providers()
    create_dim_program_year()
    create_dim_ehr_vendor()

    print("\nCreating fact tables...")
    create_fact_ehr_adoptions()
    create_fact_workflow_metrics()

    cur.close()
    conn.close()
    print("\nAll tables created successfully.")
