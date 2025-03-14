DELETE FROM sales.orders
WHERE sales.orders.order_date = CAST('2016-01-01');

SELECT * FROM sales.orders

SELECT * FROM sales.orders

DELETE FROM sales.customers
WHERE sales.customers.customer_id = (SELECT * FROM sales.orders  WHERE sales.orders.customer_id = 2)