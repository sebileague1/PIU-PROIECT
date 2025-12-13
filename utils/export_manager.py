from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QPainter, QFont, QColor, QPen, QPageSize, QPageLayout
from PyQt6.QtCore import QRect, Qt, QMarginsF
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
import csv
from datetime import datetime
from typing import List, Dict, Optional

class ExportManager:
    def __init__(self, parent_widget: Optional[QWidget] = None):
        self.parent = parent_widget
        
    def export_to_pdf(self, schedule_data: List[Dict], weather_data: Optional[Dict] = None, statistics: Optional[Dict] = None) -> bool:
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent, 
            "Salvează raportul PDF", 
            f"WeatherScheduler_Raport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
            "Fișiere PDF (*.pdf)"
        )
        
        if not file_path:
            return False
            
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            
            page_size = QPageSize(QPageSize.PageSizeId.A4)
            page_layout = QPageLayout(page_size, QPageLayout.Orientation.Portrait, QMarginsF(15, 15, 15, 15))
            printer.setPageLayout(page_layout)
            
            painter = QPainter()
            if not painter.begin(printer):
                raise Exception("Nu s-a putut inițializa motorul de desenare PDF.")
                
            self._draw_pdf_content(painter, printer, schedule_data, weather_data, statistics)
            
            painter.end()
            
            if self.parent:
                QMessageBox.information(self.parent, "Export reușit", f"Raportul PDF a fost salvat la:\n{file_path}")
            return True
            
        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "Eroare export PDF", f"Eroare critică: {str(e)}")
            return False

    def _draw_pdf_content(self, painter, printer, schedule_data, weather_data, statistics):
        
        unit_symbol = statistics.get('unit', '°C') if statistics else '°C'
        
        page_rect = printer.pageRect(QPrinter.Unit.Point)
        width = int(page_rect.width())
        height = int(page_rect.height())
        
        y = 50
        
        painter.setPen(QColor(0, 51, 102))
        painter.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        painter.drawText(50, y, "Raport WeatherScheduler")
        y += 40
        
        painter.setPen(QColor(100, 100, 100))
        painter.setFont(QFont("Arial", 12))
        data_gen = datetime.now().strftime("%d.%m.%Y %H:%M")
        painter.drawText(50, y, f"Generat la: {data_gen}")
        y += 40
        
        if statistics and statistics.get('avg_temperature') is not None:
            painter.setPen(Qt.GlobalColor.black)
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            painter.drawText(50, y, "Statistici Generale:")
            y += 25
            painter.setFont(QFont("Arial", 11))
            temp_medie = statistics.get('avg_temperature', 0)
            
            painter.drawText(70, y, f"• Temperatură medie: {temp_medie:.1f}{unit_symbol}")
            y += 20
            
            precip = statistics.get('total_precipitation', 0)
            painter.drawText(70, y, f"• Total precipitații estimate: {precip:.1f} mm")
            y += 40

        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        COL_POS = {
            "ZI": 50,
            "INTERVAL": 150,
            "ACTIVITATE": 280,
            "TEMP": 430,
            "CONDITII": 520
        }
        
        painter.drawText(COL_POS["ZI"], y, "Zi")
        painter.drawText(COL_POS["INTERVAL"], y, "Interval")
        painter.drawText(COL_POS["ACTIVITATE"], y, "Activitate / Materie")
        painter.drawText(COL_POS["TEMP"], y, f"Temp. ({unit_symbol})")
        painter.drawText(COL_POS["CONDITII"], y, "Condiții")
        
        y += 10
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawLine(50, y, width - 50, y)
        y += 25
        
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 10))
        
        for entry in schedule_data:
            if y > height - 60:
                printer.newPage()
                y = 50
                
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.drawText(50, y, "Continuare raport...")
                y += 30
                painter.setFont(QFont("Arial", 10))

            zi = str(entry.get('day', '-'))
            ora = str(entry.get('time', '-'))
            materie = str(entry.get('subject', '-'))[:25]

            temp_value = None
            cond_text = '-'
            
            weather = entry.get('weather')
            
            if weather:
                temp_value = weather.get('temperature')
                cond_text = weather.get('weather_description', '-')
            
            temp_text = f"{temp_value:.1f}{unit_symbol}" if temp_value is not None else "-" 

            painter.drawText(COL_POS["ZI"], y, zi)
            painter.drawText(COL_POS["INTERVAL"], y, ora)
            painter.drawText(COL_POS["ACTIVITATE"], y, materie)
            painter.drawText(COL_POS["TEMP"], y, temp_text)
            painter.drawText(COL_POS["CONDITII"], y, cond_text)
            
            y += 25

    def export_to_csv(self, schedule_data: List[Dict]) -> bool:
        file_path, _ = QFileDialog.getSaveFileName(self.parent, "Salvează raportul CSV", "Raport_Weather.csv", "CSV (*.csv)")
        if not file_path: return False
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['Zi', 'Interval', 'Materie', 'Temperatura', 'Conditii'])
                writer.writeheader()
                for e in schedule_data:
                    w = e.get('weather', {})
                    writer.writerow({
                        'Zi': e.get('day'),
                        'Interval': e.get('time'),
                        'Materie': e.get('subject'),
                        'Temperatura': w.get('temperature', '-'),
                        'Conditii': w.get('weather_description', '-')
                    })
            return True
        except Exception as e:
            if self.parent: QMessageBox.critical(self.parent, "Eroare CSV", str(e))
            return False