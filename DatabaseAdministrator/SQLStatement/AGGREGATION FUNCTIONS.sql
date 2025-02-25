USE BikeStores;

SELECT * FROM sales.customers
SELECT * FROM sales.orders
SELECT * FROM sales.staffs
SELECT * FROM sales.stores
SELECT * FROM sales.order_items

-- COUNT FUNCTION

--	THIS COMMAND IS USED TO COUNT NUMBER OF ROWS BASED ON THE SPECIFIED CONDITION IN 'WHERE' CLASUE
-- THIS COMMAND WITH '*' COUNTS EVERY COLUMN EVEN IF IT HAS A VALUE NULL, 
-- IF THE COMMAND IS USED WITHOUT '*' COUNT(Column_name) THIS WILL ONLY COUNT COLUMNS WITH NO NULL VALUES

SELECT COUNT(*) 
FROM sales.orders

SELECT COUNT(sales.orders.order_status) AS [order status]
FROM sales.orders
WHERE sales.orders.order_date
BETWEEN '2016-01-01' AND '2016-05-01'

-- THE COUNT FUNCTION CAN ALSO BE USED WITH DISTINCT TO COUNT ONLY UNIQUE VALUES
-- e.g THE DATABASE HAS 1445 CITIES IF I AM NOT USING COUNT BUT AFTER USING DISTINCT ITS 195 CITIES 
-- THIS MEANS THAT THE ARE ONY 195 CITIES THAT ARE UNIQUE THAT ARE NOT REPEATED

SELECt COUNT(DISTINCT(sales.customers.city)) AS [unique cities]
FROM sales.customers

-- SUM FUNCTION

SELECT SUM(sales.order_items.list_price) AS [sum of price]
FROM sales.order_items
WHERE sales.order_items.order_id = 2

-- AVG FUNCTION

SELECT AVG(sales.order_items.list_price) AS [average of price]
FROM sales.order_items
WHERE sales.order_items.order_id = 2


-- MAX FUNCTION

SELECT MAX(sales.order_items.list_price) AS [maximum price]
FROM sales.order_items
WHERE sales.order_items.order_id = 2

-- MIN FUNCTION

SELECT MIN(sales.order_items.list_price) AS [minimum price]
FROM sales.order_items
WHERE sales.order_items.order_id = 2