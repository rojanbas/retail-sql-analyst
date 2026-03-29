import pandas as pd
import sqlite3
import os

def build_database():
    # Create data folder if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Connect to SQLite — creates retail.db automatically
    conn = sqlite3.connect("data/retail.db")
    
    print("Loading your CSV files into database...")

    tables = {
        "CUSTOMERS":      "data/CUSTOMERS.csv",
        "ORDERS":         "data/ORDERS.csv",
        "ORDER_ITEMS":    "data/ORDER_ITEMS.csv",
        "PRODUCTS":       "data/PRODUCTS.csv",
        "PAYMENTS":       "data/PAYMENTS.csv",
        "SHIPPING":       "data/SHIPPING.csv",
        "COUNTRIES":      "data/COUNTRIES.csv",
        "RETAIL_STAGING": "data/RETAIL_STAGING.csv",
    }

    for table_name, csv_path in tables.items():
        df = pd.read_csv(csv_path)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"  ✅ Loaded {table_name} — {len(df)} rows")

    conn.close()
    print("\n🎉 Database ready at data/retail.db")

if __name__ == "__main__":
    build_database()
    