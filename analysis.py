import sqlite3
import pandas as pd

connection = sqlite3.connect('retail_sales.db')

for name in ['customers', 'inventory', 'products','sales','stores']:
    df = pd.read_csv(f'{name}.csv')
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
#Redo the joins for this query  
query = """
SELECT st.store_name,st.city,st.region, SUM(s.quantity * p.price) AS total_revenue, SUM(s.quantity) AS total_units_sold, COUNT(DISTINCT s.customer_id) AS distinct_customers
FROM sales s INNER JOIN stores st ON s.store_id = st.store_id
GROUP BY st.location
ORDER BY total_revenue DESC, total_units_sold DESC, distinct_customers DESC
""" 
query_df = pd.read_sql_query(query, connection)
print("The following depicts which location has the highest sales (in terms of total price, number of units sold, number of distinct customers) \n", query_df)
