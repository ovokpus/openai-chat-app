-- SQL Data Lineage: COREP Capital Adequacy Calculation
-- This script demonstrates the data lineage for Basel III capital calculations
-- Source: Regulatory Reporting ETL Pipeline

-- =============================================================================
-- CAPITAL ADEQUACY RATIO CALCULATION - BASEL III COMPLIANT
-- =============================================================================

-- Step 1: Extract Common Equity Tier 1 (CET1) components
WITH cet1_components AS (
    SELECT 
        reporting_date,
        institution_id,
        -- Common shares and related stock surplus
        common_shares_outstanding * share_price AS common_share_capital,
        retained_earnings,
        accumulated_oci AS accumulated_other_comprehensive_income,
        -- Regulatory adjustments
        goodwill * -1 AS goodwill_deduction,
        intangible_assets * -1 AS intangible_deduction,
        deferred_tax_assets * -1 AS dta_deduction
    FROM 
        regulatory_capital.balance_sheet_items bsi
    JOIN regulatory_capital.market_data md ON bsi.reporting_date = md.reporting_date
    WHERE 
        reporting_date = '2024-12-31'
        AND institution_id = 'BANK001'
),

-- Step 2: Calculate Total Risk-Weighted Assets (RWA)
risk_weighted_assets AS (
    SELECT 
        reporting_date,
        institution_id,
        -- Credit Risk RWA (Standardised Approach)
        SUM(CASE 
            WHEN exposure_class = 'SOVEREIGN' THEN exposure_amount * 0.00
            WHEN exposure_class = 'INSTITUTION' THEN exposure_amount * 0.20
            WHEN exposure_class = 'CORPORATE' THEN exposure_amount * 1.00
            WHEN exposure_class = 'RETAIL' THEN exposure_amount * 0.75
            WHEN exposure_class = 'SECURED_REAL_ESTATE' THEN exposure_amount * 0.35
            ELSE exposure_amount * 1.25
        END) AS credit_rwa,
        
        -- Market Risk RWA (Standardised Approach)
        SUM(CASE 
            WHEN risk_type = 'INTEREST_RATE' THEN capital_charge * 12.5
            WHEN risk_type = 'EQUITY' THEN capital_charge * 12.5
            WHEN risk_type = 'FX' THEN capital_charge * 12.5
            WHEN risk_type = 'COMMODITY' THEN capital_charge * 12.5
            ELSE 0
        END) AS market_rwa,
        
        -- Operational Risk RWA (Basic Indicator Approach)
        AVG(gross_income) * 0.15 * 12.5 AS operational_rwa
        
    FROM 
        regulatory_capital.credit_exposures ce
    LEFT JOIN regulatory_capital.market_risk_positions mrp 
        ON ce.institution_id = mrp.institution_id 
        AND ce.reporting_date = mrp.reporting_date
    LEFT JOIN regulatory_capital.income_statement inc 
        ON ce.institution_id = inc.institution_id 
        AND YEAR(ce.reporting_date) = YEAR(inc.reporting_date)
    WHERE 
        ce.reporting_date = '2024-12-31'
        AND ce.institution_id = 'BANK001'
    GROUP BY 
        reporting_date, 
        institution_id
),

-- Step 3: Finalize CET1 Capital Calculation
cet1_capital AS (
    SELECT 
        reporting_date,
        institution_id,
        common_share_capital + 
        retained_earnings + 
        accumulated_other_comprehensive_income +
        goodwill_deduction +
        intangible_deduction +
        dta_deduction AS cet1_capital_amount
    FROM cet1_components
),

-- Step 4: Calculate Capital Ratios for COREP Template C 01.00
capital_ratios AS (
    SELECT 
        c.reporting_date,
        c.institution_id,
        c.cet1_capital_amount,
        r.credit_rwa + r.market_rwa + r.operational_rwa AS total_rwa,
        
        -- Basel III Minimum Requirements
        (c.cet1_capital_amount / NULLIF(r.credit_rwa + r.market_rwa + r.operational_rwa, 0)) * 100 AS cet1_ratio_pct,
        
        -- COREP Template mapping
        'C 01.00' AS corep_template,
        '010' AS cet1_capital_row,
        '020' AS total_rwa_row
        
    FROM cet1_capital c
    JOIN risk_weighted_assets r 
        ON c.reporting_date = r.reporting_date 
        AND c.institution_id = r.institution_id
)

-- Final Output: Insert into COREP reporting table
INSERT INTO regulatory_reporting.corep_capital_adequacy (
    reporting_date,
    institution_id,
    template_id,
    row_id,
    metric_name,
    metric_value,
    currency,
    created_timestamp
)
SELECT 
    reporting_date,
    institution_id,
    corep_template,
    cet1_capital_row,
    'Common Equity Tier 1 Capital',
    cet1_capital_amount,
    'EUR',
    CURRENT_TIMESTAMP
FROM capital_ratios

UNION ALL

SELECT 
    reporting_date,
    institution_id,
    corep_template,
    total_rwa_row,
    'Total Risk Weighted Assets', 
    total_rwa,
    'EUR',
    CURRENT_TIMESTAMP
FROM capital_ratios

UNION ALL

SELECT 
    reporting_date,
    institution_id,
    corep_template,
    '030',
    'CET1 Ratio (%)',
    cet1_ratio_pct,
    'PCT',
    CURRENT_TIMESTAMP
FROM capital_ratios;

-- Data Quality Checks
-- ===================

-- Check 1: CET1 Ratio must be >= 4.5% (Basel III minimum)
SELECT 
    institution_id,
    cet1_ratio_pct,
    CASE 
        WHEN cet1_ratio_pct >= 4.5 THEN 'PASS'
        ELSE 'FAIL - Below Basel III minimum'
    END AS basel_iii_compliance
FROM capital_ratios;

-- Check 2: Validate data lineage completeness
SELECT 
    'Data Lineage Check' AS check_type,
    COUNT(DISTINCT ce.exposure_id) AS total_exposures,
    COUNT(DISTINCT mrp.position_id) AS total_market_positions,
    COUNT(DISTINCT inc.period_id) AS income_periods
FROM regulatory_capital.credit_exposures ce
FULL OUTER JOIN regulatory_capital.market_risk_positions mrp 
    ON ce.institution_id = mrp.institution_id
FULL OUTER JOIN regulatory_capital.income_statement inc 
    ON ce.institution_id = inc.institution_id;

-- Source System Mapping:
-- ======================
-- Credit Exposures: Core Banking System (CBS) -> DWH.credit_exposures -> regulatory_capital.credit_exposures
-- Market Risk: Trading System (MUREX) -> DWH.trading_positions -> regulatory_capital.market_risk_positions  
-- Income Statement: General Ledger (SAP) -> DWH.financial_data -> regulatory_capital.income_statement
-- Final Output: regulatory_reporting.corep_capital_adequacy -> EBA XBRL submission 