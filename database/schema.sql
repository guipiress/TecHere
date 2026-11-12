--===============================
--USERS
--===============================
CREATE TABLE users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'CUSTOMER'
        CHECK (role IN ('ADMIN', 'EMPLOYEE', 'CUSTOMER')),
    telephone VARCHAR(20),
    cpf CHAR(11) UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_name_not_blank
        CHECK (length(trim(name)) > 0),
    CONSTRAINT users_email_not_blank
        CHECK (length(trim(email)) > 0),
    CONSTRAINT users_cpf_digits
        CHECK (cpf IS NULL OR cpf ~ '^[0-9]{11}$')
);

-- E-mail must be unique regardless of case ("Ana@x.com" == "ana@x.com").
CREATE UNIQUE INDEX users_email_lower_key ON users (lower(email));

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

-- PostgreSQL does not index foreign keys automatically.
CREATE INDEX address_user_id_idx ON address (user_id);


--===============================
--CATEGORY
--===============================
CREATE TABLE category (
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
name VARCHAR(100) UNIQUE NOT NULL,
CONSTRAINT category_name_not_blank
    CHECK (length(trim(name)) > 0)
);

CREATE UNIQUE INDEX category_name_lower_key ON category (lower(name));


--===============================
--PRODUCT
--===============================
CREATE TABLE product (
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
name VARCHAR(150) NOT NULL,
purchase_price NUMERIC(10,2) NOT NULL
    CHECK(purchase_price >= 0),
sale_price NUMERIC(10,2) NOT NULL
    CHECK(sale_price >= 0),
stock INTEGER NOT NULL
    CHECK(stock >= 0),
brand VARCHAR(50) NOT NULL,
category_id INTEGER NOT NULL REFERENCES category(id),
description TEXT,
CONSTRAINT product_name_not_blank
    CHECK (length(trim(name)) > 0),
CONSTRAINT product_brand_not_blank
    CHECK (length(trim(brand)) > 0)
);

CREATE INDEX product_category_id_idx ON product (category_id);


--===============================
--ORDERS
--===============================
CREATE TABLE orders (
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
user_id INTEGER NOT NULL REFERENCES users(id),
address_id INTEGER NOT NULL REFERENCES address(id),
status VARCHAR(20) NOT NULL
    CHECK (status IN ('PENDING', 'PAID', 'CANCELLED')),
total_price NUMERIC(10,2) NOT NULL
    CHECK (total_price >= 0),
created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX orders_user_id_idx ON orders (user_id);
CREATE INDEX orders_address_id_idx ON orders (address_id);


--==============================
--order_items
--==============================
CREATE TABLE order_items (
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
order_id INTEGER NOT NULL REFERENCES orders(id),
product_id INTEGER NOT NULL REFERENCES product(id),
quantity INTEGER NOT NULL
    CHECK(quantity > 0),
unit_price NUMERIC(10,2) NOT NULL
    CHECK(unit_price >=0),
CONSTRAINT order_items_order_product_key
    UNIQUE (order_id, product_id)
);

-- order_id is already covered by the UNIQUE (order_id, product_id) index.
CREATE INDEX order_items_product_id_idx ON order_items (product_id);


--==============================
--updated_at maintenance
--==============================
-- The application never sets users.updated_at, so without this trigger it
-- would stay equal to created_at forever.
CREATE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
