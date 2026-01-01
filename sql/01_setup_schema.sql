-- ============================================================================
-- StockPulse AI - Database and Schema Setup
-- ============================================================================
-- Description: Creates the database, schemas, warehouses, and stages needed
--              for the StockPulse AI application
-- Usage: Run this script first as ACCOUNTADMIN or similar role
-- ============================================================================

-- Set context
USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- 1. CREATE DATABASE
-- ============================================================================

CREATE DATABASE IF NOT EXISTS STOCKPULSE_AI
    COMMENT = 'StockPulse AI - Inventory Intelligence for Critical Supply Chains';

-- ============================================================================
-- 2. CREATE SCHEMAS
-- ============================================================================

-- Schema for raw and processed data
CREATE SCHEMA IF NOT EXISTS STOCKPULSE_AI.DATA
    COMMENT = 'Raw daily stock data and reference tables';

-- Schema for calculated metrics and analytics
CREATE SCHEMA IF NOT EXISTS STOCKPULSE_AI.ANALYTICS
    COMMENT = 'Stock health metrics, dynamic tables, and analytical views';

-- Schema for application layer (Streamlit, procedures, functions)
CREATE SCHEMA IF NOT EXISTS STOCKPULSE_AI.APP
    COMMENT = 'Application layer components - Streamlit, UDFs, procedures';

-- Schema for monitoring and alerts
CREATE SCHEMA IF NOT EXISTS STOCKPULSE_AI.MONITORING
    COMMENT = 'Streams, tasks, and alert definitions';

-- ============================================================================
-- 3. CREATE COMPUTE WAREHOUSES
-- ============================================================================

-- Primary warehouse for data processing and analytics
CREATE WAREHOUSE IF NOT EXISTS STOCKPULSE_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Main compute warehouse for StockPulse AI';

-- Warehouse for Streamlit application (can be shared or dedicated)
CREATE WAREHOUSE IF NOT EXISTS STOCKPULSE_APP_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for Streamlit dashboard queries';

-- Warehouse for background tasks and scheduled jobs
CREATE WAREHOUSE IF NOT EXISTS STOCKPULSE_TASK_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for scheduled tasks and alerts';

-- ============================================================================
-- 4. CREATE FILE FORMATS
-- ============================================================================

CREATE OR REPLACE FILE FORMAT STOCKPULSE_AI.DATA.CSV_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    NULL_IF = ('NULL', 'null', '', 'N/A', 'NA')
    COMMENT = 'Standard CSV format for data ingestion';

CREATE OR REPLACE FILE FORMAT STOCKPULSE_AI.DATA.JSON_FORMAT
    TYPE = 'JSON'
    STRIP_OUTER_ARRAY = TRUE
    COMMENT = 'JSON format for configuration and metadata';

-- ============================================================================
-- 5. CREATE INTERNAL STAGES
-- ============================================================================

-- Stage for data ingestion
CREATE STAGE IF NOT EXISTS STOCKPULSE_AI.DATA.STOCK_DATA_STAGE
    FILE_FORMAT = STOCKPULSE_AI.DATA.CSV_FORMAT
    COMMENT = 'Stage for loading daily stock data files';

-- Stage for Streamlit application files
CREATE STAGE IF NOT EXISTS STOCKPULSE_AI.APP.STREAMLIT_STAGE
    COMMENT = 'Stage for Streamlit application code and dependencies';

-- Stage for exports
CREATE STAGE IF NOT EXISTS STOCKPULSE_AI.DATA.EXPORT_STAGE
    COMMENT = 'Stage for exporting procurement recommendations and reports';

-- ============================================================================
-- 6. CREATE ROLES AND GRANT PRIVILEGES
-- ============================================================================

-- Create application role
CREATE ROLE IF NOT EXISTS STOCKPULSE_ADMIN
    COMMENT = 'Administrator role for StockPulse AI application';

CREATE ROLE IF NOT EXISTS STOCKPULSE_USER
    COMMENT = 'Standard user role for StockPulse AI dashboard access';

CREATE ROLE IF NOT EXISTS STOCKPULSE_READONLY
    COMMENT = 'Read-only role for viewing reports and dashboards';

-- Grant database and schema usage
GRANT USAGE ON DATABASE STOCKPULSE_AI TO ROLE STOCKPULSE_ADMIN;
GRANT USAGE ON ALL SCHEMAS IN DATABASE STOCKPULSE_AI TO ROLE STOCKPULSE_ADMIN;
GRANT USAGE ON FUTURE SCHEMAS IN DATABASE STOCKPULSE_AI TO ROLE STOCKPULSE_ADMIN;

-- Grant warehouse usage
GRANT USAGE ON WAREHOUSE STOCKPULSE_WH TO ROLE STOCKPULSE_ADMIN;
GRANT USAGE ON WAREHOUSE STOCKPULSE_APP_WH TO ROLE STOCKPULSE_ADMIN;
GRANT USAGE ON WAREHOUSE STOCKPULSE_TASK_WH TO ROLE STOCKPULSE_ADMIN;

-- Grant comprehensive privileges to admin role
GRANT ALL ON ALL TABLES IN SCHEMA STOCKPULSE_AI.DATA TO ROLE STOCKPULSE_ADMIN;
GRANT ALL ON ALL TABLES IN SCHEMA STOCKPULSE_AI.ANALYTICS TO ROLE STOCKPULSE_ADMIN;
GRANT ALL ON ALL TABLES IN SCHEMA STOCKPULSE_AI.APP TO ROLE STOCKPULSE_ADMIN;
GRANT ALL ON ALL TABLES IN SCHEMA STOCKPULSE_AI.MONITORING TO ROLE STOCKPULSE_ADMIN;

GRANT ALL ON FUTURE TABLES IN SCHEMA STOCKPULSE_AI.DATA TO ROLE STOCKPULSE_ADMIN;
GRANT ALL ON FUTURE TABLES IN SCHEMA STOCKPULSE_AI.ANALYTICS TO ROLE STOCKPULSE_ADMIN;
GRANT ALL ON FUTURE TABLES IN SCHEMA STOCKPULSE_AI.APP TO ROLE STOCKPULSE_ADMIN;
GRANT ALL ON FUTURE TABLES IN SCHEMA STOCKPULSE_AI.MONITORING TO ROLE STOCKPULSE_ADMIN;

-- Grant stage access
GRANT READ, WRITE ON STAGE STOCKPULSE_AI.DATA.STOCK_DATA_STAGE TO ROLE STOCKPULSE_ADMIN;
GRANT READ, WRITE ON STAGE STOCKPULSE_AI.APP.STREAMLIT_STAGE TO ROLE STOCKPULSE_ADMIN;
GRANT READ, WRITE ON STAGE STOCKPULSE_AI.DATA.EXPORT_STAGE TO ROLE STOCKPULSE_ADMIN;

-- Grant privileges to user role
GRANT USAGE ON DATABASE STOCKPULSE_AI TO ROLE STOCKPULSE_USER;
GRANT USAGE ON ALL SCHEMAS IN DATABASE STOCKPULSE_AI TO ROLE STOCKPULSE_USER;
GRANT USAGE ON WAREHOUSE STOCKPULSE_APP_WH TO ROLE STOCKPULSE_USER;
GRANT SELECT ON ALL TABLES IN SCHEMA STOCKPULSE_AI.ANALYTICS TO ROLE STOCKPULSE_USER;
GRANT SELECT ON ALL VIEWS IN SCHEMA STOCKPULSE_AI.ANALYTICS TO ROLE STOCKPULSE_USER;
GRANT SELECT ON FUTURE TABLES IN SCHEMA STOCKPULSE_AI.ANALYTICS TO ROLE STOCKPULSE_USER;

-- Grant privileges to readonly role
GRANT USAGE ON DATABASE STOCKPULSE_AI TO ROLE STOCKPULSE_READONLY;
GRANT USAGE ON SCHEMA STOCKPULSE_AI.ANALYTICS TO ROLE STOCKPULSE_READONLY;
GRANT USAGE ON WAREHOUSE STOCKPULSE_APP_WH TO ROLE STOCKPULSE_READONLY;
GRANT SELECT ON ALL TABLES IN SCHEMA STOCKPULSE_AI.ANALYTICS TO ROLE STOCKPULSE_READONLY;
GRANT SELECT ON ALL VIEWS IN SCHEMA STOCKPULSE_AI.ANALYTICS TO ROLE STOCKPULSE_READONLY;

-- Grant roles to SYSADMIN (role hierarchy)
GRANT ROLE STOCKPULSE_ADMIN TO ROLE SYSADMIN;
GRANT ROLE STOCKPULSE_USER TO ROLE STOCKPULSE_ADMIN;
GRANT ROLE STOCKPULSE_READONLY TO ROLE STOCKPULSE_USER;

-- ============================================================================
-- 7. SET DEFAULT CONTEXT
-- ============================================================================

USE ROLE STOCKPULSE_ADMIN;
USE DATABASE STOCKPULSE_AI;
USE SCHEMA DATA;
USE WAREHOUSE STOCKPULSE_WH;

-- ============================================================================
-- 8. VERIFICATION QUERIES
-- ============================================================================

-- Show created objects
SHOW DATABASES LIKE 'STOCKPULSE_AI';
SHOW SCHEMAS IN DATABASE STOCKPULSE_AI;
SHOW WAREHOUSES LIKE 'STOCKPULSE%';
SHOW FILE FORMATS IN SCHEMA STOCKPULSE_AI.DATA;
SHOW STAGES IN DATABASE STOCKPULSE_AI;
SHOW ROLES LIKE 'STOCKPULSE%';

-- Display setup summary
SELECT 
    'Setup Complete' AS status,
    CURRENT_DATABASE() AS current_database,
    CURRENT_SCHEMA() AS current_schema,
    CURRENT_WAREHOUSE() AS current_warehouse,
    CURRENT_ROLE() AS current_role;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. Adjust warehouse sizes based on your data volume and performance needs
-- 2. AUTO_SUSPEND values are optimized for cost efficiency - adjust as needed
-- 3. Grant additional roles to users as needed: GRANT ROLE STOCKPULSE_USER TO USER your_username;
-- 4. For production, consider implementing row-level security for multi-tenant scenarios
-- 5. Ensure your Snowflake account has Streamlit enabled before deploying the app
-- ============================================================================
