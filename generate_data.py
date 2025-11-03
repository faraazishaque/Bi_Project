import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_big_dataset(num_rows=10000):
    np.random.seed(42)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=395) 
    dates = pd.to_datetime([start_date + timedelta(days=i) for i in range(396)])
    
    data = {
        'order_id': range(10001, 10001 + num_rows),
        'order_date': np.random.choice(dates, size=num_rows),
        'customer_id': np.random.randint(2000, 5500, size=num_rows),
        'total_amount': np.round(np.random.normal(loc=110, scale=45, size=num_rows), 2),
    }
    df = pd.DataFrame(data)
    
    products_map = {
        'Electronics': ['Wireless Earbuds', 'Smart Watch', 'Laptop'],
        'Apparel': ['T-Shirt', 'Denim Jeans', 'Winter Jacket'],
        'Home Goods': ['Candle Set', 'Air Fryer', 'Robot Vacuum'],
        'Sports': ['Yoga Mat', 'Running Shoes', 'Dumbbell Set'],
        'Books & Media': ['E-Reader', 'Best-Seller Novel', 'Vinyl Record'],
        'Food & Beverage': ['Coffee Subscription', 'Protein Bars', 'Gourmet Tea']
    }
    categories = list(products_map.keys())
    
    df['product_category'] = np.random.choice(categories, p=[0.25, 0.2, 0.15, 0.15, 0.15, 0.1], size=num_rows)
    df['product_name'] = df.apply(lambda row: np.random.choice(products_map[row['product_category']]), axis=1)
    df['quantity'] = np.random.randint(1, 6, size=num_rows)
    df['customer_age'] = np.random.randint(18, 70, size=num_rows)
    df['customer_gender'] = np.random.choice(['Male', 'Female', 'Non-Binary', 'Not Specified'], p=[0.4, 0.45, 0.05, 0.1], size=num_rows)
    df['region'] = np.random.choice(['N. America', 'Europe', 'Asia-Pacific', 'Latin America'], p=[0.4, 0.3, 0.2, 0.1], size=num_rows)
    df['sales_channel'] = np.random.choice(['Website', 'Mobile App', 'Affiliate', 'In-Store Pickup'], p=[0.55, 0.3, 0.1, 0.05], size=num_rows)
    df['order_status'] = np.random.choice(['Shipped', 'Delivered', 'Cancelled', 'Returned'], p=[0.75, 0.15, 0.05, 0.05], size=num_rows)
    df['cost_of_goods_sold'] = np.round(df['total_amount'] * np.random.uniform(0.5, 0.75, size=num_rows), 2)
    df['gross_margin'] = df['total_amount'] - df['cost_of_goods_sold']
    
    # Apply a 15% uplift in the last 30 days for positive MoM KPI delta
    last_30_days = df['order_date'].dt.date >= (end_date - timedelta(days=30))
    df.loc[last_30_days, 'total_amount'] *= 1.15
    df.loc[last_30_days, 'gross_margin'] *= 1.15

    df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')
    df = df.sort_values(by='order_date').reset_index(drop=True)
    
    file_name = 'ecommerce_big_data_10000.csv'
    df.to_csv(file_name, index=False)
    print(f"✅ Generated {len(df)} rows and saved to {file_name}")
    return df

if __name__ == "__main__":
    generate_big_dataset()
