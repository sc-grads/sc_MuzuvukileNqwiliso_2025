USE BikeStores

SELECT * FROM sales.customers;
SELECT * FROM sales.order_items;
SELECT * FROM sales.orders;
SELECT * FROM sales.staffs;
SELECT * FROM sales.stores;

SELECT * FROM production.brands;
SELECT * FROM production.products;
SELECT * FROM production.categories;
SELECT * FROM production.stocks;

CREATE FUNCTION AllOrdersByDate(@date DATE) -- this code returns a table order details with the specified date
RETURNS TABLE
AS 
RETURN 
(
    SELECT 
        c.customer_id, 
        ord.shipped_date, 
        p.product_name
    FROM sales.customers c
    INNER JOIN sales.orders ord ON c.customer_id = ord.customer_id
    INNER JOIN sales.order_items ord_item ON ord.order_id = ord_item.order_id
    INNER JOIN production.products p ON ord_item.product_id = p.product_id
    WHERE CAST(ord.shipped_date AS DATE) = @date 
);

SELECT * FROM dbo.AllOrdersByDate('2016-01-06'); -- this statement excecutes the function 


CREATE FUNCTION getAverageOfYear(@year INT)
RETURNS TABLE 
AS 
RETURN 
		(
		SELECT model_year,FORMAT(AVG(list_price),'N2') AS [Average] -- the FORMAT function is a system funtion used to round the decimal to 2 points
		FROM production.products
		WHERE model_year = @year
		GROUP BY model_year
		)

SELECT * FROM dbo.getAverageOfYear(2017) -- this is used to run getAverageOfYear function

DROP FUNCTION dbo.getAverageOfYear -- this is used to delete getAverageOfYear


