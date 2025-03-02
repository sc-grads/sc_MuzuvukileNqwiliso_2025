-- BELOW IS THERE ARE SQL SCRIPTS FOR THE TABLES I USED AND ALSO SOME SUB-QUERIES AND ALSO SOME AGGREGATION FUNCTIONS

SELECT * FROM sales.order_items
SELECT *FROM sales.customers
SELECT *FROM sales.orders
SELECT *FROM production.products

SELECT first_name,last_name,COUNT(quantity) AS [no of items]
FROM (SELECT ctmer.first_name,ctmer.last_name,
	ord.order_id,prd.product_name,ord_i.quantity,
	ord_i.list_price AS price

	FROM sales.customers ctmer
	INNER JOIN sales.orders ord
	ON ctmer.customer_id = ord.customer_id
	INNER JOIN sales.order_items ord_i 
	ON  ord.order_id = ord_i.order_id
	INNER JOIN production.products prd
	ON ord_i.product_id  = prd.product_id
	) sub_query

WHERE first_name LIKE 'J%'
GROUP BY first_name	,last_name
ORDER BY first_name DESC

-- THIS SQL SCRIPT ABOVE RETURNS EVERYONE WHO'S NAME START WITH 'J' AND COUNTS HOW MANY ORDERS DID HE OR SHE ORDERED

SELECT first_name,last_name,SUM(quantity) AS [no of items]
FROM (SELECT ctmer.first_name,ctmer.last_name,
	ord.order_id,prd.product_name,ord_i.quantity,
	ord_i.list_price AS price

	FROM sales.customers ctmer
	INNER JOIN sales.orders ord
	ON ctmer.customer_id = ord.customer_id
	INNER JOIN sales.order_items ord_i 
	ON  ord.order_id = ord_i.order_id
	INNER JOIN production.products prd
	ON ord_i.product_id  = prd.product_id
	) sub_query

WHERE first_name LIKE 'J%'
GROUP BY first_name	,last_name
ORDER BY first_name DESC

-- THE ABOVE SQL SCRIPT SUMS UP THE NUMBER ORDERS H/SHE ORDERED


SELECT first_name,last_name,MAX(quantity) AS [max quantity]
FROM (SELECT ctmer.first_name,ctmer.last_name,
	ord.order_id,prd.product_name,ord_i.quantity,
	ord_i.list_price AS price

	FROM sales.customers ctmer
	INNER JOIN sales.orders ord
	ON ctmer.customer_id = ord.customer_id
	INNER JOIN sales.order_items ord_i 
	ON  ord.order_id = ord_i.order_id
	INNER JOIN production.products prd
	ON ord_i.product_id  = prd.product_id
	) sub_query

WHERE first_name LIKE 'J%'
GROUP BY first_name	,last_name
ORDER BY [max quantity] DESC

-- THE ABOVE RETURNS THE LARGEST ORDER EACH PERSON WITH A STARNG LETTER 'J' HAS ORDERED 

SELECT first_name,last_name,MIN(quantity) AS [min quantity]
FROM (SELECT ctmer.first_name,ctmer.last_name,
	ord.order_id,prd.product_name,ord_i.quantity,
	ord_i.list_price AS price

	FROM sales.customers ctmer
	INNER JOIN sales.orders ord
	ON ctmer.customer_id = ord.customer_id
	INNER JOIN sales.order_items ord_i 
	ON  ord.order_id = ord_i.order_id
	INNER JOIN production.products prd
	ON ord_i.product_id  = prd.product_id
	) sub_query

WHERE first_name LIKE 'J%'
GROUP BY first_name	,last_name
ORDER BY [min quantity] ASC

-- THE ABOVE RETURNS THE SMALLEST ORDER EACH PERSON WITH A STARNG LETTER 'J' HAS ORDERED 

SELECT AVG(quantity) AS [quantity avg]
FROM (SELECT ctmer.first_name,ctmer.last_name,
	ord.order_id,prd.product_name,ord_i.quantity,
	ord_i.list_price AS price

	FROM sales.customers ctmer
	INNER JOIN sales.orders ord
	ON ctmer.customer_id = ord.customer_id
	INNER JOIN sales.order_items ord_i 
	ON  ord.order_id = ord_i.order_id
	INNER JOIN production.products prd
	ON ord_i.product_id  = prd.product_id
	) sub_query
