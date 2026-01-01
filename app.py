import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import snowflake.connector
from snowflake.connector import DictCursor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="StockPulse AI - Inventory Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-align: center;
        animation: fadeIn 1s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #6b7280;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 65px;
        padding: 0 35px;
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        border-radius: 12px 12px 0 0;
        font-weight: 600;
        font-size: 1.05rem;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    .alert-critical {
        background: linear-gradient(135deg, #fee2e2 0%, #fef2f2 100%);
        border-left: 6px solid #dc2626;
        padding: 1.3rem;
        margin: 1rem 0;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(220, 38, 38, 0.15);
        transition: transform 0.2s ease;
    }
    
    .alert-critical:hover {
        transform: translateX(5px);
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%);
        border-left: 6px solid #f59e0b;
        padding: 1.3rem;
        margin: 1rem 0;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(245, 158, 11, 0.15);
        transition: transform 0.2s ease;
    }
    
    .alert-warning:hover {
        transform: translateX(5px);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.65rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
        font-size: 0.95rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
    }
    
    .stat-badge {
        display: inline-block;
        padding: 0.45rem 1.1rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.9rem;
        margin: 0.3rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .badge-critical {
        background-color: #fee2e2;
        color: #dc2626;
    }
    
    .badge-warning {
        background-color: #fef3c7;
        color: #f59e0b;
    }
    
    .badge-success {
        background-color: #d1fae5;
        color: #059669;
    }
    
    .badge-info {
        background-color: #dbeafe;
        color: #2563eb;
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
        border-right: 1px solid #e5e7eb;
    }
    
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    div[data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'acknowledged_alerts' not in st.session_state:
    st.session_state.acknowledged_alerts = set()
if 'alert_history' not in st.session_state:
    st.session_state.alert_history = []
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 300
if 'alert_threshold' not in st.session_state:
    st.session_state.alert_threshold = 7
if 'show_healthy' not in st.session_state:
    st.session_state.show_healthy = True
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'compare_locations' not in st.session_state:
    st.session_state.compare_locations = []
if 'custom_alert_items' not in st.session_state:
    st.session_state.custom_alert_items = {}
if 'favorite_items' not in st.session_state:
    st.session_state.favorite_items = set()
if 'dashboard_layout' not in st.session_state:
    st.session_state.dashboard_layout = 'default'
if 'simulation_params' not in st.session_state:
    st.session_state.simulation_params = {}

@st.cache_resource
def get_snowflake_connection():
    """Create Snowflake connection"""
    try:
        conn = snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            user=os.getenv('SNOWFLAKE_USERNAME'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema='ANALYTICS',
            role=os.getenv('SNOWFLAKE_ROLE')
        )
        return conn
    except Exception as e:
        st.error(f"❌ Failed to connect to Snowflake: {str(e)}")
        return None

@st.cache_data(ttl=300)
def get_executive_summary():
    """Fetch executive summary data"""
    conn = get_snowflake_connection()
    if not conn:
        return None
    
    query = """
        SELECT 
            TOTAL_LOCATIONS,
            TOTAL_ITEMS,
            OUT_OF_STOCK_COUNT,
            CRITICAL_COUNT,
            HIGH_RISK_COUNT,
            MEDIUM_RISK_COUNT,
            HEALTHY_COUNT,
            OVERSTOCK_COUNT,
            PCT_REQUIRING_ATTENTION,
            PCT_HEALTHY,
            AVG_STOCK_HEALTH_SCORE,
            AVG_DAYS_OF_COVER,
            CRITICAL_ITEMS_AT_RISK,
            DATA_AS_OF_DATE
        FROM DT_EXECUTIVE_SUMMARY
        LIMIT 1
    """
    
    try:
        cursor = conn.cursor(DictCursor)
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        return result
    except Exception as e:
        st.error(f"Error fetching summary: {str(e)}")
        return None

@st.cache_data(ttl=300)
def get_stock_heatmap(location=None, category=None, risk=None):
    """Fetch stock health heatmap data"""
    conn = get_snowflake_connection()
    if not conn:
        return pd.DataFrame()
    
    query = """
        SELECT 
            LOCATION_NAME,
            ITEM_NAME,
            ITEM_CATEGORY,
            CLOSING_STOCK AS CURRENT_STOCK,
            STOCK_HEALTH_SCORE,
            RISK_CLASSIFICATION,
            DAYS_OF_COVER,
            DAYS_UNTIL_STOCKOUT,
            AVG_DAILY_ISSUE,
            IS_CRITICAL_ITEM,
            REQUIRES_ATTENTION
        FROM DT_STOCK_HEALTH_CLASSIFICATION
        WHERE 1=1
    """
    
    params = []
    if location:
        query += " AND LOCATION_NAME = %s"
        params.append(location)
    if category:
        query += " AND ITEM_CATEGORY = %s"
        params.append(category)
    if risk:
        query += " AND RISK_CLASSIFICATION = %s"
        params.append(risk)
    
    query += " ORDER BY STOCK_HEALTH_SCORE ASC, LOCATION_NAME, ITEM_NAME"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        cursor.close()
        return pd.DataFrame(data, columns=columns)
    except Exception as e:
        st.error(f"Error fetching heatmap: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_alerts():
    """Fetch active alerts"""
    conn = get_snowflake_connection()
    if not conn:
        return pd.DataFrame()
    
    query = """
        SELECT 
            CONCAT(LOCATION_NAME, '-', ITEM_NAME) as ALERT_ID,
            LOCATION_NAME,
            ITEM_NAME,
            ITEM_CATEGORY,
            CLOSING_STOCK AS CURRENT_STOCK,
            DAYS_UNTIL_STOCKOUT,
            RISK_CLASSIFICATION AS SEVERITY,
            IS_CRITICAL_ITEM,
            PROJECTED_STOCKOUT_DATE,
            CALCULATED_TIMESTAMP AS CREATED_AT
        FROM DT_STOCK_HEALTH_CLASSIFICATION
        WHERE REQUIRES_ATTENTION = TRUE
        ORDER BY 
            CASE RISK_CLASSIFICATION
                WHEN 'OUT_OF_STOCK' THEN 1
                WHEN 'CRITICAL' THEN 2
                WHEN 'HIGH_RISK' THEN 3
                ELSE 4
            END,
            DAYS_UNTIL_STOCKOUT ASC
        LIMIT 100
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        cursor.close()
        df = pd.DataFrame(data, columns=columns)
        # Filter out acknowledged alerts
        df = df[~df['ALERT_ID'].isin(st.session_state.acknowledged_alerts)]
        return df
    except Exception as e:
        st.error(f"Error fetching alerts: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_reorder_recommendations():
    """Fetch reorder recommendations"""
    conn = get_snowflake_connection()
    if not conn:
        return pd.DataFrame()
    
    query = """
        SELECT 
            LOCATION_NAME,
            ITEM_NAME,
            ITEM_CATEGORY,
            CURRENT_STOCK,
            AVG_DAILY_ISSUE,
            SUGGESTED_REORDER_QUANTITY,
            ESTIMATED_ORDER_VALUE,
            PROCUREMENT_PRIORITY_SCORE,
            URGENCY_SCORE,
            RECOMMENDED_ACTION_DATE,
            IS_CRITICAL_ITEM,
            DAYS_UNTIL_STOCKOUT,
            RISK_CLASSIFICATION
        FROM DT_REORDER_RECOMMENDATIONS
        ORDER BY PROCUREMENT_PRIORITY_SCORE DESC
        LIMIT 50
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        cursor.close()
        return pd.DataFrame(data, columns=columns)
    except Exception as e:
        st.error(f"Error fetching reorders: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_filter_options():
    """Get filter options"""
    conn = get_snowflake_connection()
    if not conn:
        return [], [], []
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT LOCATION_NAME FROM DT_STOCK_HEALTH_CLASSIFICATION ORDER BY LOCATION_NAME")
        locations = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT ITEM_CATEGORY FROM DT_STOCK_HEALTH_CLASSIFICATION ORDER BY ITEM_CATEGORY")
        categories = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT RISK_CLASSIFICATION FROM DT_STOCK_HEALTH_CLASSIFICATION ORDER BY RISK_CLASSIFICATION")
        risks = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        return locations, categories, risks
    except Exception as e:
        st.error(f"Error fetching filters: {str(e)}")
        return [], [], []

def get_risk_color(risk):
    """Get color for risk classification"""
    colors = {
        'OUT_OF_STOCK': '#1f2937',
        'CRITICAL': '#dc2626',
        'HIGH_RISK': '#f59e0b',
        'MEDIUM_RISK': '#fbbf24',
        'HEALTHY': '#10b981',
        'OVERSTOCK': '#3b82f6',
    }
    return colors.get(risk, '#6b7280')

def get_risk_icon(risk):
    """Get icon for risk classification"""
    icons = {
        'OUT_OF_STOCK': '🚫',
        'CRITICAL': '🔴',
        'HIGH_RISK': '⚠️',
        'MEDIUM_RISK': '🟡',
        'HEALTHY': '✅',
        'OVERSTOCK': '📦',
    }
    return icons.get(risk, '⚪')

def calculate_cost_savings(reorders_df):
    """Calculate potential cost savings from optimized reordering"""
    if reorders_df.empty:
        return 0, 0, 0
    
    total_reorder_value = float(reorders_df['ESTIMATED_ORDER_VALUE'].sum())
    # Assume 15% savings from bulk ordering and timing optimization
    potential_savings = total_reorder_value * 0.15
    # Estimate stockout cost prevention (avg $500 per stockout)
    critical_items = len(reorders_df[reorders_df['IS_CRITICAL_ITEM'] == True])
    stockout_prevention = float(critical_items * 500)
    
    return total_reorder_value, potential_savings, stockout_prevention

@st.cache_data(ttl=300)
def get_location_comparison(locations_list):
    """Compare metrics across selected locations"""
    conn = get_snowflake_connection()
    if not conn or not locations_list:
        return pd.DataFrame()
    
    placeholders = ','.join(['%s'] * len(locations_list))
    query = f"""
        SELECT 
            LOCATION_NAME,
            COUNT(*) as TOTAL_ITEMS,
            AVG(STOCK_HEALTH_SCORE) as AVG_HEALTH,
            SUM(CASE WHEN REQUIRES_ATTENTION = TRUE THEN 1 ELSE 0 END) as AT_RISK,
            SUM(CASE WHEN IS_CRITICAL_ITEM = TRUE THEN 1 ELSE 0 END) as CRITICAL_ITEMS,
            AVG(DAYS_OF_COVER) as AVG_DAYS_COVER
        FROM DT_STOCK_HEALTH_CLASSIFICATION
        WHERE LOCATION_NAME IN ({placeholders})
        GROUP BY LOCATION_NAME
        ORDER BY AVG_HEALTH DESC
    """
    
    try:
        return pd.read_sql(query, conn, params=locations_list)
    except Exception as e:
        st.error(f"Error comparing locations: {str(e)}")
        return pd.DataFrame()

def main():
    # Apply dark mode if enabled
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
            /* Dark Mode Theme */
            .stApp {
                background-color: #0f172a !important;
                color: #e2e8f0 !important;
            }
            
            /* Main content area */
            .main .block-container {
                background-color: #0f172a !important;
                color: #e2e8f0 !important;
            }
            
            /* Headers */
            .main-header {
                background: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%) !important;
                -webkit-background-clip: text !important;
                -webkit-text-fill-color: transparent !important;
            }
            
            .subtitle {
                color: #94a3b8 !important;
            }
            
            /* Sidebar */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important;
            }
            
            section[data-testid="stSidebar"] * {
                color: #e2e8f0 !important;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                background-color: transparent !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
                color: #e2e8f0 !important;
            }
            
            .stTabs [data-baseweb="tab"]:hover {
                background: linear-gradient(135deg, #334155 0%, #475569 100%) !important;
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: white !important;
            }
            
            /* Metrics */
            div[data-testid="stMetricValue"] {
                color: #f1f5f9 !important;
            }
            
            div[data-testid="stMetricLabel"] {
                color: #cbd5e1 !important;
            }
            
            div[data-testid="stMetricDelta"] {
                color: #94a3b8 !important;
            }
            
            /* Text elements */
            h1, h2, h3, h4, h5, h6, p, span, div, label {
                color: #e2e8f0 !important;
            }
            
            /* Dataframes */
            .dataframe {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
            }
            
            .dataframe th {
                background-color: #334155 !important;
                color: #f1f5f9 !important;
            }
            
            .dataframe td {
                color: #e2e8f0 !important;
            }
            
            /* Input elements */
            .stTextInput input, .stSelectbox select, .stMultiSelect, .stSlider {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
                border-color: #475569 !important;
            }
            
            /* Selectbox dropdown */
            .stSelectbox > div > div {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
            }
            
            .stSelectbox [data-baseweb="select"] {
                background-color: #1e293b !important;
            }
            
            .stSelectbox [data-baseweb="select"] > div {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
                border-color: #475569 !important;
            }
            
            /* Dropdown menu */
            [data-baseweb="popover"] {
                background-color: #1e293b !important;
            }
            
            [data-baseweb="menu"] {
                background-color: #1e293b !important;
            }
            
            [data-baseweb="menu"] li {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
            }
            
            [data-baseweb="menu"] li:hover {
                background-color: #334155 !important;
            }
            
            /* Text input */
            .stTextInput input {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
                border-color: #475569 !important;
            }
            
            .stTextInput input::placeholder {
                color: #94a3b8 !important;
            }
            
            /* Number input */
            .stNumberInput input {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
                border-color: #475569 !important;
            }
            
            /* Multiselect */
            .stMultiSelect [data-baseweb="tag"] {
                background-color: #334155 !important;
                color: #e2e8f0 !important;
            }
            
            .stMultiSelect input {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
            }
            
            /* Buttons */
            .stButton>button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: white !important;
            }
            
            /* Expanders */
            .streamlit-expanderHeader {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
            }
            
            /* Progress bars */
            .stProgress > div > div {
                background-color: #1e293b !important;
            }
            
            /* Info/Warning/Error boxes */
            .stAlert {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
            }
            
            /* Divider */
            hr {
                border-color: #334155 !important;
            }
            
            /* Code blocks */
            code {
                background-color: #1e293b !important;
                color: #94a3b8 !important;
            }
            
            /* Markdown text */
            .stMarkdown {
                color: #e2e8f0 !important;
            }
            
            /* Caption text */
            .caption {
                color: #94a3b8 !important;
            }
            
            /* Stat badges and custom divs */
            .stat-badge {
                background-color: #1e293b !important;
                border: 1px solid #475569 !important;
            }
            
            .badge-critical {
                background-color: #7f1d1d !important;
                color: #fca5a5 !important;
            }
            
            .badge-warning {
                background-color: #78350f !important;
                color: #fcd34d !important;
            }
            
            .badge-success {
                background-color: #14532d !important;
                color: #86efac !important;
            }
            
            .badge-info {
                background-color: #1e3a8a !important;
                color: #93c5fd !important;
            }
            
            /* Alert boxes */
            .alert-critical {
                background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%) !important;
                border-left: 6px solid #dc2626 !important;
                color: #fca5a5 !important;
            }
            
            .alert-warning {
                background: linear-gradient(135deg, #451a03 0%, #78350f 100%) !important;
                border-left: 6px solid #f59e0b !important;
                color: #fcd34d !important;
            }
            
            /* Custom colored divs */
            div[style*="background: linear-gradient"] {
                filter: brightness(0.8) contrast(1.1) !important;
            }
            
            div[style*="background-color"] {
                filter: brightness(0.85) !important;
            }
            
            /* Override for specific custom divs with inline styles */
            .main div[style*="text-align: center"][style*="padding"] {
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
                border: 1px solid #475569 !important;
            }
            
            .main div[style*="text-align: center"][style*="padding"] div[style*="font-size: 2"] {
                color: #f1f5f9 !important;
                text-shadow: 0 0 10px rgba(255,255,255,0.3) !important;
            }
            
            .main div[style*="text-align: center"][style*="padding"] div[style*="color"] {
                color: #cbd5e1 !important;
            }
            
            /* Plotly charts */
            .js-plotly-plot .plotly {
                background-color: #1e293b !important;
            }
            
            .js-plotly-plot .plotly .bg {
                fill: #1e293b !important;
            }
            
            /* Table headers and cells */
            table {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
            }
            
            thead tr th {
                background-color: #334155 !important;
                color: #f1f5f9 !important;
            }
            
            tbody tr {
                background-color: #1e293b !important;
            }
            
            tbody tr:hover {
                background-color: #334155 !important;
            }
            
            tbody td {
                color: #e2e8f0 !important;
            }
            
            /* Download buttons */
            .stDownloadButton button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: white !important;
            }
            
            /* Checkbox and radio */
            .stCheckbox, .stRadio {
                color: #e2e8f0 !important;
            }
            
            /* Styled dataframes - additional specificity */
            [data-testid="stDataFrame"] {
                background-color: #1e293b !important;
            }
            
            [data-testid="stDataFrame"] table {
                background-color: #1e293b !important;
            }
            
            [data-testid="stDataFrame"] thead {
                background-color: #334155 !important;
            }
            
            [data-testid="stDataFrame"] tbody {
                background-color: #1e293b !important;
            }
            
            [data-testid="stDataFrame"] tr {
                background-color: transparent !important;
            }
            
            [data-testid="stDataFrame"] th {
                background-color: #334155 !important;
                color: #f1f5f9 !important;
                border-color: #475569 !important;
            }
            
            [data-testid="stDataFrame"] td {
                border-color: #475569 !important;
            }
            
            /* Override background colors in styled cells while keeping gradients visible */
            [data-testid="stDataFrame"] td[style*="background-color: #d1fae5"] {
                background-color: #14532d !important;
                color: #bbf7d0 !important;
            }
            
            [data-testid="stDataFrame"] td[style*="background-color: #fef3c7"] {
                background-color: #78350f !important;
                color: #fde68a !important;
            }
            
            [data-testid="stDataFrame"] td[style*="background-color: #fed7aa"] {
                background-color: #9a3412 !important;
                color: #fed7aa !important;
            }
            
            [data-testid="stDataFrame"] td[style*="background-color: #fecaca"] {
                background-color: #7f1d1d !important;
                color: #fecaca !important;
            }
            
            /* Streamlit data editor */
            .element-container div[data-testid="stDataFrame"] > div {
                background-color: #1e293b !important;
            }
        </style>
        """, unsafe_allow_html=True)
    
    # Enhanced Header with Icon Background
    st.markdown('''
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h1 style="margin: 0; font-size: 3rem; font-weight: 800; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            📦 StockPulse AI
        </h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; color: rgba(255,255,255,0.95); font-weight: 500;">
            🏥 Real-time Inventory Intelligence for Healthcare & Humanitarian Organizations
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    with col2:
        time_diff = (datetime.now() - st.session_state.last_refresh).seconds
        st.metric("⏱️ Last Refresh", f"{time_diff}s ago")
    with col3:
        conn_status = "🟢 Connected" if get_snowflake_connection() else "🔴 Disconnected"
        st.metric("📡 Snowflake", conn_status)
    with col4:
        st.metric("🕒 System Time", datetime.now().strftime('%H:%M:%S'))
    
    st.divider()
    
    # Enhanced Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Refresh settings
        with st.expander("🔄 Refresh Settings", expanded=False):
            st.session_state.auto_refresh = st.toggle("Enable Auto-refresh", value=st.session_state.auto_refresh)
            st.session_state.refresh_interval = st.select_slider(
                "Refresh Interval",
                options=[30, 60, 300, 600, 1800],
                value=st.session_state.refresh_interval,
                format_func=lambda x: f"{x//60} min" if x >= 60 else f"{x}s"
            )
        
        # Alert settings
        with st.expander("⚠️ Alert Thresholds", expanded=False):
            st.session_state.alert_threshold = st.slider(
                "Days to Stockout Alert",
                1, 30, st.session_state.alert_threshold
            )
            st.session_state.show_healthy = st.checkbox(
                "Show Healthy Items",
                value=st.session_state.show_healthy
            )
        
        # Advanced Search & Filters Feature (12)
        with st.expander("🔍 Advanced Search", expanded=False):
            st.markdown("**Multi-Criteria Filters**")
            min_stock = st.number_input("📦 Min Stock Level", min_value=0, value=0, step=10)
            max_stock = st.number_input("📦 Max Stock Level", min_value=0, value=10000, step=10)
            min_health = st.slider("🎯 Min Health Score", 0, 100, 0)
            search_mode = st.radio("🔎 Search Mode", ["Contains", "Exact Match", "Starts With"])
            st.session_state['advanced_filters'] = {
                'min_stock': min_stock,
                'max_stock': max_stock,
                'min_health': min_health,
                'search_mode': search_mode
            }
        
        # Custom Item Alerts Feature (13)
        with st.expander("🔔 Custom Item Alerts", expanded=False):
            st.markdown("**Set Item-Specific Thresholds**")
            item_name = st.text_input("🏷️ Item Name")
            custom_threshold = st.number_input("⚠️ Custom Alert Days", 1, 60, 7)
            if st.button("➕ Add Custom Alert"):
                if item_name:
                    st.session_state.custom_alert_items[item_name] = custom_threshold
                    st.success(f"✅ Alert set for {item_name}")
            
            if st.session_state.custom_alert_items:
                st.markdown("**Active Custom Alerts:**")
                for item, days in list(st.session_state.custom_alert_items.items()):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.caption(f"{item}: {days} days")
                    with col2:
                        if st.button("❌", key=f"del_{item}"):
                            del st.session_state.custom_alert_items[item]
                            st.rerun()
        
        # Location Comparison Tool
        with st.expander("🔄 Compare Locations", expanded=False):
            locations, _, _ = get_filter_options()
            st.session_state.compare_locations = st.multiselect(
                "Select locations to compare",
                locations,
                default=st.session_state.compare_locations[:3] if st.session_state.compare_locations else []
            )
            if len(st.session_state.compare_locations) > 1:
                st.caption(f"✅ Comparing {len(st.session_state.compare_locations)} locations")
        
        st.divider()
        st.subheader("📍 Filters")
        locations, categories, risks = get_filter_options()
        
        selected_location = st.selectbox("🏥 Location", ["All"] + locations, index=0)
        selected_category = st.selectbox("📦 Category", ["All"] + categories, index=0)
        selected_risk = st.selectbox("⚠️ Risk Level", ["All"] + risks, index=0)
        
        location_filter = None if selected_location == "All" else selected_location
        category_filter = None if selected_category == "All" else selected_category
        risk_filter = None if selected_risk == "All" else selected_risk
        
        st.divider()
        st.subheader("📥 Quick Export")
        
        heatmap_data = get_stock_heatmap(location_filter, category_filter, risk_filter)
        if not heatmap_data.empty:
            # Format numeric columns to avoid ### display in Excel
            export_df = heatmap_data.copy()
            numeric_cols = ['CURRENT_STOCK', 'AVG_DAILY_CONSUMPTION', 'DAYS_OF_COVER', 'STOCK_HEALTH_SCORE']
            for col in numeric_cols:
                if col in export_df.columns and pd.api.types.is_numeric_dtype(export_df[col]):
                    export_df[col] = export_df[col].round(2)
            
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="📊 Download Heatmap",
                data=csv,
                file_name=f"stock_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        reorders = get_reorder_recommendations()
        if not reorders.empty:
            # Format numeric columns to avoid ### display in Excel
            export_df = reorders.copy()
            numeric_cols = ['CURRENT_STOCK', 'AVG_DAILY_CONSUMPTION', 'DAYS_OF_COVER', 'REORDER_POINT', 'SUGGESTED_ORDER_QTY', 'ESTIMATED_ORDER_VALUE', 'PRIORITY_SCORE']
            for col in numeric_cols:
                if col in export_df.columns and pd.api.types.is_numeric_dtype(export_df[col]):
                    export_df[col] = export_df[col].round(2)
            
            csv_reorder = export_df.to_csv(index=False)
            st.download_button(
                label="🛒 Download Reorders",
                data=csv_reorder,
                file_name=f"reorder_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.divider()
        st.caption("💡 **Pro Tip:** Use filters to focus on specific locations or categories")
    
    # Enhanced Executive Summary
    summary = get_executive_summary()
    
    if summary:
        st.header("📊 Executive Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            health_score = summary['AVG_STOCK_HEALTH_SCORE']
            st.metric(
                label="🎯 Overall Health Score",
                value=f"{health_score:.1f}/100",
                delta=f"{summary['TOTAL_ITEMS']} items",
                delta_color="off"
            )
            st.progress(float(health_score) / 100)
            if health_score >= 80:
                st.markdown('<span class="stat-badge badge-success">✅ Excellent</span>', unsafe_allow_html=True)
            elif health_score >= 60:
                st.markdown('<span class="stat-badge badge-warning">⚠️ Fair</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="stat-badge badge-critical">🔴 Critical</span>', unsafe_allow_html=True)
        
        with col2:
            attention_count = (summary['OUT_OF_STOCK_COUNT'] or 0) + (summary['CRITICAL_COUNT'] or 0) + (summary['HIGH_RISK_COUNT'] or 0)
            pct = summary['PCT_REQUIRING_ATTENTION']
            st.metric(
                label="⚠️ Items Requiring Attention",
                value=attention_count,
                delta=f"{pct:.1f}% of inventory",
                delta_color="inverse"
            )
            st.progress(min(float(pct) / 100, 1.0))
            st.markdown(f'<span class="stat-badge badge-critical">🚫 Out: {summary["OUT_OF_STOCK_COUNT"] or 0}</span>', unsafe_allow_html=True)
            st.markdown(f'<span class="stat-badge badge-critical">🔴 Critical: {summary["CRITICAL_COUNT"] or 0}</span>', unsafe_allow_html=True)
        
        with col3:
            critical_items = summary['CRITICAL_ITEMS_AT_RISK'] or 0
            out_of_stock = summary['OUT_OF_STOCK_COUNT'] or 0
            st.metric(
                label="🔴 Critical Items at Risk",
                value=critical_items,
                delta=f"{out_of_stock} already out",
                delta_color="inverse"
            )
            risk_pct = (critical_items / summary['TOTAL_ITEMS'] * 100) if summary['TOTAL_ITEMS'] > 0 else 0
            st.progress(min(float(risk_pct) / 100, 1.0))
            st.markdown(f'<span class="stat-badge badge-info">🎯 {summary["TOTAL_LOCATIONS"]} locations</span>', unsafe_allow_html=True)
        
        with col4:
            reorders = get_reorder_recommendations()
            total_value = reorders['ESTIMATED_ORDER_VALUE'].sum() if not reorders.empty else 0
            reorder_count = len(reorders) if not reorders.empty else 0
            st.metric(
                label="🛒 Estimated Reorder Value",
                value=f"${total_value:,.0f}",
                delta=f"{reorder_count} items"
            )
            avg_days_cover = summary['AVG_DAYS_OF_COVER']
            st.progress(min(float(avg_days_cover) / 30, 1.0))
            st.markdown(f'<span class="stat-badge badge-info">📅 Avg {avg_days_cover:.1f}d cover</span>', unsafe_allow_html=True)
        
        # Quick stats bar
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Conditional styling based on dark mode
        if st.session_state.dark_mode:
            healthy_bg = "linear-gradient(135deg, #14532d, #166534)"
            healthy_num_color = "#86efac"
            healthy_text_color = "#bbf7d0"
            
            medium_bg = "linear-gradient(135deg, #78350f, #92400e)"
            medium_num_color = "#fcd34d"
            medium_text_color = "#fde68a"
            
            high_bg = "linear-gradient(135deg, #9a3412, #c2410c)"
            high_num_color = "#fdba74"
            high_text_color = "#fed7aa"
            
            critical_bg = "linear-gradient(135deg, #7f1d1d, #991b1b)"
            critical_num_color = "#fca5a5"
            critical_text_color = "#fecaca"
            
            overstock_bg = "linear-gradient(135deg, #1e3a8a, #1e40af)"
            overstock_num_color = "#93c5fd"
            overstock_text_color = "#bfdbfe"
        else:
            healthy_bg = "linear-gradient(135deg, #d1fae5, #ecfdf5)"
            healthy_num_color = "#065f46"
            healthy_text_color = "#10b981"
            
            medium_bg = "linear-gradient(135deg, #fef3c7, #fffbeb)"
            medium_num_color = "#92400e"
            medium_text_color = "#f59e0b"
            
            high_bg = "linear-gradient(135deg, #fed7aa, #ffedd5)"
            high_num_color = "#9a3412"
            high_text_color = "#f97316"
            
            critical_bg = "linear-gradient(135deg, #fecaca, #fee2e2)"
            critical_num_color = "#991b1b"
            critical_text_color = "#dc2626"
            
            overstock_bg = "linear-gradient(135deg, #dbeafe, #eff6ff)"
            overstock_num_color = "#1e3a8a"
            overstock_text_color = "#3b82f6"
        
        with col1:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: {healthy_bg}; border-radius: 10px;">
                <div style="font-size: 2.5rem;">✅</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: {healthy_num_color};">{summary['HEALTHY_COUNT'] or 0}</div>
                <div style="color: {healthy_text_color}; font-weight: 600; font-size: 0.9rem;">Healthy</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: {medium_bg}; border-radius: 10px;">
                <div style="font-size: 2.5rem;">🟡</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: {medium_num_color};">{summary['MEDIUM_RISK_COUNT'] or 0}</div>
                <div style="color: {medium_text_color}; font-weight: 600; font-size: 0.9rem;">Medium Risk</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: {high_bg}; border-radius: 10px;">
                <div style="font-size: 2.5rem;">⚠️</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: {high_num_color};">{summary['HIGH_RISK_COUNT'] or 0}</div>
                <div style="color: {high_text_color}; font-weight: 600; font-size: 0.9rem;">High Risk</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: {critical_bg}; border-radius: 10px;">
                <div style="font-size: 2.5rem;">🔴</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: {critical_num_color};">{summary['CRITICAL_COUNT'] or 0}</div>
                <div style="color: {critical_text_color}; font-weight: 600; font-size: 0.9rem;">Critical</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: {overstock_bg}; border-radius: 10px;">
                <div style="font-size: 2.5rem;">📦</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: {overstock_num_color};">{summary['OVERSTOCK_COUNT'] or 0}</div>
                <div style="color: {overstock_text_color}; font-weight: 600; font-size: 0.9rem;">Overstock</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("⚠️ Unable to load executive summary. Please check your Snowflake connection.")
    
    st.divider()
    
    # Location Comparison Section (if enabled)
    if len(st.session_state.compare_locations) > 1:
        st.header("🔄 Location Comparison")
        comparison_data = get_location_comparison(st.session_state.compare_locations)
        
        if not comparison_data.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Bar chart comparison
                fig = px.bar(
                    comparison_data,
                    x='LOCATION_NAME',
                    y='AVG_HEALTH',
                    title="Average Health Score by Location",
                    color='AVG_HEALTH',
                    color_continuous_scale='RdYlGn',
                    text_auto='.1f'
                )
                if st.session_state.dark_mode:
                    fig.update_layout(
                        template='plotly_dark',
                        paper_bgcolor='#1e293b',
                        plot_bgcolor='#1e293b',
                        font=dict(color='#e2e8f0'),
                        height=300
                    )
                else:
                    fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # At-risk items comparison
                fig2 = px.bar(
                    comparison_data,
                    x='LOCATION_NAME',
                    y=['AT_RISK', 'CRITICAL_ITEMS'],
                    title="Risk Items by Location",
                    barmode='group',
                    color_discrete_map={'AT_RISK': '#f59e0b', 'CRITICAL_ITEMS': '#dc2626'}
                )
                if st.session_state.dark_mode:
                    fig2.update_layout(
                        template='plotly_dark',
                        paper_bgcolor='#1e293b',
                        plot_bgcolor='#1e293b',
                        font=dict(color='#e2e8f0'),
                        height=300
                    )
                else:
                    fig2.update_layout(height=300)
                st.plotly_chart(fig2, use_container_width=True)
            
            # Detailed comparison table
            st.dataframe(
                comparison_data.style.background_gradient(subset=['AVG_HEALTH'], cmap='RdYlGn')
                .format({
                    'TOTAL_ITEMS': '{:.0f}',
                    'AVG_HEALTH': '{:.1f}',
                    'AT_RISK': '{:.0f}',
                    'CRITICAL_ITEMS': '{:.0f}',
                    'AVG_DAYS_COVER': '{:.1f}'
                }),
                use_container_width=True
            )
        
        st.divider()
    
    # Main Content Tabs with Enhanced Features
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔥 Stock Heatmap", 
        "⚠️ Active Alerts", 
        "🛒 Reorder Queue", 
        "📊 Analytics",
        "💰 Cost Insights",
        "🏆 Top Performers"
    ])
    
    with tab1:
        st.subheader("🔥 Stock Health Matrix")
        
        # Filters and search
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search = st.text_input("🔍 Search items or locations...", "", key="heatmap_search")
        with col2:
            sort_by = st.selectbox("🔄 Sort by", ["Health Score", "Location", "Item Name", "Days to Stockout"])
        with col3:
            show_count = st.selectbox("📄 Show", ["All", "Top 50", "Top 100", "Bottom 50"])
        
        heatmap_data = get_stock_heatmap(location_filter, category_filter, risk_filter)
        
        if not heatmap_data.empty:
            # Apply search filter
            if search:
                mask = heatmap_data.apply(lambda row: search.lower() in str(row).lower(), axis=1)
                heatmap_data = heatmap_data[mask]
            
            # Apply sorting
            if sort_by == "Health Score":
                heatmap_data = heatmap_data.sort_values('STOCK_HEALTH_SCORE')
            elif sort_by == "Location":
                heatmap_data = heatmap_data.sort_values('LOCATION_NAME')
            elif sort_by == "Item Name":
                heatmap_data = heatmap_data.sort_values('ITEM_NAME')
            elif sort_by == "Days to Stockout":
                heatmap_data = heatmap_data.sort_values('DAYS_UNTIL_STOCKOUT')
            
            # Apply count filter
            if show_count == "Top 50":
                heatmap_data = heatmap_data.head(50)
            elif show_count == "Top 100":
                heatmap_data = heatmap_data.head(100)
            elif show_count == "Bottom 50":
                heatmap_data = heatmap_data.tail(50)
            
            # Summary stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.info(f"📄 **{len(heatmap_data)}** items displayed")
            with col2:
                avg_health = heatmap_data['STOCK_HEALTH_SCORE'].mean()
                st.info(f"🎯 **{avg_health:.1f}** avg health")
            with col3:
                at_risk = len(heatmap_data[heatmap_data['REQUIRES_ATTENTION'] == True])
                st.warning(f"⚠️ **{at_risk}** at risk")
            with col4:
                critical = len(heatmap_data[heatmap_data['IS_CRITICAL_ITEM'] == True])
                st.error(f"🔴 **{critical}** critical")
            
            # Style the dataframe with icons
            display_df = heatmap_data.copy()
            display_df['🎯 RISK'] = display_df['RISK_CLASSIFICATION'].apply(lambda x: f"{get_risk_icon(x)} {x}")
            display_df['⚡ CRITICAL'] = display_df['IS_CRITICAL_ITEM'].apply(lambda x: '✅' if x else '')
            display_df['⚠️ ALERT'] = display_df['REQUIRES_ATTENTION'].apply(lambda x: '⚠️' if x else '')
            
            # Reorder columns
            display_columns = [
                'LOCATION_NAME', 'ITEM_NAME', 'ITEM_CATEGORY', 
                'CURRENT_STOCK', 'STOCK_HEALTH_SCORE', '🎯 RISK',
                'DAYS_OF_COVER', 'DAYS_UNTIL_STOCKOUT', 'AVG_DAILY_ISSUE',
                '⚡ CRITICAL', '⚠️ ALERT'
            ]
            
            # Color styling
            def color_health_score(val):
                if pd.isna(val):
                    return ''
                try:
                    val = float(val)
                    if val >= 80:
                        return 'background-color: #d1fae5; color: #065f46; font-weight: bold;'
                    elif val >= 60:
                        return 'background-color: #fef3c7; color: #92400e; font-weight: bold;'
                    elif val >= 40:
                        return 'background-color: #fed7aa; color: #9a3412; font-weight: bold;'
                    else:
                        return 'background-color: #fecaca; color: #991b1b; font-weight: bold;'
                except:
                    return ''
            
            styled_df = display_df[display_columns].style.map(
                color_health_score, subset=['STOCK_HEALTH_SCORE']
            ).format({
                'CURRENT_STOCK': '{:,.0f}',
                'STOCK_HEALTH_SCORE': '{:.1f}',
                'DAYS_OF_COVER': '{:.1f}',
                'DAYS_UNTIL_STOCKOUT': '{:.0f}',
                'AVG_DAILY_ISSUE': '{:.2f}'
            })
            
            st.dataframe(styled_df, use_container_width=True, height=600)
            
            # Export button with formatted data
            export_df = display_df.copy()
            numeric_cols = ['CURRENT_STOCK', 'STOCK_HEALTH_SCORE', 'DAYS_OF_COVER', 'DAYS_UNTIL_STOCKOUT', 'AVG_DAILY_ISSUE']
            for col in numeric_cols:
                if col in export_df.columns and pd.api.types.is_numeric_dtype(export_df[col]):
                    export_df[col] = export_df[col].round(2)
            
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="📊 Download Filtered Data",
                data=csv,
                file_name=f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("🔍 No data available for selected filters.")
    
    with tab2:
        st.subheader("⚠️ Active Alerts")
        alerts = get_alerts()
        
        if not alerts.empty:
            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🚨 Total Active Alerts", len(alerts))
            with col2:
                critical_alerts = len(alerts[alerts['SEVERITY'].isin(['OUT_OF_STOCK', 'CRITICAL'])])
                st.metric("🔴 Critical Alerts", critical_alerts)
            with col3:
                st.metric("✅ Acknowledged Today", len(st.session_state.acknowledged_alerts))
            
            st.markdown("---")
            
            # Bulk Actions Feature
            st.subheader("⚡ Bulk Actions")
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("✅ Acknowledge All Alerts", type="primary", use_container_width=True):
                    for idx, alert in alerts.iterrows():
                        st.session_state.acknowledged_alerts.add(alert['ALERT_ID'])
                        st.session_state.alert_history.append({
                            'timestamp': datetime.now(),
                            'alert_id': alert['ALERT_ID'],
                            'location': alert['LOCATION_NAME'],
                            'item': alert['ITEM_NAME'],
                            'severity': alert['SEVERITY']
                        })
                    st.success(f"✅ Acknowledged {len(alerts)} alerts!")
                    st.rerun()
            with col2:
                if st.button("🗑️ Clear History", use_container_width=True):
                    st.session_state.alert_history = []
                    st.success("🧹 History cleared!")
                    st.rerun()
            
            st.markdown("---")
            
            for idx, alert in alerts.iterrows():
                severity_class = "alert-critical" if alert['SEVERITY'] in ['OUT_OF_STOCK', 'CRITICAL'] else "alert-warning"
                icon = get_risk_icon(alert['SEVERITY'])
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Format category name for display
                    category_display = alert['ITEM_CATEGORY'].replace('_', ' ').title()
                    status_display = alert['SEVERITY'].replace('_', ' ').title()
                    stock_display = f"{float(alert['CURRENT_STOCK']):.0f}"
                    days_display = f"{int(alert['DAYS_UNTIL_STOCKOUT'])}" if alert['DAYS_UNTIL_STOCKOUT'] else "N/A"
                    critical_badge = ' | <span style="color: #dc2626; font-weight: 600;">⚠️ CRITICAL ITEM</span>' if alert['IS_CRITICAL_ITEM'] else ''
                    
                    alert_html = f"""
                    <div class="{severity_class}" style="padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                        <strong style="font-size: 1.1rem;">{icon} {alert['LOCATION_NAME']} - {alert['ITEM_NAME']}</strong>
                        <span style="display: inline-block; margin-left: 10px; padding: 3px 10px; background-color: rgba(255,255,255,0.3); border-radius: 12px; font-size: 0.85rem;">
                            {category_display}
                        </span>
                        <br/><br/>
                        <div style="font-size: 0.95rem; line-height: 1.6;">
                            📊 Status: <strong>{status_display}</strong> | 
                            📦 Stock: <strong>{stock_display}</strong> units | 
                            ⏰ Days to stockout: <strong>{days_display}</strong>{critical_badge}
                        </div>
                    </div>
                    """
                    st.markdown(alert_html, unsafe_allow_html=True)
                
                with col2:
                    if st.button("✅ Acknowledge", key=f"ack_{alert['ALERT_ID']}", use_container_width=True):
                        st.session_state.acknowledged_alerts.add(alert['ALERT_ID'])
                        st.session_state.alert_history.append({
                            'timestamp': datetime.now(),
                            'alert_id': alert['ALERT_ID'],
                            'location': alert['LOCATION_NAME'],
                            'item': alert['ITEM_NAME'],
                            'severity': alert['SEVERITY']
                        })
                        st.success(f"✅ Alert acknowledged!")
                        st.rerun()
            
            st.caption(f"📋 {len(alerts)} active alerts | {len(st.session_state.acknowledged_alerts)} acknowledged in this session")
            
            # Alert History Section
            if st.session_state.alert_history:
                with st.expander("📜 Alert History (This Session)", expanded=False):
                    history_df = pd.DataFrame(st.session_state.alert_history)
                    history_df['timestamp'] = history_df['timestamp'].dt.strftime('%H:%M:%S')
                    st.dataframe(history_df, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No active alerts! All stock levels are healthy.")
            st.balloons()
    
    with tab3:
        st.subheader("🛒 Reorder Recommendations")
        reorders = get_reorder_recommendations()
        
        if not reorders.empty:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            total_value = reorders['ESTIMATED_ORDER_VALUE'].sum()
            with col1:
                st.metric("💰 Total Reorder Value", f"${total_value:,.2f}")
            with col2:
                st.metric("📦 Items to Reorder", len(reorders))
            with col3:
                avg_priority = reorders['PROCUREMENT_PRIORITY_SCORE'].mean()
                st.metric("🎯 Avg Priority Score", f"{avg_priority:.1f}")
            
            st.markdown("---")
            
            # Add icons and format
            display_reorders = reorders.copy()
            display_reorders['🎯 RISK'] = display_reorders['RISK_CLASSIFICATION'].apply(lambda x: f"{get_risk_icon(x)} {x}")
            display_reorders['⚡ CRITICAL'] = display_reorders['IS_CRITICAL_ITEM'].apply(lambda x: '✅' if x else '')
            
            # Display as styled dataframe
            st.dataframe(
                display_reorders[['LOCATION_NAME', 'ITEM_NAME', 'ITEM_CATEGORY', 'CURRENT_STOCK', 
                                 'AVG_DAILY_ISSUE', 'SUGGESTED_REORDER_QUANTITY', 'ESTIMATED_ORDER_VALUE',
                                 'PROCUREMENT_PRIORITY_SCORE', 'DAYS_UNTIL_STOCKOUT', '🎯 RISK', '⚡ CRITICAL']].style.format({
                    'CURRENT_STOCK': '{:,.0f}',
                    'AVG_DAILY_ISSUE': '{:.2f}',
                    'SUGGESTED_REORDER_QUANTITY': '{:,.1f}',
                    'ESTIMATED_ORDER_VALUE': '${:,.2f}',
                    'PROCUREMENT_PRIORITY_SCORE': '{:.0f}',
                    'DAYS_UNTIL_STOCKOUT': '{:.0f}'
                }).background_gradient(subset=['PROCUREMENT_PRIORITY_SCORE'], cmap='RdYlGn_r'),
                use_container_width=True,
                height=600
            )
            
            # Download button with formatted data
            export_df = reorders.copy()
            numeric_cols = ['CURRENT_STOCK', 'AVG_DAILY_ISSUE', 'DAYS_OF_COVER', 'REORDER_POINT', 
                          'SUGGESTED_REORDER_QUANTITY', 'ESTIMATED_ORDER_VALUE', 'PROCUREMENT_PRIORITY_SCORE', 'DAYS_UNTIL_STOCKOUT']
            for col in numeric_cols:
                if col in export_df.columns and pd.api.types.is_numeric_dtype(export_df[col]):
                    export_df[col] = export_df[col].round(2)
            
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Complete Reorder List",
                data=csv,
                file_name=f"reorder_recommendations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("📋 No reorder recommendations at this time.")
    
    with tab4:
        st.subheader("📊 Risk Distribution & Analytics")
        heatmap_data = get_stock_heatmap(location_filter, category_filter, risk_filter)
        
        if not heatmap_data.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart
                risk_counts = heatmap_data['RISK_CLASSIFICATION'].value_counts()
                fig = px.pie(
                    values=risk_counts.values,
                    names=risk_counts.index,
                    title="📊 Stock Items by Risk Classification",
                    color=risk_counts.index,
                    color_discrete_map={
                        'OUT_OF_STOCK': '#1f2937',
                        'CRITICAL': '#dc2626',
                        'HIGH_RISK': '#f59e0b',
                        'MEDIUM_RISK': '#fbbf24',
                        'HEALTHY': '#10b981',
                        'OVERSTOCK': '#3b82f6',
                    },
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=12)
                if st.session_state.dark_mode:
                    fig.update_layout(
                        template='plotly_dark',
                        paper_bgcolor='#1e293b',
                        plot_bgcolor='#1e293b',
                        font=dict(color='#e2e8f0'),
                        height=400
                    )
                else:
                    fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Health score distribution
                fig2 = px.histogram(
                    heatmap_data,
                    x='STOCK_HEALTH_SCORE',
                    nbins=20,
                    title="📈 Health Score Distribution",
                    color_discrete_sequence=['#667eea']
                )
                if st.session_state.dark_mode:
                    fig2.update_layout(
                        template='plotly_dark',
                        paper_bgcolor='#1e293b',
                        plot_bgcolor='#1e293b',
                        font=dict(color='#e2e8f0'),
                        xaxis_title="Health Score",
                        yaxis_title="Number of Items",
                        height=400
                    )
                else:
                    fig2.update_layout(
                        xaxis_title="Health Score",
                        yaxis_title="Number of Items",
                        height=400
                    )
                st.plotly_chart(fig2, use_container_width=True)
            
            # Bar chart by location
            location_risk = heatmap_data.groupby(['LOCATION_NAME', 'RISK_CLASSIFICATION']).size().reset_index(name='count')
            fig3 = px.bar(
                location_risk,
                x='LOCATION_NAME',
                y='count',
                color='RISK_CLASSIFICATION',
                title="🏥 Risk Distribution by Location",
                color_discrete_map={
                    'OUT_OF_STOCK': '#1f2937',
                    'CRITICAL': '#dc2626',
                    'HIGH_RISK': '#f59e0b',
                    'MEDIUM_RISK': '#fbbf24',
                    'HEALTHY': '#10b981',
                    'OVERSTOCK': '#3b82f6',
                },
                barmode='stack'
            )
            if st.session_state.dark_mode:
                fig3.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='#1e293b',
                    plot_bgcolor='#1e293b',
                    font=dict(color='#e2e8f0'),
                    height=450,
                    xaxis_tickangle=-45
                )
            else:
                fig3.update_layout(height=450, xaxis_tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)
            
            # Category analysis
            st.subheader("📦 Category Performance")
            category_stats = heatmap_data.groupby('ITEM_CATEGORY').agg({
                'STOCK_HEALTH_SCORE': 'mean',
                'ITEM_NAME': 'count',
                'REQUIRES_ATTENTION': 'sum'
            }).reset_index()
            category_stats.columns = ['Category', 'Avg Health Score', 'Total Items', 'Items at Risk']
            
            st.dataframe(
                category_stats.style.format({
                    'Avg Health Score': '{:.1f}',
                    'Total Items': '{:.0f}',
                    'Items at Risk': '{:.0f}'
                }).background_gradient(subset=['Avg Health Score'], cmap='RdYlGn'),
                use_container_width=True
            )
            
            # Item Movement Velocity Feature
            st.markdown("---")
            st.subheader("🚀 Item Movement Velocity Analysis")
            
            # Convert numeric columns to float
            heatmap_data['AVG_DAILY_ISSUE'] = pd.to_numeric(heatmap_data['AVG_DAILY_ISSUE'], errors='coerce').fillna(0)
            
            # Calculate velocity classification
            heatmap_data['VELOCITY'] = heatmap_data['AVG_DAILY_ISSUE'].apply(lambda x: 
                'Fast Mover' if x > 5 else ('Normal Mover' if x > 1 else 'Slow Mover')
            )
            
            velocity_counts = heatmap_data['VELOCITY'].value_counts()
            
            col1, col2 = st.columns(2)
            with col1:
                # Velocity distribution pie chart
                fig_velocity = px.pie(
                    values=velocity_counts.values,
                    names=velocity_counts.index,
                    title="📊 Item Movement Distribution",
                    color=velocity_counts.index,
                    color_discrete_map={
                        'Fast Mover': '#10b981',
                        'Normal Mover': '#f59e0b',
                        'Slow Mover': '#ef4444'
                    },
                    hole=0.4
                )
                fig_velocity.update_traces(textposition='inside', textinfo='percent+label')
                fig_velocity.update_layout(height=350)
                st.plotly_chart(fig_velocity, use_container_width=True)
            
            with col2:
                # Top fast movers
                fast_movers = heatmap_data[heatmap_data['VELOCITY'] == 'Fast Mover'].nlargest(5, 'AVG_DAILY_ISSUE')[['ITEM_NAME', 'LOCATION_NAME', 'AVG_DAILY_ISSUE']]
                st.markdown("**🔥 Top 5 Fast Moving Items**")
                if not fast_movers.empty:
                    for idx, item in fast_movers.iterrows():
                        st.markdown(f"- **{item['ITEM_NAME']}** ({item['LOCATION_NAME']}): {item['AVG_DAILY_ISSUE']:.1f} units/day")
                else:
                    st.info("No fast moving items found")
                
                st.markdown("")
                # Slow movers warning
                slow_movers = heatmap_data[heatmap_data['VELOCITY'] == 'Slow Mover']
                st.metric("🐢 Slow Moving Items", len(slow_movers), delta=f"{len(slow_movers)/len(heatmap_data)*100:.1f}% of total")
            
            # Stock Level Trend Simulation Feature (14)
            st.markdown("---")
            st.subheader("📈 Stock Level Trend Projection")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                selected_item_trend = st.selectbox(
                    "🏷️ Select Item for Trend Analysis",
                    heatmap_data['ITEM_NAME'].unique()[:20]
                )
            with col2:
                projection_days = st.slider("📅 Projection Days", 7, 90, 30)
            
            if selected_item_trend:
                item_data = heatmap_data[heatmap_data['ITEM_NAME'] == selected_item_trend].iloc[0]
                current_stock = float(pd.to_numeric(item_data['CURRENT_STOCK'], errors='coerce') or 0)
                daily_consumption = float(pd.to_numeric(item_data['AVG_DAILY_ISSUE'], errors='coerce') or 0)
                
                # Generate projection
                days = list(range(projection_days + 1))
                projected_stock = [max(0, current_stock - (daily_consumption * day)) for day in days]
                
                fig_trend = px.line(
                    x=days,
                    y=projected_stock,
                    title=f"📊 {selected_item_trend} - Stock Projection",
                    labels={'x': 'Days from Now', 'y': 'Projected Stock Level'}
                )
                fig_trend.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Stockout")
                fig_trend.update_layout(height=350)
                st.plotly_chart(fig_trend, use_container_width=True)
                
                stockout_day = int(current_stock / daily_consumption) if daily_consumption > 0 else 999
                if stockout_day <= projection_days:
                    st.warning(f"⚠️ Projected stockout in **{stockout_day} days**")
                else:
                    st.success(f"✅ Stock sufficient for next **{projection_days}+ days**")
        else:
            st.info("🔍 No data available for selected filters.")
    
    with tab5:
        st.subheader("💰 Cost Insights & Savings Analysis")
        reorders = get_reorder_recommendations()
        
        if not reorders.empty:
            total_value, savings, stockout_prevention = calculate_cost_savings(reorders)
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💵 Total Reorder Cost", f"${total_value:,.2f}")
            with col2:
                st.metric("💰 Potential Savings", f"${savings:,.2f}", delta="15% optimization")
            with col3:
                st.metric("🛡️ Stockout Prevention", f"${stockout_prevention:,.2f}")
            with col4:
                net_benefit = savings + stockout_prevention
                st.metric("✨ Total Net Benefit", f"${net_benefit:,.2f}", delta_color="normal")
            
            st.markdown("---")
            
            # Cost breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Cost Breakdown by Category")
                category_costs = reorders.groupby('ITEM_CATEGORY')['ESTIMATED_ORDER_VALUE'].sum().reset_index()
                category_costs['ESTIMATED_ORDER_VALUE'] = category_costs['ESTIMATED_ORDER_VALUE'].astype(float)
                fig = px.pie(
                    category_costs,
                    values='ESTIMATED_ORDER_VALUE',
                    names='ITEM_CATEGORY',
                    title="Reorder Value by Category",
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                if st.session_state.dark_mode:
                    fig.update_layout(
                        template='plotly_dark',
                        paper_bgcolor='#1e293b',
                        plot_bgcolor='#1e293b',
                        font=dict(color='#e2e8f0')
                    )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("🏥 Cost Distribution by Location")
                location_costs = reorders.groupby('LOCATION_NAME')['ESTIMATED_ORDER_VALUE'].sum().reset_index()
                location_costs['ESTIMATED_ORDER_VALUE'] = location_costs['ESTIMATED_ORDER_VALUE'].astype(float)
                location_costs = location_costs.sort_values('ESTIMATED_ORDER_VALUE', ascending=True)
                fig2 = px.bar(
                    location_costs,
                    x='ESTIMATED_ORDER_VALUE',
                    y='LOCATION_NAME',
                    orientation='h',
                    title="Reorder Value by Location",
                    color='ESTIMATED_ORDER_VALUE',
                    color_continuous_scale='Blues'
                )
                if st.session_state.dark_mode:
                    fig2.update_layout(
                        template='plotly_dark',
                        paper_bgcolor='#1e293b',
                        plot_bgcolor='#1e293b',
                        font=dict(color='#e2e8f0')
                    )
                st.plotly_chart(fig2, use_container_width=True)
            
            # ROI Analysis
            st.subheader("📈 Return on Investment (ROI) Analysis")
            roi_percentage = ((savings + stockout_prevention) / total_value * 100) if total_value > 0 else 0
            
            # Conditional styling for ROI badges
            if st.session_state.dark_mode:
                roi_bg = "linear-gradient(135deg, #14532d, #166534)"
                roi_num_color = "#86efac"
                roi_text_color = "#bbf7d0"
                
                avg_bg = "linear-gradient(135deg, #1e3a8a, #1e40af)"
                avg_num_color = "#93c5fd"
                avg_text_color = "#bfdbfe"
                
                critical_bg = "linear-gradient(135deg, #7f1d1d, #991b1b)"
                critical_num_color = "#fca5a5"
                critical_text_color = "#fecaca"
            else:
                roi_bg = "linear-gradient(135deg, #d1fae5, #ecfdf5)"
                roi_num_color = "#065f46"
                roi_text_color = "#10b981"
                
                avg_bg = "linear-gradient(135deg, #dbeafe, #eff6ff)"
                avg_num_color = "#1e3a8a"
                avg_text_color = "#3b82f6"
                
                critical_bg = "linear-gradient(135deg, #fecaca, #fee2e2)"
                critical_num_color = "#991b1b"
                critical_text_color = "#dc2626"
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style="text-align: center; padding: 1.5rem; background: {roi_bg}; border-radius: 12px;">
                    <div style="font-size: 2rem; color: {roi_num_color}; font-weight: bold;">{roi_percentage:.1f}%</div>
                    <div style="color: {roi_text_color}; font-weight: 600;">Expected ROI</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                avg_reorder = total_value / len(reorders) if len(reorders) > 0 else 0
                st.markdown(f"""
                <div style="text-align: center; padding: 1.5rem; background: {avg_bg}; border-radius: 12px;">
                    <div style="font-size: 2rem; color: {avg_num_color}; font-weight: bold;">${avg_reorder:,.0f}</div>
                    <div style="color: {avg_text_color}; font-weight: 600;">Avg Order Value</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                critical_value = float(reorders[reorders['IS_CRITICAL_ITEM'] == True]['ESTIMATED_ORDER_VALUE'].sum())
                st.markdown(f"""
                <div style="text-align: center; padding: 1.5rem; background: {critical_bg}; border-radius: 12px;">
                    <div style="font-size: 2rem; color: {critical_num_color}; font-weight: bold;">${critical_value:,.0f}</div>
                    <div style="color: {critical_text_color}; font-weight: 600;">Critical Items</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Insights
            st.markdown("---")
            st.subheader("💡 AI-Powered Insights")
            
            insights = []
            if roi_percentage > 20:
                insights.append("✅ **Excellent ROI**: Expected returns exceed 20%, indicating highly efficient inventory management.")
            elif roi_percentage > 10:
                insights.append("⚠️ **Good ROI**: Returns are positive but there's room for optimization.")
            else:
                insights.append("🔴 **Action Required**: Consider reviewing procurement strategies to improve ROI.")
            
            if total_value > 0 and critical_value / total_value > 0.3:
                insights.append("🔴 **High Critical Spend**: Over 30% of reorder budget is for critical items. Consider increasing safety stock.")
            
            top_category = category_costs.nlargest(1, 'ESTIMATED_ORDER_VALUE')['ITEM_CATEGORY'].values[0]
            insights.append(f"📦 **Top Category**: {top_category} requires the highest reorder investment.")
            
            for insight in insights:
                st.info(insight)
            
            # Inventory Turnover Analysis Feature (15)
            st.markdown("---")
            st.subheader("🔄 Inventory Turnover Metrics")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_daily_value = total_value / 30 if total_value > 0 else 0
                st.metric("💵 Avg Daily Investment", f"${avg_daily_value:,.0f}")
            
            with col2:
                turnover_rate = len(reorders) / summary['TOTAL_ITEMS'] * 100 if summary and summary['TOTAL_ITEMS'] > 0 else 0
                st.metric("🔁 Turnover Rate", f"{turnover_rate:.1f}%")
            
            with col3:
                efficiency_score = (100 - turnover_rate) if turnover_rate < 100 else 0
                st.metric("⭐ Efficiency Score", f"{efficiency_score:.0f}/100")
            
            # Stock Transfer Recommendations Feature (16)
            st.markdown("---")
            st.subheader("🚚 Stock Transfer Suggestions")
            
            heatmap_all = get_stock_heatmap(None, None, None)
            if not heatmap_all.empty:
                st.markdown("**📦 Recommended Transfers to Balance Stock**")
                
                # Find overstocked and understocked locations for same items
                item_groups = heatmap_all.groupby('ITEM_NAME')
                transfer_suggestions = []
                
                for item_name, group in item_groups:
                    if len(group) > 1:
                        overstock = group[group['RISK_CLASSIFICATION'] == 'OVERSTOCK']
                        critical = group[group['RISK_CLASSIFICATION'].isin(['CRITICAL', 'OUT_OF_STOCK'])]
                        
                        if not overstock.empty and not critical.empty:
                            for _, over_loc in overstock.iterrows():
                                for _, crit_loc in critical.iterrows():
                                    over_stock_qty = float(pd.to_numeric(over_loc['CURRENT_STOCK'], errors='coerce') or 0)
                                    crit_consumption = float(pd.to_numeric(crit_loc['AVG_DAILY_ISSUE'], errors='coerce') or 0)
                                    transfer_qty = min(over_stock_qty * 0.3, crit_consumption * 14)
                                    if transfer_qty > 0:
                                        transfer_suggestions.append({
                                            'Item': item_name,
                                            'From': over_loc['LOCATION_NAME'],
                                            'To': crit_loc['LOCATION_NAME'],
                                            'Qty': f"{transfer_qty:.0f}",
                                            'Priority': 'High' if crit_loc['RISK_CLASSIFICATION'] == 'OUT_OF_STOCK' else 'Medium'
                                        })
                
                if transfer_suggestions:
                    transfer_df = pd.DataFrame(transfer_suggestions[:10])
                    st.dataframe(transfer_df, use_container_width=True, hide_index=True)
                    
                    csv_transfer = transfer_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Transfer Plan",
                        csv_transfer,
                        "transfer_recommendations.csv",
                        "text/csv"
                    )
                else:
                    st.success("✅ No urgent transfers needed - stock is well balanced!")
            else:
                st.info("🔍 No data available for transfer analysis")
        else:
            st.info("📋 No cost data available at this time.")
    
    with tab6:
        st.subheader("🏆 Top & Bottom Performers")
        heatmap_data = get_stock_heatmap(None, None, None)
        
        if not heatmap_data.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🌟 Top Performers")
                
                # Convert numeric columns
                heatmap_data['STOCK_HEALTH_SCORE'] = pd.to_numeric(heatmap_data['STOCK_HEALTH_SCORE'], errors='coerce').fillna(0)
                heatmap_data['CURRENT_STOCK'] = pd.to_numeric(heatmap_data['CURRENT_STOCK'], errors='coerce').fillna(0)
                
                # Best locations by health score
                st.markdown("**🏥 Healthiest Locations**")
                top_locations = heatmap_data.groupby('LOCATION_NAME')['STOCK_HEALTH_SCORE'].mean().nlargest(5).reset_index()
                for idx, loc in top_locations.iterrows():
                    st.success(f"{idx+1}. **{loc['LOCATION_NAME']}**: {loc['STOCK_HEALTH_SCORE']:.1f}/100")
                
                st.markdown("")
                
                # Best managed items
                st.markdown("**✅ Best Managed Items**")
                top_items = heatmap_data[heatmap_data['RISK_CLASSIFICATION'] == 'HEALTHY'].nlargest(5, 'STOCK_HEALTH_SCORE')[['ITEM_NAME', 'LOCATION_NAME', 'STOCK_HEALTH_SCORE']]
                for idx, item in top_items.iterrows():
                    st.success(f"• **{item['ITEM_NAME']}** at {item['LOCATION_NAME']}: {item['STOCK_HEALTH_SCORE']:.1f}/100")
                
                st.markdown("")
                
                # Optimal stock coverage
                st.markdown("**📊 Optimal Stock Coverage**")
                heatmap_data['DAYS_OF_COVER'] = pd.to_numeric(heatmap_data['DAYS_OF_COVER'], errors='coerce').fillna(0)
                optimal_coverage = heatmap_data[(heatmap_data['DAYS_OF_COVER'] >= 30) & (heatmap_data['DAYS_OF_COVER'] <= 90)].nlargest(5, 'DAYS_OF_COVER')[['ITEM_NAME', 'LOCATION_NAME', 'DAYS_OF_COVER']]
                for idx, item in optimal_coverage.iterrows():
                    st.info(f"• **{item['ITEM_NAME']}** at {item['LOCATION_NAME']}: {item['DAYS_OF_COVER']:.0f} days")
            
            with col2:
                st.markdown("### ⚠️ Needs Attention")
                
                # Worst locations by health score
                st.markdown("**🚨 Locations Needing Support**")
                bottom_locations = heatmap_data.groupby('LOCATION_NAME')['STOCK_HEALTH_SCORE'].mean().nsmallest(5).reset_index()
                for idx, loc in bottom_locations.iterrows():
                    st.error(f"{idx+1}. **{loc['LOCATION_NAME']}**: {loc['STOCK_HEALTH_SCORE']:.1f}/100")
                
                st.markdown("")
                
                # Critical items
                st.markdown("**🔴 Most Critical Items**")
                critical_items = heatmap_data[heatmap_data['RISK_CLASSIFICATION'].isin(['CRITICAL', 'OUT_OF_STOCK'])].nsmallest(5, 'STOCK_HEALTH_SCORE')[['ITEM_NAME', 'LOCATION_NAME', 'CURRENT_STOCK']]
                for idx, item in critical_items.iterrows():
                    st.error(f"• **{item['ITEM_NAME']}** at {item['LOCATION_NAME']}: {item['CURRENT_STOCK']:.0f} units")
                
                st.markdown("")
                
                # Overstock issues
                st.markdown("**📦 Overstock Situations**")
                heatmap_data['DAYS_OF_COVER'] = pd.to_numeric(heatmap_data['DAYS_OF_COVER'], errors='coerce').fillna(0)
                overstock = heatmap_data[heatmap_data['RISK_CLASSIFICATION'] == 'OVERSTOCK'].nlargest(5, 'DAYS_OF_COVER')[['ITEM_NAME', 'LOCATION_NAME', 'DAYS_OF_COVER']]
                if not overstock.empty:
                    for idx, item in overstock.iterrows():
                        st.warning(f"• **{item['ITEM_NAME']}** at {item['LOCATION_NAME']}: {item['DAYS_OF_COVER']:.0f} days")
                else:
                    st.success("✅ No overstock issues!")
            
            # Summary statistics
            st.markdown("---")
            st.subheader("📊 Overall Performance Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                healthy_pct = len(heatmap_data[heatmap_data['RISK_CLASSIFICATION'] == 'HEALTHY']) / len(heatmap_data) * 100
                st.metric("✅ Healthy Rate", f"{healthy_pct:.1f}%")
            
            with col2:
                critical_pct = len(heatmap_data[heatmap_data['RISK_CLASSIFICATION'].isin(['CRITICAL', 'OUT_OF_STOCK'])]) / len(heatmap_data) * 100
                st.metric("🔴 Critical Rate", f"{critical_pct:.1f}%", delta=f"-{critical_pct:.1f}%", delta_color="inverse")
            
            with col3:
                avg_coverage = heatmap_data['DAYS_OF_COVER'].mean()
                st.metric("📊 Avg Coverage", f"{avg_coverage:.0f} days")
            
            with col4:
                total_locations = heatmap_data['LOCATION_NAME'].nunique()
                st.metric("🏥 Active Locations", total_locations)
        else:
            st.info("🔍 No data available for performance analysis.")
        
        # What-If Scenario Simulator Feature (17)
        st.markdown("---")
        st.subheader("🧪 What-If Scenario Simulator")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🎯 Adjust Parameters**")
            demand_change = st.slider("📈 Demand Change", -50, 100, 0, help="% change in consumption")
            lead_time_change = st.slider("🚚 Lead Time Change", -50, 100, 0, help="% change in delivery time")
            budget_factor = st.slider("💰 Budget Adjustment", 50, 200, 100, help="% of current budget")
        
        with col2:
            st.markdown("**📊 Simulation Results**")
            
            if not heatmap_data.empty:
                base_critical = len(heatmap_data[heatmap_data['RISK_CLASSIFICATION'].isin(['CRITICAL', 'OUT_OF_STOCK'])])
                
                # Simulate impact
                demand_factor = 1 + (demand_change / 100)
                simulated_critical = int(base_critical * demand_factor)
                
                st.metric(
                    "🚨 Projected Critical Items",
                    simulated_critical,
                    delta=f"{simulated_critical - base_critical:+d}",
                    delta_color="inverse"
                )
                
                simulated_stockouts = int(simulated_critical * (1 + lead_time_change / 100))
                st.metric(
                    "⚠️ Potential Stockouts",
                    simulated_stockouts,
                    delta=f"{simulated_stockouts - base_critical:+d}",
                    delta_color="inverse"
                )
                
                budget_needed = (budget_factor / 100) * float(get_reorder_recommendations()['ESTIMATED_ORDER_VALUE'].sum())
                st.metric("💵 Budget Required", f"${budget_needed:,.0f}")
        
        # Smart Recommendations Engine Feature (18)
        st.markdown("---")
        st.subheader("🤖 AI Smart Recommendations")
        
        recommendations = []
        
        if not heatmap_data.empty:
            critical_rate = len(heatmap_data[heatmap_data['RISK_CLASSIFICATION'].isin(['CRITICAL', 'OUT_OF_STOCK'])]) / len(heatmap_data)
            overstock_rate = len(heatmap_data[heatmap_data['RISK_CLASSIFICATION'] == 'OVERSTOCK']) / len(heatmap_data)
            
            if critical_rate > 0.15:
                recommendations.append({
                    'priority': '🔴 High',
                    'action': 'Increase Safety Stock',
                    'reason': f'{critical_rate*100:.1f}% items at risk',
                    'impact': 'Reduce stockout risk by 40%'
                })
            
            if overstock_rate > 0.20:
                recommendations.append({
                    'priority': '🟡 Medium',
                    'action': 'Optimize Reorder Quantities',
                    'reason': f'{overstock_rate*100:.1f}% items overstocked',
                    'impact': 'Free up $5K-10K in working capital'
                })
            
            slow_movers = heatmap_data[heatmap_data['AVG_DAILY_ISSUE'] < 0.5]
            if len(slow_movers) > 10:
                recommendations.append({
                    'priority': '🟠 Low',
                    'action': 'Review Slow-Moving Items',
                    'reason': f'{len(slow_movers)} slow movers identified',
                    'impact': 'Reduce holding costs by 15%'
                })
            
            # Location-specific recommendations
            location_health = heatmap_data.groupby('LOCATION_NAME')['STOCK_HEALTH_SCORE'].mean()
            worst_location = location_health.idxmin()
            worst_score = location_health.min()
            
            if worst_score < 60:
                recommendations.append({
                    'priority': '🔴 High',
                    'action': f'Priority Support for {worst_location}',
                    'reason': f'Health score: {worst_score:.1f}/100',
                    'impact': 'Improve overall system health by 8%'
                })
            
            # Top performers to replicate
            best_location = location_health.idxmax()
            best_score = location_health.max()
            
            recommendations.append({
                'priority': '⭐ Strategic',
                'action': f'Replicate Best Practices from {best_location}',
                'reason': f'Health score: {best_score:.1f}/100',
                'impact': 'System-wide efficiency improvement'
            })
        
        if recommendations:
            for rec in recommendations:
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
                    with col1:
                        st.markdown(f"**{rec['priority']}**")
                    with col2:
                        st.markdown(f"**{rec['action']}**")
                    with col3:
                        st.caption(rec['reason'])
                    with col4:
                        st.caption(f"✅ {rec['impact']}")
                    st.markdown("")
        else:
            st.success("✅ All systems operating optimally!")
        
        # Export with Advanced Formatting Feature (19)
        st.markdown("---")
        st.subheader("📊 Advanced Export Options")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Executive Summary Report", use_container_width=True):
                summary = get_executive_summary()
                if summary:
                    summary_data = pd.DataFrame([summary])
                    csv = summary_data.to_csv(index=False)
                    st.download_button(
                        "📥 Download Summary",
                        csv,
                        f"executive_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv"
                    )
        
        with col2:
            if st.button("🚨 Critical Items Report", use_container_width=True):
                critical_data = heatmap_data[heatmap_data['RISK_CLASSIFICATION'].isin(['CRITICAL', 'OUT_OF_STOCK'])]
                if not critical_data.empty:
                    csv = critical_data.to_csv(index=False)
                    st.download_button(
                        "📥 Download Critical Items",
                        csv,
                        f"critical_items_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv"
                    )
        
        with col3:
            if st.button("🎯 Performance Metrics", use_container_width=True):
                location_perf = heatmap_data.groupby('LOCATION_NAME').agg({
                    'STOCK_HEALTH_SCORE': 'mean',
                    'ITEM_NAME': 'count',
                    'REQUIRES_ATTENTION': 'sum'
                }).round(2)
                csv = location_perf.to_csv()
                st.download_button(
                    "📥 Download Performance",
                    csv,
                    f"location_performance_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption("© 2026 StockPulse AI - Powered by Snowflake | Real-time Inventory Intelligence")
    with col2:
        st.caption(f"⏰ Data as of: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with col3:
        st.caption("🏥 AI for Good Initiative")

if __name__ == "__main__":
    main()
