from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QPainter, QFont, QColor, QPen, QPageSize, QPageLayout, QImage
from PyQt6.QtCore import QRect, Qt, QMarginsF, QRectF
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
import csv
from datetime import datetime
from typing import List, Dict, Optional

class ExportManager:
    def __init__(self, parent_widget: Optional[QWidget] = None, chart_widget=None):
        """
        Args:
            parent_widget: Widget părinte pentru dialoguri
            chart_widget: Widget-ul cu graficele meteo (WeatherChartWidget)
        """
        self.parent = parent_widget
        self.chart_widget = chart_widget
        
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
                QMessageBox.critical(self.parent, "Eroare export PDF", f"Eroare critică la desenare: {str(e)}")
            print(f"Eroare detaliu export PDF: {e}")
            return False

    def _draw_pdf_content(self, painter, printer, schedule_data, weather_data, statistics):
        """Desenează tot conținutul PDF-ului pe mai multe pagini."""
        
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
            temp_min = statistics.get('min_temperature', 0)
            temp_max = statistics.get('max_temperature', 0)
            
            painter.drawText(70, y, f"• Temperatură medie: {temp_medie:.1f}{unit_symbol}")
            y += 20
            painter.drawText(70, y, f"• Temperatură minimă: {temp_min:.1f}{unit_symbol}")
            y += 20
            painter.drawText(70, y, f"• Temperatură maximă: {temp_max:.1f}{unit_symbol}")
            y += 20
            
            precip = statistics.get('total_precipitation', 0)
            painter.drawText(70, y, f"• Total precipitații estimate: {precip:.1f} mm")
            y += 20
            
            rainy_periods = statistics.get('rainy_periods', 0)
            painter.drawText(70, y, f"• Perioade cu risc de ploaie: {rainy_periods}")
            y += 40

        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
         
        COL_POS = {
            "ZI": 50,
            "INTERVAL": 120,
            "ACTIVITATE": 210,
            "TEMP": 420,
            "CONDITII": 490,
            "PRECIP": 600
        }
        
        painter.drawText(COL_POS["ZI"], y, "Zi")
        painter.drawText(COL_POS["INTERVAL"], y, "Interval")
        painter.drawText(COL_POS["ACTIVITATE"], y, "Activitate / Materie")
        painter.drawText(COL_POS["TEMP"], y, f"Temp. ({unit_symbol})")
        painter.drawText(COL_POS["CONDITII"], y, "Condiții")
        painter.drawText(COL_POS["PRECIP"], y, "Ploaie (%)")
        
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
                
                painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                painter.drawText(COL_POS["ZI"], y, "Zi")
                painter.drawText(COL_POS["INTERVAL"], y, "Interval")
                painter.drawText(COL_POS["ACTIVITATE"], y, "Activitate / Materie")
                painter.drawText(COL_POS["TEMP"], y, f"Temp. ({unit_symbol})")
                painter.drawText(COL_POS["CONDITII"], y, "Condiții")
                painter.drawText(COL_POS["PRECIP"], y, "Ploaie (%)")
                y += 10
                painter.setPen(QPen(QColor(200, 200, 200), 1))
                painter.drawLine(50, y, width - 50, y)
                y += 25
                painter.setPen(Qt.GlobalColor.black)
                painter.setFont(QFont("Arial", 10))

            zi = str(entry.get('day', '-'))
            ora = str(entry.get('time', '-'))
            materie = str(entry.get('subject', '-'))[:25]
            
            temp_value = None
            cond_text = '-'
            precip_prob = '-'
            
            weather = entry.get('weather')
            
            if weather:
                temp_value = weather.get('temperature')
                cond_text = weather.get('weather_description', '-')
                precip_prob = f"{weather.get('precipitation_probability', 0):.0f}%"
            
            temp_text = f"{temp_value:.1f}{unit_symbol}" if temp_value is not None else "-" 

            painter.drawText(COL_POS["ZI"], y, zi)
            painter.drawText(COL_POS["INTERVAL"], y, ora)
            painter.drawText(COL_POS["ACTIVITATE"], y, materie)
            painter.drawText(COL_POS["TEMP"], y, temp_text)
            painter.drawText(COL_POS["CONDITII"], y, cond_text)
            painter.drawText(COL_POS["PRECIP"], y, precip_prob)
            
            y += 25
        
        if self.chart_widget:
            printer.newPage()
            y = 50
            
            painter.setPen(QColor(0, 51, 102))
            painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
            painter.drawText(50, y, "Grafice Meteo Interactive")
            y += 50
            
            try:
                if hasattr(self.chart_widget, 'temp_plot'):
                    temp_pixmap = self.chart_widget.temp_plot.grab()
                    temp_image = temp_pixmap.toImage()
                    
                    chart_width = width - 100
                    chart_height = (height - 200) // 2 
                    
                    painter.setPen(Qt.GlobalColor.black)
                    painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                    painter.drawText(50, y, "🌡️ Temperatură")
                    y += 25
                    
                    temp_rect = QRectF(50, y, chart_width, chart_height)
                    painter.drawImage(temp_rect, temp_image)
                    y += chart_height + 30
                
                if hasattr(self.chart_widget, 'precip_plot'):
                    precip_pixmap = self.chart_widget.precip_plot.grab()
                    precip_image = precip_pixmap.toImage()
                    
                    chart_width = width - 100
                    chart_height = (height - 200) // 2
                    
                    if y + chart_height + 100 > height:
                        printer.newPage()
                        y = 50
                    
                    painter.setPen(Qt.GlobalColor.black)
                    painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                    painter.drawText(50, y, "💧 Precipitații")
                    y += 25
                    
                    precip_rect = QRectF(50, y, chart_width, chart_height)
                    painter.drawImage(precip_rect, precip_image)
                    y += chart_height + 30
                
            except Exception as e:
                print(f"Eroare la capturarea graficelor: {e}")
                painter.setPen(QColor(150, 150, 150))
                painter.setFont(QFont("Arial", 11))
                painter.drawText(50, y, "Graficele nu au putut fi capturate pentru export.")
                y += 30
        
        self._draw_footer(painter, printer, height)
    
    def _draw_footer(self, painter, printer, page_height):
        """Desenează footer-ul paginii."""
        footer_y = page_height - 30
        
        page_rect = printer.pageRect(QPrinter.Unit.Point)
        width = int(page_rect.width())
        
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawLine(50, footer_y - 10, width - 50, footer_y - 10)
        
        painter.setFont(QFont("Arial", 8))
        painter.setPen(QColor(100, 100, 100))
        
        footer_text = "WeatherScheduler - Planificator Meteo Orar | Generat automat"
        painter.drawText(50, footer_y, footer_text)
        
        page_num_text = f"Pagina"
        text_width = painter.fontMetrics().horizontalAdvance(page_num_text)
        painter.drawText(width - 50 - text_width, footer_y, page_num_text)

    def export_to_csv(self, schedule_data: List[Dict]) -> bool:
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent, 
            "Salvează raportul CSV", 
            f"WeatherScheduler_Raport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
            "CSV (*.csv)"
        )
        if not file_path: 
            return False
            
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['Zi', 'Interval', 'Materie', 'Temperatura', 'Conditii', 'Precipitații'])
                writer.writeheader()
                for e in schedule_data:
                    w = e.get('weather', {})
                    writer.writerow({
                        'Zi': e.get('day', '-'),
                        'Interval': e.get('time', '-'),
                        'Materie': e.get('subject', '-'),
                        'Temperatura': w.get('temperature', '-'),
                        'Conditii': w.get('weather_description', '-'),
                        'Precipitații': f"{w.get('precipitation_probability', 0):.0f}%"
                    })
            
            if self.parent:
                QMessageBox.information(
                    self.parent, 
                    "Export reușit", 
                    f"Raportul CSV a fost salvat la:\n{file_path}"
                )
            return True
            
        except Exception as e:
            if self.parent: 
                QMessageBox.critical(self.parent, "Eroare CSV", str(e))
            return False