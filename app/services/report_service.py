from io import BytesIO
from datetime import datetime, timedelta, UTC
from openpyxl import Workbook
from openpyxl.styles import Font


class ReportService:
    @staticmethod
    def generate_batch_report(batch) -> tuple[BytesIO, int]:
        wb = Workbook()

        # Лист 1: Summary
        ws_summary = wb.active
        ws_summary.title = "Summary"

        ws_summary["A1"] = "Batch Report"
        ws_summary["A1"].font = Font(bold=True, size=14)

        ws_summary["A3"] = "Batch ID"
        ws_summary["B3"] = batch.id

        ws_summary["A4"] = "Batch Name"
        ws_summary["B4"] = getattr(batch, "name", "")

        ws_summary["A5"] = "Created At"
        ws_summary["B5"] = str(getattr(batch, "created_at", ""))

        products = getattr(batch, "products", []) or []

        ws_summary["A6"] = "Products Count"
        ws_summary["B6"] = len(products)

        # Лист 2: Products
        ws_products = wb.create_sheet("Products")
        headers = ["ID", "Name", "Code", "Quantity", "Price"]

        for col_num, header in enumerate(headers, start=1):
            cell = ws_products.cell(row=1, column=col_num, value=header)
            cell.font = Font(bold=True)

        total_quantity = 0
        total_price = 0

        for row_num, product in enumerate(products, start=2):
            quantity = getattr(product, "quantity", 0) or 0
            price = getattr(product, "price", 0) or 0

            ws_products.cell(row=row_num, column=1, value=getattr(product, "id", None))
            ws_products.cell(row=row_num, column=2, value=getattr(product, "name", ""))
            ws_products.cell(row=row_num, column=3, value=getattr(product, "code", ""))
            ws_products.cell(row=row_num, column=4, value=quantity)
            ws_products.cell(row=row_num, column=5, value=price)

            total_quantity += quantity
            total_price += price

        # Лист 3: Statistics
        ws_stats = wb.create_sheet("Statistics")
        ws_stats["A1"] = "Statistics"
        ws_stats["A1"].font = Font(bold=True, size=14)

        ws_stats["A3"] = "Total Products"
        ws_stats["B3"] = len(products)

        ws_stats["A4"] = "Total Quantity"
        ws_stats["B4"] = total_quantity

        ws_stats["A5"] = "Total Price"
        ws_stats["B5"] = total_price

        ws_stats["A6"] = "Generated At"
        ws_stats["B6"] = datetime.now(UTC).isoformat()

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        file_size = len(output.getvalue())
        return output, file_size

    @staticmethod
    def build_report_result(file_url: str, file_size: int, expires_in_hours: int = 24) -> dict:
        expires_at = datetime.now(UTC) + timedelta(hours=expires_in_hours)
        return {
            "file_url": file_url,
            "file_size": file_size,
            "expires_at": expires_at.isoformat()
        }