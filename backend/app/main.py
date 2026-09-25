from fastapi import FastAPI
from backend.app.api.routes.products import router


app = FastAPI()

app.include_router(router)


@app.get("/")
async def root():
    return "Store"
