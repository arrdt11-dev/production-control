from fastapi import FastAPI
from app.api.v1.tasks import router as tasks_router
from app.api.v1.batches import router as batches_router
from app.api.v1.products import router as products_router
from app.api.v1.work_centers import router as work_centers_router

app = FastAPI(title="Production Control API", version="1.0.0")

app.include_router(batches_router)
app.include_router(products_router)
app.include_router(work_centers_router)
app.include_router(tasks_router) 

@app.get("/health")
async def health():
    return {"status": "ok"}
