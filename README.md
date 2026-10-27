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

- User management, including create, retrieve, update, and delete operations.
- Product and category API routes.
- Request data validation.
- PostgreSQL database integration.
- Automated tests for backend components.

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

Authentication, additional security controls, and further improvements to the testing infrastructure are planned as the project evolves.

## Running Tests

After installing the project dependencies and configuring the appropriate environment, run the test suite with:

```bash
python -m pytest -v
```

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
