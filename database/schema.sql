--===============================
--USERS
--===============================
CREATE TABLE users (
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
name VARCHAR(50) NOT NULL,
role VARCHAR(20) NOT NULL
 CHECK (role IN ('ADMIN', 'EMPLOYEE', 'CUSTOMER')      --roles: ADMIN, EMPLOYEE, CUSTOMER
),
email VARCHAR(255) UNIQUE NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
password_hash VARCHAR(255) NOT NULL,
telephone VARCHAR(20) NOT NULL,
cpf CHAR(11) UNIQUE NOT NULL
);


--===============================
--ADDRESS
--===============================
CREATE TABLE address (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    street VARCHAR(100) NOT NULL,
    street_number VARCHAR(10) NOT NULL,
    district VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    country CHAR(2) NOT NULL,
    complement VARCHAR(100)
);


--===============================
--CATEGORY
--===============================
CREATE TABLE category (
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
name VARCHAR(100) UNIQUE NOT NULL
);


--===============================
--PRODUCT
--===============================
CREATE TABLE product (
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
name VARCHAR(150) NOT NULL,
purchase_price NUMERIC(10,2) NOT NULL,
sale_price NUMERIC(10,2) NOT NULL,
stock INTEGER NOT NULL,
brand VARCHAR(50) NOT NULL,
category_id INTEGER NOT NULL REFERENCES category(id),
description TEXT
);


--===============================
--ORDERS
--===============================
CREATE TABLE order (
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
user_id INTEGER NOT NULL REFERENCES users(id),
address_id INTEGER NOT NULL REFERENCES address(id),
status VARCHAR(50) NOT NULL,
total_price NUMERIC(10,2) NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


--==============================
--order_items
--==============================
CREATE TABLE order_items (
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
order_id INTEGER NOT NULL REFERENCES orders(id),
product_id INTEGER NOT NULL REFERENCES product(id),
quantity INTEGER NOT NULL CHECK(quantity > 0),
unit_price NUMERIC(10,2) NOT NULL
);
