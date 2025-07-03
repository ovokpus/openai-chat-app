# SQL Data Lineage for Regulatory Reporting

## FINREP F 18.00 - Information on performing and non-performing exposures

### Row 120 - Debt Securities Calculation

```sql
WITH performing_debt_securities AS (
    SELECT 
        instrument_id,
        carrying_amount,
        days_past_due,
        instrument_classification
    FROM raw_exposures
    WHERE instrument_type = 'DEBT_SECURITY'
        AND days_past_due <= 90
        AND default_status = 'NOT_DEFAULT'
),

non_performing_flags AS (
    SELECT 
        instrument_id,
        CASE 
            WHEN unlikeliness_to_pay = 1 THEN 1
            WHEN days_past_due > 90 THEN 1
            ELSE 0
        END as is_non_performing
    FROM exposure_flags
)

SELECT 
    SUM(pds.carrying_amount) as total_carrying_amount,
    COUNT(DISTINCT pds.instrument_id) as total_instruments,
    instrument_classification
FROM performing_debt_securities pds
LEFT JOIN non_performing_flags npf 
    ON pds.instrument_id = npf.instrument_id
WHERE npf.is_non_performing = 0
GROUP BY instrument_classification;
```

### Data Flow
1. Source tables:
   - `raw_exposures`: Primary exposure data
   - `exposure_flags`: Default and unlikeliness to pay indicators
2. Transformations:
   - Filter for debt securities
   - Apply performing exposure criteria
   - Calculate non-performing flags
   - Aggregate by classification
3. Target: FINREP template F 18.00, row 120

## COREP C 01.00 - Own Funds Disclosure

### Capital Ratios Calculation

```sql
WITH capital_components AS (
    SELECT 
        regulatory_capital_type,
        SUM(amount) as total_amount
    FROM capital_instruments
    WHERE valid_from <= CURRENT_DATE
        AND (valid_to IS NULL OR valid_to > CURRENT_DATE)
    GROUP BY regulatory_capital_type
),

risk_weighted_assets AS (
    SELECT 
        exposure_type,
        SUM(exposure_value * risk_weight) as rwa_amount
    FROM credit_risk_exposures
    WHERE reporting_date = CURRENT_DATE
    GROUP BY exposure_type
)

SELECT 
    cc.regulatory_capital_type,
    cc.total_amount / SUM(rwa.rwa_amount) * 100 as capital_ratio
FROM capital_components cc
CROSS JOIN (
    SELECT SUM(rwa_amount) as rwa_amount 
    FROM risk_weighted_assets
) rwa;
```

### Metadata
- **Source Systems**: 
  - Capital Management System
  - Risk Weighted Assets Calculator
- **Update Frequency**: Daily
- **Dependencies**: 
  - Capital instruments validation
  - RWA calculation completion
- **Validation Rules**:
  - CET1 ratio must be > 4.5%
  - Tier 1 ratio must be > 6%
  - Total capital ratio must be > 8% 