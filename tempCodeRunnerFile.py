query = """
# SELECT p.category, SUM(p.price * s.quantity) AS total_revenue
# FROM sales s JOIN products p ON s.product_id = p.product_id
# GROUP BY p.category
# ORDER BY total_revenue
# """
# df_revenue = pd.read_sql_query(query, connection)
# print("Below is the categorical revenue\n", df_revenue)