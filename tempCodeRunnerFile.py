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
sales_total AS(
    SELECT s.customer_id, SUM(s.quantity * p.price) AS total_spent
    FROM sales s INNER JOIN products p ON s.product_id = p.product_id
    GROUP BY s.customer_id
)
SELECT a.age_group, SUM(s.total_spent) AS total_spent
FROM age_groups a INNER JOIN sales_total s ON a.customer_id = s.customer_id
GROUP BY a.age_group
ORDER BY total_spent DESC
"""
query_df = pd.read_sql_query(query, connection)
print("\n\nT