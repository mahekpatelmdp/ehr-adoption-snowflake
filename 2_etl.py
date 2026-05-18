"""
2_etl.py
Reads raw CSVs, transforms into dimensional model, loads into Snowflake.
"""

import pandas as pd
import numpy as np
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import configparser

config = configparser.ConfigParser()
config.read("snowflake.cfg")

conn = snowflake.connector.connect(
    user=config["SNOWFLAKE"]["user"],
    password=config["SNOWFLAKE"]["password"],
    account=config["SNOWFLAKE"]["account"],
    warehouse=config["SNOWFLAKE"]["warehouse"],
    database=config["SNOWFLAKE"]["database"],
    schema=config["SNOWFLAKE"]["schema"],
)

DB = config["SNOWFLAKE"]["database"]
SCHEMA = config["SNOWFLAKE"]["schema"]


def load_table(df, table_name):
    df.columns = [c.upper() for c in df.columns]
    success, nchunks, nrows, _ = write_pandas(conn, df, table_name.upper())
    print(f"  Loaded {nrows:,} rows → {table_name}")


# ── Dimension Transforms ──────────────────────────────────────────────────────

def transform_dim_providers(df):
    df = df.copy().reset_index(drop=True)
    df.insert(0, "provider_key", range(1, len(df) + 1))
    return df


def transform_dim_program_year():
    years = [2019, 2020, 2021, 2022, 2023]
    era_map = {2019: "Pre-COVID", 2020: "COVID Onset", 2021: "COVID Peak",
               2022: "Post-COVID Recovery", 2023: "Post-COVID Recovery"}
    rows = [{"year_key": y, "program_year": y, "era": era_map[y]} for y in years]
    return pd.DataFrame(rows)


def transform_dim_ehr_vendor():
    vendors = ["Epic", "Cerner", "Meditech", "Allscripts", "athenahealth", "NextGen", "eClinicalWorks"]
    tier_map = {"Epic": "Tier 1", "Cerner": "Tier 1", "Meditech": "Tier 2",
                "Allscripts": "Tier 2", "athenahealth": "Tier 2",
                "NextGen": "Tier 3", "eClinicalWorks": "Tier 3"}
    rows = [{"vendor_key": i + 1, "vendor_name": v, "vendor_tier": tier_map[v]}
            for i, v in enumerate(vendors)]
    return pd.DataFrame(rows)


def transform_fact_ehr_adoptions(adoptions_df, providers_dim, year_dim, vendor_dim):
    df = adoptions_df.copy()

    prov_map = dict(zip(providers_dim["provider_id"], providers_dim["provider_key"]))
    year_map = dict(zip(year_dim["program_year"], year_dim["year_key"]))
    vendor_map = dict(zip(vendor_dim["vendor_name"], vendor_dim["vendor_key"]))

    df["provider_key"] = df["provider_id"].map(prov_map)
    df["year_key"] = df["program_year"].map(year_map)
    df["vendor_key"] = df["ehr_vendor"].map(vendor_map)
    df.insert(0, "adoption_key", range(1, len(df) + 1))

    cols = ["adoption_key", "adoption_id", "provider_key", "year_key", "vendor_key",
            "certification_level", "adoption_score", "meaningful_use_stage",
            "interoperability_enabled", "patient_portal_enabled", "telehealth_enabled",
            "staff_trained_pct", "downtime_hours_annual"]
    return df[cols]


def transform_fact_workflow_metrics(metrics_df, adoptions_fact, providers_dim, year_dim):
    df = metrics_df.copy()

    adoption_map = dict(zip(
        adoptions_fact["adoption_id"] if "adoption_id" in adoptions_fact.columns
        else adoptions_fact["ADOPTION_ID"],
        adoptions_fact["adoption_key"] if "adoption_key" in adoptions_fact.columns
        else adoptions_fact["ADOPTION_KEY"]
    ))
    prov_map = dict(zip(providers_dim["provider_id"], providers_dim["provider_key"]))
    year_map = dict(zip(year_dim["program_year"], year_dim["year_key"]))

    df["adoption_key"] = df["adoption_id"].map(adoption_map)
    df["provider_key"] = df["provider_id"].map(prov_map)
    df["year_key"] = df["program_year"].map(year_map)
    df.insert(0, "metric_key", range(1, len(df) + 1))

    cols = ["metric_key", "metric_id", "adoption_key", "provider_key", "year_key",
            "avg_documentation_time_min", "order_entry_error_rate_pct",
            "duplicate_record_rate_pct", "data_completeness_pct",
            "patient_satisfaction_score", "readmission_rate_pct", "avg_length_of_stay_days"]
    return df[cols]


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Reading source CSVs...")
    providers_raw = pd.read_csv("data/providers.csv")
    adoptions_raw = pd.read_csv("data/ehr_adoptions.csv")
    metrics_raw = pd.read_csv("data/workflow_metrics.csv")
    print(f"  providers: {len(providers_raw):,} | adoptions: {len(adoptions_raw):,} | metrics: {len(metrics_raw):,}")

    print("\nTransforming dimensions...")
    dim_providers = transform_dim_providers(providers_raw)
    dim_year = transform_dim_program_year()
    dim_vendor = transform_dim_ehr_vendor()

    print("\nTransforming fact tables...")
    fact_adoptions = transform_fact_ehr_adoptions(adoptions_raw, dim_providers, dim_year, dim_vendor)
    fact_metrics = transform_fact_workflow_metrics(metrics_raw, fact_adoptions, dim_providers, dim_year)

    print("\nLoading into Snowflake...")
    load_table(dim_providers, "dim_providers")
    load_table(dim_year, "dim_program_year")
    load_table(dim_vendor, "dim_ehr_vendor")
    load_table(fact_adoptions, "fact_ehr_adoptions")
    load_table(fact_metrics, "fact_workflow_metrics")

    conn.close()
    print("\nETL complete.")
