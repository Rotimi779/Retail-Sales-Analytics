import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

connection = sqlite3.connect('retail_sales.db')

for name in ['customers', 'inventory', 'products','sales','stores']:
    df = pd.read_csv(f'{name}.csv')
    if name in ['sales', 'inventory']:
        # Convert date columns to datetime format
        if 'last_updated' in df.columns:
            df['last_updated'] = pd.to_datetime(df['last_updated'], errors='coerce').dt.date
        if 'sale_date' in df.columns:
            df['sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce').dt.date
    df.to_sql(name, connection, if_exists='replace', index=False)

#Overview section of the database

#Query to get total revenue,total orders, units sold and AOV.
# query = """
# SELECT strftime('%Y-%m',s.sale_date) AS month_year, SUM(p.price * s.quantity) AS total_revenue, COUNT(DISTINCT s.sale_id) AS total_orders, SUM(s.quantity) AS units_sold, ROUND(SUM(p.price * s.quantity) / COUNT(DISTINCT s.sale_id),2) AS average_order_value
# FROM sales s JOIN products p ON s.product_id = p.product_id
# GROUP BY month_year 
# ORDER BY  month_year
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is the revenue by month\n", df_revenue)

# query = """
# SELECT p.category, SUM(p.price * s.quantity) AS total_revenue
# FROM sales s JOIN products p ON s.product_id = p.product_id
# GROUP BY p.category
# ORDER BY total_revenue
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is the categorical revenue\n", df_revenue)


# query = """
# SELECT p.category, SUM(p.price * s.quantity) AS total_revenue,st.region
# FROM stores st JOIN sales s ON st.store_id = s.store_id JOIN products p ON s.product_id = p.product_id
# GROUP BY p.category,st.region
# ORDER BY total_revenue
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is the categorical revenue\n", df_revenue)

# query ="""
# SELECT st.store_name,st.region,SUM(p.price * s.quantity) AS total_revenue,COUNT(s.sale_id) AS total_orders,SUM(s.quantity) AS units_sold
# FROM stores st JOIN sales s ON st.store_id = s.store_id JOIN products p ON s.product_id = p.product_id
# GROUP BY st.store_id
# ORDER BY total_revenue DESC
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is store data\n", df_revenue)

query ="""
SELECT strftime('%Y-%m',s.sale_date) AS month_year, st.region,SUM(p.price * s.quantity) AS total_revenue,COUNT(s.sale_id) AS total_orders,SUM(s.quantity) AS units_sold
FROM stores st JOIN sales s ON st.store_id = s.store_id JOIN products p ON s.product_id = p.product_id
WHERE st.store_name = 'Travel Orthopedic Pillow'
GROUP BY month_year
ORDER BY month_year,total_revenue DESC
"""
df_revenue = pd.read_sql_query(query, connection)
print("Below is revenue trend for the selected store\n", df_revenue)




