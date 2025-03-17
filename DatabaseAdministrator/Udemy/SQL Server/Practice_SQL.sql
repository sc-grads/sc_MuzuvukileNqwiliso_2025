USE BikeStores
GO 

-- sales schema

SELECT * FROM sales.customers
SELECT * FROM sales.order_items
SELECT * FROM sales.orders
SELECT * FROM sales.staffs
SELECT  * FROM sales.stores

-- production schema

SELECT * FROM production.brands
SELECT * FROM production.categories
SELECT * FROM production.products
SELECT * FROM production.stocks

-- inner join questions 
-- Retrieve the order ID, customer name, product name, and quantity for all orders.

-- inner join 1

SELECT 
o.order_id,
c.first_name,
p.product_name,
SUM(i.quantity) AS [total orders]

FROM sales.customers c
INNER JOIN sales.orders o 
ON c.customer_id = o.customer_id
INNER JOIN sales.order_items i
ON o.order_id = i.order_id 
INNER JOIN production.products p
ON i.product_id = p.product_id
GROUP BY 
		c.first_name, 
		o.order_id,
		p.product_name
ORDER BY c.first_name
-- This is a pagination it returns 20 rows - I used it because it's more flexable than TOP 
OFFSET 0 ROWS FETCH NEXT 20 ROWS ONLY


-- inner join 2
-- List all staff members and the stores they work at.

SELECT stf.*,s.store_name
FROM sales.staffs stf
INNER JOIN sales.stores s
ON stf.store_id = s.store_id

-- Return all staff members that work at Santa Cruz Bikes
SELECT stf.*,s.store_name
FROM sales.staffs stf
INNER JOIN sales.stores s
ON stf.store_id = s.store_id
WHERE s.store_name = 'Santa Cruz Bikes'

-- Return all staff members that don't have managers
SELECT stf.*,s.store_name
FROM sales.staffs stf
INNER JOIN sales.stores s
ON stf.store_id = s.store_id
WHERE stf.manager_id IS NULL

-- Return all staff members that have managers
SELECT stf.*,s.store_name
FROM sales.staffs stf
INNER JOIN sales.stores s
ON stf.store_id = s.store_id
WHERE stf.manager_id IS NOT NULL

-- inner join 3
-- Get a list of orders, the products ordered, and their price.

SELECT 
o.order_id,
o.item_id,o.quantity,
(o.list_price * o.discount)+ o.list_price AS [total price],
p.product_name

FROM sales.order_items o
INNER JOIN production.products p 
ON o.product_id = p.product_id
