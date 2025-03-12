-- Select the BikeStores database
USE BikeStores;
GO

-- View all data from the sales schema tables
SELECT * FROM sales.customers;
SELECT * FROM sales.order_items;
SELECT * FROM sales.orders;
SELECT * FROM sales.staffs;
SELECT * FROM sales.stores;

-- View all data from the products schema tables
SELECT * FROM production.brands;
SELECT * FROM production.products;
SELECT * FROM production.categories;
SELECT * FROM production.stocks;

-- Retrieve store details with associated staff names
SELECT 
    s.store_id,
    s.store_name,
    s.phone,
    s.email,
    s.street,
    s.city,
    s.state,
    s.zip_code,
    st.first_name AS staff_name
FROM sales.stores AS s
LEFT JOIN sales.staffs AS st 
    ON s.store_id = st.store_id;

-- Retrieve customers and their corresponding orders
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.phone,
    c.email,
    c.street,
    c.city,
    c.state,
    c.zip_code,
    o.order_id,
    o.order_status,
    o.order_date,
    o.required_date,
    o.shipped_date,
    o.store_id,
    o.staff_id
FROM sales.customers AS c
LEFT JOIN sales.orders AS o 
    ON c.customer_id = o.customer_id;

-- View all sales staff members
SELECT * FROM sales.staffs;

