# TecHere

A backend application for managing the operations of a technology store, developed with Python, FastAPI, and PostgreSQL.

## Overview

TecHere is a project focused on building a structured backend for a technology store management system. It aims to provide a foundation for managing users, products, categories, customers' orders, and related data.

The project is being developed with an emphasis on API design, data validation, database integration, and automated testing.

## Technologies

- **Python** — Backend development.
- **FastAPI** — REST API development.
- **PostgreSQL** — Relational database.
- **Psycopg 3** — PostgreSQL connectivity.
- **pytest** — Automated testing.

## Features

The project includes backend functionality for:

- User management: public sign-up, profile read/update, admin-only listing and deletion.
- JWT authentication (`POST /auth/login`) with role-based authorization.
- Product and category API routes (public catalogue, staff-managed).
- Orders with stock locking, ownership checks and a status workflow.
- Request data validation aligned with the database schema.
- PostgreSQL database integration.
- Automated tests for backend components.

## Authentication and roles

Log in with `POST /auth/login` (`{"email", "password"}`) and send the returned
token as `Authorization: Bearer <token>`. Tokens expire after
`ACCESS_TOKEN_EXPIRE_MINUTES` (default 30). The user's role and active flag are
read from the database on every request, so deactivating an account or changing
its role takes effect immediately.

| Area | Anonymous | CUSTOMER | EMPLOYEE | ADMIN |
|---|---|---|---|---|
| `POST /users` (sign-up) | yes | | | |
| `GET /products`, `/categories` (no purchase price) | yes | yes | yes | yes |
| Create / update products and categories | | | yes | yes |
| Delete products and categories | | | | yes |
| `GET /users/me`, own profile (name, phone) | | yes | yes | yes |
| Change an e-mail, read another user, list or delete users | | | | yes |
| Create orders; list / read **own** orders | | yes | yes | yes |
| List / read **all** orders, change order status | | | yes | yes |

Rules live next to each route (`Depends(require_staff)`, `Depends(require_admin)`,
`ensure_self_or_roles`). A test (`tests/security/test_route_protection.py`) fails
if a new route is left without authentication.

### Creating the first administrator

There is deliberately no API to grant roles. Register a normal account with
`POST /users`, then promote it directly in the database:

```sql
UPDATE users SET role = 'ADMIN' WHERE email = 'you@example.com';
```

## Configuration

Copy `.env.example` to `.env`. `SECRET_KEY` is required and must be at least 32
bytes (the app refuses to start otherwise):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Set `APP_ENV=production` to hide `/docs`, `/redoc` and `/openapi.json`.

## Database

The database schema defines the following entities:

- Users
- Addresses
- Categories
- Products
- Orders
- Order items

The schema uses relational constraints to represent relationships between entities and enforce data integrity.

## Project Status

**Under development.**

Planned: address management endpoints (an order needs an address that belongs to the buyer), password change and reset, e-mail verification, audit logging and payment integration.

## Database setup

Create the database, apply `database/schema.sql`, and for an existing database
apply the migrations in `database/migrations/` in order (each runs in a
transaction and can be repeated). `database/roles.sql` creates a role with only
the privileges the application needs; use it instead of the `postgres`
superuser.

## Running Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -v
```

The unit tests need neither PostgreSQL nor a `.env`. The integration tests
(`tests/integration`) use a real database named `techere_test`, configured in
`.env.test` (`TEST_DB_*`), and refuse to run against any other database.

## Running in production

- Run behind a TLS-terminating reverse proxy; the app does not enforce HTTPS or
  send HSTS itself.
- Start uvicorn with `--proxy-headers` and a trusted `--forwarded-allow-ips`, or
  the login rate limiter will see the proxy's address for every client.
- The login and sign-up limiters are in-memory and per process. With several
  workers (or after a restart) the counters are not shared; use a shared store
  such as Redis if that matters.
- There is no password reset, e-mail verification, token revocation or refresh
  token yet.

## API Documentation

When the application is running, FastAPI provides interactive API documentation through Swagger UI, typically available at:

- `http://127.0.0.1:8000/docs`

The actual available endpoints depend on the current application implementation.

## Security

- Do not commit environment files containing credentials.
- Configure database connection settings through environment variables.
- Use a separate test database for integration tests.

## License

No license has been specified yet.
