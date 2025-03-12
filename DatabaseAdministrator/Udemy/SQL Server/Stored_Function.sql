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

CREATE FUNCTION AllOrdersByDate(@date DATE)
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

SELECT * FROM dbo.AllOrdersByDate('2016-01-06');
