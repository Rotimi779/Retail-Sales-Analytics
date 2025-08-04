query = """
SELECT p.category, SUM(s.quantity * p.price) AS total_revenue, SUM(s.quantity) AS total_units_sold
FROM sales s INNER JOIN products p ON s.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC, total_units_sold DESC
"""
query_df = pd.read_sql_query(query, connection)
print("The following depicts which category was the most popular in terms of total price, and also in terms of the number