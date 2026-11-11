import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from psycopg import errors as pg_errors
from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool, PoolTimeout
from backend.app.api.routes.products import router as product_router
from backend.app.api.routes.category import router as category_router
from backend.app.api.routes import users
from backend.app.api.routes.orders import router as orders_router

load_dotenv()

logger = logging.getLogger("techere.api")

REQUIRED_DB_VARS = (
    "DB_HOST",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_PORT",
)

missing_vars = [
    name for name in REQUIRED_DB_VARS
    if not os.getenv(name)
]

if missing_vars:
    raise RuntimeError(
        "Variáveis de ambiente obrigatórias ausentes: "
        + ", ".join(missing_vars)
    )

# Set APP_ENV=production to hide the interactive docs / OpenAPI schema.
IS_PRODUCTION = os.getenv("APP_ENV", "development").lower() == "production"


def build_conninfo() -> str:
    # make_conninfo quotes and escapes every value. The previous f-string
    # broke (or allowed extra connection parameters to be injected) as soon as
    # a value contained a space or a quote, which is common in passwords.
    return make_conninfo(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT"),
        connect_timeout=5,
        # Server-side guard rails: a slow query, a stuck row lock or an
        # abandoned transaction cannot hold a pooled connection forever.
        options=(
            "-c statement_timeout=15000 "
            "-c lock_timeout=5000 "
            "-c idle_in_transaction_session_timeout=30000"
        ),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = ConnectionPool(
        conninfo=build_conninfo(),
        min_size=1,
        max_size=10,
        # Fail fast (HTTP 503) instead of letting requests queue for 30s
        # (the default) when every connection is busy.
        timeout=5.0,
        open=False,
        )

    app.state.pool.open()
    app.state.pool.wait()

    try:
        yield
    finally:
        app.state.pool.close()


app = FastAPI(
    lifespan=lifespan,
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)

app.include_router(product_router)
app.include_router(category_router)
app.include_router(users.router)
app.include_router(orders_router)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    # Responses carry personal data (CPF, e-mail, phone, orders).
    response.headers.setdefault("Cache-Control", "no-store")
    return response


# ---------------------------------------------------------------------------
# Database error handling
#
# Without these handlers any database error that a route does not catch
# itself becomes an opaque HTTP 500. The handlers translate them into the
# right status code and a generic message.
#
# The raw PostgreSQL message is deliberately NOT returned to the client and
# NOT logged: it contains table/constraint names and the offending values
# (for example "Key (email)=(x@y.com) already exists"), i.e. personal data.
# ---------------------------------------------------------------------------

def _db_error_response(
    request: Request,
    exc: Exception,
    status_code: int,
    detail: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    logger.warning(
        "database error on %s %s: %s (sqlstate=%s)",
        request.method,
        request.scope.get("path"),
        type(exc).__name__,
        getattr(exc, "sqlstate", None),
    )
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers=headers,
    )


@app.exception_handler(pg_errors.UniqueViolation)
async def unique_violation_handler(request: Request, exc: Exception):
    return _db_error_response(request, exc, 409, "Resource already exists")


@app.exception_handler(pg_errors.ForeignKeyViolation)
async def foreign_key_violation_handler(request: Request, exc: Exception):
    return _db_error_response(
        request, exc, 409, "Operation conflicts with related records"
    )


@app.exception_handler(pg_errors.NotNullViolation)
@app.exception_handler(pg_errors.CheckViolation)
@app.exception_handler(pg_errors.DataError)
async def invalid_data_handler(request: Request, exc: Exception):
    return _db_error_response(request, exc, 422, "Invalid data")


@app.exception_handler(pg_errors.IntegrityError)
async def integrity_error_handler(request: Request, exc: Exception):
    return _db_error_response(request, exc, 409, "Data integrity violation")


@app.exception_handler(PoolTimeout)
async def pool_timeout_handler(request: Request, exc: Exception):
    return _db_error_response(
        request,
        exc,
        503,
        "Service temporarily unavailable",
        headers={"Retry-After": "5"},
    )


@app.exception_handler(pg_errors.OperationalError)
async def operational_error_handler(request: Request, exc: Exception):
    # Covers lock/statement timeouts, deadlocks and lost connections.
    return _db_error_response(
        request,
        exc,
        503,
        "Service temporarily unavailable",
        headers={"Retry-After": "5"},
    )


@app.get("/")
async def root():
    return "Store"
