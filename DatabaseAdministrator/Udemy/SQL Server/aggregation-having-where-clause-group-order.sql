SELECT * FROM production.brands
SELECT * FROM production.categories
SELECT * FROM production.products
SELECT * FROM production.stocks

SELECT * FROM sales.customers
SELECT * FROM sales.orders
SELECT * FROM sales.order_items

-- WHERE clause
SELECT product_name,category_id,list_price 
FROM production.products
WHERE list_price >= 500

-- ORDER BY
SELECT * FROM production.products
ORDER BY product_id DESC -- this desc means the tample data or items will be arranged in descending order 

SELECT * FROM production.products
ORDER BY product_id ASC -- this asc means the tample data or items will be arranged in ascending order 

-- GROUP BY
SELECT category_id AS each_category, 
SUM(list_price) AS total_price_for_each_category
FROM production.products
GROUP BY category_id -- the group by must be before order by 
ORDER BY category_id ASC 

-- using group by with join
SELECT c.first_name, 
       c.email, 
       items.product_id AS products,
       SUM(items.quantity) AS total_items_ordered,
       COUNT(items.quantity) AS number_items
FROM sales.customers c
INNER JOIN sales.orders ord ON c.customer_id = ord.customer_id
INNER JOIN sales.order_items items ON ord.order_id = items.order_id
GROUP BY c.first_name, c.email, items.product_id;


-- HAVING 
SELECT category_id AS each_category, 
SUM(list_price) AS total_price_for_each_category
FROM production.products
GROUP BY category_id -- the group by must be before order by 
HAVING SUM(list_price) = 98985.44 
ORDER BY category_id ASC 