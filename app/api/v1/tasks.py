from fastapi import APIRouter
from celery.result import AsyncResult

from app.celery_app import celery_app

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
