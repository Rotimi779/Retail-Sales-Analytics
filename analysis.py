import sqlite3
import pandas as pd

connection = sqlite3.connect('retail_sales.db')

for name in ['customers', 'inventory', 'products','sales','stores']:
    df = pd.read_csv(f'{name}.csv')
    if name in ['sales', 'inventory']:
        # Convert date columns to datetime format
        if 'last_updated' in df.columns:
            df['last_updated'] = pd.to_datetime(df['last_updated'], errors='coerce').dt.date
    df.to_sql(name, connection, if_exists='replace', index=False)

#Run some queries to analyze the data for customers
#Check which customers have made the most purchases(or bought the most units OR visited the most stores OR bought the most distinct units)
# query =  """
# SELECT c.name, COUNT(*)   AS number_of_purchases
# FROM sales s INNER JOIN customers c ON s.customer_id = c.customer_id
# GROUP BY c.customer_id
# ORDER BY number_of_purchases DESC
# """
# query_df = pd.read_sql_query(query, connection)
# print(query_df)

#Check who has bought the most units
# query =  """
# SELECT c.name, SUM(s.quantity)   AS number_of_purchases
# FROM sales s INNER JOIN customers c ON s.customer_id = c.customer_id
# GROUP BY c.customer_id
# ORDER BY number_of_purchases DESC
# """
# query_df = pd.read_sql_query(query, connection)
# print("The following depicts which customer had bought the most units across all the stores \n",query_df)

#Check which customers have visited the most stores.
# querty =  """
# SELECT c.name, COUNT(DISTINCT s.store_id)   AS number_of_stores_visited
# FROM sales s INNER JOIN customers c ON s.customer_id = c.customer_id
# GROUP BY c.customer_id
# ORDER BY number_of_stores_visited DESC  
# """
# query_df = pd.read_sql_query(querty, connection)
# print("The following depicts which customer had visited the most stores \n",query_df)

#Check which customers have bought the most distinct units.
# query =  """
# SELECT c.name, COUNT(DISTINCT s.product_id)   AS number_of_distinct_units_bought
# FROM sales s INNER JOIN customers c ON s.customer_id = c.customer_id        
# GROUP BY c.customer_id
# ORDER BY number_of_distinct_units_bought DESC
# """
# query_df = pd.read_sql_query(query, connection)
# print("The following depicts which customer had bought the most distinct units \n",query_df)




#Run some queries to analyze the data for products
#Check which products have been sold the most (in terms of number of units OR number of distinct customers OR number of distinct stores)
# query = """
# SELECT p.product_name, SUM(s.quantity) AS total_units_sold
# FROM sales s INNER JOIN products p ON s.product_id = p.product_id
# GROUP BY p.product_name
# ORDER BY total_units_sold DESC
# """
# query_df = pd.read_sql_query(query, connection)
# print("The following depicts which product has been sold the most in terms of number of units \n", query_df)

#Check what category was the most popular in terms of total price, and also in terms of the number of units sold.
# query = """
# SELECT p.category, SUM(s.quantity * p.price) AS total_revenue, SUM(s.quantity) AS total_units_sold
# FROM sales s INNER JOIN products p ON s.product_id = p.product_id
# GROUP BY p.category
# ORDER BY total_revenue DESC, total_units_sold DESC
# """
# query_df = pd.read_sql_query(query, connection)
# print("The following depicts which category was the most popular in terms of total price, and also in terms of the number of units sold \n", query_df)


#Run some queries to analyze the data for stores

#Check the location of each of the stores and see which location has the highest sales (in terms of total price, number of units sold, number of distinct customers)
# query = """
# SELECT st.region, SUM(s.quantity * p.price) AS total_revenue, SUM(s.quantity) AS total_units_sold, COUNT(DISTINCT s.customer_id) AS distinct_customers
# FROM sales s INNER JOIN stores st ON s.store_id = st.store_id INNER JOIN products p ON s.product_id = p.product_id
# GROUP BY st.region
# ORDER BY total_revenue DESC, total_units_sold DESC, distinct_customers DESC
# """ 
# query_df = pd.read_sql_query(query, connection)
# print("The following depicts which location has the highest sales (in terms of total price, number of units sold, number of distinct customers) \n", query_df)

#Check which stores are the most popular in terms of number of customers and the number of sold products.
# query = """
# SELECT st.store_name,COUNT(DISTINCT s.customer_id) AS num_customers, COUNT(DISTINCT s.product_id) AS num_distinct_products
# FROM sales s INNER JOIN stores st ON s.store_id = st.store_id
# GROUP BY st.store_name
# ORDER BY num_customers DESC, num_distinct_products DESC
# """
# query_df = pd.read_sql_query(query, connection)
# print("The following depicts which stores are the most popular in terms of number of customers and the  number of sold products a: \n", query_df)

#Check which cities are most popular in terms of total revenue accumulated, the number of customers and the number of sold products.
# query = """
# SELECT st.city, SUM(s.quantity * p.price) AS total_revenue, COUNT(DISTINCT s.customer_id) AS num_customers, COUNT(DISTINCT s.product_id) AS num_distinct_products
# FROM sales s INNER JOIN stores st ON s.store_id = st.store_id INNER JOIN products p ON s.product_id = p.product_id
# GROUP BY st.city
# ORDER BY total_revenue DESC, num_customers DESC, num_distinct_products DESC
# """
# query_df = pd.read_sql_query(query, connection)
# print("The following depicts which cities are most popular in terms of total revenue accumulated, number of customers and the number of sold products\n", query_df)




#Create dashboards to visualize the queries below
#What is the total revenue over the course of the past year for each of the locations?
# query = """
# WITH monthly_rev AS(
#     SELECT s.store_id,SUM(s.quantity * p.price) AS revenue, last_updated
#     FROM sales s INNER JOIN products p ON s.product_id = p.product_id
#     GROUP BY s.store_id,last_updated
# )
# SELECT s.region, SUM(m.revenue) AS total_revenue, strftime('%m/%Y', m.last_updated) AS month_year
# FROM monthly_rev m INNER JOIN stores s ON m.store_id = s.store_id
# GROUP BY s.region, strftime('%Y-%m', m.last_updated)
# ORDER BY s.region,strftime('%Y-%m', m.last_updated)
# """
# query_df = pd.read_sql_query(query, connection)
# print("The following depicts the total monthly revenue over tthe course of the past year for each of the locations:\n", query_df)




#Now check the cumulative monthly revenue for each of the locations.
# query = """
# WITH cumulative AS(
#     SELECT s.store_id, SUM(s.quantity * p.price) AS revenue, strftime('%Y-%m', last_updated) AS month_year
#     FROM sales s INNER JOIN products p ON s.product_id = p.product_id
#     GROUP BY s.store_id, month_year
# )
# SELECT s.region,SUM(c.revenue) AS rv FROM cumulative c JOIN stores s ON c.store_id = s.store_id

# GROUP BY s.region

# """
query = """
WITH combined AS(
    SELECT s.store_id, SUM(s.quantity * p.price) AS revenue, s.last_updated
    FROM sales s INNER JOIN products p ON s.product_id = p.product_id
    GROUP BY s.store_id, s.last_updated
),
monthly_rev AS(
    SELECT s.region, SUM(c.revenue) AS total_revenue, strftime('%Y-%m', c.last_updated) AS year_month
    FROM combined c INNER JOIN stores s ON c.store_id = s.store_id
    GROUP BY s.region, year_month
)
SELECT region, year_month, SUM(total_revenue) OVER (PARTITION BY region ORDER BY year_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue
FROM monthly_rev
ORDER BY region, year_month

"""
query_df = pd.read_sql_query(query, connection)
print("The following depicts the cumulative monthly revenue for each of the locations:\n", query_df)




#Time to analyze the customer behavior. Look at customer behavior metrics such as average purchase frequency, average purchase value, and customer lifetime value.
#Average purchase frequency is the average number of purchases made by a customer in a given time period