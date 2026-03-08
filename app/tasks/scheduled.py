from app.celery_app import celery_app


@celery_app.task
def auto_close_expired_batches():
    return {"success": True, "message": "scheduled task placeholder"}


@celery_app.task
def cleanup_old_files():
    return {"success": True, "message": "scheduled task placeholder"}


@celery_app.task
def update_cached_statistics():
    return {"success": True, "message": "scheduled task placeholder"}


@celery_app.task
def retry_failed_webhooks():
    return {"success": True, "message": "scheduled task placeholder"}