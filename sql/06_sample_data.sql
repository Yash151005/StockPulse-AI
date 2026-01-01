-- ============================================================================
-- StockPulse AI - Sample Data Generation
-- ============================================================================
-- Description: Generates realistic sample data for testing and demo purposes
-- Usage: Run this script after all previous setup scripts
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE STOCKPULSE_AI;
USE SCHEMA DATA;
USE WAREHOUSE STOCKPULSE_WH;

-- ============================================================================
-- 1. POPULATE LOCATION MASTER
-- ============================================================================

INSERT INTO LOCATION_MASTER (
    location_code, location_name, location_type, region, district, state, 
    priority_level, is_active
) VALUES
    ('LOC001', 'City General Hospital', 'HOSPITAL', 'North', 'Mumbai', 'Maharashtra', 'HIGH', TRUE),
    ('LOC002', 'District Health Center', 'HOSPITAL', 'North', 'Pune', 'Maharashtra', 'MEDIUM', TRUE),
    ('LOC003', 'Rural Primary Care', 'HOSPITAL', 'North', 'Nashik', 'Maharashtra', 'MEDIUM', TRUE),
    ('LOC004', 'Central Warehouse', 'WAREHOUSE', 'Central', 'Mumbai', 'Maharashtra', 'HIGH', TRUE),
    ('LOC005', 'Community Clinic A', 'HOSPITAL', 'South', 'Bangalore', 'Karnataka', 'LOW', TRUE),
    ('LOC006', 'NGO Distribution Center', 'NGO_CENTER', 'East', 'Kolkata', 'West Bengal', 'MEDIUM', TRUE),
    ('LOC007', 'State Medical Store', 'WAREHOUSE', 'North', 'Delhi', 'Delhi', 'HIGH', TRUE),
    ('LOC008', 'Tribal Health Center', 'HOSPITAL', 'Central', 'Indore', 'Madhya Pradesh', 'HIGH', TRUE),
    ('LOC009', 'Urban Health Post', 'HOSPITAL', 'South', 'Chennai', 'Tamil Nadu', 'MEDIUM', TRUE),
    ('LOC010', 'Regional Distribution Hub', 'WAREHOUSE', 'West', 'Ahmedabad', 'Gujarat', 'MEDIUM', TRUE);

-- ============================================================================
-- 2. POPULATE ITEM MASTER
-- ============================================================================

INSERT INTO ITEM_MASTER (
    item_code, item_name, item_category, unit_of_measure, 
    is_critical, default_lead_time_days, unit_cost, safety_stock, is_active
) VALUES
    -- Medicines
    ('MED001', 'Paracetamol 500mg', 'MEDICINE_ANALGESIC', 'TABLETS', TRUE, 7, 0.50, 1000, TRUE),
    ('MED002', 'Amoxicillin 250mg', 'MEDICINE_ANTIBIOTIC', 'CAPSULES', TRUE, 10, 2.00, 500, TRUE),
    ('MED003', 'Insulin Glargine 100U', 'MEDICINE_CARDIOVASCULAR', 'VIALS', TRUE, 14, 15.00, 100, TRUE),
    ('MED004', 'Aspirin 75mg', 'MEDICINE_CARDIOVASCULAR', 'TABLETS', TRUE, 7, 0.30, 800, TRUE),
    ('MED005', 'Ciprofloxacin 500mg', 'MEDICINE_ANTIBIOTIC', 'TABLETS', TRUE, 10, 3.00, 400, TRUE),
    ('MED006', 'Metformin 500mg', 'MEDICINE_CARDIOVASCULAR', 'TABLETS', TRUE, 7, 0.80, 600, TRUE),
    ('MED007', 'Ibuprofen 400mg', 'MEDICINE_ANALGESIC', 'TABLETS', FALSE, 7, 0.60, 500, TRUE),
    ('MED008', 'Azithromycin 500mg', 'MEDICINE_ANTIBIOTIC', 'TABLETS', TRUE, 10, 4.00, 300, TRUE),
    
    -- Food Items
    ('FOOD001', 'Rice - Premium', 'FOOD_GRAIN', 'KG', TRUE, 5, 50.00, 500, TRUE),
    ('FOOD002', 'Wheat Flour', 'FOOD_GRAIN', 'KG', TRUE, 5, 40.00, 400, TRUE),
    ('FOOD003', 'Lentils - Dal', 'FOOD_PROTEIN', 'KG', TRUE, 7, 80.00, 200, TRUE),
    ('FOOD004', 'Milk Powder', 'FOOD_DAIRY', 'KG', TRUE, 10, 200.00, 100, TRUE),
    ('FOOD005', 'Cooking Oil', 'FOOD', 'LITERS', TRUE, 7, 150.00, 150, TRUE),
    
    -- Medical Supplies
    ('SUPP001', 'Surgical Gloves (Box)', 'MEDICAL_SUPPLY_CONSUMABLE', 'BOXES', TRUE, 7, 10.00, 50, TRUE),
    ('SUPP002', 'Syringes 5ml', 'MEDICAL_SUPPLY_CONSUMABLE', 'PIECES', TRUE, 7, 0.50, 1000, TRUE),
    ('SUPP003', 'Bandages (Roll)', 'MEDICAL_SUPPLY_CONSUMABLE', 'ROLLS', FALSE, 5, 5.00, 100, TRUE),
    ('SUPP004', 'Gauze Pads', 'MEDICAL_SUPPLY_CONSUMABLE', 'PACKS', FALSE, 5, 3.00, 200, TRUE),
    
    -- PPE
    ('PPE001', 'N95 Masks', 'PPE', 'PIECES', TRUE, 14, 15.00, 500, TRUE),
    ('PPE002', 'Surgical Masks', 'PPE', 'PIECES', TRUE, 7, 2.00, 1000, TRUE),
    ('PPE003', 'Hand Sanitizer 500ml', 'PPE', 'BOTTLES', TRUE, 7, 50.00, 100, TRUE);

-- ============================================================================
-- 3. POPULATE SUPPLIER MASTER
-- ============================================================================

INSERT INTO SUPPLIER_MASTER (
    supplier_code, supplier_name, supplier_type, average_lead_time_days, 
    reliability_rating, is_active
) VALUES
    ('SUP001', 'PharmaCorp India', 'PHARMACEUTICAL', 7, 4.5, TRUE),
    ('SUP002', 'MedSupply Solutions', 'PHARMACEUTICAL', 10, 4.2, TRUE),
    ('SUP003', 'National Food Distributors', 'FOOD', 5, 4.8, TRUE),
    ('SUP004', 'Healthcare Equipment Ltd', 'EQUIPMENT', 14, 4.0, TRUE),
    ('SUP005', 'Safety First PPE', 'PPE', 7, 4.6, TRUE);

-- ============================================================================
-- 4. GENERATE DAILY STOCK DATA (Last 60 days)
-- ============================================================================

-- Create a temporary table with date series
CREATE OR REPLACE TEMPORARY TABLE temp_dates AS
SELECT DATEADD(day, -seq4(), CURRENT_DATE()) AS record_date
FROM TABLE(GENERATOR(ROWCOUNT => 60))
ORDER BY record_date;

-- Generate daily stock records directly into the table
INSERT INTO DAILY_STOCK_RAW (
    record_date, location_code, location_name, item_code, item_name, item_category,
    opening_stock, receipts, issues, closing_stock, unit_of_measure, lead_time_days, data_source
)
WITH location_item_combinations AS (
    SELECT 
        l.location_code,
        l.location_name,
        i.item_code,
        i.item_name,
        i.item_category,
        i.unit_of_measure,
        i.default_lead_time_days,
        -- Different daily usage patterns by location type and item
        CASE 
            WHEN l.location_type = 'HOSPITAL' AND i.is_critical THEN UNIFORM(50, 150, RANDOM())
            WHEN l.location_type = 'HOSPITAL' THEN UNIFORM(20, 80, RANDOM())
            WHEN l.location_type = 'WAREHOUSE' THEN UNIFORM(100, 300, RANDOM())
            WHEN l.location_type = 'NGO_CENTER' THEN UNIFORM(30, 100, RANDOM())
            ELSE UNIFORM(10, 50, RANDOM())
        END AS base_daily_usage,
        -- Initial stock levels
        CASE 
            WHEN l.location_type = 'WAREHOUSE' THEN UNIFORM(5000, 10000, RANDOM())
            WHEN i.is_critical THEN UNIFORM(1000, 3000, RANDOM())
            ELSE UNIFORM(500, 1500, RANDOM())
        END AS initial_stock
    FROM LOCATION_MASTER l
    CROSS JOIN ITEM_MASTER i
    WHERE l.is_active = TRUE AND i.is_active = TRUE
),
daily_transactions AS (
    SELECT 
        d.record_date,
        lic.location_code,
        lic.location_name,
        lic.item_code,
        lic.item_name,
        lic.item_category,
        lic.unit_of_measure,
        lic.default_lead_time_days,
        
        -- Calculate stock movements with variability
        ROUND(
            lic.base_daily_usage * 
            (1 + (UNIFORM(-0.3, 0.3, RANDOM())))  -- ±30% variability
            * CASE DAYOFWEEK(d.record_date)
                WHEN 0 THEN 0.5  -- Sunday - lower usage
                WHEN 6 THEN 0.7  -- Saturday - lower usage
                ELSE 1.0
              END
        , 2) AS daily_issue,
        
        -- Receipts (every 7-14 days with some randomness)
        CASE 
            WHEN MOD(DATEDIFF(day, '2024-01-01', d.record_date), 10) = 0 
            THEN ROUND(lic.base_daily_usage * lic.default_lead_time_days * 1.5, 2)
            ELSE 0
        END AS daily_receipt,
        
        lic.initial_stock,
        ROW_NUMBER() OVER (PARTITION BY lic.location_code, lic.item_code ORDER BY d.record_date) AS day_num
        
    FROM temp_dates d
    CROSS JOIN location_item_combinations lic
),
calculated_balances AS (
    SELECT 
        record_date,
        location_code,
        location_name,
        item_code,
        item_name,
        item_category,
        unit_of_measure,
        default_lead_time_days,
        daily_receipt,
        daily_issue,
        initial_stock,
        day_num,
        -- Calculate running balance
        initial_stock + SUM(daily_receipt - daily_issue) OVER (
            PARTITION BY location_code, item_code 
            ORDER BY record_date 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS closing_stock
    FROM daily_transactions
    WHERE daily_issue IS NOT NULL
)
SELECT 
    record_date,
    location_code,
    location_name,
    item_code,
    item_name,
    item_category,
    
    -- Opening stock is previous day's closing stock or initial stock for day 1
    CASE 
        WHEN day_num = 1 THEN initial_stock
        ELSE LAG(closing_stock, 1) OVER (PARTITION BY location_code, item_code ORDER BY record_date)
    END AS opening_stock,
    
    daily_receipt AS receipts,
    daily_issue AS issues,
    closing_stock,
    
    unit_of_measure,
    default_lead_time_days AS lead_time_days,
    'SAMPLE_DATA_GENERATOR' AS data_source
    
FROM calculated_balances
ORDER BY location_code, item_code, record_date;

-- ============================================================================
-- 5. CREATE SOME CRITICAL SCENARIOS FOR TESTING
-- ============================================================================

-- Scenario 1: Create an out-of-stock situation
UPDATE DAILY_STOCK_RAW
SET 
    issues = closing_stock + 10,
    closing_stock = -10
WHERE 
    location_code = 'LOC001'
    AND item_code = 'MED003'
    AND record_date = CURRENT_DATE();

-- Fix the negative stock
UPDATE DAILY_STOCK_RAW
SET closing_stock = 0
WHERE closing_stock < 0;

-- Scenario 2: Create a critical low stock situation
UPDATE DAILY_STOCK_RAW
SET closing_stock = 50
WHERE 
    location_code = 'LOC002'
    AND item_code = 'MED001'
    AND record_date = CURRENT_DATE();

-- Scenario 3: Create an overstock situation (no movement)
UPDATE DAILY_STOCK_RAW
SET 
    issues = 0,
    receipts = 0
WHERE 
    location_code = 'LOC005'
    AND item_code = 'SUPP003'
    AND record_date >= DATEADD(day, -40, CURRENT_DATE());

-- ============================================================================
-- 6. POPULATE ITEM-LOCATION PARAMETERS
-- ============================================================================

INSERT INTO ITEM_LOCATION_PARAMS (
    location_code, item_code, custom_lead_time_days, 
    custom_reorder_point, custom_safety_stock, is_stocked
)
SELECT 
    l.location_code,
    i.item_code,
    CASE 
        WHEN l.region IN ('North', 'Central') THEN i.default_lead_time_days + 2
        ELSE i.default_lead_time_days
    END AS custom_lead_time_days,
    i.safety_stock * 1.5 AS custom_reorder_point,
    i.safety_stock AS custom_safety_stock,
    TRUE AS is_stocked
FROM LOCATION_MASTER l
CROSS JOIN ITEM_MASTER i
WHERE 
    l.is_active = TRUE 
    AND i.is_active = TRUE
    -- Only stock medicines at hospitals
    AND (
        (l.location_type = 'HOSPITAL' AND i.item_category LIKE 'MEDICINE%')
        OR (l.location_type = 'HOSPITAL' AND i.item_category LIKE 'MEDICAL%')
        OR (l.location_type IN ('WAREHOUSE', 'NGO_CENTER'))
    )
LIMIT 50;  -- Limit to avoid too many combinations

-- ============================================================================
-- 7. POPULATE ALERT CONFIGURATION
-- ============================================================================

INSERT INTO ALERT_CONFIG (
    alert_name, alert_type, threshold_days, severity, is_active
) VALUES
    ('Critical Stock-Out Alert', 'STOCK_OUT', 0, 'CRITICAL', TRUE),
    ('3-Day Stock-Out Warning', 'CRITICAL', 3, 'CRITICAL', TRUE),
    ('Low Stock Alert', 'LOW_STOCK', 7, 'HIGH', TRUE),
    ('Overstock Warning', 'OVERSTOCK', 60, 'MEDIUM', TRUE),
    ('Expiry Warning - 30 Days', 'EXPIRY_WARNING', 30, 'MEDIUM', TRUE);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check data counts
SELECT 
    'Daily Stock Records' AS data_type,
    COUNT(*) AS record_count,
    MIN(record_date) AS earliest_date,
    MAX(record_date) AS latest_date
FROM DAILY_STOCK_RAW

UNION ALL

SELECT 
    'Locations' AS data_type,
    COUNT(*) AS record_count,
    NULL AS earliest_date,
    NULL AS latest_date
FROM LOCATION_MASTER

UNION ALL

SELECT 
    'Items' AS data_type,
    COUNT(*) AS record_count,
    NULL AS earliest_date,
    NULL AS latest_date
FROM ITEM_MASTER;

-- Show sample stock data
SELECT 
    location_name,
    item_name,
    record_date,
    closing_stock,
    issues
FROM DAILY_STOCK_RAW
WHERE record_date >= DATEADD(day, -7, CURRENT_DATE())
ORDER BY location_code, item_code, record_date DESC
LIMIT 50;

-- Check for critical items
SELECT 
    location_name,
    item_name,
    closing_stock,
    record_date
FROM DAILY_STOCK_RAW
WHERE 
    closing_stock < 100
    AND record_date = CURRENT_DATE()
ORDER BY closing_stock
LIMIT 20;

-- ============================================================================
-- REFRESH DYNAMIC TABLES (if needed)
-- ============================================================================

-- Dynamic tables should auto-refresh, but you can manually refresh if needed:
-- ALTER DYNAMIC TABLE STOCKPULSE_AI.ANALYTICS.DT_STOCK_HEALTH_CLASSIFICATION REFRESH;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. This generates 60 days of sample data for testing
-- 2. Data includes realistic patterns: weekend effects, periodic receipts, variability
-- 3. Several critical scenarios are created to test alert generation
-- 4. Dynamic Tables will automatically process this data
-- 5. Wait a few minutes for Dynamic Tables to refresh before viewing dashboard
-- 6. To regenerate data, truncate DAILY_STOCK_RAW and run this script again
-- ============================================================================
