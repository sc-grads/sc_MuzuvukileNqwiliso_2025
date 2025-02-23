-- SPECIFY DATABASE TO USE
USE BikeStores

-- SALES
SELECT * FROM sales.customers
SELECT * FROM sales.order_items
SELECT * FROM sales.orders
SELECT * FROM sales.staffs
SELECT * FROM sales.stores
-- PRODUCTS
SELECT * FROM production.brands
SELECT * FROM production.products
SELECT * FROM production.categories
SELECT * FROM production.stocks

-- TASKS
-- e.g 1: Tables - stores , staffs
SELECT [str].*,stff.first_name as [staff name]
FROM sales.stores [str]
LEFT JOIN sales.staffs stff
ON stff.store_id = [str].store_id

-- e.g 2: Tables - customers, orders
SELECT c.*,ord.*
FROM sales.customers c
LEFT JOIN sales.orders ord
ON c.customer_id = ord.customer_id

-- e.g 3 : Tables - staffs, managers
SELECT * FROM sales.staffs