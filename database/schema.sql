--===============================
--USERS
CREATE TABLE users (
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
name VARCHAR(50) NOT NULL,
role VARCHAR(20) NOT NULL,      --roles: ADMIN, EMPLOYEE, CUSTOMER
email VARCHAR(255) UNIQUE NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
password_hash VARCHAR(255) NOT NULL,
telephone VARCHAR(20) NOT NULL,
cpf CHAR(11) UNIQUE NOT NULL
);


--===============================
--ADDRESS
CREATE TABLE address (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    street VARCHAR(100) NOT NULL,
    street_number VARCHAR(10) NOT NULL,
    district VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    zip_code VARCHAR(20) NOT NULL,
    country CHAR(2) NOT NULL,
    complement VARCHAR(100)
);


--================================
--CATEGORY
CREATE TABLE category (
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
name VARCHAR(100) UNIQUE NOT NULL
);

