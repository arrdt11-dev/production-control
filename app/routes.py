from fastapi import APIRouter

from app.api.v1.batches import router as batches_router
from app.api.v1.products import router as products_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.work_centers import router as work_centers_router
from app.api.v1.analytics import router as analytics_router

router = APIRouter()

router.include_router(work_centers_router)
router.include_router(batches_router)
router.include_router(products_router)
router.include_router(tasks_router)
router.include_router(webhooks_router)
router.include_router(analytics_router)
