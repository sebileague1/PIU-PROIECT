from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QPainter, QFont, QColor, QPen, QFontMetrics
from PyQt6.QtCore import Qt, QRect, QRectF, QMarginsF
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget

import csv
from datetime import datetime
from typing import List, Dict, Optional


class ExportManager:
    def __init__(self, parent_widget: Optional[QWidget] = None):
        self.parent = parent_widget

    def export_to_pdf(
        self,
        schedule_data: List[Dict],
        weather_data: Optional[Dict] = None,
        statistics: Optional[Dict] = None
    ) -> bool:

        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Salvează raport PDF",
            f"WeatherScheduler_Raport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF (*.pdf)"
        )
        if not file_path:
            return False

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageMargins(QMarginsF(15, 15, 15, 15))

            painter = QPainter(printer)
            if not painter.isActive():
                raise RuntimeError("Nu s-a putut inițializa QPainter")

            page_rect = printer.pageRect(QPrinter.Unit.Point)
            page_width = int(page_rect.width())
            page_height = int(page_rect.height())

            y = 40
            painter.setFont(QFont("Arial", 20, QFont.Weight.Bold))
            painter.setPen(QColor(0, 51, 102))
            painter.drawText(
                QRectF(0, y, page_width, 40),
                Qt.AlignmentFlag.AlignCenter,
                "Raport WeatherScheduler"
            )
            y += 50

            painter.setFont(QFont("Arial", 10))
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(40, y, f"Generat la: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            y += 30

            if statistics:
                painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
                painter.drawText(40, y, "Statistici generale:")
                y += 22

                painter.setFont(QFont("Arial", 10))
                unit = statistics.get("unit", "°C")

                for line in [
                    f"Temperatură medie: {statistics.get('avg_temperature', 0):.1f}{unit}",
                    f"Temperatură minimă: {statistics.get('min_temperature', 0):.1f}{unit}",
                    f"Temperatură maximă: {statistics.get('max_temperature', 0):.1f}{unit}",
                    f"Total precipitații: {statistics.get('total_precipitation', 0):.1f} mm",
                    f"Perioade cu risc de ploaie: {statistics.get('rainy_periods', 0)}"
                ]:
                    painter.drawText(60, y, line)
                    y += 18

                y += 20

            headers = ["Zi", "Interval", "Activitate", "Temperatura", "Condiții", "Ploaie"]
            col_widths = [70, 90, 260, 90, 130, 60]
            x_positions = [40]

            for w in col_widths[:-1]:
                x_positions.append(x_positions[-1] + w)

            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            header_height = 28

            for i, header in enumerate(headers):
                painter.drawText(
                    QRectF(x_positions[i], y, col_widths[i], header_height),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    header
                )

            y += header_height
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.drawLine(40, y, page_width - 40, y)
            y += 6

            painter.setFont(QFont("Arial", 9))
            metrics = QFontMetrics(painter.font())

            for entry in schedule_data:
                weather = entry.get("weather", {})

                values = [
                    entry.get("day", "-"),
                    entry.get("time", "-"),
                    entry.get("subject", "-"),
                    weather.get("temperature", "-"),
                    weather.get("weather_description", "-"),
                    f"{weather.get('precipitation_probability', 0)}%"
                ]

                activity_rect = metrics.boundingRect(
                    QRect(0, 0, col_widths[2], 1000),
                    Qt.TextFlag.TextWordWrap,
                    values[2]
                )

                row_height = max(28, activity_rect.height() + 10)

                if y + row_height > page_height - 50:
                    printer.newPage()
                    y = 40

                for i, value in enumerate(values):
                    flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop

                    if i == 2: 
                        flags |= Qt.TextFlag.TextWordWrap

                    painter.drawText(
                        QRectF(x_positions[i], y, col_widths[i], row_height),
                        flags,
                        str(value)
                    )

                y += row_height

            painter.setFont(QFont("Arial", 8))
            painter.setPen(QColor(120, 120, 120))
            painter.drawText(
                QRectF(40, page_height - 30, page_width - 80, 20),
                Qt.AlignmentFlag.AlignCenter,
                "WeatherScheduler - Planificator Meteo Orar | Generat automat"
            )

            painter.end()

            QMessageBox.information(self.parent, "Export PDF", "Raport PDF generat corect.")
            return True

        except Exception as e:
            QMessageBox.critical(self.parent, "Eroare PDF", str(e))
            return False

    def export_to_csv(self, schedule_data: List[Dict]) -> bool:
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Salvează raport CSV",
            f"WeatherScheduler_Raport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV (*.csv)"
        )
        if not file_path:
            return False

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Zi", "Interval", "Activitate", "Temperatura", "Condiții", "Ploaie"])

                for e in schedule_data:
                    w = e.get("weather", {})
                    writer.writerow([
                        e.get("day", "-"),
                        e.get("time", "-"),
                        e.get("subject", "-"),
                        w.get("temperature", "-"),
                        w.get("weather_description", "-"),
                        f"{w.get('precipitation_probability', 0)}%"
                    ])

            QMessageBox.information(self.parent, "Export CSV", "CSV salvat corect.")
            return True

        except Exception as e:
            QMessageBox.critical(self.parent, "Eroare CSV", str(e))
            return False
