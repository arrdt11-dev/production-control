from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.models import Batch
from app.settings import settings
from app.storage.minio_service import MinioService

_sync_engine = None
_SyncSessionLocal = None


def get_sync_engine():
    global _sync_engine

    if _sync_engine is None:
        sync_database_url = settings.database_url.replace("+asyncpg", "")
        _sync_engine = create_engine(
            sync_database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=settings.db_pool_recycle,
            future=True,
        )

    return _sync_engine


def get_sync_session_local():
    global _SyncSessionLocal

    if _SyncSessionLocal is None:
        _SyncSessionLocal = sessionmaker(
            bind=get_sync_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    return _SyncSessionLocal


def _serialize_batch(batch: Batch) -> dict[str, Any]:
    return {
        "id": batch.id,
        "batch_number": batch.batch_number,
        "work_center_id": batch.work_center_id,
        "batch_date": str(batch.batch_date) if batch.batch_date else None,
        "shift_start": batch.shift_start.isoformat() if batch.shift_start else None,
        "shift_end": batch.shift_end.isoformat() if batch.shift_end else None,
        "task_description": batch.task_description,
        "shift": getattr(batch, "shift", "") or "",
        "team": getattr(batch, "team", "") or "",
        "nomenclature": getattr(batch, "nomenclature", "") or "",
        "ekn_code": getattr(batch, "ekn_code", "") or "",
        "is_closed": batch.is_closed,
        "created_at": batch.created_at.isoformat()
        if getattr(batch, "created_at", None)
        else None,
        "updated_at": batch.updated_at.isoformat()
        if getattr(batch, "updated_at", None)
        else None,
    }


@celery_app.task(name="app.tasks.import_export.export_batches_to_file")
def export_batches_to_file(batch_ids: list[int] | None = None) -> dict[str, Any]:
    db = get_sync_session_local()()
    minio_service = MinioService()

    try:
        stmt = select(Batch)
        if batch_ids:
            stmt = stmt.where(Batch.id.in_(batch_ids))

        batches = list(db.execute(stmt).scalars().all())

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(
            [
                "id",
                "batch_number",
                "work_center_id",
                "batch_date",
                "shift_start",
                "shift_end",
                "task_description",
                "shift",
                "team",
                "nomenclature",
                "ekn_code",
                "is_closed",
                "created_at",
                "updated_at",
            ]
        )

        for batch in batches:
            row = _serialize_batch(batch)
            writer.writerow(
                [
                    row["id"],
                    row["batch_number"],
                    row["work_center_id"],
                    row["batch_date"],
                    row["shift_start"],
                    row["shift_end"],
                    row["task_description"],
                    row["shift"],
                    row["team"],
                    row["nomenclature"],
                    row["ekn_code"],
                    row["is_closed"],
                    row["created_at"],
                    row["updated_at"],
                ]
            )

        content = output.getvalue().encode("utf-8")
        file_name = (
            f"batches_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        )

        file_url = minio_service.upload_bytes(
            bucket_name=settings.minio_bucket_exports,
            object_name=file_name,
            content=content,
            content_type="text/csv",
        )

        return {
            "success": True,
            "file_name": file_name,
            "file_url": file_url,
            "exported_count": len(batches),
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.import_export.import_batches_from_file")
def import_batches_from_file(file_bytes: bytes, filename: str) -> dict[str, Any]:
    db = get_sync_session_local()()

    created = 0
    skipped = 0
    errors: list[dict[str, Any]] = []

    try:
        decoded = file_bytes.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))

        for index, row in enumerate(reader, start=2):
            try:
                with db.begin_nested():
                    batch_number_raw = row.get("batch_number")
                    work_center_id_raw = row.get("work_center_id")
                    batch_date_raw = row.get("batch_date")
                    shift_start_raw = row.get("shift_start")
                    shift_end_raw = row.get("shift_end")
                    task_description = row.get("task_description") or ""

                    if not batch_number_raw:
                        raise ValueError("batch_number is required")
                    if not work_center_id_raw:
                        raise ValueError("work_center_id is required")
                    if not batch_date_raw:
                        raise ValueError("batch_date is required")
                    if not shift_start_raw:
                        raise ValueError("shift_start is required")
                    if not shift_end_raw:
                        raise ValueError("shift_end is required")

                    batch_number = int(batch_number_raw)
                    work_center_id = int(work_center_id_raw)
                    batch_date = datetime.fromisoformat(batch_date_raw).date()
                    shift_start = datetime.fromisoformat(
                        shift_start_raw.replace("Z", "+00:00")
                    )
                    shift_end = datetime.fromisoformat(
                        shift_end_raw.replace("Z", "+00:00")
                    )

                    existing = db.execute(
                        select(Batch).where(Batch.batch_number == batch_number)
                    ).scalar_one_or_none()

                    if existing is not None:
                        raise ValueError(f"batch_number={batch_number} already exists")

                    batch = Batch(
                        batch_number=batch_number,
                        work_center_id=work_center_id,
                        batch_date=batch_date,
                        shift_start=shift_start,
                        shift_end=shift_end,
                        task_description=task_description,
                        shift=row.get("shift") or "",
                        team=row.get("team") or "",
                        nomenclature=row.get("nomenclature") or "",
                        ekn_code=row.get("ekn_code") or "",
                        is_closed=str(row.get("is_closed", "false")).lower() == "true",
                    )

                    db.add(batch)
                    db.flush()
                    created += 1

            except Exception as exc:
                skipped += 1
                errors.append(
                    {
                        "row": index,
                        "error": str(exc),
                    }
                )

        db.commit()

        return {
            "success": True,
            "filename": filename,
            "created": created,
            "skipped": skipped,
            "errors": errors,
        }

    except SQLAlchemyError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()