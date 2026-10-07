import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from psycopg_pool import ConnectionPool
from backend.app.api.routes.products import router as product_router
from backend.app.api.routes.category import router as category_router


load_dotenv()


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
        max_size=10
    )

    yield

    app.state.pool.close()


app = FastAPI(lifespan=lifespan)

app.include_router(product_router)
app.include_router(category_router)


@app.get("/")
async def root():
    return "Store"
