 -- the script below selects customers with their orders status
CREATE VIEW view_customerwithorders
AS 
	SELECT c.first_name,c.last_name, c.city,ord.order_status
	FROM sales.customers c
	INNER JOIN sales.orders ord
	ON c.customer_id =ord.customer_id

-- this sccript will run the view above
SELECT * FROM view_customerwithorders
