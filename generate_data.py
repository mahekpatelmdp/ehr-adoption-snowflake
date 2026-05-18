"""
generate_data.py
Generates realistic dummy EHR adoption datasets.
Run once before the ETL pipeline.
"""

import pandas as pd
import numpy as np
import random
import os

random.seed(42)
np.random.seed(42)

STATES = ["CA", "TX", "FL", "NY", "IL", "PA", "OH", "GA", "NC", "AZ",
          "WA", "MA", "CO", "TN", "IN", "MO", "MD", "WI", "MN", "OR"]

HOSPITAL_TYPES = ["Acute Care", "Critical Access", "Specialty", "Psychiatric", "Rehabilitation"]
OWNERSHIP_TYPES = ["Non-Profit", "For-Profit", "Government"]
EHR_VENDORS = ["Epic", "Cerner", "Meditech", "Allscripts", "athenahealth", "NextGen", "eClinicalWorks"]
PROGRAM_YEARS = [2019, 2020, 2021, 2022, 2023]
CERTIFICATION_LEVELS = ["Basic EHR", "Certified EHR", "Advanced EHR", "Not Certified"]


def generate_providers(n=500):
    rows = []
    for i in range(1, n + 1):
        state = random.choice(STATES)
        rows.append({
            "provider_id": f"PRV{i:06d}",
            "provider_name": f"{random.choice(['General','Memorial','Regional','Community','University'])} Health {i}",
            "hospital_type": random.choice(HOSPITAL_TYPES),
            "ownership_type": random.choice(OWNERSHIP_TYPES),
            "state": state,
            "region": _get_region(state),
            "bed_count": random.randint(25, 900),
            "rural_urban": random.choices(["Urban", "Suburban", "Rural"], weights=[0.5, 0.3, 0.2])[0],
            "teaching_hospital": random.choices([1, 0], weights=[0.2, 0.8])[0],
        })
    return pd.DataFrame(rows)


def generate_ehr_adoptions(providers_df):
    rows = []
    adoption_id = 1
    for _, prov in providers_df.iterrows():
        for year in PROGRAM_YEARS:
            cert_level = random.choices(CERTIFICATION_LEVELS, weights=[0.15, 0.45, 0.25, 0.15])[0]
            rows.append({
                "adoption_id": f"ADO{adoption_id:08d}",
                "provider_id": prov["provider_id"],
                "program_year": year,
                "ehr_vendor": random.choice(EHR_VENDORS),
                "certification_level": cert_level,
                "adoption_score": round(np.random.beta(5, 2) * 100, 1),
                "meaningful_use_stage": random.choice([1, 2, 3]) if cert_level != "Not Certified" else 0,
                "interoperability_enabled": random.choices([1, 0], weights=[0.65, 0.35])[0],
                "patient_portal_enabled": random.choices([1, 0], weights=[0.70, 0.30])[0],
                "telehealth_enabled": random.choices([1, 0], weights=[0.55, 0.45])[0] if year >= 2020 else 0,
                "staff_trained_pct": round(random.uniform(40, 100), 1),
                "downtime_hours_annual": round(random.uniform(0, 120), 1),
            })
            adoption_id += 1
    return pd.DataFrame(rows)


def generate_workflow_metrics(adoptions_df):
    rows = []
    metric_id = 1
    sample = adoptions_df.sample(frac=0.6, random_state=42)
    for _, row in sample.iterrows():
        rows.append({
            "metric_id": f"MET{metric_id:08d}",
            "adoption_id": row["adoption_id"],
            "provider_id": row["provider_id"],
            "program_year": row["program_year"],
            "avg_documentation_time_min": round(random.uniform(5, 45), 1),
            "order_entry_error_rate_pct": round(random.uniform(0.5, 8.0), 2),
            "duplicate_record_rate_pct": round(random.uniform(0.1, 5.0), 2),
            "data_completeness_pct": round(random.uniform(60, 99), 1),
            "patient_satisfaction_score": round(random.uniform(2.5, 5.0), 2),
            "readmission_rate_pct": round(random.uniform(5, 25), 1),
            "avg_length_of_stay_days": round(random.uniform(2, 12), 1),
        })
        metric_id += 1
    return pd.DataFrame(rows)


def _get_region(state):
    regions = {
        "Northeast": ["NY", "PA", "MA", "MD"],
        "South": ["TX", "FL", "GA", "NC", "TN"],
        "Midwest": ["IL", "OH", "IN", "MO", "WI", "MN"],
        "West": ["CA", "WA", "CO", "AZ", "OR"],
    }
    for region, states in regions.items():
        if state in states:
            return region
    return "Other"


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    print("Generating providers...")
    providers = generate_providers(500)
    providers.to_csv("data/providers.csv", index=False)

    print("Generating EHR adoptions...")
    adoptions = generate_ehr_adoptions(providers)
    adoptions.to_csv("data/ehr_adoptions.csv", index=False)

    print("Generating workflow metrics...")
    metrics = generate_workflow_metrics(adoptions)
    metrics.to_csv("data/workflow_metrics.csv", index=False)

    print("\nDone! Files written to data/:")
    for f in sorted(os.listdir("data")):
        size = os.path.getsize(f"data/{f}")
        print(f"  {f:35s} {size/1024:.1f} KB")
