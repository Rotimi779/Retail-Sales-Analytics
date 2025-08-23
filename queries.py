import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

connection = sqlite3.connect('retail_sales.db')

for name in ['customers', 'inventory', 'products','sales','stores']:
    df = pd.read_csv(f'csv_files/{name}.csv')
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

# query ="""
# SELECT strftime('%Y-%m',s.sale_date) AS month_year, st.region,SUM(p.price * s.quantity) AS total_revenue,COUNT(s.sale_id) AS total_orders,SUM(s.quantity) AS units_sold, ROUND(SUM(p.price * s.quantity) / COUNT(DISTINCT s.sale_id),2) AS average_order_value
# FROM stores st JOIN sales s ON st.store_id = s.store_id JOIN products p ON s.product_id = p.product_id
# WHERE st.store_name = ?
# GROUP BY month_year
# ORDER BY month_year,total_revenue DESC
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is revenue trend for the selected store\n", df_revenue)


# query ="""
# SELECT p.product_name, SUM(s.quantity * p.price) AS revenue
# FROM stores st JOIN sales s ON st.store_id = s.store_id JOIN products p ON p.product_id = s.product_id 
# WHERE st.store_name = "Sweet Corn Fritters"
# GROUP BY p.product_name
# ORDER BY revenue DESC
# LIMIT 15
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is product trend for the selected store\n", df_revenue)

# query ="""
# SELECT p.category AS category, SUM(s.quantity * p.price) AS revenue
# FROM stores st JOIN sales s ON st.store_id = s.store_id JOIN products p ON p.product_id = s.product_id 
# WHERE st.store_name = "Sweet Corn Fritters"
# GROUP BY p.category
# ORDER BY revenue DESC
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is category trend for the selected store\n", df_revenue)

# query ="""
# WITH monthly_sales AS (
#     SELECT s.product_id, strftime('%Y-%m', s.sale_date) AS month, SUM(s.quantity) AS sales_per_month
#     FROM sales s
#     GROUP BY s.product_id, month
# ),
# avg_sales AS (
#     SELECT product_id, AVG(sales_per_month) AS avg_monthly_sales
#     FROM monthly_sales
#     GROUP BY product_id
# ),
# stock_summary AS
# (
#     SELECT i.product_id, p.product_name, p.category, ROUND(AVG(i.stock_quantity),2) AS avg_stock, ROUND(a.avg_monthly_sales,2) AS avg_monthly_sales
#     FROM inventory i JOIN products p ON p.product_id = i.product_id JOIN avg_sales a ON a.product_id = i.product_id
#     GROUP BY i.product_id, p.product_name, p.category
# )
# SELECT product_id, product_name, category, COALESCE(avg_stock, 0) AS avg_stock, COALESCE(avg_monthly_sales, 0) AS avg_monthly_sales,
#     CASE 
#         WHEN COALESCE(avg_monthly_sales, 0) = 0 THEN NULL
#         ELSE (avg_stock * 1.0 / avg_monthly_sales)
#     END AS stock_coverage
# FROM stock_summary
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is inventory trend\n", df_revenue)



# query ="""
# WITH monthly_sales AS (
#     SELECT s.product_id, strftime('%Y-%m', s.sale_date) AS month, SUM(s.quantity) AS sales_per_month
#     FROM sales s
#     GROUP BY s.product_id, month
# ),
# avg_sales AS (
#     SELECT product_id, AVG(sales_per_month) AS avg_monthly_sales
#     FROM monthly_sales
#     GROUP BY product_id
# ),
# stock_summary AS
# (
#     SELECT i.product_id, p.product_name, p.category, ROUND(AVG(i.stock_quantity),2) AS avg_stock, ROUND(a.avg_monthly_sales,2) AS avg_monthly_sales
#     FROM inventory i JOIN products p ON p.product_id = i.product_id JOIN avg_sales a ON a.product_id = i.product_id
#     GROUP BY i.product_id, p.product_name, p.category
# )
# SELECT category,
#     ROUND(AVG(avg_stock),2) AS avg_stock,
#     ROUND(AVG(avg_monthly_sales),2) AS avg_monthly_sales,
#     COUNT(*) AS sku_count
# FROM stock_summary
# GROUP BY category
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is inventory trend part 2\n", df_revenue)






# query ="""
# SELECT s.customer_id, DATE(s.sale_date) AS sale_date, CAST(strftime('%Y-%m-01', s.sale_date) AS TEXT) AS order_month, (s.quantity * p.price) AS revenue
# FROM sales s
# JOIN products p ON p.product_id = s.product_id
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is customer data\n", df_revenue)

# query ="""
# SELECT COUNT(DISTINCT customer_id)
# FROM sales
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is customer analysis data\n", df_revenue)

query ="""
WITH ranked AS (
    SELECT c.name AS customer_name, p.category, SUM(s.quantity * p.price) AS total_revenue
    FROM sales s JOIN products p ON p.product_id = s.product_id JOIN customers c ON c.customer_id = s.customer_id
    GROUP BY c.customer_id, c.name, p.category
)
SELECT
    category,
    customer_name,
    total_revenue
FROM ranked
ORDER BY category, total_revenue DESC
"""
df_revenue = pd.read_sql_query(query, connection)
print("Below is top customer data based on revenue\n", df_revenue)



