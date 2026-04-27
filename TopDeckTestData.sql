USE TopDeckCardShop;

-- 1. Insert Locations
INSERT INTO LOCATION (LOCATION_ID, LOCATION_ADDRESS) VALUES
(1, '123 Game Way, New York, NY'),
(2, '456 Hobby Lane, Los Angeles, CA'),
(3, '789 Collector St, Chicago, IL');

-- 2. Insert Customers
-- Note: Some of these will also be used as Cashiers/Managers
INSERT INTO CUSTOMER (CUSTOMER_ID, CUSTOMER_FNAME, CUSTOMER_LNAME, CUSTOMER_EMAIL, CUSTOMER_PHONE) VALUES
(101, 'Alice', 'Smith', 'alice.s@email.com', '555-0101'),
(102, 'Bob', 'Johnson', 'bob.j@email.com', '555-0102'),
(103, 'Charlie', 'Davis', 'charlie.d@email.com', '555-0103'),
(104, 'Diana', 'Prince', 'diana.p@email.com', '555-0104'),
(105, 'Ethan', 'Hunt', 'ethan.h@email.com', '555-0105');

-- 3. Insert Products
INSERT INTO PRODUCT (PRODUCT_ID, PRODUCT_NAME, PRODUCT_PRICEBOUGHT, PRODUCT_PRICELISTED, PRODUCT_STOCK) VALUES
(501, 'Black Lotus - Proxy', 5.00, 25.00, 10),
(502, 'Booster Pack: Neon Dynasty', 2.50, 4.99, 100),
(503, 'Dragon Shield Sleeves (Blue)', 6.00, 11.99, 50),
(504, 'Charizard VMAX', 40.00, 85.00, 3),
(505, 'Standard Playmat', 10.00, 19.99, 20);

-- 4. Insert Cashiers (linking to Customer IDs)
INSERT INTO CASHIER (CASHIER_ID, CASHIER_WAGE, CASHIER_HOURSWORKED, CUSTOMER_ID, LOCATION_ID) VALUES
(1, 15.50, 40, 101, 1),
(2, 16.00, 35, 102, 2);

-- 5. Insert Managers (linking to Customer IDs)
INSERT INTO MANAGER (MANAGER_ID, MANAGER_WAGE, MANAGER_HOURSWORKED, CUSTOMER_ID, LOCATION_ID) VALUES
(1, 25.00, 45, 103, 1),
(2, 27.50, 40, 104, 2);

-- 6. Insert Checkouts
-- (Checkout ID, Total Price, Date, Cashier ID, Customer ID)
INSERT INTO CHECKOUT (CHECKOUT_ID, CHECKOUT_TOTAL_PRICE, CHECKOUT_DATE, CASHIER_ID, CUSTOMER_ID) VALUES
(1001, 36.99, '2023-10-01', 1, 105),
(1002, 85.00, '2023-10-02', 2, 101),
(1003, 11.99, '2023-10-03', 1, 102);

-- 7. Insert Purchases (Line items for the checkouts above)
-- (Purchase ID, Quantity, Product ID, Checkout ID)
INSERT INTO PURCHASES (PURCHASES_ID, PURCHASES_QUANTITY, PRODUCT_ID, CHECKOUT_ID) VALUES
(1, 1, 501, 1001), -- 1 Black Lotus Proxy in Checkout 1001
(2, 2, 502, 1001), -- 2 Booster packs in Checkout 1001
(3, 1, 504, 1002), -- 1 Charizard in Checkout 1002
(4, 1, 503, 1003); -- 1 Blue Sleeves in Checkout 1003
