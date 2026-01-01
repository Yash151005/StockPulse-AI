-- ============================================================================
-- StockPulse AI - Stock Health Metrics & Analytics Views
-- ============================================================================
-- Description: Core calculation logic for stock health, consumption trends,
--              and reorder intelligence
-- Usage: Run this script after 02_create_tables.sql
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE STOCKPULSE_AI;
USE SCHEMA ANALYTICS;
USE WAREHOUSE STOCKPULSE_WH;

-- ============================================================================
-- 1. LATEST STOCK POSITION VIEW
-- ============================================================================

CREATE OR REPLACE VIEW V_LATEST_STOCK_POSITION AS
SELECT 
    location_code,
    location_name,
    item_code,
    item_name,
    item_category,
    record_date AS latest_date,
    closing_stock,
    unit_of_measure,
    lead_time_days
FROM (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY location_code, item_code ORDER BY record_date DESC) AS rn
    FROM STOCKPULSE_AI.DATA.DAILY_STOCK_RAW
)
WHERE rn = 1;


-- ============================================================================
-- 2. CONSUMPTION METRICS VIEW (7, 14, 30 day averages)
-- ============================================================================

CREATE OR REPLACE VIEW V_CONSUMPTION_METRICS AS
WITH daily_issues AS (
    SELECT 
        location_code,
        location_name,
        item_code,
        item_name,
        item_category,
        record_date,
        issues,
        unit_of_measure
    FROM STOCKPULSE_AI.DATA.DAILY_STOCK_RAW
    WHERE record_date >= DATEADD(day, -90, CURRENT_DATE())  -- Last 90 days
)
SELECT 
    location_code,
    location_name,
    item_code,
    item_name,
    item_category,
    unit_of_measure,
    
    -- 7-day metrics
    AVG(CASE WHEN record_date >= DATEADD(day, -7, CURRENT_DATE()) THEN issues END) AS avg_daily_issue_7d,
    SUM(CASE WHEN record_date >= DATEADD(day, -7, CURRENT_DATE()) THEN issues ELSE 0 END) AS total_issues_7d,
    STDDEV(CASE WHEN record_date >= DATEADD(day, -7, CURRENT_DATE()) THEN issues END) AS stddev_issues_7d,
    
    -- 14-day metrics
    AVG(CASE WHEN record_date >= DATEADD(day, -14, CURRENT_DATE()) THEN issues END) AS avg_daily_issue_14d,
    SUM(CASE WHEN record_date >= DATEADD(day, -14, CURRENT_DATE()) THEN issues ELSE 0 END) AS total_issues_14d,
    STDDEV(CASE WHEN record_date >= DATEADD(day, -14, CURRENT_DATE()) THEN issues END) AS stddev_issues_14d,
    
    -- 30-day metrics
    AVG(CASE WHEN record_date >= DATEADD(day, -30, CURRENT_DATE()) THEN issues END) AS avg_daily_issue_30d,
    SUM(CASE WHEN record_date >= DATEADD(day, -30, CURRENT_DATE()) THEN issues ELSE 0 END) AS total_issues_30d,
    STDDEV(CASE WHEN record_date >= DATEADD(day, -30, CURRENT_DATE()) THEN issues END) AS stddev_issues_30d,
    
    -- Movement metrics
    COUNT(DISTINCT CASE WHEN record_date >= DATEADD(day, -30, CURRENT_DATE()) AND issues > 0 THEN record_date END) AS days_with_movement_30d,
    MAX(CASE WHEN issues > 0 THEN record_date END) AS last_movement_date,
    DATEDIFF(day, MAX(CASE WHEN issues > 0 THEN record_date END), CURRENT_DATE()) AS days_since_last_movement
    
FROM daily_issues
GROUP BY 
    location_code, location_name, item_code, item_name, item_category, unit_of_measure;

-- ============================================================================
-- 3. STOCK HEALTH CORE METRICS VIEW
-- ============================================================================

CREATE OR REPLACE VIEW V_STOCK_HEALTH_METRICS AS
SELECT 
    l.location_code,
    l.location_name,
    l.item_code,
    l.item_name,
    l.item_category,
    l.latest_date,
    l.closing_stock,
    l.unit_of_measure,
    
    -- Lead time (with fallbacks)
    COALESCE(
        ilp.custom_lead_time_days,
        im.default_lead_time_days,
        l.lead_time_days,
        7
    ) AS lead_time_days,
    
    -- Safety stock and reorder parameters
    COALESCE(ilp.custom_safety_stock, im.safety_stock, 0) AS safety_stock,
    COALESCE(ilp.custom_reorder_point, im.reorder_point) AS reorder_point,
    COALESCE(ilp.max_stock_level, 999999) AS max_stock_level,
    
    -- Consumption metrics (prioritize 14-day, fallback to 7-day, then 30-day)
    COALESCE(c.avg_daily_issue_14d, c.avg_daily_issue_7d, c.avg_daily_issue_30d, 0) AS avg_daily_issue,
    c.total_issues_7d,
    c.total_issues_14d,
    c.total_issues_30d,
    c.days_with_movement_30d,
    c.last_movement_date,
    c.days_since_last_movement,
    
    -- Days of cover calculation
    CASE 
        WHEN COALESCE(c.avg_daily_issue_14d, c.avg_daily_issue_7d, c.avg_daily_issue_30d, 0) > 0 
        THEN l.closing_stock / COALESCE(c.avg_daily_issue_14d, c.avg_daily_issue_7d, c.avg_daily_issue_30d)
        ELSE 999
    END AS days_of_cover,
    
    -- Projected stock-out date
    CASE 
        WHEN COALESCE(c.avg_daily_issue_14d, c.avg_daily_issue_7d, c.avg_daily_issue_30d, 0) > 0 
        THEN DATEADD(
            day, 
            FLOOR(l.closing_stock / COALESCE(c.avg_daily_issue_14d, c.avg_daily_issue_7d, c.avg_daily_issue_30d)),
            CURRENT_DATE()
        )
        ELSE NULL
    END AS projected_stockout_date,
    
    -- Days until stock-out
    CASE 
        WHEN COALESCE(c.avg_daily_issue_14d, c.avg_daily_issue_7d, c.avg_daily_issue_30d, 0) > 0 
        THEN FLOOR(l.closing_stock / COALESCE(c.avg_daily_issue_14d, c.avg_daily_issue_7d, c.avg_daily_issue_30d))
        ELSE 999
    END AS days_until_stockout,
    
    -- Critical flags
    im.is_critical AS is_critical_item,
    lm.priority_level AS location_priority,
    
    CURRENT_TIMESTAMP() AS calculated_timestamp
    
FROM V_LATEST_STOCK_POSITION l
LEFT JOIN V_CONSUMPTION_METRICS c 
    ON l.location_code = c.location_code AND l.item_code = c.item_code
LEFT JOIN STOCKPULSE_AI.DATA.ITEM_MASTER im 
    ON l.item_code = im.item_code
LEFT JOIN STOCKPULSE_AI.DATA.LOCATION_MASTER lm 
    ON l.location_code = lm.location_code
LEFT JOIN STOCKPULSE_AI.DATA.ITEM_LOCATION_PARAMS ilp 
    ON l.location_code = ilp.location_code AND l.item_code = ilp.item_code;


-- ============================================================================
-- 4. STOCK HEALTH SCORE & CLASSIFICATION VIEW
-- ============================================================================

CREATE OR REPLACE VIEW V_STOCK_HEALTH_CLASSIFICATION AS
SELECT 
    *,
    
    -- Stock Health Score (0-100)
    CASE 
        -- No movement = potential overstock
        WHEN days_since_last_movement > 30 THEN 60
        
        -- Healthy: More than lead time + 50% buffer
        WHEN days_of_cover > (lead_time_days * 1.5) THEN 
            LEAST(100, 80 + ((days_of_cover - (lead_time_days * 1.5)) / lead_time_days * 10))
        
        -- Monitoring: Between lead time and lead time + 50%
        WHEN days_of_cover > lead_time_days THEN 
            50 + ((days_of_cover - lead_time_days) / (lead_time_days * 0.5) * 30)
        
        -- Warning: Between half lead time and lead time
        WHEN days_of_cover > (lead_time_days * 0.5) THEN 
            25 + ((days_of_cover - (lead_time_days * 0.5)) / (lead_time_days * 0.5) * 25)
        
        -- Critical: Less than half lead time
        WHEN days_of_cover > 0 THEN 
            (days_of_cover / (lead_time_days * 0.5)) * 25
        
        -- Out of stock
        ELSE 0
    END AS stock_health_score,
    
    -- Risk Classification
    CASE 
        WHEN closing_stock <= 0 THEN 'OUT_OF_STOCK'
        WHEN days_until_stockout <= 3 THEN 'CRITICAL'
        WHEN days_until_stockout <= lead_time_days THEN 'HIGH_RISK'
        WHEN days_until_stockout <= (lead_time_days * 1.5) THEN 'MEDIUM_RISK'
        WHEN days_since_last_movement > 60 THEN 'OVERSTOCK'
        WHEN days_since_last_movement > 30 THEN 'SLOW_MOVING'
        ELSE 'HEALTHY'
    END AS risk_classification,
    
    -- Color code for heatmap
    CASE 
        WHEN closing_stock <= 0 THEN 'BLACK'
        WHEN days_until_stockout <= 3 THEN 'DARK_RED'
        WHEN days_until_stockout <= lead_time_days THEN 'RED'
        WHEN days_until_stockout <= (lead_time_days * 1.5) THEN 'ORANGE'
        WHEN days_since_last_movement > 60 THEN 'PURPLE'
        WHEN days_since_last_movement > 30 THEN 'YELLOW'
        ELSE 'GREEN'
    END AS risk_color,
    
    -- Requires immediate attention
    CASE 
        WHEN closing_stock <= 0 OR days_until_stockout <= lead_time_days THEN TRUE
        ELSE FALSE
    END AS requires_attention,
    
    -- Overstock flag
    CASE 
        WHEN days_since_last_movement > 30 AND closing_stock > avg_daily_issue * 60 THEN TRUE
        ELSE FALSE
    END AS is_overstock

FROM V_STOCK_HEALTH_METRICS;


-- ============================================================================
-- 5. REORDER RECOMMENDATIONS VIEW
-- ============================================================================

CREATE OR REPLACE VIEW V_REORDER_RECOMMENDATIONS AS
SELECT 
    shc.location_code,
    shc.location_name,
    shc.item_code,
    shc.item_name,
    shc.item_category,
    shc.closing_stock AS current_stock,
    shc.avg_daily_issue,
    shc.lead_time_days,
    shc.safety_stock,
    shc.days_of_cover,
    shc.days_until_stockout,
    shc.projected_stockout_date,
    shc.risk_classification,
    shc.stock_health_score,
    
    -- Reorder calculation
    CASE 
        WHEN shc.avg_daily_issue > 0 THEN
            GREATEST(0, 
                ROUND(
                    (shc.avg_daily_issue * shc.lead_time_days * 1.2)  -- Lead time demand + 20% buffer
                    + shc.safety_stock                             -- Safety stock
                    - shc.closing_stock,                           -- Minus current stock
                    2
                )
            )
        ELSE 0
    END AS suggested_reorder_quantity,
    
    -- Order value (if unit cost is available)
    CASE 
        WHEN shc.avg_daily_issue > 0 THEN
            GREATEST(0, 
                (shc.avg_daily_issue * shc.lead_time_days * 1.2 + shc.safety_stock - shc.closing_stock)
            ) * COALESCE(im.unit_cost, 0)
        ELSE 0
    END AS estimated_order_value,
    
    -- Urgency score (0-100)
    CASE 
        WHEN shc.closing_stock <= 0 THEN 100
        WHEN shc.days_until_stockout = 0 THEN 100
        WHEN shc.days_until_stockout <= 3 THEN 95
        WHEN shc.days_until_stockout <= shc.lead_time_days THEN 
            100 - ((shc.days_until_stockout / shc.lead_time_days) * 30)
        WHEN shc.days_until_stockout <= (shc.lead_time_days * 1.5) THEN 
            70 - (((shc.days_until_stockout - shc.lead_time_days) / (shc.lead_time_days * 0.5)) * 20)
        ELSE 50
    END AS urgency_score,
    
    -- Procurement priority score (combines urgency and criticality)
    (
        CASE 
            WHEN shc.closing_stock <= 0 THEN 100
            WHEN shc.days_until_stockout <= shc.lead_time_days THEN 
                100 - ((shc.days_until_stockout / shc.lead_time_days) * 30)
            ELSE 50
        END
        * CASE WHEN shc.is_critical_item THEN 1.5 ELSE 1.0 END
        * CASE shc.location_priority 
            WHEN 'HIGH' THEN 1.3 
            WHEN 'MEDIUM' THEN 1.0 
            WHEN 'LOW' THEN 0.8 
            ELSE 1.0 
          END
    ) AS procurement_priority_score,
    
    -- Recommended action date
    CASE 
        WHEN shc.days_until_stockout <= shc.lead_time_days THEN CURRENT_DATE()
        ELSE DATEADD(day, -(shc.lead_time_days), shc.projected_stockout_date)
    END AS recommended_action_date,
    
    -- Supplier information
    im.supplier_name,
    im.supplier_code,
    
    shc.is_critical_item,
    shc.location_priority,
    shc.unit_of_measure,
    shc.latest_date AS data_as_of_date

FROM V_STOCK_HEALTH_CLASSIFICATION shc
LEFT JOIN STOCKPULSE_AI.DATA.ITEM_MASTER im 
    ON shc.item_code = im.item_code

WHERE 
    -- Only include items requiring reorder
    shc.days_until_stockout <= (shc.lead_time_days * 1.5)
    OR shc.closing_stock <= COALESCE(shc.reorder_point, 0)
    OR shc.risk_classification IN ('CRITICAL', 'HIGH_RISK', 'OUT_OF_STOCK');



-- ============================================================================
-- 6. LOCATION RISK SUMMARY VIEW
-- ============================================================================

CREATE OR REPLACE VIEW V_LOCATION_RISK_SUMMARY AS
SELECT 
    location_code,
    location_name,
    location_priority,
    
    -- Stock counts by risk level
    COUNT(*) AS total_items,
    SUM(CASE WHEN risk_classification = 'OUT_OF_STOCK' THEN 1 ELSE 0 END) AS out_of_stock_count,
    SUM(CASE WHEN risk_classification = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN risk_classification = 'HIGH_RISK' THEN 1 ELSE 0 END) AS high_risk_count,
    SUM(CASE WHEN risk_classification = 'MEDIUM_RISK' THEN 1 ELSE 0 END) AS medium_risk_count,
    SUM(CASE WHEN risk_classification = 'HEALTHY' THEN 1 ELSE 0 END) AS healthy_count,
    SUM(CASE WHEN risk_classification IN ('OVERSTOCK', 'SLOW_MOVING') THEN 1 ELSE 0 END) AS overstock_count,
    
    -- Average metrics
    ROUND(AVG(stock_health_score), 2) AS avg_stock_health_score,
    ROUND(AVG(days_of_cover), 2) AS avg_days_of_cover,
    
    -- Location risk score (weighted average)
    ROUND(
        (
            SUM(CASE WHEN risk_classification = 'OUT_OF_STOCK' THEN 100 ELSE 0 END) +
            SUM(CASE WHEN risk_classification = 'CRITICAL' THEN 90 ELSE 0 END) +
            SUM(CASE WHEN risk_classification = 'HIGH_RISK' THEN 70 ELSE 0 END) +
            SUM(CASE WHEN risk_classification = 'MEDIUM_RISK' THEN 40 ELSE 0 END) +
            SUM(CASE WHEN risk_classification = 'HEALTHY' THEN 0 ELSE 0 END)
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS location_risk_score,
    
    -- Classification
    CASE 
        WHEN SUM(CASE WHEN risk_classification = 'OUT_OF_STOCK' THEN 1 ELSE 0 END) > 0 THEN 'CRITICAL'
        WHEN SUM(CASE WHEN risk_classification IN ('CRITICAL', 'HIGH_RISK') THEN 1 ELSE 0 END) > (COUNT(*) * 0.3) THEN 'HIGH_RISK'
        WHEN SUM(CASE WHEN risk_classification IN ('CRITICAL', 'HIGH_RISK', 'MEDIUM_RISK') THEN 1 ELSE 0 END) > (COUNT(*) * 0.5) THEN 'MEDIUM_RISK'
        ELSE 'HEALTHY'
    END AS location_risk_classification,
    
    MAX(latest_date) AS data_as_of_date

FROM V_STOCK_HEALTH_CLASSIFICATION
GROUP BY location_code, location_name, location_priority;


-- ============================================================================
-- 7. ITEM RISK SUMMARY VIEW
-- ============================================================================

CREATE OR REPLACE VIEW V_ITEM_RISK_SUMMARY AS
SELECT 
    item_code,
    item_name,
    item_category,
    is_critical_item,
    
    -- Location counts by risk level
    COUNT(*) AS total_locations,
    SUM(CASE WHEN risk_classification = 'OUT_OF_STOCK' THEN 1 ELSE 0 END) AS out_of_stock_locations,
    SUM(CASE WHEN risk_classification IN ('CRITICAL', 'HIGH_RISK') THEN 1 ELSE 0 END) AS at_risk_locations,
    SUM(CASE WHEN risk_classification = 'HEALTHY' THEN 1 ELSE 0 END) AS healthy_locations,
    
    -- Total stock across all locations
    SUM(closing_stock) AS total_stock_all_locations,
    SUM(avg_daily_issue) AS total_daily_consumption,
    
    -- Average metrics
    ROUND(AVG(stock_health_score), 2) AS avg_stock_health_score,
    ROUND(AVG(days_of_cover), 2) AS avg_days_of_cover,
    
    -- Item-level risk score
    ROUND(
        (
            SUM(CASE WHEN risk_classification = 'OUT_OF_STOCK' THEN 100 ELSE 0 END) +
            SUM(CASE WHEN risk_classification = 'CRITICAL' THEN 90 ELSE 0 END) +
            SUM(CASE WHEN risk_classification = 'HIGH_RISK' THEN 70 ELSE 0 END) +
            SUM(CASE WHEN risk_classification = 'MEDIUM_RISK' THEN 40 ELSE 0 END)
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS item_risk_score,
    
    MAX(latest_date) AS data_as_of_date

FROM V_STOCK_HEALTH_CLASSIFICATION
GROUP BY item_code, item_name, item_category, is_critical_item;


-- ============================================================================
-- 8. EXECUTIVE SUMMARY VIEW
-- ============================================================================

CREATE OR REPLACE VIEW V_EXECUTIVE_SUMMARY AS
SELECT 
    -- Overall counts
    COUNT(DISTINCT location_code) AS total_locations,
    COUNT(DISTINCT item_code) AS total_items,
    COUNT(*) AS total_location_item_combinations,
    
    -- Stock status distribution
    SUM(CASE WHEN risk_classification = 'OUT_OF_STOCK' THEN 1 ELSE 0 END) AS out_of_stock_count,
    SUM(CASE WHEN risk_classification = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN risk_classification = 'HIGH_RISK' THEN 1 ELSE 0 END) AS high_risk_count,
    SUM(CASE WHEN risk_classification = 'MEDIUM_RISK' THEN 1 ELSE 0 END) AS medium_risk_count,
    SUM(CASE WHEN risk_classification = 'HEALTHY' THEN 1 ELSE 0 END) AS healthy_count,
    SUM(CASE WHEN risk_classification IN ('OVERSTOCK', 'SLOW_MOVING') THEN 1 ELSE 0 END) AS overstock_count,
    
    -- Percentages
    ROUND(SUM(CASE WHEN risk_classification IN ('OUT_OF_STOCK', 'CRITICAL', 'HIGH_RISK') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS pct_requiring_attention,
    ROUND(SUM(CASE WHEN risk_classification = 'HEALTHY' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS pct_healthy,
    
    -- Average metrics
    ROUND(AVG(stock_health_score), 2) AS avg_stock_health_score,
    ROUND(AVG(days_of_cover), 2) AS avg_days_of_cover,
    
    -- Critical items
    SUM(CASE WHEN is_critical_item AND risk_classification IN ('OUT_OF_STOCK', 'CRITICAL') THEN 1 ELSE 0 END) AS critical_items_at_risk,
    
    -- Reorder recommendations
    (SELECT COUNT(*) FROM V_REORDER_RECOMMENDATIONS) AS total_reorder_recommendations,
    (SELECT SUM(estimated_order_value) FROM V_REORDER_RECOMMENDATIONS) AS total_estimated_order_value,
    
    MAX(latest_date) AS data_as_of_date,
    CURRENT_TIMESTAMP() AS report_generated_timestamp

FROM V_STOCK_HEALTH_CLASSIFICATION;


-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

GRANT SELECT ON ALL VIEWS IN SCHEMA STOCKPULSE_AI.ANALYTICS TO ROLE STOCKPULSE_USER;
GRANT SELECT ON ALL VIEWS IN SCHEMA STOCKPULSE_AI.ANALYTICS TO ROLE STOCKPULSE_READONLY;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Show all created views
SHOW VIEWS IN SCHEMA STOCKPULSE_AI.ANALYTICS;

-- Test executive summary (will be empty until data is loaded)
SELECT * FROM V_EXECUTIVE_SUMMARY;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. These views provide the analytical foundation for the dashboard
-- 2. All calculations use simple, transparent SQL logic (no black boxes)
-- 3. Prioritizes 14-day consumption average with fallbacks to 7-day and 30-day
-- 4. Stock health score is normalized 0-100 for easy comparison
-- 5. Dynamic Tables (next script) will materialize these for performance
-- ============================================================================

