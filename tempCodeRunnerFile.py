query = """
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