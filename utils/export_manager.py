"""
Funcționalitate de export în format PDF și CSV
Responsabil: Moscalu Sebastian
"""

from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QPainter, QFont, QColor, QPen, QPageSize
from PyQt6.QtCore import QRect, Qt, QDate
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
import csv
from datetime import datetime
from typing import List, Dict, Optional

class ExportManager:
    def __init__(self, parent_widget: Optional[QWidget] = None):
        self.parent = parent_widget
        
    def export_to_pdf(self, schedule_data: List[Dict], weather_data: Optional[Dict] = None, statistics: Optional[Dict] = None) -> bool:
        file_path, _ = QFileDialog.getSaveFileName(self.parent, "Salvează PDF", f"Raport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", "PDF (*.pdf)")
        if not file_path: return False
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            # CORECȚIE QT6
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            printer.setPageMargins(15, 15, 15, 15, QPrinter.Unit.Millimeter)
            
            painter = QPainter()
            if not painter.begin(printer): raise Exception("Eroare painter")
            self._draw_pdf_content(painter, printer, schedule_data, weather_data, statistics)
            painter.end()
            if self.parent: QMessageBox.information(self.parent, "Succes", "PDF salvat!")
            return True
        except Exception as e:
            if self.parent: QMessageBox.critical(self.parent, "Eroare PDF", str(e))
            return False

    def _draw_pdf_content(self, painter, printer, schedule_data, weather_data, statistics):
        page_rect = printer.pageRect(QPrinter.Unit.Point)
        page_width, page_height = int(page_rect.width()), int(page_rect.height())
        y = 50
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        painter.drawText(50, y, "WeatherScheduler Report")
        y += 60
        if statistics:
            painter.setFont(QFont("Arial", 12))
            painter.drawText(50, y, f"Temp Medie: {statistics.get('avg_temperature', 0):.1f}°C")
            y += 40
        # Tabel simplificat pentru export
        painter.setFont(QFont("Arial", 10))
        for entry in schedule_data:
            text = f"{entry.get('day')} | {entry.get('time')} | {entry.get('subject')}"
            painter.drawText(50, y, text)
            y += 25
            if y > page_height - 50:
                printer.newPage()
                y = 50

    def export_to_csv(self, schedule_data: List[Dict]) -> bool:
        file_path, _ = QFileDialog.getSaveFileName(self.parent, "Salvează CSV", "Raport.csv", "CSV (*.csv)")
        if not file_path: return False
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['Zi', 'Interval', 'Materie', 'Temp'])
                writer.writeheader()
                for e in schedule_data:
                    w = e.get('weather', {})
                    writer.writerow({'Zi': e.get('day'), 'Interval': e.get('time'), 'Materie': e.get('subject'), 'Temp': w.get('temperature', '')})
            return True
        except Exception as e:
            if self.parent: QMessageBox.critical(self.parent, "Eroare CSV", str(e))
            return False