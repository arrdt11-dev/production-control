from celery import states
from celery.exceptions import Ignore

from app.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def aggregate_products_batch(self, batch_id: int, unique_codes: list[str], user_id: int | None = None):
    """
    Асинхронная массовая агрегация продукции.
    Пока базовая реализация по ТЗ с прогрессом.
    """
    total = len(unique_codes)

    if total == 0:
        return {
            "success": True,
            "total": 0,
            "aggregated": 0,
            "failed": 0,
            "errors": [],
        }

    # Временная базовая реализация.
    # Следующим шагом подключим реальную логику через сервисы/БД.
    self.update_state(
        state="PROGRESS",
        meta={"current": 0, "total": total, "progress": 0},
    )

    aggregated = 0
    failed = 0
    errors: list[dict] = []

    for idx, code in enumerate(unique_codes, start=1):
        # пока заглушка: просто имитируем обработку
        failed += 1
        errors.append({"code": code, "reason": "not implemented yet"})

        progress = int(idx / total * 100)
        self.update_state(
            state="PROGRESS",
            meta={"current": idx, "total": total, "progress": progress},
        )

    return {
        "success": True,
        "total": total,
        "aggregated": aggregated,
        "failed": failed,
        "errors": errors,
    }