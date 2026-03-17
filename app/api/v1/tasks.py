from fastapi import APIRouter
from celery.result import AsyncResult

from app.celery_app import celery_app

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    try:
        result = AsyncResult(task_id, app=celery_app)

        status = result.status

        if status == "PROGRESS":
            return {
                "task_id": task_id,
                "status": status,
                "result": result.info,
            }

        if status == "FAILURE":
            info = result.info
            return {
                "task_id": task_id,
                "status": status,
                "result": {
                    "success": False,
                    "error": str(info),
                },
            }

        return {
            "task_id": task_id,
            "status": status,
            "result": result.result if result.ready() else None,
        }
    except Exception as e:
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "result": {
                "success": False,
                "error": f"Failed to read task result: {str(e)}",
            },
        }