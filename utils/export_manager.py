"""
Funcționalitate de export în format PDF și CSV
Responsabil: Moscalu Sebastian
"""

from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QPainter, QFont, QColor, QPen
from PyQt6.QtCore import QRect, Qt, QDate
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
import csv
from datetime import datetime
from typing import List, Dict, Optional

class ExportManager:
    """
    Gestionează exportul datelor aplicației în formate PDF și CSV
    Folosește Qt Print Framework pentru PDF (fără dependențe externe)
    """
    
    def __init__(self, parent_widget: Optional[QWidget] = None):
        self.parent = parent_widget
        
    def export_to_pdf(
        self, 
        schedule_data: List[Dict], 
        weather_data: Optional[Dict] = None,
        statistics: Optional[Dict] = None
    ) -> bool:
        """
        Exportă datele în format PDF folosind Qt Print Framework
        
        Args:
            schedule_data: Lista cu intrări din orar și date meteo
            weather_data: Datele meteo complete (opțional, pentru statistici suplimentare)
            statistics: Statistici calculate (opțional)
            
        Returns:
            True dacă exportul a reușit, False altfel
        """
        # Dialogul pentru selectarea fișierului de salvare
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Salvează raportul PDF",
            f"WeatherScheduler_Raport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "Fișiere PDF (*.pdf)"
        )
        
        if not file_path:
            return False
            
        try:
            # Creăm printer-ul pentru PDF
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageSize(QPrinter.PageSize.A4)
            printer.setPageMargins(15, 15, 15, 15, QPrinter.Unit.Millimeter)
            
            # Creăm painter-ul pentru desenare
            painter = QPainter()
            
            if not painter.begin(printer):
                raise Exception("Nu s-a putut inițializa painter-ul pentru PDF")
                
            # Desenăm conținutul PDF-ului
            self._draw_pdf_content(painter, printer, schedule_data, weather_data, statistics)
            
            painter.end()
            
            # Mesaj de succes
            if self.parent:
                QMessageBox.information(
                    self.parent,
                    "Export reușit",
                    f"Raportul a fost salvat cu succes:\n{file_path}"
                )
                
            return True
            
        except Exception as e:
            if self.parent:
                QMessageBox.critical(
                    self.parent,
                    "Eroare export PDF",
                    f"Nu s-a putut crea fișierul PDF:\n{str(e)}"
                )
            print(f"Eroare la export PDF: {e}")
            return False
            
    def _draw_pdf_content(
        self,
        painter: QPainter,
        printer: QPrinter,
        schedule_data: List[Dict],
        weather_data: Optional[Dict],
        statistics: Optional[Dict]
    ):
        """
        Desenează conținutul complet al PDF-ului
        """
        page_rect = printer.pageRect(QPrinter.Unit.Point)
        page_width = int(page_rect.width())
        page_height = int(page_rect.height())
        
        y_position = 50  # Poziția verticală curentă
        
        # === HEADER ===
        font_title = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font_title)
        painter.setPen(QColor(0, 51, 102))
        
        title_text = "WeatherScheduler"
        painter.drawText(50, y_position, title_text)
        y_position += 40
        
        # Subtitle
        font_subtitle = QFont("Arial", 14)
        painter.setFont(font_subtitle)
        painter.setPen(QColor(100, 100, 100))
        
        subtitle_text = f"Raport generat: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        painter.drawText(50, y_position, subtitle_text)
        y_position += 30
        
        # Linie separator
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawLine(50, y_position, page_width - 50, y_position)
        y_position += 40
        
        # === STATISTICI (dacă sunt disponibile) ===
        if statistics:
            y_position = self._draw_statistics_section(painter, statistics, y_position, page_width)
            y_position += 30
            
        # === TABELUL CU DATE ===
        font_normal = QFont("Arial", 10)
        painter.setFont(font_normal)
        
        # Header tabel
        painter.setPen(QColor(255, 255, 255))
        painter.setBrush(QColor(0, 51, 102))
        painter.drawRect(50, y_position, page_width - 100, 30)
        
        painter.drawText(60, y_position + 20, "Zi")
        painter.drawText(130, y_position + 20, "Interval")
        painter.drawText(230, y_position + 20, "Materie")
        painter.drawText(360, y_position + 20, "Temp.")
        painter.drawText(430, y_position + 20, "Condiții")
        painter.drawText(520, y_position + 20, "Precip.")
        
        y_position += 35
        
        # Rânduri date
        painter.setPen(QColor(0, 0, 0))
        row_height = 25
        alternate = False
        
        for entry in schedule_data:
            # Verifică dacă mai avem spațiu pe pagină
            if y_position + row_height > page_height - 50:
                # Trecem la o nouă pagină
                printer.newPage()
                y_position = 50
                
            # Fundal alternant pentru rânduri
            if alternate:
                painter.setBrush(QColor(245, 245, 245))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(50, y_position - 5, page_width - 100, row_height)
                painter.setPen(QColor(0, 0, 0))
                
            alternate = not alternate
            
            # Extragem datele
            day = entry.get("day", "-")
            time_range = entry.get("time", "-")
            subject = entry.get("subject", "-")
            
            weather = entry.get("weather")
            if weather:
                temp = f"{weather.get('temperature', '-')}°C" if weather.get('temperature') else "-"
                conditions = weather.get("weather_description", "-")
                precip_prob = weather.get("precipitation_probability", 0)
                precip_text = f"{precip_prob}%"
            else:
                temp = "-"
                conditions = "-"
                precip_text = "-"
                
            # Desenăm datele
            painter.drawText(60, y_position + 15, day[:10])  # Limităm lungimea
            painter.drawText(130, y_position + 15, time_range)
            painter.drawText(230, y_position + 15, subject[:20])  # Limităm lungimea
            painter.drawText(360, y_position + 15, temp)
            painter.drawText(430, y_position + 15, conditions[:15])
            painter.drawText(520, y_position + 15, precip_text)
            
            y_position += row_height
            
        # === FOOTER ===
        y_position = page_height - 40
        painter.setPen(QColor(150, 150, 150))
        font_footer = QFont("Arial", 8)
        painter.setFont(font_footer)
        
        footer_text = "Generat de WeatherScheduler - PIU Project 2025"
        painter.drawText(50, y_position, footer_text)
        
    def _draw_statistics_section(
        self,
        painter: QPainter,
        statistics: Dict,
        y_position: int,
        page_width: int
    ) -> int:
        """
        Desenează secțiunea cu statistici în PDF
        
        Returns:
            Noua poziție Y după desenare
        """
        # Titlu secțiune
        font_section = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font_section)
        painter.setPen(QColor(0, 51, 102))
        
        painter.drawText(50, y_position, "📊 Statistici meteo")
        y_position += 30
        
        # Casetă pentru statistici
        stats_box_height = 80
        painter.setBrush(QColor(240, 248, 255))
        painter.setPen(QPen(QColor(70, 130, 180), 2))
        painter.drawRoundedRect(50, y_position, page_width - 100, stats_box_height, 10, 10)
        
        # Text statistici
        font_stats = QFont("Arial", 11)
        painter.setFont(font_stats)
        painter.setPen(QColor(0, 0, 0))
        
        y_offset = y_position + 25
        
        avg_temp = statistics.get("avg_temperature")
        if avg_temp is not None:
            painter.drawText(70, y_offset, f"Temperatură medie: {avg_temp:.1f}°C")
        y_offset += 20
        
        min_temp = statistics.get("min_temperature")
        max_temp = statistics.get("max_temperature")
        if min_temp is not None and max_temp is not None:
            painter.drawText(70, y_offset, f"Interval temperatură: {min_temp:.1f}°C - {max_temp:.1f}°C")
        y_offset += 20
        
        rainy_periods = statistics.get("rainy_periods", 0)
        total_precip = statistics.get("total_precipitation", 0)
        painter.drawText(70, y_offset, f"Perioade cu ploaie: {rainy_periods} | Total precipitații: {total_precip:.1f}mm")
        
        return y_position + stats_box_height
        
    def export_to_csv(self, schedule_data: List[Dict]) -> bool:
        """
        Exportă datele în format CSV
        
        Args:
            schedule_data: Lista cu intrări din orar și date meteo
            
        Returns:
            True dacă exportul a reușit, False altfel
        """
        # Dialog pentru selectarea fișierului
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Salvează raportul CSV",
            f"WeatherScheduler_Raport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "Fișiere CSV (*.csv)"
        )
        
        if not file_path:
            return False
            
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                # Definim coloanele
                fieldnames = [
                    'Zi', 'Data', 'Interval Orar', 'Materie/Activitate', 'Locatie',
                    'Temperatura (°C)', 'Conditii', 'Probabilitate Precipitatii (%)',
                    'Precipitatii (mm)', 'Viteza Vant (km/h)'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Scriem datele
                for entry in schedule_data:
                    weather = entry.get("weather")
                    
                    if weather:
                        temp = weather.get("temperature", "")
                        conditions = weather.get("weather_description", "")
                        precip_prob = weather.get("precipitation_probability", "")
                        precip_amount = weather.get("precipitation", "")
                        wind_speed = weather.get("wind_speed", "")
                    else:
                        temp = conditions = precip_prob = precip_amount = wind_speed = ""
                        
                    row = {
                        'Zi': entry.get("day", ""),
                        'Data': entry.get("date", ""),
                        'Interval Orar': entry.get("time", ""),
                        'Materie/Activitate': entry.get("subject", ""),
                        'Locatie': entry.get("location", ""),
                        'Temperatura (°C)': temp,
                        'Conditii': conditions,
                        'Probabilitate Precipitatii (%)': precip_prob,
                        'Precipitatii (mm)': precip_amount,
                        'Viteza Vant (km/h)': wind_speed
                    }
                    
                    writer.writerow(row)
                    
            # Mesaj de succes
            if self.parent:
                QMessageBox.information(
                    self.parent,
                    "Export reușit",
                    f"Raportul CSV a fost salvat cu succes:\n{file_path}"
                )
                
            return True
            
        except Exception as e:
            if self.parent:
                QMessageBox.critical(
                    self.parent,
                    "Eroare export CSV",
                    f"Nu s-a putut crea fișierul CSV:\n{str(e)}"
                )
            print(f"Eroare la export CSV: {e}")
            return False
            
    def quick_print(self, schedule_data: List[Dict]):
        """
        Deschide dialogul de printare rapid
        
        Args:
            schedule_data: Datele care trebuie printate
        """
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        
        dialog = QPrintDialog(printer, self.parent)
        dialog.setWindowTitle("Printează raportul")
        
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            painter = QPainter()
            
            if painter.begin(printer):
                self._draw_pdf_content(painter, printer, schedule_data, None, None)
                painter.end()
                
                if self.parent:
                    QMessageBox.information(
                        self.parent,
                        "Printare",
                        "Documentul a fost trimis la printer."
                    )