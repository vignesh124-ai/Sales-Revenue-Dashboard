"""Data loading utilities for various sources."""

import pandas as pd
from sqlalchemy import create_engine
from typing import Optional


def load_csv(file) -> pd.DataFrame:
    """Load data from CSV file."""
    return pd.read_csv(file, parse_dates=True)


def load_excel(file, sheet_name: str = 0) -> pd.DataFrame:
    """Load data from Excel file."""
    return pd.read_excel(file, sheet_name=sheet_name, parse_dates=True)


def load_from_database(
    connection_string: str,
    query: str
) -> pd.DataFrame:
    """Load data from SQL database."""
    engine = create_engine(connection_string)
    return pd.read_sql(query, engine)


def validate_sales_data(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Validate that dataframe has required columns for sales analysis.
    Returns (is_valid, list of missing columns).
    """
    required_columns = {'date', 'product', 'quantity', 'revenue'}
    df_columns = set(col.lower().strip() for col in df.columns)
    
    missing = required_columns - df_columns
    return len(missing) == 0, list(missing)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to lowercase."""
    df.columns = df.columns.str.lower().str.strip()
    
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Ensure numeric columns
    for col in ['quantity', 'revenue', 'price']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def generate_sample_data(n_rows: int = 1000) -> pd.DataFrame:
    """Generate sample sales data for testing."""
    import numpy as np
    
    np.random.seed(42)
    
    products = ['Laptop', 'Phone', 'Tablet', 'Headphones', 'Monitor', 
                'Keyboard', 'Mouse', 'Webcam', 'Speaker', 'Charger']
    regions = ['North', 'South', 'East', 'West']
    categories = ['Electronics', 'Accessories', 'Peripherals']
    
    product_prices = {
        'Laptop': 999, 'Phone': 699, 'Tablet': 449, 'Headphones': 199,
        'Monitor': 349, 'Keyboard': 79, 'Mouse': 49, 'Webcam': 89,
        'Speaker': 129, 'Charger': 29
    }
    
    product_categories = {
        'Laptop': 'Electronics', 'Phone': 'Electronics', 'Tablet': 'Electronics',
        'Headphones': 'Accessories', 'Monitor': 'Peripherals', 
        'Keyboard': 'Peripherals', 'Mouse': 'Peripherals', 'Webcam': 'Peripherals',
        'Speaker': 'Accessories', 'Charger': 'Accessories'
    }
    
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    
    data = []
    for _ in range(n_rows):
        product = np.random.choice(products)
        quantity = np.random.randint(1, 20)
        base_price = product_prices[product]
        # Add some price variation
        price = base_price * np.random.uniform(0.9, 1.1)
        
        data.append({
            'date': np.random.choice(dates),
            'product': product,
            'category': product_categories[product],
            'region': np.random.choice(regions),
            'quantity': quantity,
            'price': round(price, 2),
            'revenue': round(price * quantity, 2)
        })
    
    return pd.DataFrame(data).sort_values('date').reset_index(drop=True)
