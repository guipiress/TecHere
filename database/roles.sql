-- =========================================================================
-- roles.sql  (OPTIONAL, recommended before any real deployment)
--
-- The application currently connects as the `postgres` superuser. A single
-- SQL-injection or logic bug would then expose the whole server, not just
-- this app's data. This creates a role that can only read and write the
-- application's tables: it cannot drop tables, create roles, or read other
-- databases.
--
-- 1. Replace the password placeholder below with a long random value
--    (do NOT commit the real one).
-- 2. Run as a superuser, connected to the `techere` database:
--      psql -d techere -f database/roles.sql
-- 3. Put the new user/password in .env (DB_USER / DB_PASSWORD).
--
-- Keep using a privileged account only for running schema migrations.
-- =========================================================================

CREATE ROLE techere_app LOGIN PASSWORD 'REPLACE_WITH_A_LONG_RANDOM_PASSWORD';

REVOKE ALL ON DATABASE techere FROM PUBLIC;
GRANT CONNECT ON DATABASE techere TO techere_app;

GRANT USAGE ON SCHEMA public TO techere_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO techere_app;

-- Tables created by later migrations get the same grants automatically.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO techere_app;
