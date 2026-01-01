-- ============================================================================
-- StockPulse AI - Streams and Tasks for Real-Time Monitoring
-- ============================================================================
-- Description: Creates Streams for change detection and Tasks for automated
--              alerts and scheduled calculations
-- Usage: Run this script after 04_dynamic_tables.sql
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE STOCKPULSE_AI;
USE SCHEMA MONITORING;
USE WAREHOUSE STOCKPULSE_TASK_WH;

-- ============================================================================
-- 1. STREAM: Monitor New/Changed Stock Data
-- ============================================================================

CREATE OR REPLACE STREAM STR_DAILY_STOCK_CHANGES
    ON TABLE STOCKPULSE_AI.DATA.DAILY_STOCK_RAW
    COMMENT = 'Tracks inserts and updates to daily stock data for real-time processing';

-- ============================================================================
-- 2. TABLE: Alert Notifications
-- ============================================================================

CREATE OR REPLACE TABLE ALERT_NOTIFICATIONS (
    alert_id NUMBER AUTOINCREMENT PRIMARY KEY,
    alert_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    alert_type VARCHAR(50), -- 'STOCK_OUT', 'CRITICAL', 'HIGH_RISK', 'OVERSTOCK'
    severity VARCHAR(20), -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    location_code VARCHAR(50),
    location_name VARCHAR(200),
    item_code VARCHAR(50),
    item_name VARCHAR(200),
    item_category VARCHAR(100),
    current_stock NUMBER(18,2),
    days_until_stockout NUMBER(10,0),
    recommended_action VARCHAR(500),
    alert_message TEXT,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_timestamp TIMESTAMP_NTZ,
    action_taken TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_timestamp TIMESTAMP_NTZ
)
COMMENT = 'Central repository for all generated alerts and notifications';

-- ============================================================================
-- 3. TABLE: Alert History (for trend analysis)
-- ============================================================================

CREATE OR REPLACE TABLE ALERT_HISTORY (
    history_id NUMBER AUTOINCREMENT PRIMARY KEY,
    alert_date DATE,
    location_code VARCHAR(50),
    item_code VARCHAR(50),
    alert_type VARCHAR(50),
    severity VARCHAR(20),
    stock_health_score NUMBER(5,2),
    days_of_cover NUMBER(10,2),
    created_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Historical record of alerts for trending and analysis';

-- ============================================================================
-- 4. SIMPLIFIED ALERT GENERATION
-- ============================================================================

-- Stock Alerts View (no stored procedure needed)
CREATE OR REPLACE VIEW STOCK_ALERTS AS
SELECT 
    ROW_NUMBER() OVER (ORDER BY 
        CASE 
            WHEN risk_classification = 'OUT_OF_STOCK' THEN 1
            WHEN risk_classification = 'CRITICAL' THEN 2
            WHEN risk_classification = 'HIGH_RISK' THEN 3
            ELSE 4
        END, days_until_stockout) AS alert_id,
    
    CURRENT_TIMESTAMP() AS alert_timestamp,
    
    CASE 
        WHEN risk_classification = 'OUT_OF_STOCK' THEN 'STOCK_OUT'
        WHEN risk_classification = 'CRITICAL' THEN 'CRITICAL_LOW'
        WHEN risk_classification = 'HIGH_RISK' THEN 'HIGH_RISK'
        WHEN risk_classification = 'OVERSTOCK' THEN 'OVERSTOCK'
        ELSE 'LOW_STOCK'
    END AS alert_type,
    
    CASE 
        WHEN risk_classification = 'OUT_OF_STOCK' THEN 'CRITICAL'
        WHEN risk_classification = 'CRITICAL' OR is_critical_item THEN 'CRITICAL'
        WHEN risk_classification = 'HIGH_RISK' THEN 'HIGH'
        WHEN risk_classification = 'MEDIUM_RISK' THEN 'MEDIUM'
        ELSE 'LOW'
    END AS severity,
    
    location_code,
    location_name,
    item_code,
    item_name,
    item_category,
    closing_stock AS current_stock,
    days_until_stockout,
    
    CASE 
        WHEN risk_classification = 'OUT_OF_STOCK' THEN 
            'URGENT: Place emergency order immediately'
        WHEN days_until_stockout <= lead_time_days THEN 
            'Place order today - stock-out expected in ' || days_until_stockout || ' days'
        WHEN risk_classification = 'OVERSTOCK' THEN 
            'Review for redistribution or reduced ordering'
        ELSE 
            'Monitor stock levels and plan replenishment'
    END AS recommended_action,
    
    CASE 
        WHEN risk_classification = 'OUT_OF_STOCK' THEN 
            item_name || ' is OUT OF STOCK at ' || location_name || '. Immediate action required.'
        WHEN risk_classification = 'CRITICAL' THEN 
            item_name || ' at ' || location_name || ' will run out in ' || days_until_stockout || ' days. Current stock: ' || closing_stock || ' ' || unit_of_measure
        WHEN risk_classification = 'HIGH_RISK' THEN 
            item_name || ' at ' || location_name || ' requires reorder. ' || days_until_stockout || ' days of supply remaining.'
        WHEN risk_classification = 'OVERSTOCK' THEN 
            item_name || ' at ' || location_name || ' has not moved in ' || days_since_last_movement || ' days. Consider redistribution.'
        ELSE 
            item_name || ' at ' || location_name || ' approaching reorder point.'
    END AS alert_message
    
FROM STOCKPULSE_AI.ANALYTICS.DT_STOCK_HEALTH_CLASSIFICATION

WHERE 
    -- Only alert on actionable items
    risk_classification IN ('OUT_OF_STOCK', 'CRITICAL', 'HIGH_RISK')
    OR (risk_classification = 'OVERSTOCK' AND closing_stock > avg_daily_issue * 90);

-- ============================================================================
-- 5. GRANT PERMISSIONS
-- ============================================================================

GRANT SELECT ON VIEW STOCK_ALERTS TO ROLE STOCKPULSE_USER;
GRANT SELECT ON VIEW STOCK_ALERTS TO ROLE STOCKPULSE_READONLY;
GRANT SELECT ON ALL TABLES IN SCHEMA STOCKPULSE_AI.MONITORING TO ROLE STOCKPULSE_USER;
GRANT SELECT ON ALL VIEWS IN SCHEMA STOCKPULSE_AI.MONITORING TO ROLE STOCKPULSE_USER;
GRANT SELECT ON ALL TABLES IN SCHEMA STOCKPULSE_AI.MONITORING TO ROLE STOCKPULSE_READONLY;
GRANT SELECT ON ALL VIEWS IN SCHEMA STOCKPULSE_AI.MONITORING TO ROLE STOCKPULSE_READONLY;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. Streams track changes to source tables for incremental processing
-- 2. STOCK_ALERTS view provides real-time alerts from Dynamic Tables
-- 3. Alert history tables available for tracking and trending
-- 4. To add automated tasks, create them separately based on business needs
-- ============================================================================
