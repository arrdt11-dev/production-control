import asyncio
import os
import tempfile
from datetime import datetime
from uuid import uuid4

import pandas as pd
from celery import shared_task
from sqlalchemy import select

from app.database import async_session
from app.models import Batch, WorkCenter
from app.settings import settings
from app.storage.minio_service import MinIOService


def _normalize_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y", "да"}


def _to_naive_dt(value):
    if value is None:
        return None
    if getattr(value, "tzinfo", None) is not None:
        return value.replace(tzinfo=None)
    return value


def _read_import_file(file_path: str) -> list[dict]:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Use csv/xlsx/xls")

    df = df.where(pd.notna(df), None)
    return df.to_dict(orient="records")


def _map_import_row(row: dict) -> dict:
    return {
        "is_closed": _normalize_bool(row.get("СтатусЗакрытия", False)),
        "task_description": str(row["ПредставлениеЗаданияНаСмену"]).strip(),
        "work_center_name": str(row["РабочийЦентр"]).strip(),
        "shift": str(row["Смена"]).strip(),
        "team": str(row["Бригада"]).strip(),
        "batch_number": int(row["НомерПартии"]),
        "batch_date": pd.to_datetime(row["ДатаПартии"]).date(),
        "nomenclature": str(row["Номенклатура"]).strip(),
        "ekn_code": str(row["КодЕКН"]).strip(),
        "work_center_identifier": str(row["ИдентификаторРЦ"]).strip(),
        "shift_start": _to_naive_dt(pd.to_datetime(row["ДатаВремяНачалаСмены"]).to_pydatetime()),
        "shift_end": _to_naive_dt(pd.to_datetime(row["ДатаВремяОкончанияСмены"]).to_pydatetime()),
    }


async def _import_batches_async(task, bucket: str, object_name: str):
    minio = MinIOService()

    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = os.path.join(tmpdir, os.path.basename(object_name))
        minio.download_file(bucket=bucket, object_name=object_name, file_path=local_path)

        rows = _read_import_file(local_path)
        total_rows = len(rows)

        created = 0
        skipped = 0
        errors: list[dict] = []

        async with async_session() as db:
            for index, row in enumerate(rows, start=1):
                try:
                    mapped = _map_import_row(row)

                    wc_result = await db.execute(
                        select(WorkCenter).where(
                            WorkCenter.identifier == mapped["work_center_identifier"]
                        )
                    )
                    work_center = wc_result.scalar_one_or_none()

                    if work_center is None:
                        work_center = WorkCenter(
                            identifier=mapped["work_center_identifier"],
                            name=mapped["work_center_name"],
                        )
                        db.add(work_center)
                        await db.flush()

                    batch_result = await db.execute(
                        select(Batch).where(
                            Batch.batch_number == mapped["batch_number"],
                            Batch.batch_date == mapped["batch_date"],
                        )
                    )
                    existing_batch = batch_result.scalar_one_or_none()

                    if existing_batch:
                        skipped += 1
                        errors.append(
                            {"row": index, "error": "Duplicate batch number and date"}
                        )
                    else:
                        batch = Batch(
                            is_closed=mapped["is_closed"],
                            closed_at=None,
                            task_description=mapped["task_description"],
                            work_center_id=work_center.id,
                            shift=mapped["shift"],
                            team=mapped["team"],
                            batch_number=mapped["batch_number"],
                            batch_date=mapped["batch_date"],
                            nomenclature=mapped["nomenclature"],
                            ekn_code=mapped["ekn_code"],
                            shift_start=mapped["shift_start"],
                            shift_end=mapped["shift_end"],
                        )
                        db.add(batch)
                        await db.flush()
                        created += 1

                    task.update_state(
                        state="PROGRESS",
                        meta={
                            "current": index,
                            "total": total_rows,
                            "created": created,
                            "skipped": skipped,
                        },
                    )

                except Exception as e:
                    await db.rollback()
                    skipped += 1
                    errors.append({"row": index, "error": str(e)})

            await db.commit()

        return {
            "success": True,
            "total_rows": total_rows,
            "created": created,
            "skipped": skipped,
            "errors": errors,
        }


@shared_task(bind=True, max_retries=1)
def import_batches_from_file(self, bucket: str, object_name: str, user_id: int | None = None):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_import_batches_async(self, bucket, object_name))
    finally:
        loop.close()


async def _export_batches_async(filters: dict, format: str):
    async with async_session() as db:
        stmt = (
            select(Batch, WorkCenter)
            .join(WorkCenter, Batch.work_center_id == WorkCenter.id)
            .order_by(Batch.id.desc())
        )

        if filters.get("is_closed") is not None:
            stmt = stmt.where(Batch.is_closed == filters["is_closed"])
        if filters.get("batch_number") is not None:
            stmt = stmt.where(Batch.batch_number == filters["batch_number"])
        if filters.get("date_from") is not None:
            stmt = stmt.where(Batch.batch_date >= filters["date_from"])
        if filters.get("date_to") is not None:
            stmt = stmt.where(Batch.batch_date <= filters["date_to"])
        if filters.get("shift") is not None:
            stmt = stmt.where(Batch.shift == filters["shift"])
        if filters.get("work_center_id") is not None:
            stmt = stmt.where(Batch.work_center_id == filters["work_center_id"])

        result = await db.execute(stmt)
        rows = result.all()

        data = []
        for batch, work_center in rows:
            data.append(
                {
                    "ID": batch.id,
                    "СтатусЗакрытия": batch.is_closed,
                    "ДатаЗакрытия": _to_naive_dt(batch.closed_at),
                    "ПредставлениеЗаданияНаСмену": batch.task_description,
                    "РабочийЦентр": work_center.name,
                    "ИдентификаторРЦ": work_center.identifier,
                    "Смена": batch.shift,
                    "Бригада": batch.team,
                    "НомерПартии": batch.batch_number,
                    "ДатаПартии": batch.batch_date,
                    "Номенклатура": batch.nomenclature,
                    "КодЕКН": batch.ekn_code,
                    "ДатаВремяНачалаСмены": _to_naive_dt(batch.shift_start),
                    "ДатаВремяОкончанияСмены": _to_naive_dt(batch.shift_end),
                    "Создано": _to_naive_dt(batch.created_at),
                    "Обновлено": _to_naive_dt(batch.updated_at),
                }
            )

        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            ext = "xlsx" if format == "excel" else "csv"
            filename = f"batches_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}.{ext}"
            local_path = os.path.join(tmpdir, filename)

            if format == "excel":
                df.to_excel(local_path, index=False)
            elif format == "csv":
                df.to_csv(local_path, index=False)
            else:
                raise ValueError("Unsupported export format")

            minio = MinIOService()
            upload_result = minio.upload_file(
                bucket=settings.minio_bucket_exports,
                file_path=local_path,
                object_name=filename,
                expires_days=7,
            )

            return {
                "success": True,
                "file_url": upload_result["file_url"],
                "file_name": filename,
                "file_size": upload_result["file_size"],
                "total_batches": len(data),
            }


@shared_task(bind=True)
def export_batches_to_file(self, filters: dict, format: str = "excel"):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_export_batches_async(filters, format))
    finally:
        loop.close()
