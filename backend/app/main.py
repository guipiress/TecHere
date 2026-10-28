import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from psycopg_pool import ConnectionPool
from backend.app.api.routes.products import router as product_router
from backend.app.api.routes.category import router as category_router
from backend.app.api.routes import users
from backend.app.api.routes.orders import router as orders_router

load_dotenv()

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



@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = ConnectionPool(
        conninfo=(
            f"host={os.getenv('DB_HOST')} "
            f"dbname={os.getenv('DB_NAME')} "
            f"user={os.getenv('DB_USER')} "
            f"password={os.getenv('DB_PASSWORD')} "
            f"port={os.getenv('DB_PORT')}"
        ),
        min_size=1,
        max_size=10,
        open=False,
        )

    app.state.pool.open()
    app.state.pool.wait()

    try:
        yield
    finally:
        app.state.pool.close()


app = FastAPI(lifespan=lifespan)

app.include_router(product_router)
app.include_router(category_router)
app.include_router(users.router)
app.include_router(orders_router)

@app.get("/")
async def root():
    return "Store"
