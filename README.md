# 🏥 EHR Adoption & Workflow Optimization — Snowflake ETL Pipeline

An end-to-end ETL pipeline analyzing EHR adoption patterns and clinical workflow efficiency across U.S. healthcare providers — built on **Snowflake** with a star-schema dimensional model.

---

## 📊 Project Overview

This project simulates a healthcare data engineering workflow focused on understanding how EHR adoption varies across hospital types, regions, and program years, and how adoption levels impact clinical workflow outcomes. Data is generated, transformed with Python, and loaded into Snowflake for SQL-based analysis.

**Stack:** Python · Pandas · Snowflake · SQL

---

## 🗂️ Star Schema (Dimensional Model)

```
                    ┌──────────────────────┐
                    │   fact_ehr_adoptions  │
                    │──────────────────────│
                    │ adoption_key    (PK)  │
                    │ provider_key    ──────┼──► dim_providers
                    │ year_key        ──────┼──► dim_program_year
                    │ vendor_key      ──────┼──► dim_ehr_vendor
                    │ certification_level   │
                    │ adoption_score        │
                    │ telehealth_enabled    │
                    │ interoperability_...  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ fact_workflow_metrics │
                    │──────────────────────│
                    │ metric_key      (PK)  │
                    │ adoption_key          │
                    │ provider_key          │
                    │ avg_doc_time_min      │
                    │ error_rate_pct        │
                    │ data_completeness_pct │
                    │ patient_satisfaction  │
                    │ readmission_rate_pct  │
                    └──────────────────────┘
```

| Table | Type | Rows |
|-------|------|------|
| `fact_ehr_adoptions` | Fact | 2,500 |
| `fact_workflow_metrics` | Fact | ~1,500 |
| `dim_providers` | Dimension | 500 |
| `dim_program_year` | Dimension | 5 |
| `dim_ehr_vendor` | Dimension | 7 |

---

## 📁 Repository Structure

```
ehr-adoption-snowflake/
├── generate_data.py              # Generates realistic dummy CSV datasets
├── 1_create_tables.py            # Creates all tables in Snowflake
├── 2_etl.py                      # Transforms and loads data into Snowflake
├── sql_queries.sql               # 10 analytical queries against the model
├── notebooks/
│   └── 3_test_queries.ipynb      # Validates schema and runs analytics
├── data/                         # Generated CSVs (git-ignored)
├── snowflake.cfg                 # Snowflake credentials (git-ignored)
├── requirements.txt
└── .gitignore
```

---

## 🚀 Setup & Usage

### 1. Prerequisites
- Python 3.9+
- A [Snowflake free trial account](https://signup.snowflake.com/) (30 days, no credit card)

### 2. Install dependencies
```bash
pip install -r requirements.txt
```


---

## 🔍 Key Business Questions Answered

- How has EHR adoption score changed year-over-year by region?
- Did telehealth adoption spike after COVID onset (2020)?
- Do providers with higher EHR certification have lower readmission rates?
- Which EHR vendor has the highest average adoption score?
- How does adoption differ between rural vs urban hospitals?

---

## 👤 Author

**Mahek Patel**
- GitHub: [@mahekpatelmdp](https://github.com/mahekpatelmdp)
- LinkedIn: [linkedin.com/in/yourprofile](https://linkedin.com/in/yourprofile](https://www.linkedin.com/in/mahek-patel-8ba264286)

---

## 📝 License

MIT License
