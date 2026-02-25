from fastapi import FastAPI

from app.api.v1 import batches_router, products_router

app = FastAPI(title="Production Control API", version="0.1.0")

app.include_router(batches_router)
app.include_router(products_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
