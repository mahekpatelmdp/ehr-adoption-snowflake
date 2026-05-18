-- sql_queries.sql
-- Analytical queries for EHR Adoption & Workflow Optimization
-- Replace EHR_DB.EHR_SCHEMA with your Snowflake database and schema

-- ── 1. Row counts per table ───────────────────────────────────────────────────

SELECT 'fact_ehr_adoptions'    AS tbl, COUNT(*) AS rows FROM EHR_DB.EHR_SCHEMA.fact_ehr_adoptions
UNION ALL
SELECT 'fact_workflow_metrics', COUNT(*) FROM EHR_DB.EHR_SCHEMA.fact_workflow_metrics
UNION ALL
SELECT 'dim_providers',         COUNT(*) FROM EHR_DB.EHR_SCHEMA.dim_providers
UNION ALL
SELECT 'dim_program_year',      COUNT(*) FROM EHR_DB.EHR_SCHEMA.dim_program_year
UNION ALL
SELECT 'dim_ehr_vendor',        COUNT(*) FROM EHR_DB.EHR_SCHEMA.dim_ehr_vendor;


-- ── 2. EHR adoption score by state and year ───────────────────────────────────

SELECT
    p.state,
    y.program_year,
    COUNT(f.adoption_key)            AS total_providers,
    ROUND(AVG(f.adoption_score), 2)  AS avg_adoption_score,
    ROUND(AVG(f.staff_trained_pct), 1) AS avg_staff_trained_pct
FROM EHR_DB.EHR_SCHEMA.fact_ehr_adoptions  f
JOIN EHR_DB.EHR_SCHEMA.dim_providers        p ON f.provider_key = p.provider_key
JOIN EHR_DB.EHR_SCHEMA.dim_program_year     y ON f.year_key = y.year_key
GROUP BY p.state, y.program_year
ORDER BY y.program_year, avg_adoption_score DESC;


-- ── 3. Certification level distribution by hospital type ─────────────────────

SELECT
    p.hospital_type,
    f.certification_level,
    COUNT(*) AS provider_count,
    ROUND(AVG(f.adoption_score), 2) AS avg_adoption_score
FROM EHR_DB.EHR_SCHEMA.fact_ehr_adoptions f
JOIN EHR_DB.EHR_SCHEMA.dim_providers       p ON f.provider_key = p.provider_key
GROUP BY p.hospital_type, f.certification_level
ORDER BY p.hospital_type, provider_count DESC;


-- ── 4. EHR vendor market share by tier ───────────────────────────────────────

SELECT
    v.vendor_name,
    v.vendor_tier,
    COUNT(f.adoption_key)            AS total_adoptions,
    ROUND(AVG(f.adoption_score), 2)  AS avg_adoption_score,
    ROUND(AVG(f.staff_trained_pct), 1) AS avg_staff_trained_pct
FROM EHR_DB.EHR_SCHEMA.fact_ehr_adoptions f
JOIN EHR_DB.EHR_SCHEMA.dim_ehr_vendor      v ON f.vendor_key = v.vendor_key
GROUP BY v.vendor_name, v.vendor_tier
ORDER BY total_adoptions DESC;


-- ── 5. Telehealth adoption trend (pre vs post COVID) ─────────────────────────

SELECT
    y.program_year,
    y.era,
    COUNT(f.adoption_key)                                   AS total_providers,
    SUM(f.telehealth_enabled)                               AS telehealth_enabled_count,
    ROUND(AVG(f.telehealth_enabled) * 100, 1)               AS telehealth_adoption_pct,
    ROUND(AVG(f.interoperability_enabled) * 100, 1)         AS interoperability_pct
FROM EHR_DB.EHR_SCHEMA.fact_ehr_adoptions f
JOIN EHR_DB.EHR_SCHEMA.dim_program_year    y ON f.year_key = y.year_key
GROUP BY y.program_year, y.era
ORDER BY y.program_year;


-- ── 6. Workflow efficiency: documentation time by certification level ─────────

SELECT
    f2.certification_level,
    COUNT(m.metric_key)                              AS providers_measured,
    ROUND(AVG(m.avg_documentation_time_min), 1)      AS avg_doc_time_min,
    ROUND(AVG(m.order_entry_error_rate_pct), 2)      AS avg_error_rate_pct,
    ROUND(AVG(m.data_completeness_pct), 1)           AS avg_data_completeness_pct,
    ROUND(AVG(m.patient_satisfaction_score), 2)      AS avg_patient_satisfaction
FROM EHR_DB.EHR_SCHEMA.fact_workflow_metrics  m
JOIN EHR_DB.EHR_SCHEMA.fact_ehr_adoptions      f2 ON m.adoption_key = f2.adoption_key
GROUP BY f2.certification_level
ORDER BY avg_doc_time_min;


-- ── 7. Rural vs urban adoption gap ───────────────────────────────────────────

SELECT
    p.rural_urban,
    ROUND(AVG(f.adoption_score), 2)          AS avg_adoption_score,
    ROUND(AVG(f.staff_trained_pct), 1)       AS avg_staff_trained_pct,
    ROUND(AVG(f.downtime_hours_annual), 1)   AS avg_downtime_hours,
    COUNT(DISTINCT p.provider_key)           AS provider_count
FROM EHR_DB.EHR_SCHEMA.fact_ehr_adoptions f
JOIN EHR_DB.EHR_SCHEMA.dim_providers       p ON f.provider_key = p.provider_key
GROUP BY p.rural_urban
ORDER BY avg_adoption_score DESC;


-- ── 8. Top performing providers (high adoption + low error rate) ──────────────

SELECT
    p.provider_name,
    p.state,
    p.hospital_type,
    ROUND(AVG(f.adoption_score), 2)              AS avg_adoption_score,
    ROUND(AVG(m.order_entry_error_rate_pct), 2)  AS avg_error_rate,
    ROUND(AVG(m.data_completeness_pct), 1)       AS avg_data_completeness
FROM EHR_DB.EHR_SCHEMA.fact_ehr_adoptions     f
JOIN EHR_DB.EHR_SCHEMA.dim_providers           p ON f.provider_key = p.provider_key
JOIN EHR_DB.EHR_SCHEMA.fact_workflow_metrics   m ON f.adoption_key = m.adoption_key
GROUP BY p.provider_name, p.state, p.hospital_type
HAVING avg_adoption_score > 80 AND avg_error_rate < 2.0
ORDER BY avg_adoption_score DESC
LIMIT 15;


-- ── 9. Readmission rate vs EHR adoption score correlation ────────────────────

SELECT
    CASE
        WHEN f.adoption_score < 50  THEN 'Low (< 50)'
        WHEN f.adoption_score < 75  THEN 'Medium (50-75)'
        ELSE 'High (> 75)'
    END AS adoption_tier,
    COUNT(m.metric_key)                          AS provider_count,
    ROUND(AVG(m.readmission_rate_pct), 2)        AS avg_readmission_rate,
    ROUND(AVG(m.avg_length_of_stay_days), 2)     AS avg_los_days
FROM EHR_DB.EHR_SCHEMA.fact_workflow_metrics  m
JOIN EHR_DB.EHR_SCHEMA.fact_ehr_adoptions      f ON m.adoption_key = f.adoption_key
GROUP BY adoption_tier
ORDER BY avg_readmission_rate;


-- ── 10. Year-over-year adoption score improvement by region ──────────────────

SELECT
    p.region,
    y.program_year,
    ROUND(AVG(f.adoption_score), 2) AS avg_adoption_score,
    ROUND(AVG(f.adoption_score) - LAG(ROUND(AVG(f.adoption_score), 2))
        OVER (PARTITION BY p.region ORDER BY y.program_year), 2) AS yoy_change
FROM EHR_DB.EHR_SCHEMA.fact_ehr_adoptions f
JOIN EHR_DB.EHR_SCHEMA.dim_providers       p ON f.provider_key = p.provider_key
JOIN EHR_DB.EHR_SCHEMA.dim_program_year    y ON f.year_key = y.year_key
GROUP BY p.region, y.program_year
ORDER BY p.region, y.program_year;
