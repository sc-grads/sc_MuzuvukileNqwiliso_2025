USE BikeStores

SELECT * FROM sales.customers

SELECT TOP 5 * FROM sales.customers

SELECT * FROM
sales.order_items
ORDER BY sales.order_items.order_id DESC