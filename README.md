# StockPulse AI

**AI-Powered Stock Health Intelligence for Critical Supply Chains**

StockPulse AI is a Snowflake-native web application that provides hospitals, public distribution systems, and NGOs with real-time visibility into stock health for medicines, food, and other critical essentials. By consolidating fragmented operational data, it enables early risk detection, informed replenishment decisions, and proactive supply chain management.

## 🎯 Problem Statement

Healthcare facilities and distribution systems face operational data fragmentation where:
- Daily usage, inventory balances, and purchase information exist in separate systems
- Stock-outs are detected only after service disruption occurs
- Overstocking leads to waste and expiry of critical supplies
- Manual processes delay response to emerging risks

## 💡 Solution Overview

StockPulse AI consolidates daily stock data into a unified analytical layer that:
- **Detects risks early** through predictive stock-out calculations
- **Prioritizes action** with intelligent reorder recommendations
- **Enables execution** via clean exports for procurement teams
- **Ensures transparency** with auditable, explainable AI logic

## 🏗️ Architecture

### Technology Stack
- **Database & Compute**: Snowflake (tables, dynamic tables, streams, tasks)
- **Processing**: SQL + Snowpark (Python)
- **Presentation**: Streamlit (deployed in Snowflake)
- **Deployment**: 100% Snowflake-native (no external infrastructure)

### Data Flow
```
Raw Daily Stock Data → Snowflake Tables → Dynamic Tables (Auto-refresh)
                                         ↓
                              Stock Health Calculations
                                         ↓
                              Streams (Change Detection)
                                         ↓
                              Tasks (Alerts & Recalculation)
                                         ↓
                              Streamlit Dashboard → Export (CSV/Excel)
```

## 📊 Core Features

### 1. Stock Health Dashboard
- **Location-by-Item Heatmap**: Visual matrix with color-coded risk indicators
  - 🟢 Green: Healthy stock levels (>lead time + safety buffer)
  - 🟡 Yellow: Monitoring required (approaching reorder point)
  - 🔴 Red: Critical risk (stock-out expected within lead time)
- **Drill-down Analysis**: Click any cell to view detailed metrics
- **Real-time Updates**: Auto-refresh powered by Dynamic Tables

### 2. Early Warning System
- **Days-to-Stock-Out Countdown**: Predictive timeline based on consumption trends
- **Lead-Time-Aware Alerts**: Flags items requiring action before stock reaches zero
- **Rolling Metrics**: 7/14/30-day average consumption rates

### 3. Reorder Intelligence
- **Automated Suggestions**: Calculates optimal replenishment quantities
  - Formula: `(Avg Daily Issue × Lead Time) + Safety Stock - Current Stock`
- **Priority Scoring**: Ranks items by urgency and impact
- **Explainable Logic**: All calculations traceable to simple SQL

### 4. Action-Ready Exports
- **Procurement-Ready Files**: CSV/Excel with item, location, risk, quantity, action date
- **Batch Operations**: Export filtered subsets (by location, risk level, item category)
- **Audit Trail**: Timestamps and user actions logged (optional Unistore)

### 5. Advanced Analytics (Optional)
- **Demand Forecasting**: Moving average-based short-term predictions (Snowpark)
- **Overstock Detection**: Flags slow-moving items at risk of expiry
- **Location Risk Rankings**: Identifies facilities with highest overall risk
- **Stock Health Index**: Normalized 0-100 score for quick comparison

## 📁 Project Structure

```
StockPulse AI/
├── sql/
│   ├── 01_setup_schema.sql          # Database and schema creation
│   ├── 02_create_tables.sql         # Raw data tables and reference tables
│   ├── 03_stock_health_metrics.sql  # Core calculation views
│   ├── 04_dynamic_tables.sql        # Auto-refreshing materialized views
│   ├── 05_streams_and_tasks.sql     # Change detection and scheduling
│   └── 06_sample_data.sql           # Test data generation
├── webapp/
│   ├── src/                         # React components and pages
│   ├── server/                      # Express.js API server
│   ├── package.json                 # Node.js dependencies
│   └── README.md                    # Web app documentation
├── config/
│   └── snowflake_config.json        # Connection parameters (template)
├── docs/
│   ├── DEPLOYMENT_GUIDE.md          # Step-by-step setup instructions
│   ├── USER_GUIDE.md                # Dashboard usage documentation
│   └── TECHNICAL_SPECS.md           # Detailed technical documentation
├── tests/
│   ├── test_calculations.sql        # SQL unit tests
│   └── validate_data.py             # Data quality checks
└── README.md                        # This file
```

## 🚀 Quick Start

### Prerequisites
- Snowflake account with ACCOUNTADMIN or similar privileges
- Node.js 18+ installed
- npm or yarn package manager

### Installation Steps

1. **Clone or download this repository**

2. **Run SQL setup scripts in order**
   ```bash
   # Execute in Snowsight or SnowSQL
   # 01_setup_schema.sql through 06_sample_data.sql
   ```

3. **Configure and start the web application**
   ```bash
   cd webapp
   npm install
   cp .env.example .env
   # Edit .env with your Snowflake credentials
   npm start
   ```

4. **Access the dashboard**
   - Open browser: http://localhost:3000
   - Login with demo credentials (see webapp/README.md)

### Loading Your Data

```sql
-- Copy your daily stock data to the raw table
COPY INTO STOCKPULSE_AI.DATA.DAILY_STOCK_RAW
FROM @your_stage/stock_data.csv
FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1);

-- Dynamic tables will auto-refresh calculations
```

## 📈 Key Metrics & Calculations

### Stock Health Score (0-100)
```
Healthy (80-100):   Days of Cover > Lead Time + Safety Buffer
Monitoring (50-79): Lead Time < Days of Cover ≤ Lead Time + Buffer
Critical (0-49):    Days of Cover ≤ Lead Time
```

### Days of Cover
```
Days of Cover = Closing Stock / Average Daily Issue Rate
```

### Projected Stock-Out Date
```
Stock-Out Date = Current Date + (Closing Stock / Avg Daily Issue)
```

### Reorder Quantity
```
Reorder Qty = (Avg Daily Issue × Lead Time × 1.2) + Safety Stock - Closing Stock
```

## 🎨 Dashboard Preview

```
┌─────────────────────────────────────────────────────────────┐
│  StockPulse AI - Stock Health Dashboard                     │
├─────────────────────────────────────────────────────────────┤
│  Filters: [Location ▼] [Item Category ▼] [Risk Level ▼]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  STOCK HEALTH HEATMAP                                        │
│                                                              │
│          Item_A   Item_B   Item_C   Item_D   Item_E         │
│  Loc_1    🟢      🟡      🔴      🟢      🟡              │
│  Loc_2    🟢      🟢      🟡      🔴      🟢              │
│  Loc_3    🔴      🟢      🟢      🟢      🔴              │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  CRITICAL ALERTS (5)          TOP REORDER PRIORITIES (10)   │
│  ├─ Item_C @ Loc_1: 2 days   ├─ Item_C @ Loc_1: 500 units  │
│  ├─ Item_D @ Loc_2: 3 days   ├─ Item_E @ Loc_3: 300 units  │
│  └─ ...                       └─ ...                         │
├─────────────────────────────────────────────────────────────┤
│  [📥 Export Critical Items] [📥 Export All Recommendations] │
└─────────────────────────────────────────────────────────────┘
```

## 🌟 Innovation Highlights

1. **100% Snowflake-Native**: No external infrastructure or ETL pipelines
2. **Auto-Refreshing Intelligence**: Dynamic Tables maintain real-time calculations
3. **Transparent AI Logic**: All formulas are simple, auditable SQL
4. **Minimal Data Requirements**: Just 8 fields per daily stock record
5. **Low Operational Overhead**: Fully managed, no servers to maintain
6. **Scalable**: Handles millions of daily records with Snowflake compute
7. **Accessible**: Web-based UI suitable for field users and central teams

## 🤝 AI-for-Good Impact

- ✅ **Reduced Waste**: Early detection of overstock and slow-moving items
- ✅ **Improved Service Continuity**: Proactive stock-out prevention
- ✅ **Equitable Distribution**: Location-level risk visibility ensures fair allocation
- ✅ **Operational Efficiency**: Automated insights free staff for higher-value work
- ✅ **Resource Optimization**: Right supplies at the right place and time

## 📚 Documentation

- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Detailed setup instructions
- [User Guide](docs/USER_GUIDE.md) - Dashboard usage and workflows
- [Technical Specifications](docs/TECHNICAL_SPECS.md) - Architecture and algorithms

## 🔒 Security & Compliance

- Role-based access control (RBAC) through Snowflake
- Row-level security for multi-tenant scenarios
- Audit logging of all data access and modifications
- HIPAA/GDPR compliant when deployed in appropriate Snowflake regions

## 🛠️ Maintenance & Support

### Monitoring
- Monitor Dynamic Table refresh status
- Review Task execution history
- Check Stream lag for real-time updates

### Optimization
- Adjust refresh intervals based on data freshness requirements
- Scale warehouse size for larger datasets
- Archive historical data per retention policy

## 📝 License

This project is provided as-is for AI-for-Good initiatives. Please adapt and extend it to meet your specific organizational needs.

## 🙏 Acknowledgments

Built for the AI-for-Good Snowflake Hackathon to address critical supply chain challenges in healthcare and humanitarian sectors.

---

**For questions or support, please refer to the documentation or open an issue.**
