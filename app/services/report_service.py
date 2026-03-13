from __future__ import annotations

from io import BytesIO
from typing import Any

from openpyxl import Workbook

from app.uow import UnitOfWork


class ReportService:
    @staticmethod
    async def build_batch_excel(batch_id: int) -> tuple[bytes, str]:
        async with UnitOfWork() as uow:
            batch = await uow.batches.get_by_id_with_products(batch_id)
            if not batch:
                raise ValueError("Batch not found")

            wb = Workbook()

            ws1 = wb.active
            ws1.title = "Информация о партии"
            ws1["A1"] = "Номер партии"
            ws1["B1"] = batch.batch_number
            ws1["A2"] = "Дата партии"
            ws1["B2"] = str(batch.batch_date)
            ws1["A3"] = "Статус"
            ws1["B3"] = "Закрыта" if batch.is_closed else "Открыта"
            ws1["A4"] = "Рабочий центр ID"
            ws1["B4"] = batch.work_center_id
            ws1["A5"] = "Смена"
            ws1["B5"] = batch.shift
            ws1["A6"] = "Бригада"
            ws1["B6"] = batch.team
            ws1["A7"] = "Номенклатура"
            ws1["B7"] = batch.nomenclature
            ws1["A8"] = "Код ЕКН"
            ws1["B8"] = batch.ekn_code
            ws1["A9"] = "Начало смены"
            ws1["B9"] = str(batch.shift_start)
            ws1["A10"] = "Окончание смены"
            ws1["B10"] = str(batch.shift_end)

            ws2 = wb.create_sheet("Продукция")
            ws2.append(["ID", "Уникальный код", "Агрегирована", "Дата агрегации"])
            for product in batch.products:
                ws2.append([
                    product.id,
                    product.unique_code,
                    "Да" if product.is_aggregated else "Нет",
                    str(product.aggregated_at) if product.aggregated_at else "-",
                ])

            total_products = len(batch.products)
            aggregated = sum(1 for p in batch.products if p.is_aggregated)
            remaining = total_products - aggregated
            rate = round((aggregated / total_products) * 100, 2) if total_products else 0

            ws3 = wb.create_sheet("Статистика")
            ws3["A1"] = "Всего продукции"
            ws3["B1"] = total_products
            ws3["A2"] = "Агрегировано"
            ws3["B2"] = aggregated
            ws3["A3"] = "Осталось"
            ws3["B3"] = remaining
            ws3["A4"] = "Процент выполнения"
            ws3["B4"] = f"{rate}%"

            stream = BytesIO()
            wb.save(stream)
            return stream.getvalue(), f"batch_{batch_id}_report.xlsx"
