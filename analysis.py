import sqlite3
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
#     SELECT s.store_id,SUM(s.quantity * p.price) AS revenue, sale_date
#     FROM sales s INNER JOIN products p ON s.product_id = p.product_id
#     GROUP BY s.store_id,sale_date
# )
# SELECT s.region, SUM(m.revenue) AS total_revenue, strftime('%m/%Y', m.sale_date) AS month_year
# FROM monthly_rev m INNER JOIN stores s ON m.store_id = s.store_id
# GROUP BY s.region, strftime('%Y-%m', m.sale_date)
# ORDER BY s.region,strftime('%Y-%m', m.sale_date)
# """
# query_df = pd.read_sql_query(query, connection)
# print("The following depicts the total monthly revenue over tthe course of the past year for each of the locations:\n", query_df)




#Now check the cumulative monthly revenue for each of the locations.
# query = """
# WITH cumulative AS(
#     SELECT s.store_id, SUM(s.quantity * p.price) AS revenue, strftime('%Y-%m', sale_date) AS month_year
#     FROM sales s INNER JOIN products p ON s.product_id = p.product_id
#     GROUP BY s.store_id, month_year
# )
# SELECT s.region,SUM(c.revenue) AS rv FROM cumulative c JOIN stores s ON c.store_id = s.store_id

# GROUP BY s.region
# """
# query = """
# WITH combined AS(
#     SELECT s.store_id, SUM(s.quantity * p.price) AS revenue, s.sale_date
#     FROM sales s INNER JOIN products p ON s.product_id = p.product_id
#     GROUP BY s.store_id, s.sale_date
# ),
# monthly_rev AS(
#     SELECT s.region, SUM(c.revenue) AS total_revenue, strftime('%Y-%m', c.sale_date) AS year_month
#     FROM combined c INNER JOIN stores s ON c.store_id = s.store_id
#     GROUP BY s.region, year_month
# )
# SELECT region, year_month, SUM(total_revenue) OVER (PARTITION BY region ORDER BY year_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue
# FROM monthly_rev
# ORDER BY region, year_month

# """
# query_df = pd.read_sql_query(query, connection)
# print("The following depicts the cumulative monthly revenue for each of the locations:\n", query_df)




#Time to analyze the customer behavior. Look at customer behavior metrics such as average purchase value, and customer lifetime value.

#1.
#Total number of sales to customers in the past twelve months
# query = """
# WITH past_sales AS(
#     SELECT c.customer_id, COUNT(s.sale_id) AS total_purchases
#     FROM sales s RIGHT JOIN customers c ON s.customer_id = c.customer_id
#     GROUP BY c.customer_id
# )
# SELECT * FROM past_sales
# ORDER BY total_purchases DESC
# """
# query_df = pd.read_sql_query(query, connection)
# total_customers = query_df
# print("Total number of sales to customers in the past twelve months\n", total_customers)


#2.
#Get the average purchase value for each customer and how many items they have purchased
# query = """
# WITH customer_purchases AS (
#     SELECT s.customer_id, AVG(s.quantity * p.price) AS avg_purchase_value,COUNT(s.sale_id) AS number_of_purchases
#     FROM sales s INNER JOIN products p ON p.product_id = s.product_id
#     GROUP BY s.customer_id
# )
# SELECT c.name, COALESCE(cp.avg_purchase_value,0) AS average_purchase_value, COALESCE(cp.number_of_purchases,0) AS number_of_purchases
# FROM customer_purchases cp RIGHT JOIN customers c ON cp.customer_id = c.customer_id
# ORDER BY cp.avg_purchase_value DESC, cp.number_of_purchases DESC
# """
# query_df = pd.read_sql_query(query, connection)
# print("\n\nThe following depicts the average purchase value and number of purchases for each customer:\n", query_df)


#3.
#Which age groups spend the most money
# query = """
# WITH age_groups AS (
#     SELECT customer_id, name, CASE
#         WHEN age BETWEEN 18 AND 24 THEN 'Young Adults'
#         WHEN age BETWEEN 25 AND 34 THEN 'Early Career Adults'
#         WHEN age BETWEEN 35 AND 44 THEN 'Mid-Career Professionals'
#         WHEN age BETWEEN 45 AND 54 THEN 'Experienced Adults'
#         WHEN age >= 55 THEN 'Seniors'
#         ELSE 'Unknown Age Group'
#     END AS age_group
#     FROM customers
# ),
# sales_total AS(
#     SELECT s.customer_id, SUM(s.quantity * p.price) AS total_spent
#     FROM sales s INNER JOIN products p ON s.product_id = p.product_id
#     GROUP BY s.customer_id
# )
# SELECT a.age_group, SUM(s.total_spent) AS total_spent
# FROM age_groups a INNER JOIN sales_total s ON a.customer_id = s.customer_id
# GROUP BY a.age_group
# ORDER BY total_spent DESC
# """
# query_df = pd.read_sql_query(query, connection)
# print("\n\nThe following depicts which age groups spend the most money and what they usually buy:\n", query_df)

#4.
#What are the most popular products for each age group, and which catgeory does this product belong to? Is there a better way of showing this data?
# query = """
# WITH age_groups AS (
#     SELECT customer_id, name, CASE
#         WHEN age BETWEEN 18 AND 24 THEN 'Young Adults'
#         WHEN age BETWEEN 25 AND 34 THEN 'Early Career Adults'
#         WHEN age BETWEEN 35 AND 44 THEN 'Mid-Career Professionals'
#         WHEN age BETWEEN 45 AND 54 THEN 'Experienced Adults'
#         WHEN age >= 55 THEN 'Seniors'
#         ELSE 'Unknown Age Group'
#     END AS age_group
#     FROM customers
# )
# SELECT a.age_group, p.category, SUM(s.quantity) AS total_units_sold
# FROM age_groups a INNER JOIN sales s ON a.customer_id = s.customer_id INNER JOIN products p ON s.product_id = p.product_id
# GROUP BY a.age_group, p.category
# ORDER BY a.age_group,total_units_sold DESC 
# """
# query_df = pd.read_sql_query(query, connection)
# print("\n\nThe following depicts the most popular products for each age group, and which catgeory does this product belong to:\n", query_df)


#5.
#Look at what product categories each gender buys the most and how much they spend.
# query = """
# SELECT c.gender, p.category, SUM(s.quantity * p.price) AS total_spent
# FROM sales s INNER JOIN customers c ON s.customer_id = c.customer_id INNER JOIN products p ON s.product_id = p.product_id
# GROUP BY c.gender, p.category
# ORDER BY c.gender, p.category,total_spent DESC
# """
# query_df = pd.read_sql_query(query, connection)
# print("\n\nThe following depicts what product categories each gender buys the most and how much they spend:\n", query_df)

#6
#Finally for customer behavior metrics, look at customer retention rates and churn rates over the past year by age group.\
query = """
WITH age_groups AS (
    SELECT customer_id, name, CASE
        WHEN age BETWEEN 18 AND 24 THEN 'Young Adults'
        WHEN age BETWEEN 25 AND 34 THEN 'Early Career Adults'
        WHEN age BETWEEN 35 AND 44 THEN 'Mid-Career Professionals'
        WHEN age BETWEEN 45 AND 54 THEN 'Experienced Adults'
        WHEN age >= 55 THEN 'Seniors'
        ELSE 'Unknown Age Group'
    END AS age_group
    FROM customers
),
customer_activity AS (
    SELECT a.age_group, s.customer_id, 
           MAX(s.sale_date) AS last_purchase_date,
           MIN(s.sale_date) AS first_purchase_date,
           COUNT(s.sale_id) AS total_purchases
    FROM age_groups a LEFT JOIN sales s ON a.customer_id = s.customer_id
    GROUP BY a.age_group, s.customer_id
)
SELECT a.age_group, COUNT(ca.customer_id) AS total_customers,
       SUM(CASE WHEN ca.last_purchase_date >= DATE('now', '-6 months') THEN 1 ELSE 0 END) AS active_customers,
       SUM(CASE WHEN ca.last_purchase_date < DATE('now', '-6 months') OR    ca.last_purchase_date IS NULL THEN 1 ELSE 0 END) AS churned_customers,  
         ROUND( (CAST(SUM(CASE WHEN ca.last_purchase_date >= DATE('now', '-6 months') THEN 1 ELSE 0 END) AS FLOAT) / COUNT(ca.customer_id)) * 100, 2) AS retention_rate,
         ROUND( (CAST(SUM(CASE WHEN ca.last_purchase_date < DATE('now', '-6 months') OR ca.last_purchase_date IS NULL THEN 1 ELSE 0 END) AS FLOAT) / COUNT(ca.customer_id)) * 100, 2) AS churn_rate
FROM age_groups a  JOIN customer_activity ca ON a.age_group = ca.age_group
GROUP BY a.age_group
ORDER BY a.age_group
"""
query_df = pd.read_sql_query(query, connection)
print("\n\nThe following depicts customer retention rates and churn rates over the past year by age group:\n", query_df)
