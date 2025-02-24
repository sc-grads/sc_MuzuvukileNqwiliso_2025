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


  -- ================================
-- ?? left join practice questions
-- ================================

-- 6. get a list of all stores and their staff members, including stores that currently have no staff.
-- 7. retrieve a list of all customers and their orders, including those who have never placed an order.
-- 8. show a list of all staff members and their managers, including staff who don’t have a manager.
-- 9. get a list of all products and their sales orders, including products that have never been ordered.
-- 10. list all stores and the products they stock, including stores that do not have any products in stock.

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
