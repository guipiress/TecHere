-- =========================================================================
-- 001_security_hardening.sql
--
-- Brings an EXISTING database in line with database/schema.sql.
-- Apply it to BOTH `techere` and `techere_test`:
--
--   psql -v ON_ERROR_STOP=1 -d techere      -f database/migrations/001_security_hardening.sql
--   psql -v ON_ERROR_STOP=1 -d techere_test -f database/migrations/001_security_hardening.sql
--
-- It runs in one transaction: if any statement fails, nothing is applied.
-- Safe to run more than once.
--
-- BEFORE RUNNING, look for data that would block the new constraints. Each of
-- these queries should return zero rows:
--
--   SELECT lower(email), count(*) FROM users    GROUP BY 1 HAVING count(*) > 1;
--   SELECT lower(name),  count(*) FROM category GROUP BY 1 HAVING count(*) > 1;
--   SELECT id FROM category WHERE length(trim(name))  = 0;
--   SELECT id FROM product  WHERE length(trim(name))  = 0 OR length(trim(brand)) = 0;
--   SELECT order_id, product_id, count(*) FROM order_items
--     GROUP BY 1, 2 HAVING count(*) > 1;
-- =========================================================================

BEGIN;

-- 1) Case-insensitive uniqueness ------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_key
    ON users (lower(email));

CREATE UNIQUE INDEX IF NOT EXISTS category_name_lower_key
    ON category (lower(name));

-- 2) Reject blank names/brands at the database level -----------------------
ALTER TABLE category DROP CONSTRAINT IF EXISTS category_name_not_blank;
ALTER TABLE category ADD CONSTRAINT category_name_not_blank
    CHECK (length(trim(name)) > 0);

ALTER TABLE product DROP CONSTRAINT IF EXISTS product_name_not_blank;
ALTER TABLE product ADD CONSTRAINT product_name_not_blank
    CHECK (length(trim(name)) > 0);

ALTER TABLE product DROP CONSTRAINT IF EXISTS product_brand_not_blank;
ALTER TABLE product ADD CONSTRAINT product_brand_not_blank
    CHECK (length(trim(brand)) > 0);

-- 3) One line per product in an order (the app already enforces this) ------
ALTER TABLE order_items DROP CONSTRAINT IF EXISTS order_items_order_product_key;
ALTER TABLE order_items ADD CONSTRAINT order_items_order_product_key
    UNIQUE (order_id, product_id);

-- 4) Indexes on foreign keys ------------------------------------------------
CREATE INDEX IF NOT EXISTS address_user_id_idx       ON address (user_id);
CREATE INDEX IF NOT EXISTS product_category_id_idx   ON product (category_id);
CREATE INDEX IF NOT EXISTS orders_user_id_idx        ON orders (user_id);
CREATE INDEX IF NOT EXISTS orders_address_id_idx     ON orders (address_id);
CREATE INDEX IF NOT EXISTS order_items_product_id_idx ON order_items (product_id);

-- 5) orders.created_at: TIMESTAMP -> TIMESTAMPTZ ----------------------------
-- Existing values were stored without a zone. They are interpreted in this
-- session's TimeZone, which is how they were written. Guarded so a second
-- run does not shift the data again.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'orders'
          AND column_name = 'created_at'
          AND data_type = 'timestamp without time zone'
    ) THEN
        UPDATE orders SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL;

        ALTER TABLE orders
            ALTER COLUMN created_at TYPE TIMESTAMPTZ
            USING created_at AT TIME ZONE current_setting('TimeZone');
    END IF;
END
$$;

ALTER TABLE orders ALTER COLUMN created_at SET NOT NULL;

-- 6) users.updated_at maintenance -------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_set_updated_at ON users;
CREATE TRIGGER users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

COMMIT;
