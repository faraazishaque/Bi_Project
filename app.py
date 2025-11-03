import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import os

# --- 1. CONFIGURATION AND STYLING ---

st.set_page_config(
    page_title="Fusion Sales & Customer Insights",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Custom styles to enhance the professional look */
    /* Only hide the default Streamlit elements like the main menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* FIX: Removed aggressive CSS that targeted the entire header or layout containers, 
    as these were likely hiding the sidebar or forcing the main content to w-full.
    */

    /* General styling adjustments */
    div.stMetric > label { color: #7f8c8d; }
    /* Target Streamlit's main block container to adjust padding */
    .block-container { 
        padding-top: 1rem; 
        padding-bottom: 0rem; 
        padding-left: 2rem; 
        padding-right: 2rem; 
    }
    /* Style for the sidebar header/title text */
    .st-emotion-cache-12fm5qf { 
        font-weight: bold; 
        color: #2c3e50; 
    }
    /* Fix for radio button text overflow */
    .st-emotion-cache-1r6i0t9 { 
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)


# --- 2. DATA LOADING AND PROCESSING ---

def generate_mock_data(num_rows=10000):
    """Generates synthetic data if the CSV file is missing."""
    st.warning("⚠️ Data file not found. Generating mock data for demonstration.")
    
    start_date = datetime.now() - timedelta(days=120)
    
    data = {
        'order_date': [start_date + timedelta(days=np.random.randint(1, 120)) for _ in range(num_rows)],
        'customer_id': [f"CUST{i % 3000}" for i in range(num_rows)],
        'order_status': np.random.choice(['Delivered', 'Shipped', 'Cancelled', 'Processing'], num_rows, p=[0.7, 0.2, 0.05, 0.05]),
        'total_amount': np.random.randint(20, 500, num_rows) + np.random.rand(num_rows),
        'product_category': np.random.choice(['Electronics', 'Apparel', 'Home Goods', 'Sports Equipment', 'Food & Beverage'], num_rows, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
    }
    df = pd.DataFrame(data)
    df['total_amount'] = df['total_amount'].round(2)
    
    # Add a mock gross_margin column for the KPI calculations
    df['gross_margin'] = df['total_amount'] * 0.40

    return df

@st.cache_data
def load_data():
    """Loads the 10,000-row CSV file or generates mock data if missing."""
    file_path = 'ecommerce_big_data_10000.csv'
    
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            st.error(f"🚨 Error reading data file: {e}. Generating mock data instead.")
            df = generate_mock_data()
    else:
        df = generate_mock_data()

    df['order_date'] = pd.to_datetime(df['order_date'])
    
    # Filter only delivered/shipped orders for reliable sales metrics
    df_delivered = df[df['order_status'].isin(['Delivered', 'Shipped'])].copy()
    
    # Calculate Gross Margin (assuming 40% margin for demo if not present)
    if 'gross_margin' not in df_delivered.columns:
        df_delivered['gross_margin'] = df_delivered['total_amount'] * 0.40

    return df_delivered

@st.cache_data
def calculate_kpis(df):
    """Calculates all key metrics and MoM change using the new columns (Last 30 days vs Previous 30 days)."""
    
    if df.empty:
        return {}

    today = datetime.now().date()
    # Define time periods (Last 30 days vs Previous 30 days)
    current_start_date = today - timedelta(days=30)
    prev_end_date = current_start_date - timedelta(days=1)
    prev_start_date = prev_end_date - timedelta(days=30)

    df_current = df[df['order_date'].dt.date >= current_start_date]
    df_prev = df[(df['order_date'].dt.date >= prev_start_date) & (df['order_date'].dt.date <= prev_end_date)]

    def get_metrics(data):
        """Helper to calculate raw metrics for a period."""
        return {
            'revenue': data['total_amount'].sum(),
            'orders': data.shape[0],
            'customers': data['customer_id'].nunique(),
            'gross_margin': data['gross_margin'].sum()
        }

    current = get_metrics(df_current)
    previous = get_metrics(df_prev)

    def calculate_delta(current_val, prev_val):
        """Calculates percentage change."""
        # Handle zero division gracefully
        if prev_val == 0 or prev_val is None: 
            # If previous was 0 and current is > 0, treat as a large positive change
            return 100.0 if current_val > 0 else 0.0
        return ((current_val - prev_val) / prev_val) * 100

    kpis = {}
    
    # 1. Total Revenue
    rev_change = calculate_delta(current['revenue'], previous['revenue'])
    kpis['Total Revenue'] = {'value': f"${current['revenue']:,.0f}", 'delta': f"{rev_change:.1f}% vs last month"}
    
    # 2. Average Order Value (AOV)
    aov_current = current['revenue'] / current['orders'] if current['orders'] else 0
    aov_prev = previous['revenue'] / previous['orders'] if previous['orders'] else 0
    aov_change = calculate_delta(aov_current, aov_prev)
    kpis['Average Value'] = {'value': f"${aov_current:.2f}", 'delta': f"{aov_change:.1f}% vs last month"}
    
    # 3. Unique Customers
    cust_change = calculate_delta(current['customers'], previous['customers'])
    kpis['Unique Customers'] = {'value': f"{current['customers']:,}", 'delta': f"{cust_change:.1f}% vs last month"}

    # 4. Gross Margin
    gm_change = calculate_delta(current['gross_margin'], previous['gross_margin'])
    kpis['Gross Margin'] = {'value': f"${current['gross_margin']:,.0f}", 'delta': f"{gm_change:.1f}% vs last month"}

    return kpis

# --- 3. DASHBOARD RENDERING FUNCTIONS ---

def render_kpis(kpis):
    """Renders the four KPI boxes."""
    st.markdown("## Analytics Dashboard")
    st.caption(f"Showing Delivered/Shipped Sales Data | MoM comparison based on rolling 30-day periods | As of {datetime.now().strftime('%b %d, %Y')}")
    
    kpi_cols = st.columns(4)
    design_kpis = ['Total Revenue', 'Average Value', 'Unique Customers', 'Gross Margin']    
    
    for i, title in enumerate(design_kpis):
        with kpi_cols[i]:
            st.metric(
                label=title,
                value=kpis.get(title, {}).get('value', '$0'),
                # Adjusting delta to show 'vs last month' for clarity
                delta=kpis.get(title, {}).get('delta', '0.0% vs last month'),
                delta_color="normal"
            )
    st.markdown("---")


def render_charts(df):
    """Renders the Revenue Over Time and Category Breakdown charts."""
    
    col1, col2 = st.columns([3, 2]) # 60/40 column split

    # --- Revenue Over Time (Line Chart) ---
    with col1:
        st.subheader("Revenue Over Time (Last 90 Days)")
        
        # Filter for the last 90 days for chart visibility
        n_days_ago = datetime.now().date() - timedelta(days=90)
        df_chart = df[df['order_date'].dt.date >= n_days_ago].copy()
        
        # Aggregate data by day
        revenue_over_time = df_chart.groupby(df_chart['order_date'].dt.date)['total_amount'].sum().reset_index()
        revenue_over_time.columns = ['Date', 'Revenue']
        
        # Check current theme (Streamlit sets its own theme, but we can try to follow it for Plotly)
        template = "plotly_white"
        # Note: st._get_config_options() is usually blocked in the Canvas environment.
        # We'll stick to a default template for consistency.

        fig_time = px.line(
            revenue_over_time, 
            x='Date', 
            y='Revenue',
            labels={'Date': 'Order Date', 'Revenue': 'Total Revenue ($)'},
            template=template,
            line_shape='spline', # Smooth the line
            color_discrete_sequence=['#3498db']
        )
        fig_time.update_traces(fill='tozeroy', opacity=0.3)
        fig_time.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_time, use_container_width=True)

    # --- Category Breakdown (Bar Chart) ---
    with col2:
        st.subheader("Category Breakdown (Revenue)")
        
        # Aggregate data by category and calculate percentage
        category_breakdown = df.groupby('product_category')['total_amount'].sum().reset_index()
        category_breakdown.columns = ['Category', 'Revenue']
        category_breakdown['Percentage'] = (category_breakdown['Revenue'] / category_breakdown['Revenue'].sum()) * 100
        category_breakdown = category_breakdown.sort_values(by='Revenue', ascending=False)
        
        fig_cat = px.bar(
            category_breakdown,
            x='Revenue',
            y='Category',
            orientation='h',
            text=category_breakdown['Percentage'].apply(lambda x: f'{x:.1f}%'),
            labels={'Revenue': 'Total Revenue ($)', 'Category': ''},
            template=template
        )
        fig_cat.update_traces(marker_color='#3498db', textposition='auto')
        fig_cat.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("---")

def render_ai_module():
    """Renders the 'Ask Fusion AI anything!' module."""
    st.subheader("FUSION AI - Full Analytics Assistant")
    
    ai_col, report_col = st.columns([4, 1])

    with ai_col:
        st.text_input(
            label="Ask Fusion AI anything!",
            placeholder="e.g., Explain my dashboard analytics, What are the top 5 most profitable products?",
            label_visibility="collapsed",
            key="ai_query_input"
        )
        # Placeholder logic for AI
        if st.session_state.get('ai_query_input'):
            st.info(f"AI Query received: '{st.session_state.ai_query_input}'. The AI model integration is pending.")

    with report_col:
        st.button("Generate Report", type="primary", use_container_width=True, help="Generate a PDF summary of the current dashboard view.")


# --- NEW FUNCTION FOR MAIN MENU CONTENT ---

def render_main_menu_page(page_name):
    """Renders the content for the different main menu pages."""
    st.markdown(f"## {page_name}")
    st.markdown("---")

    if page_name == "Business Overview":
        st.subheader("Executive Summary & Performance Goals 🎯")
        st.write("This overview provides a high-level summary of your business's health and its alignment with strategic goals. Use this section to monitor aggregated financial and operational success metrics.")

        # Mock Goal Setting
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Annual Revenue Goal", "$10,000,000", "+30% from Last Year")
        with col2:
            st.metric("YTD Achievement", "$3,125,000", "31% Complete")

        st.markdown("### Next 90 Days Focus")
        st.info("The primary focus is on **improving Gross Margin** by optimizing product sourcing and reducing logistical costs in the 'Electronics' category. An aggressive Q4 marketing campaign is scheduled for Apparel.")

    elif page_name == "Customers":
        st.subheader("Customer Segmentation & Lifecycle Analysis 👥")
        st.write("Understand your customer base, track lifetime value (LTV), and identify high-value segments for targeted marketing campaigns and retention efforts.")

        # Mock Customer Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg. Customer LTV", "$450.00", "+5.2% MoM")
        with col2:
            st.metric("Churn Rate (Annual)", "2.1%", "Low")
        with col3:
            st.metric("New Customers (30D)", "1,250", "Stable")

        st.markdown("### Segment Explorer")
        segment = st.selectbox("Select Segment to Analyze", ["High-Value (A+)", "Active Buyers (B)", "At-Risk (C)"])
        if segment == "High-Value (A+)":
            st.success("This segment drives **70% of total revenue**. Focus on retention and cross-selling premium products.")
        elif segment == "At-Risk (C)":
            st.error("This segment has low recent activity. Initiate a win-back campaign immediately.")
        else:
              st.warning(f"Analysis for **{segment}** segment is currently running in the background.")

    elif page_name == "Integration":
        st.subheader("Data Source & System Connections 🔗")
        st.write("Manage connections to your core e-commerce platform, ERP, and marketing automation tools. Ensure all data sources are connected and syncing correctly.")

        # Mock Integrations Status
        integrations = [
            ("Shopify Store", "Connected", "Active Sync"),
            ("SAP ERP", "Connected", "Last Sync: 1 hour ago"),
            ("Mailchimp Marketing", "Inactive", "Authentication Error")
        ]
        
        st.markdown("### Active Integrations")
        for name, status, detail in integrations:
            status_emoji = "✅" if status == "Connected" else "❌"
            if status == "Connected":
                st.success(f"{status_emoji} **{name}**: {status} - {detail}")
            elif status == "Inactive":
                st.error(f"{status_emoji} **{name}**: {status} - {detail}. **Action Required.**")

    else:
          st.info(f"The **{page_name}** module is under active development. Check back soon!")


# --- 4. NAVIGATION AND SETTINGS RENDERING ---

def initialize_state():
    """Initializes session state variables for navigation and login."""
    # NEW: State to track if the user is logged in
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False 
    
    # current_view holds the name of the page to render in the main content area
    if 'current_view' not in st.session_state:
        st.session_state['current_view'] = 'Analytics Dashboard'
    
    # settings_menu_nav tracks which setting item is selected (used for rendering the sidebar state)
    if 'settings_menu_nav' not in st.session_state:
        st.session_state['settings_menu_nav'] = 'Profile'
    
    # theme_mode is used to potentially control custom component styling
    if 'theme_mode' not in st.session_state:
        st.session_state['theme_mode'] = 'System Default'

def render_sidebar():
    """
    Renders the sidebar navigation (MAIN MENU and SETTINGS).
    Uses on_change callbacks to manage the st.session_state.current_view for routing.
    """
    
    st.sidebar.markdown("# Fusion Sales 📈")
    st.sidebar.markdown("---")

    # --- MAIN MENU ---
    st.sidebar.markdown("### MAIN MENU")
    main_menu = ["Analytics Dashboard", "Business Overview", "Customers", "Integration"]
    
    # When a main menu item is clicked, update the current_view state
    st.sidebar.radio(
        "Navigation", 
        main_menu, 
        index=main_menu.index(st.session_state.get('main_menu_nav', 'Analytics Dashboard')), 
        key="main_menu_nav", 
        label_visibility="collapsed",
        on_change=lambda: st.session_state.update(current_view=st.session_state.main_menu_nav)
    )
    
    st.sidebar.markdown("---")
    
    # --- SETTINGS MENU ---
    st.sidebar.markdown("### SETTINGS")
    settings_menu = ["Profile", "Notifications", "Security", "Appearance", "Billing"]
    
    # When a settings item is clicked, update the current_view state
    st.sidebar.radio(
        "Settings Navigation", 
        settings_menu, 
        index=settings_menu.index(st.session_state['settings_menu_nav']), 
        key="settings_menu_nav", 
        label_visibility="collapsed",
        on_change=lambda: st.session_state.update(current_view=st.session_state.settings_menu_nav)
    )
    
    st.sidebar.markdown("---")
    
    # Logout Button Logic
    if st.sidebar.button("Logout 🚪", type="secondary", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['current_view'] = 'Analytics Dashboard' # Reset view
        st.rerun()


def render_settings_page(setting_page):
    """Renders the content for the different settings pages."""
    st.markdown(f"## Settings: {setting_page}")
    st.markdown("---")
    
    if setting_page == "Security":
        st.subheader("🔒 Security Settings")
        
        st.markdown("### Two-Factor Authentication (2FA)")
        st.toggle("Enable 2FA via Authenticator App", value=True, help="Adds an extra layer of protection to your account.")
        
        st.markdown("### Session Timeout")
        timeout = st.slider("Set Inactivity Timeout (minutes)", min_value=5, max_value=120, value=30, step=5)
        st.info(f"Your session will automatically log out after **{timeout}** minutes of inactivity.")

    elif setting_page == "Billing":
        st.subheader("💳 Billing & Subscription")
        
        st.markdown("### Current Plan")
        col_plan, col_action = st.columns([3, 1])
        with col_plan:
            st.metric(label="Subscription Plan", value="Enterprise Plan", delta="Annual Billing")
            st.caption("Plan renews: Nov 3, 2026")
        with col_action:
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("Upgrade/Manage Plan", type="primary")

        st.markdown("### Payment Method")
        st.info("VISA ending in **4242** (Exp: 10/2028)")
        st.button("Change Payment Method", type="secondary")

        st.markdown("### Billing History")
        history_data = {
            'Date': ['Oct 15, 2025', 'Sep 15, 2025', 'Aug 15, 2025'],
            'Amount': ['$999.00', '$999.00', '$999.00'],
            'Status': ['Paid', 'Paid', 'Paid']
        }
        st.dataframe(pd.DataFrame(history_data), use_container_width=True, hide_index=True)

    elif setting_page == "Appearance":
        st.subheader("🎨 Appearance Settings")
        
        theme_select = st.selectbox("Preferred Theme", ["System Default", "Light Mode", "Dark Mode"], key="theme_select_key")
        
        st.session_state['theme_mode'] = theme_select

        if theme_select == "Dark Mode":
            st.info("Theme set to **Dark Mode**. Note: Streamlit uses its own configuration, but this variable is available for custom components.")
        elif theme_select == "Light Mode":
            st.info("Theme set to **Light Mode**. Note: Streamlit uses its own configuration, but this variable is available for custom components.")
        else:
              st.info("Theme set to **System Default**.")


    elif setting_page == "Profile":
        st.subheader("👤 User Profile")
        st.text_input("Full Name", value="Mohammed Faraaz")
        st.text_input("Email Address", value="mdfaraaz@fusionanalytics.com", disabled=True)
        st.date_input("Date of Birth", value=datetime(2004, 5, 23))
        st.button("Save Profile", type="primary")

    elif setting_page == "Notifications":
        st.subheader("🔔 Notification Preferences")
        st.toggle("Email Notifications for Alerts", value=True)
        st.toggle("In-App Notifications for Sales Trends", value=True)
        st.slider("Minimum Revenue Threshold for Alerts ($)", min_value=1000, max_value=50000, value=5000)
    
    else:
        st.info(f"Content for **{setting_page}** module is under development.")


# --- NEW LOGIN PAGE IMPLEMENTATION ---

def render_login_page():
    """Renders the simple login page."""
    
    # Hide the sidebar for the login page
    # IMPORTANT: The sidebar is implicitly hidden by Streamlit when st.sidebar is not called, 
    # but we can also use an empty container if needed, though usually not necessary for a full page override.

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("Fusion Sales Dashboard")
        st.markdown("## Secure Sign In 🔐")
        st.markdown("---")
        
        # Hardcoded credentials for demo purpose
        USERNAME = "admin"
        PASSWORD = "password123" 
        
        # Form for input
        with st.form("login_form"):
            st.markdown("Enter your credentials to access the analytics.")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submitted:
                if username == USERNAME and password == PASSWORD:
                    st.session_state['logged_in'] = True
                    st.success("Login successful! Redirecting to dashboard...")
                    st.rerun() # Rerun to switch to the main dashboard
                else:
                    st.error("Invalid username or password.")
                    

# --- 5. MAIN APPLICATION ENTRY POINT ---

def main():
    """Main function to run the Streamlit application."""
    
    # 1. Initialize session state
    initialize_state()
    
    # 2. Check Login Status
    if not st.session_state['logged_in']:
        render_login_page()
        return
    
    # --- REMAINDER OF ORIGINAL MAIN FUNCTION ONLY RUNS IF LOGGED IN ---

    # 3. Render sidebar
    render_sidebar()
    
    # 4. Get the active page from the unified state variable
    active_page = st.session_state.get('current_view', 'Analytics Dashboard')
    
    # 5. Page Routing based on active_page
    if active_page == "Analytics Dashboard":
        # Load the large dataset
        df_sales = load_data() 
        if df_sales.empty:
            st.error("Data could not be loaded or generated.")
            return # Exit if data loading failed
        
        # Render the core dashboard
        kpis = calculate_kpis(df_sales)
        render_kpis(kpis)
        render_charts(df_sales)
        render_ai_module()

    elif active_page in ["Profile", "Notifications", "Security", "Appearance", "Billing"]:
        # Render the settings sub-page 
        render_settings_page(active_page)
        
    else:
        # Render the richer placeholder for other MAIN MENU items
        render_main_menu_page(active_page)


if __name__ == "__main__":
    main()
