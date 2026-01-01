-- ============================================================================
-- StockPulse AI - Table Definitions
-- ============================================================================
-- Description: Creates all raw data tables and reference/lookup tables
-- Usage: Run this script after 01_setup_schema.sql
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE STOCKPULSE_AI;
USE SCHEMA DATA;
USE WAREHOUSE STOCKPULSE_WH;

-- ============================================================================
-- 1. RAW DAILY STOCK DATA TABLE
-- ============================================================================

CREATE OR REPLACE TABLE DAILY_STOCK_RAW (
    stock_record_id NUMBER AUTOINCREMENT PRIMARY KEY,
    record_date DATE NOT NULL,
    location_code VARCHAR(50) NOT NULL,
    location_name VARCHAR(200),
    item_code VARCHAR(50) NOT NULL,
    item_name VARCHAR(200),
    item_category VARCHAR(100),
    opening_stock NUMBER(18,2) DEFAULT 0,
    receipts NUMBER(18,2) DEFAULT 0,
    issues NUMBER(18,2) DEFAULT 0,
    closing_stock NUMBER(18,2) DEFAULT 0,
    unit_of_measure VARCHAR(20) DEFAULT 'UNITS',
    lead_time_days NUMBER(5,0) DEFAULT 7,
    data_source VARCHAR(100),
    created_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    modified_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Raw daily stock transaction data - primary data source for all analytics';

-- ============================================================================
-- 2. LOCATION MASTER TABLE
-- ============================================================================

CREATE OR REPLACE TABLE LOCATION_MASTER (
    location_id NUMBER AUTOINCREMENT PRIMARY KEY,
    location_code VARCHAR(50) UNIQUE NOT NULL,
    location_name VARCHAR(200) NOT NULL,
    location_type VARCHAR(50), -- 'HOSPITAL', 'WAREHOUSE', 'DISTRIBUTION_CENTER', 'NGO_CENTER'
    region VARCHAR(100),
    district VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    address TEXT,
    contact_person VARCHAR(200),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    priority_level VARCHAR(20) DEFAULT 'MEDIUM', -- 'HIGH', 'MEDIUM', 'LOW'
    capacity_rating NUMBER(5,0), -- Optional: storage capacity indicator
    created_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    modified_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Master data for all locations (hospitals, warehouses, distribution centers)';

-- ============================================================================
-- 3. ITEM MASTER TABLE
-- ============================================================================

CREATE OR REPLACE TABLE ITEM_MASTER (
    item_id NUMBER AUTOINCREMENT PRIMARY KEY,
    item_code VARCHAR(50) UNIQUE NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    item_category VARCHAR(100), -- 'MEDICINE', 'FOOD', 'MEDICAL_SUPPLY', 'PPE', etc.
    item_subcategory VARCHAR(100),
    unit_of_measure VARCHAR(20) DEFAULT 'UNITS',
    standard_pack_size NUMBER(10,2),
    unit_cost NUMBER(18,2),
    is_critical BOOLEAN DEFAULT FALSE, -- Flag for essential/life-saving items
    is_controlled BOOLEAN DEFAULT FALSE, -- Flag for controlled substances
    storage_requirements VARCHAR(200), -- 'REFRIGERATED', 'ROOM_TEMPERATURE', etc.
    shelf_life_days NUMBER(5,0), -- For expiry tracking
    reorder_point NUMBER(18,2), -- Standard reorder threshold
    safety_stock NUMBER(18,2), -- Minimum buffer stock
    default_lead_time_days NUMBER(5,0) DEFAULT 7,
    supplier_name VARCHAR(200),
    supplier_code VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    modified_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Master data for all items (medicines, food, supplies)';

-- ============================================================================
-- 4. SUPPLIER MASTER TABLE
-- ============================================================================

CREATE OR REPLACE TABLE SUPPLIER_MASTER (
    supplier_id NUMBER AUTOINCREMENT PRIMARY KEY,
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    supplier_type VARCHAR(50), -- 'PHARMACEUTICAL', 'FOOD', 'EQUIPMENT', etc.
    contact_person VARCHAR(200),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    average_lead_time_days NUMBER(5,0) DEFAULT 7,
    reliability_rating NUMBER(3,1), -- 1.0 to 5.0 scale
    is_active BOOLEAN DEFAULT TRUE,
    payment_terms VARCHAR(100),
    created_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    modified_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Master data for suppliers and vendors';

-- ============================================================================
-- 5. ITEM-LOCATION SPECIFIC PARAMETERS TABLE
-- ============================================================================

CREATE OR REPLACE TABLE ITEM_LOCATION_PARAMS (
    param_id NUMBER AUTOINCREMENT PRIMARY KEY,
    location_code VARCHAR(50) NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    custom_lead_time_days NUMBER(5,0), -- Override default lead time
    custom_reorder_point NUMBER(18,2), -- Location-specific reorder point
    custom_safety_stock NUMBER(18,2), -- Location-specific safety buffer
    max_stock_level NUMBER(18,2), -- Maximum stock to avoid overstock
    min_order_quantity NUMBER(18,2),
    is_stocked BOOLEAN DEFAULT TRUE, -- Whether location stocks this item
    last_order_date DATE,
    notes TEXT,
    created_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    modified_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT uk_item_location UNIQUE (location_code, item_code)
)
COMMENT = 'Location-specific parameters for items (overrides default settings)';

-- ============================================================================
-- 6. STOCK ALERTS CONFIGURATION TABLE
-- ============================================================================

CREATE OR REPLACE TABLE ALERT_CONFIG (
    alert_config_id NUMBER AUTOINCREMENT PRIMARY KEY,
    alert_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- 'STOCK_OUT', 'LOW_STOCK', 'OVERSTOCK', 'EXPIRY_WARNING'
    threshold_days NUMBER(5,0), -- Days before action needed
    severity VARCHAR(20) DEFAULT 'MEDIUM', -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    notification_email VARCHAR(500), -- Comma-separated email list
    is_active BOOLEAN DEFAULT TRUE,
    location_filter VARCHAR(500), -- NULL = all locations
    item_category_filter VARCHAR(500), -- NULL = all categories
    created_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    modified_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Configuration for automated alerts and notifications';

-- ============================================================================
-- 7. AUDIT LOG TABLE
-- ============================================================================

CREATE OR REPLACE TABLE AUDIT_LOG (
    audit_id NUMBER AUTOINCREMENT PRIMARY KEY,
    event_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    event_type VARCHAR(50), -- 'DATA_LOAD', 'EXPORT', 'ALERT_SENT', 'USER_ACTION'
    event_description TEXT,
    user_name VARCHAR(100),
    location_code VARCHAR(50),
    item_code VARCHAR(50),
    old_value VARIANT,
    new_value VARIANT,
    ip_address VARCHAR(50),
    session_id VARCHAR(100)
)
COMMENT = 'Audit trail for all system actions and data changes';

-- ============================================================================
-- 8. PROCUREMENT ACTIONS TABLE (Optional Unistore Integration)
-- ============================================================================

CREATE OR REPLACE TABLE PROCUREMENT_ACTIONS (
    action_id NUMBER AUTOINCREMENT PRIMARY KEY,
    action_date DATE NOT NULL,
    location_code VARCHAR(50) NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    action_type VARCHAR(50), -- 'REORDER_CREATED', 'ORDER_PLACED', 'ORDER_RECEIVED', 'ALERT_ACKNOWLEDGED'
    recommended_quantity NUMBER(18,2),
    actual_quantity NUMBER(18,2),
    order_reference VARCHAR(100),
    supplier_code VARCHAR(50),
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    status VARCHAR(50), -- 'PENDING', 'APPROVED', 'ORDERED', 'RECEIVED', 'CANCELLED'
    notes TEXT,
    created_by VARCHAR(100),
    created_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    modified_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Tracks procurement actions and order lifecycle';

-- ============================================================================
-- 9. REFERENCE DATA - ITEM CATEGORIES
-- ============================================================================

CREATE OR REPLACE TABLE REF_ITEM_CATEGORIES (
    category_id NUMBER AUTOINCREMENT PRIMARY KEY,
    category_code VARCHAR(50) UNIQUE NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    parent_category VARCHAR(50),
    display_order NUMBER(5,0),
    icon_name VARCHAR(50),
    color_code VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE
)
COMMENT = 'Reference data for item categories and subcategories';

-- Insert sample categories
INSERT INTO REF_ITEM_CATEGORIES (category_code, category_name, parent_category, display_order, color_code) VALUES
    ('MEDICINE', 'Medicines', NULL, 1, '#FF6B6B'),
    ('MEDICINE_ANTIBIOTIC', 'Antibiotics', 'MEDICINE', 11, '#FF6B6B'),
    ('MEDICINE_ANALGESIC', 'Analgesics', 'MEDICINE', 12, '#FF6B6B'),
    ('MEDICINE_CARDIOVASCULAR', 'Cardiovascular', 'MEDICINE', 13, '#FF6B6B'),
    ('FOOD', 'Food Items', NULL, 2, '#4ECDC4'),
    ('FOOD_GRAIN', 'Grains', 'FOOD', 21, '#4ECDC4'),
    ('FOOD_DAIRY', 'Dairy Products', 'FOOD', 22, '#4ECDC4'),
    ('FOOD_PROTEIN', 'Proteins', 'FOOD', 23, '#4ECDC4'),
    ('MEDICAL_SUPPLY', 'Medical Supplies', NULL, 3, '#95E1D3'),
    ('MEDICAL_SUPPLY_CONSUMABLE', 'Consumables', 'MEDICAL_SUPPLY', 31, '#95E1D3'),
    ('PPE', 'Personal Protective Equipment', NULL, 4, '#F38181'),
    ('EQUIPMENT', 'Medical Equipment', NULL, 5, '#AA96DA');

-- ============================================================================
-- 10. DATA QUALITY RULES TABLE
-- ============================================================================

CREATE OR REPLACE TABLE DATA_QUALITY_RULES (
    rule_id NUMBER AUTOINCREMENT PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50), -- 'MISSING_DATA', 'NEGATIVE_STOCK', 'ANOMALY', 'DUPLICATE'
    rule_sql TEXT, -- SQL to detect violations
    severity VARCHAR(20) DEFAULT 'MEDIUM',
    is_active BOOLEAN DEFAULT TRUE,
    created_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Data quality validation rules';

-- Insert common quality rules
INSERT INTO DATA_QUALITY_RULES (rule_name, rule_type, rule_sql, severity) VALUES
    ('Negative Closing Stock', 'NEGATIVE_STOCK', 
     'SELECT * FROM DAILY_STOCK_RAW WHERE closing_stock < 0', 'HIGH'),
    ('Missing Location Name', 'MISSING_DATA', 
     'SELECT * FROM DAILY_STOCK_RAW WHERE location_name IS NULL OR location_name = ''''', 'MEDIUM'),
    ('Missing Item Name', 'MISSING_DATA', 
     'SELECT * FROM DAILY_STOCK_RAW WHERE item_name IS NULL OR item_name = ''''', 'MEDIUM'),
    ('Stock Mismatch', 'ANOMALY', 
     'SELECT * FROM DAILY_STOCK_RAW WHERE opening_stock + receipts - issues != closing_stock', 'HIGH'),
    ('Future Date', 'ANOMALY', 
     'SELECT * FROM DAILY_STOCK_RAW WHERE record_date > CURRENT_DATE()', 'CRITICAL');

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Show all created tables
SHOW TABLES IN SCHEMA STOCKPULSE_AI.DATA;

-- Display table summary
SELECT 
    table_schema,
    table_name,
    row_count,
    bytes,
    comment
FROM STOCKPULSE_AI.INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'DATA'
ORDER BY table_name;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. The DAILY_STOCK_RAW table is the primary data source - ensure daily loads
-- 2. Master tables should be populated with your organization's reference data
-- 3. ITEM_LOCATION_PARAMS allows customization per location-item combination
-- 4. PROCUREMENT_ACTIONS enables closed-loop tracking (optional Unistore feature)
-- 5. Adjust data types and sizes based on your specific requirements
-- 6. Consider partitioning DAILY_STOCK_RAW by date for large datasets
-- ============================================================================
