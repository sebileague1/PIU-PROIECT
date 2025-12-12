"""
UI & Interfață principală WeatherScheduler
Responsabil: Danalache Emanuel
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QLabel, QFileDialog, QMessageBox, QHeaderView, QInputDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import json
from pathlib import Path

from core.schedule_manager import ScheduleManager
from core.weather_service import WeatherService
from core.data_processor import DataProcessor
from widgets.weather_chart import WeatherChartWidget
from widgets.notification_manager import NotificationManager
from utils.export_manager import ExportManager
from ui.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.schedule_data = None
        self.weather_data = None
        self.enriched_entries = []
        
        # Componente
        self.schedule_manager = ScheduleManager()
        self.weather_service = WeatherService()
        self.data_processor = DataProcessor()
        self.notification_manager = NotificationManager(self)
        self.export_manager = ExportManager(self)
        
        self.init_ui()
        self.apply_theme()
        
        # CONECTARE SEMNALE
        self.weather_service.weather_data_ready.connect(self.on_weather_data_received)
        self.weather_service.weather_error.connect(self.on_weather_error)
        
        self.load_initial_settings()
        
        cached = self.weather_service.load_weather_from_file()
        if cached:
            self.weather_data = cached
            print("Date meteo încărcate din cache.")

    def load_initial_settings(self):
        """Sincronizează unitatea de măsură salvată cu motorul de procesare."""
        settings_path = Path("resources/settings.json")
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    unit = settings.get("temperature_unit", "celsius")
                    self.weather_service.set_temperature_unit(unit)
                    self.data_processor.set_temperature_unit(unit)
                    self.weather_service.set_location(settings.get("location_name", "București"))
            except Exception as e:
                print(f"Eroare la încărcarea setărilor inițiale: {e}")

    def init_ui(self):
        self.setWindowTitle("WeatherScheduler - Planificator Meteo")
        self.setGeometry(100, 100, 1200, 800)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Controale
        ctrl_layout = QHBoxLayout()
        self.load_btn = QPushButton("📂 Încarcă Orar")
        self.load_btn.clicked.connect(self.load_schedule)
        self.refresh_btn = QPushButton("🔄 Actualizează Meteo")
        self.refresh_btn.clicked.connect(self.refresh_weather)
        self.settings_btn = QPushButton("⚙️ Setări")
        self.settings_btn.clicked.connect(self.open_settings)
        self.export_btn = QPushButton("💾 Export")
        self.export_btn.clicked.connect(self.export_data)
        
        for btn in [self.load_btn, self.refresh_btn, self.settings_btn, self.export_btn]:
            ctrl_layout.addWidget(btn)
        layout.addLayout(ctrl_layout)
        
        self.status_label = QLabel("Pregătit.")
        layout.addWidget(self.status_label)
        
        self.table = QTableWidget()
        self.create_table()
        layout.addWidget(self.table, 3)
        
        # TRIMITERE SIGURĂ A data_processor
        self.weather_chart = WeatherChartWidget(self.data_processor, self)
        
        layout.addWidget(self.weather_chart, 2)

    def create_table(self):
        cols = ["Zi", "Interval", "Materie", "Temp.", "Condiții", "Ploaie", "Vânt"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def load_schedule(self):
        path, _ = QFileDialog.getOpenFileName(self, "Deschide orar", "", "JSON (*.json);;CSV (*.csv)")
        if not path: return
        try:
            res = self.schedule_manager.load_from_json(path) if path.endswith('.json') else self.schedule_manager.load_from_csv(path)
            if res["status"] == "success":
                self.schedule_data = {"schedule": res["schedule"]}
                self.status_label.setText(f"Orar încărcat ({len(res['schedule'])} rânduri).")
                
                if self.weather_data: self.update_view()
                
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare la încărcarea orarului: {str(e)}")

    def refresh_weather(self):
        if not self.schedule_data and not self.weather_data:
             QMessageBox.warning(self, "Atenție", "Încarcă orarul sau datele meteo pentru a începe.")
             return
        self.status_label.setText("Actualizare meteo...")
        self.refresh_btn.setEnabled(False)
        self.weather_service.fetch_weather_data(7)

    def on_weather_data_received(self, data):
        self.weather_data = data
        self.update_view()
        self.status_label.setText("Date meteo actualizate.")
        self.refresh_btn.setEnabled(True)

    def on_weather_error(self, err):
        QMessageBox.warning(self, "Eroare Meteo", err)
        self.status_label.setText(f"Eroare: {err}")
        self.refresh_btn.setEnabled(True)

    def update_view(self):
        """Metoda unificată pentru actualizarea UI-ului"""
        if not self.schedule_data or not self.weather_data: return
        
        # 1. Procesează datele
        self.enriched_entries = self.data_processor.merge_schedule_with_weather(self.schedule_data["schedule"], self.weather_data)
        
        # 2. Actualizează tabelul
        self.table.setRowCount(len(self.enriched_entries))
        for row, entry in enumerate(self.enriched_entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.get('day', '')))
            self.table.setItem(row, 1, QTableWidgetItem(entry.get('time', '')))
            self.table.setItem(row, 2, QTableWidgetItem(entry.get('subject', '')))
            w = entry.get('weather')
            if w:
                fmt = self.data_processor.format_weather_for_table(w)
                self.table.setItem(row, 3, QTableWidgetItem(fmt["temperature"]))
                self.table.setItem(row, 4, QTableWidgetItem(fmt["conditions"]))
                self.table.setItem(row, 5, QTableWidgetItem(fmt["precipitation"]))
                self.table.setItem(row, 6, QTableWidgetItem(fmt["wind"]))
            else:
                 for col in range(3, 7): self.table.setItem(row, col, QTableWidgetItem("-"))
        
        # 3. Actualizează graficele (trimite lista de intrări direct, NU prin self.parent())
        self.weather_chart.update_charts(self.weather_data, self.enriched_entries)

    def apply_theme(self):
        self.setStyleSheet("QMainWindow, QWidget { background-color: #2b2b2b; color: white; } QTableWidget { background-color: #333; }")

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.apply_new_settings)
        dialog.exec()

    def apply_new_settings(self, settings):
        unit = settings.get("temperature_unit", "celsius")
        self.weather_service.set_temperature_unit(unit)
        self.data_processor.set_temperature_unit(unit)
        self.weather_service.set_location(settings.get("location_name", "București"))
        self.weather_service.cached_weather = None
        self.refresh_weather()

    def export_data(self):
        if not self.schedule_data: return
        fmt, ok = QInputDialog.getItem(self, "Export", "Format:", ["PDF", "CSV"], 0, False)
        if ok:
            stats = self.data_processor.calculate_statistics(self.enriched_entries)
            if fmt == "PDF": self.export_manager.export_to_pdf(self.enriched_entries, self.weather_data, stats)
            else: self.export_manager.export_to_csv(self.enriched_entries)

    def closeEvent(self, event):
        if self.weather_data: self.weather_service.save_weather_to_file(self.weather_data)
        event.accept()