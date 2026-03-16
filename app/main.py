from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.tasks import router as tasks_router
from app.api.v1.batches import router as batches_router
from app.api.v1.products import router as products_router
from app.api.v1.work_centers import router as work_centers_router
from app.api.v1.webhooks import router as webhooks_router
from app.storage.minio_service import MinIOService


@asynccontextmanager
async def lifespan(app: FastAPI):
    MinIOService().ensure_all_buckets()
    yield


app = FastAPI(
    title="Production Control API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(batches_router)
app.include_router(products_router)
app.include_router(work_centers_router)
app.include_router(tasks_router)
app.include_router(webhooks_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
