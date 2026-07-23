import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

from data_loader import (
    load_csv, load_excel, validate_sales_data,
    standardize_columns, generate_sample_data
)

# Page configuration
st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
# Custom CSS
st.markdown("""
<style>

/* Dashboard Background */
.stApp{
    background-color:#0E1117;
}

/* KPI Cards */
div[data-testid="stMetric"]{
    background:linear-gradient(135deg,#1E293B,#111827);
    border:1px solid #374151;
    border-left:6px solid #00C896;
    border-radius:16px;
    padding:20px;
    box-shadow:0px 4px 15px rgba(0,0,0,0.3);
}

/* KPI Label */
div[data-testid="stMetricLabel"]{
    color:#D1D5DB !important;
    font-size:18px !important;
    font-weight:600 !important;
}

/* KPI Value */
div[data-testid="stMetricValue"]{
    color:#FFFFFF !important;
    font-size:36px !important;
    font-weight:700 !important;
}

/* KPI Delta */
div[data-testid="stMetricDelta"]{
    font-size:18px !important;
    font-weight:bold !important;
}

/* Sidebar */
section[data-testid="stSidebar"]{
    background:#1E293B;
}

/* Buttons */
.stButton>button{
    border-radius:10px;
}

</style>
""", unsafe_allow_html=True)


def load_data() -> pd.DataFrame | None:
    """Handle data loading from various sources."""
    
    st.sidebar.header("📁 Data Source")
    
    data_source = st.sidebar.radio(
        "Select data source:",
        ["Upload File", "Sample Data", "Database Connection"]
    )
    
    df = None
    
    if data_source == "Upload File":
        uploaded_file = st.sidebar.file_uploader(
            "Upload CSV or Excel",
            type=['csv', 'xlsx', 'xls']
        )
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = load_csv(uploaded_file)
                else:
                    df = load_excel(uploaded_file)
                
                df = standardize_columns(df)
                is_valid, missing = validate_sales_data(df)
                
                if not is_valid:
                    st.sidebar.error(f"Missing columns: {', '.join(missing)}")
                    st.sidebar.info("Required: date, product, quantity, revenue")
                    return None
                    
            except Exception as e:
                st.sidebar.error(f"Error loading file: {e}")
                return None
    
    elif data_source == "Sample Data":
        n_rows = st.sidebar.slider("Sample size", 500, 5000, 1000, 500)
        df = generate_sample_data(n_rows)
        st.sidebar.success(f"✓ Loaded {n_rows} sample records")
    
    elif data_source == "Database Connection":
        st.sidebar.text_input("Connection string", type="password", key="db_conn")
        st.sidebar.text_area("SQL Query", "SELECT * FROM sales", key="db_query")
        
        if st.sidebar.button("Connect"):
            st.sidebar.warning("Database connection requires valid credentials")
    
    return df


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply sidebar filters to the dataframe."""
    
    st.sidebar.header("🔍 Filters")
    
    # Date range filter
    if 'date' in df.columns:
        min_date = df['date'].min()
        max_date = df['date'].max()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            df = df[
                (df['date'] >= pd.to_datetime(date_range[0])) &
                (df['date'] <= pd.to_datetime(date_range[1]))
            ]
    
    # Product filter
    if 'product' in df.columns:
        products = ['All'] + sorted(df['product'].unique().tolist())
        selected_products = st.sidebar.multiselect(
            "Products",
            products,
            default=['All']
        )
        
        if 'All' not in selected_products and selected_products:
            df = df[df['product'].isin(selected_products)]
    
    # Category filter
    if 'category' in df.columns:
        categories = ['All'] + sorted(df['category'].unique().tolist())
        selected_categories = st.sidebar.multiselect(
            "Categories",
            categories,
            default=['All']
        )
        
        if 'All' not in selected_categories and selected_categories:
            df = df[df['category'].isin(selected_categories)]
    
    # Region filter
    if 'region' in df.columns:
        regions = ['All'] + sorted(df['region'].unique().tolist())
        selected_regions = st.sidebar.multiselect(
            "Regions",
            regions,
            default=['All']
        )
        
        if 'All' not in selected_regions and selected_regions:
            df = df[df['region'].isin(selected_regions)]
    
    return df


def calculate_kpis(df: pd.DataFrame) -> dict:
    """Calculate key performance indicators."""
    
    total_revenue = df['revenue'].sum()
    total_quantity = df['quantity'].sum()
    avg_order_value = df['revenue'].mean()
    total_transactions = len(df)
    
    # Calculate growth (comparing first half vs second half of date range)
    if 'date' in df.columns and len(df) > 1:
        mid_date = df['date'].min() + (df['date'].max() - df['date'].min()) / 2
        first_half = df[df['date'] < mid_date]['revenue'].sum()
        second_half = df[df['date'] >= mid_date]['revenue'].sum()
        
        if first_half > 0:
            growth_rate = ((second_half - first_half) / first_half) * 100
        else:
            growth_rate = 0
    else:
        growth_rate = 0
    
    return {
        'total_revenue': total_revenue,
        'total_quantity': total_quantity,
        'avg_order_value': avg_order_value,
        'total_transactions': total_transactions,
        'growth_rate': growth_rate
    }


def display_kpis(kpis: dict):
    """Display KPI metrics in cards."""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Total Revenue",
            f"${kpis['total_revenue']:,.2f}",
            delta=f"{kpis['growth_rate']:.1f}% period growth"
        )
    
    with col2:
        st.metric(
            "📦 Units Sold",
            f"{kpis['total_quantity']:,}"
        )
    
    with col3:
        st.metric(
            "🧾 Avg Order Value",
            f"${kpis['avg_order_value']:,.2f}"
        )
    
    with col4:
        st.metric(
            "🛒 Transactions",
            f"{kpis['total_transactions']:,}"
        )


def plot_revenue_trend(df: pd.DataFrame):
    """Create revenue trend line chart."""
    
    daily_revenue = df.groupby('date')['revenue'].sum().reset_index()
    
    # Add moving average
    daily_revenue['ma_7'] = daily_revenue['revenue'].rolling(7).mean()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_revenue['date'],
        y=daily_revenue['revenue'],
        mode='lines',
        name='Daily Revenue',
        line=dict(color='#667eea', width=1),
        opacity=0.7
    ))
    
    fig.add_trace(go.Scatter(
        x=daily_revenue['date'],
        y=daily_revenue['ma_7'],
        mode='lines',
        name='7-Day Average',
        line=dict(color='#f56565', width=2)
    ))
    
    fig.update_layout(
        title='Revenue Trend Over Time',
        xaxis_title='Date',
        yaxis_title='Revenue ($)',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    return fig


def plot_top_products(df: pd.DataFrame, top_n: int = 10):
    """Create top products bar chart."""
    
    product_revenue = df.groupby('product').agg({
        'revenue': 'sum',
        'quantity': 'sum'
    }).reset_index()
    
    product_revenue = product_revenue.nlargest(top_n, 'revenue')
    
    fig = px.bar(
        product_revenue,
        x='revenue',
        y='product',
        orientation='h',
        title=f'Top {top_n} Products by Revenue',
        labels={'revenue': 'Revenue ($)', 'product': 'Product'},
        color='revenue',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    fig.update_coloraxes(showscale=False)
    
    return fig


def plot_category_distribution(df: pd.DataFrame):
    """Create category distribution pie chart."""
    
    if 'category' not in df.columns:
        return None
    
    category_revenue = df.groupby('category')['revenue'].sum().reset_index()
    
    fig = px.pie(
        category_revenue,
        values='revenue',
        names='category',
        title='Revenue by Category',
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig


def plot_regional_performance(df: pd.DataFrame):
    """Create regional performance bar chart."""
    
    if 'region' not in df.columns:
        return None
    
    region_data = df.groupby('region').agg({
        'revenue': 'sum',
        'quantity': 'sum'
    }).reset_index()
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=region_data['region'],
            y=region_data['revenue'],
            name='Revenue',
            marker_color='#667eea'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=region_data['region'],
            y=region_data['quantity'],
            name='Units Sold',
            mode='lines+markers',
            marker_color='#f56565',
            line=dict(width=3)
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title='Regional Performance',
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    fig.update_yaxes(title_text='Revenue ($)', secondary_y=False)
    fig.update_yaxes(title_text='Units Sold', secondary_y=True)
    
    return fig


def plot_monthly_heatmap(df: pd.DataFrame):
    """Create monthly sales heatmap."""
    
    df_temp = df.copy()
    df_temp['month'] = df_temp['date'].dt.month_name()
    df_temp['day_of_week'] = df_temp['date'].dt.day_name()
    
    heatmap_data = df_temp.pivot_table(
        values='revenue',
        index='day_of_week',
        columns='month',
        aggfunc='sum'
    )
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(day_order)
    
    fig = px.imshow(
        heatmap_data,
        title='Revenue Heatmap: Day of Week vs Month',
        labels=dict(x='Month', y='Day of Week', color='Revenue'),
        color_continuous_scale='RdYlGn',
        aspect='auto'
    )
    
    return fig


def display_data_table(df: pd.DataFrame):
    """Display interactive data table."""
    
    st.subheader("📋 Detailed Data")
    
    # Column selector
    all_columns = df.columns.tolist()
    selected_columns = st.multiselect(
        "Select columns to display:",
        all_columns,
        default=all_columns[:6]
    )
    
    if selected_columns:
        st.dataframe(
            df[selected_columns].head(100),
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv = df[selected_columns].to_csv(index=False)
        st.download_button(
            "📥 Download Filtered Data",
            csv,
            "filtered_sales_data.csv",
            "text/csv"
        )


def main():
    """Main application entry point."""
    
    st.title("📊 Sales & Revenue Dashboard")
    st.markdown("---")
    
    # Load data
    df = load_data()
    
    if df is None or df.empty:
        st.info("👈 Upload a file or select 'Sample Data' to get started.")
        
        st.markdown("""
        ### Expected Data Format
        
        Your data should include these columns:
        
        | Column | Description | Example |
        |--------|-------------|---------|
        | date | Transaction date | 2024-01-15 |
        | product | Product name | Laptop |
        | quantity | Units sold | 5 |
        | revenue | Total sale amount | 4995.00 |
        | category | Product category (optional) | Electronics |
        | region | Sales region (optional) | North |
        """)
        return
    
    # Apply filters
    filtered_df = apply_filters(df)
    
    if filtered_df.empty:
        st.warning("No data matches the selected filters.")
        return
    
    # Calculate and display KPIs
    kpis = calculate_kpis(filtered_df)
    display_kpis(kpis)
    
    st.markdown("---")
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(plot_revenue_trend(filtered_df), use_container_width=True)
    
    with col2:
        st.plotly_chart(plot_top_products(filtered_df), use_container_width=True)
    
    # Charts row 2
    col3, col4 = st.columns(2)
    
    with col3:
        category_fig = plot_category_distribution(filtered_df)
        if category_fig:
            st.plotly_chart(category_fig, use_container_width=True)
    
    with col4:
        region_fig = plot_regional_performance(filtered_df)
        if region_fig:
            st.plotly_chart(region_fig, use_container_width=True)
    
    # Heatmap (full width)
    st.plotly_chart(plot_monthly_heatmap(filtered_df), use_container_width=True)
    
    st.markdown("---")
    
    # Data table
    display_data_table(filtered_df)


if __name__ == "__main__":
    main()
