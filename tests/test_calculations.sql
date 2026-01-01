-- ============================================================================
-- StockPulse AI - SQL Unit Tests for Calculations
-- ============================================================================
-- Description: Test cases for core calculation logic
-- Usage: Run these queries to verify calculation accuracy
-- ============================================================================

USE ROLE STOCKPULSE_ADMIN;
USE DATABASE STOCKPULSE_AI;
USE WAREHOUSE STOCKPULSE_WH;

-- ============================================================================
-- TEST 1: Stock Health Score Calculation
-- ============================================================================

WITH test_cases AS (
    SELECT 
        'Healthy Stock' AS test_case,
        20.0 AS days_of_cover,
        7 AS lead_time_days,
        0 AS days_since_movement,
        90.0 AS expected_min_score,
        100.0 AS expected_max_score
    UNION ALL
    SELECT 'Critical Stock', 3.0, 7, 0, 10.0, 30.0
    UNION ALL
    SELECT 'Out of Stock', 0.0, 7, 0, 0.0, 0.0
    UNION ALL
    SELECT 'Overstock', 30.0, 7, 35, 55.0, 65.0
)
SELECT 
    test_case,
    days_of_cover,
    lead_time_days,
    
    -- Apply stock health score formula
    CASE 
        WHEN days_since_movement > 30 THEN 60
        WHEN days_of_cover > (lead_time_days * 1.5) THEN 
            LEAST(100, 80 + ((days_of_cover - (lead_time_days * 1.5)) / lead_time_days * 10))
        WHEN days_of_cover > lead_time_days THEN 
            50 + ((days_of_cover - lead_time_days) / (lead_time_days * 0.5) * 30)
        WHEN days_of_cover > (lead_time_days * 0.5) THEN 
            25 + ((days_of_cover - (lead_time_days * 0.5)) / (lead_time_days * 0.5) * 25)
        WHEN days_of_cover > 0 THEN 
            (days_of_cover / (lead_time_days * 0.5)) * 25
        ELSE 0
    END AS calculated_score,
    
    expected_min_score,
    expected_max_score,
    
    -- Validation
    CASE 
        WHEN calculated_score BETWEEN expected_min_score AND expected_max_score 
        THEN '✅ PASS' 
        ELSE '❌ FAIL' 
    END AS test_result
FROM test_cases;

-- ============================================================================
-- TEST 2: Reorder Quantity Calculation
-- ============================================================================

WITH test_cases AS (
    SELECT 
        'Normal Reorder' AS test_case,
        50.0 AS avg_daily_issue,
        7 AS lead_time_days,
        200.0 AS current_stock,
        100.0 AS safety_stock,
        320.0 AS expected_reorder_qty  -- (50 * 7 * 1.2) + 100 - 200 = 320
    UNION ALL
    SELECT 'No Reorder Needed', 20.0, 7, 500.0, 50.0, 0.0
    UNION ALL
    SELECT 'Emergency Reorder', 100.0, 7, 50.0, 200.0, 990.0  -- (100 * 7 * 1.2) + 200 - 50 = 990
)
SELECT 
    test_case,
    avg_daily_issue,
    lead_time_days,
    current_stock,
    safety_stock,
    
    -- Apply reorder formula
    GREATEST(0, 
        ROUND(
            (avg_daily_issue * lead_time_days * 1.2) + safety_stock - current_stock,
            2
        )
    ) AS calculated_reorder_qty,
    
    expected_reorder_qty,
    
    -- Validation
    CASE 
        WHEN ABS(calculated_reorder_qty - expected_reorder_qty) < 1.0 
        THEN '✅ PASS' 
        ELSE '❌ FAIL' 
    END AS test_result
FROM test_cases;

-- ============================================================================
-- TEST 3: Days of Cover Calculation
-- ============================================================================

WITH test_cases AS (
    SELECT 
        'Standard Usage' AS test_case,
        500.0 AS current_stock,
        25.0 AS avg_daily_issue,
        20.0 AS expected_days_of_cover
    UNION ALL
    SELECT 'Zero Consumption', 500.0, 0.0, 999.0
    UNION ALL
    SELECT 'Low Stock', 50.0, 25.0, 2.0
)
SELECT 
    test_case,
    current_stock,
    avg_daily_issue,
    
    -- Apply days of cover formula
    CASE 
        WHEN avg_daily_issue > 0 THEN current_stock / avg_daily_issue
        ELSE 999
    END AS calculated_days_of_cover,
    
    expected_days_of_cover,
    
    -- Validation
    CASE 
        WHEN ABS(calculated_days_of_cover - expected_days_of_cover) < 0.1 
        THEN '✅ PASS' 
        ELSE '❌ FAIL' 
    END AS test_result
FROM test_cases;

-- ============================================================================
-- TEST 4: Risk Classification Logic
-- ============================================================================

WITH test_cases AS (
    SELECT 
        'Out of Stock' AS test_case,
        0.0 AS closing_stock,
        0 AS days_until_stockout,
        7 AS lead_time_days,
        0 AS days_since_movement,
        'OUT_OF_STOCK' AS expected_classification
    UNION ALL
    SELECT 'Critical', 50.0, 2, 7, 0, 'CRITICAL'
    UNION ALL
    SELECT 'High Risk', 200.0, 5, 7, 0, 'HIGH_RISK'
    UNION ALL
    SELECT 'Medium Risk', 300.0, 9, 7, 0, 'MEDIUM_RISK'
    UNION ALL
    SELECT 'Healthy', 500.0, 20, 7, 0, 'HEALTHY'
    UNION ALL
    SELECT 'Overstock', 1000.0, 100, 7, 65, 'OVERSTOCK'
)
SELECT 
    test_case,
    closing_stock,
    days_until_stockout,
    lead_time_days,
    
    -- Apply risk classification logic
    CASE 
        WHEN closing_stock <= 0 THEN 'OUT_OF_STOCK'
        WHEN days_until_stockout <= 3 THEN 'CRITICAL'
        WHEN days_until_stockout <= lead_time_days THEN 'HIGH_RISK'
        WHEN days_until_stockout <= (lead_time_days * 1.5) THEN 'MEDIUM_RISK'
        WHEN days_since_movement > 60 THEN 'OVERSTOCK'
        WHEN days_since_movement > 30 THEN 'SLOW_MOVING'
        ELSE 'HEALTHY'
    END AS calculated_classification,
    
    expected_classification,
    
    -- Validation
    CASE 
        WHEN calculated_classification = expected_classification 
        THEN '✅ PASS' 
        ELSE '❌ FAIL' 
    END AS test_result
FROM test_cases;

-- ============================================================================
-- TEST 5: Procurement Priority Score
-- ============================================================================

WITH test_cases AS (
    SELECT 
        'Emergency Critical Item' AS test_case,
        0 AS days_until_stockout,
        7 AS lead_time_days,
        TRUE AS is_critical_item,
        'HIGH' AS location_priority,
        150.0 AS expected_min_score,
        195.0 AS expected_max_score
    UNION ALL
    SELECT 'Normal Non-Critical', 10, 7, FALSE, 'MEDIUM', 40.0, 60.0
    UNION ALL
    SELECT 'Healthy Critical', 20, 7, TRUE, 'HIGH', 60.0, 80.0
)
SELECT 
    test_case,
    days_until_stockout,
    is_critical_item,
    location_priority,
    
    -- Apply priority score formula
    (
        CASE 
            WHEN days_until_stockout <= 0 THEN 100
            WHEN days_until_stockout <= 3 THEN 95
            WHEN days_until_stockout <= lead_time_days THEN 
                100 - ((days_until_stockout / lead_time_days) * 30)
            ELSE 50
        END
        * CASE WHEN is_critical_item THEN 1.5 ELSE 1.0 END
        * CASE location_priority 
            WHEN 'HIGH' THEN 1.3 
            WHEN 'MEDIUM' THEN 1.0 
            WHEN 'LOW' THEN 0.8 
            ELSE 1.0 
          END
    ) AS calculated_priority_score,
    
    expected_min_score,
    expected_max_score,
    
    -- Validation
    CASE 
        WHEN calculated_priority_score BETWEEN expected_min_score AND expected_max_score 
        THEN '✅ PASS' 
        ELSE '❌ FAIL' 
    END AS test_result
FROM test_cases;

-- ============================================================================
-- TEST 6: Stock Balance Validation
-- ============================================================================

-- Create test records with intentional issues
CREATE OR REPLACE TEMPORARY TABLE test_stock_balance AS
SELECT 
    'BAL_001' AS test_id,
    CURRENT_DATE() AS record_date,
    'LOC_TEST' AS location_code,
    'ITEM_TEST' AS item_code,
    100.0 AS opening_stock,
    50.0 AS receipts,
    30.0 AS issues,
    120.0 AS closing_stock,  -- Correct: 100 + 50 - 30 = 120
    'PASS' AS expected_result
UNION ALL
SELECT 
    'BAL_002',
    CURRENT_DATE(),
    'LOC_TEST',
    'ITEM_TEST2',
    100.0,
    50.0,
    30.0,
    100.0,  -- Incorrect: Should be 120
    'FAIL';

-- Test the balance validation
SELECT 
    test_id,
    opening_stock,
    receipts,
    issues,
    closing_stock,
    (opening_stock + receipts - issues) AS calculated_closing,
    CASE 
        WHEN ABS(closing_stock - (opening_stock + receipts - issues)) < 0.01 
        THEN 'PASS' 
        ELSE 'FAIL' 
    END AS actual_result,
    expected_result,
    CASE 
        WHEN actual_result = expected_result 
        THEN '✅ PASS' 
        ELSE '❌ FAIL' 
    END AS test_result
FROM test_stock_balance;

-- Clean up
DROP TABLE IF EXISTS test_stock_balance;

-- ============================================================================
-- TEST SUMMARY REPORT
-- ============================================================================

SELECT 
    '============================================' AS line
UNION ALL
SELECT 'STOCKPULSE AI - UNIT TEST SUMMARY'
UNION ALL
SELECT '============================================'
UNION ALL
SELECT ''
UNION ALL
SELECT 'All core calculation tests completed.'
UNION ALL
SELECT 'Review results above for any failures.'
UNION ALL
SELECT ''
UNION ALL
SELECT 'Test Categories:'
UNION ALL
SELECT '  1. Stock Health Score Calculation'
UNION ALL
SELECT '  2. Reorder Quantity Calculation'
UNION ALL
SELECT '  3. Days of Cover Calculation'
UNION ALL
SELECT '  4. Risk Classification Logic'
UNION ALL
SELECT '  5. Procurement Priority Score'
UNION ALL
SELECT '  6. Stock Balance Validation'
UNION ALL
SELECT ''
UNION ALL
SELECT '✅ = Test Passed'
UNION ALL
SELECT '❌ = Test Failed (Review logic or test case)'
UNION ALL
SELECT '============================================';

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. Run this script after deploying the system to verify calculations
-- 2. All tests should show ✅ PASS status
-- 3. If any test fails, review the calculation logic in the corresponding view
-- 4. Add additional test cases as needed for edge cases specific to your data
-- 5. Run these tests after any changes to core calculation logic
-- ============================================================================
