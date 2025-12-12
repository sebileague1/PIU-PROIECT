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
    schedule_loaded = pyqtSignal(dict)
    weather_update_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.schedule_data = None
        self.weather_data = None
        self.enriched_entries = []
        
        # INIȚIALIZARE
        self.schedule_manager = ScheduleManager()
        self.weather_service = WeatherService()
        self.weather_service.weather_data_ready.connect(self.on_weather_data_received)
        self.weather_service.weather_error.connect(self.on_weather_error)
        
        self.data_processor = DataProcessor()
        self.notification_manager = NotificationManager(self)
        self.export_manager = ExportManager(self)
        
        self.init_ui()
        self.apply_theme()
        
        # --- MODIFICARE: ÎNCĂRCARE SETĂRI LA PORNIRE ---
        self.load_and_apply_initial_settings()
        
        # Cache
        cached_weather = self.weather_service.load_weather_from_file()
        if cached_weather:
            self.weather_data = cached_weather
            print("Date meteo încărcate din cache")
            # Dacă avem și orar, actualizăm
            if self.schedule_data:
                self.update_schedule_with_cached_weather()

    def load_and_apply_initial_settings(self):
        """Încarcă fișierul settings.json și aplică unitățile și locația imediat."""
        settings_path = Path("resources/settings.json")
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    unit = settings.get("temperature_unit", "celsius")
                    loc = settings.get("location_name", "București")
                    interval = settings.get("update_interval_minutes", 60)
                    
                    # Aplicăm la componente
                    self.weather_service.set_temperature_unit(unit)
                    self.weather_service.set_location(loc)
                    self.data_processor.set_temperature_unit(unit)
                    self.notification_manager.set_check_interval(interval)
                    print(f"Setări inițiale aplicate: {unit}, {loc}")
            except Exception as e:
                print(f"Eroare la încărcarea setărilor inițiale: {e}")

    def init_ui(self):
        self.setWindowTitle("WeatherScheduler - Planificator Meteo Orar")
        self.setGeometry(100, 100, 1400, 900)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        header_layout = QHBoxLayout()
        title_label = QLabel("📅 WeatherScheduler")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        controls_layout = QHBoxLayout()
        self.load_schedule_button = QPushButton("📂 Încarcă Orar")
        self.load_schedule_button.clicked.connect(self.load_schedule)
        self.load_schedule_button.setFixedSize(150, 40)
        controls_layout.addWidget(self.load_schedule_button)

        self.refresh_weather_button = QPushButton("🔄 Actualizează Meteo")
        self.refresh_weather_button.clicked.connect(self.refresh_weather)
        self.refresh_weather_button.setEnabled(False)
        self.refresh_weather_button.setFixedSize(180, 40)
        controls_layout.addWidget(self.refresh_weather_button)

        controls_layout.addStretch()
        self.settings_button = QPushButton("⚙️ Setări")
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setFixedSize(120, 40)
        controls_layout.addWidget(self.settings_button)

        self.help_button = QPushButton("❓ Ajutor")
        self.help_button.clicked.connect(self.open_help)
        self.help_button.setFixedSize(120, 40)
        controls_layout.addWidget(self.help_button)

        self.export_button = QPushButton("💾 Export")
        self.export_button.clicked.connect(self.export_data)
        self.export_button.setEnabled(False)
        self.export_button.setFixedSize(120, 40)
        controls_layout.addWidget(self.export_button)
        main_layout.addLayout(controls_layout)

        self.status_label = QLabel("✅ Bine ai venit! Încarcă un orar pentru a începe.")
        self.status_label.setStyleSheet("padding: 10px; font-size: 14px;")
        main_layout.addWidget(self.status_label)

        self.create_schedule_table()
        main_layout.addWidget(self.table, 3) 
        self.weather_chart = WeatherChartWidget(self)
        main_layout.addWidget(self.weather_chart, 2)

    def create_schedule_table(self):
        self.table = QTableWidget()
        columns = ["Zi", "Interval Orar", "Materie/Activitate", "🌡️ Temperatură", "☁️ Condiții", "💧 Precipitații", "💨 Vânt"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

    def load_schedule(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selectează orarul", "", "JSON (*.json);;CSV (*.csv)")
        if not file_path: return
        try:
            result = self.schedule_manager.load_from_json(file_path) if file_path.endswith('.json') else self.schedule_manager.load_from_csv(file_path)
            if result["status"] == "error":
                QMessageBox.critical(self, "Eroare", result["message"])
                return
            self.schedule_data = {"schedule": result["schedule"]}
            self.populate_table_with_schedule()
            self.status_label.setText(f"✅ Orar încărcat: {len(result['schedule'])} intrări.")
            self.refresh_weather_button.setEnabled(True)
            self.export_button.setEnabled(True)
            if self.weather_data: self.update_schedule_with_cached_weather()
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare: {str(e)}")

    def populate_table_with_schedule(self):
        if not self.schedule_data: return
        entries = self.schedule_data.get("schedule", [])
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.get("day", "")))
            self.table.setItem(row, 1, QTableWidgetItem(entry.get("time", "")))
            self.table.setItem(row, 2, QTableWidgetItem(entry.get("subject", "")))
            for col in range(3, 7): self.table.setItem(row, col, QTableWidgetItem("-"))

    def update_schedule_with_cached_weather(self):
        if not self.schedule_data or not self.weather_data: return
        self.enriched_entries = self.data_processor.merge_schedule_with_weather(self.schedule_data.get("schedule", []), self.weather_data)
        self.update_table_with_weather_data(self.enriched_entries)
        self.weather_chart.update_charts(self.weather_data, self.enriched_entries)
        stats = self.data_processor.calculate_statistics(self.enriched_entries)
        self.status_label.setText(f"✅ Date din cache aplicate. Temp medie: {stats['avg_temperature']:.1f}{self.data_processor.temp_unit_symbol}")

    def refresh_weather(self):
        if not self.schedule_data: return
        self.status_label.setText("🔄 Se actualizează datele...")
        self.refresh_weather_button.setEnabled(False)
        self.weather_service.fetch_weather_data(days=7)

    def on_weather_data_received(self, weather_data: dict):
        self.weather_data = weather_data
        if not self.schedule_data:
            self.refresh_weather_button.setEnabled(True)
            return
        self.enriched_entries = self.data_processor.merge_schedule_with_weather(self.schedule_data.get("schedule", []), weather_data)
        self.update_table_with_weather_data(self.enriched_entries)
        self.weather_chart.update_charts(weather_data, self.enriched_entries)
        stats = self.data_processor.calculate_statistics(self.enriched_entries)
        self.status_label.setText(f"✅ Date actualizate. Temp medie: {stats['avg_temperature']:.1f}{self.data_processor.temp_unit_symbol}")
        self.refresh_weather_button.setEnabled(True)

    def on_weather_error(self, err: str):
        self.status_label.setText(f"❌ Eroare: {err}")
        self.refresh_weather_button.setEnabled(True)

    def update_table_with_weather_data(self, entries: list):
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.get("day", "")))
            self.table.setItem(row, 1, QTableWidgetItem(entry.get("time", "")))
            self.table.setItem(row, 2, QTableWidgetItem(entry.get("subject", "")))
            weather = entry.get("weather")
            if weather:
                fmt = self.data_processor.format_weather_for_table(weather)
                self.table.setItem(row, 3, QTableWidgetItem(fmt["temperature"]))
                self.table.setItem(row, 4, QTableWidgetItem(fmt["conditions"]))
                self.table.setItem(row, 5, QTableWidgetItem(fmt["precipitation"]))
                self.table.setItem(row, 6, QTableWidgetItem(fmt["wind"]))
                is_rain, sev = self.data_processor.detect_rain_conditions(weather)
                if is_rain:
                    color = QColor(255, 200, 200) if sev == "heavy" else QColor(255, 240, 200)
                    for col in range(7): self.table.item(row, col).setBackground(color)
            else:
                for col in range(3, 7): self.table.setItem(row, col, QTableWidgetItem("-"))

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #2b2b2b; color: #ffffff; }
            QPushButton { background-color: #3d3d3d; border: 1px solid #555555; border-radius: 5px; padding: 8px; }
            QPushButton:hover { background-color: #4d4d4d; }
            QTableWidget { background-color: #3d3d3d; gridline-color: #555555; font-size: 14px; }
            QHeaderView::section { background-color: #4d4d4d; padding: 5px; border: 1px solid #555555; }
            QScrollBar:vertical { border: 1px solid #555555; background: #3d3d3d; width: 15px; }
            QScrollBar::handle:vertical { background: #555555; border-radius: 7px; }
        """)

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.apply_new_settings)
        dialog.exec()

    def apply_new_settings(self, settings: dict):
        unit = settings.get("temperature_unit", "celsius")
        self.weather_service.set_temperature_unit(unit)
        self.data_processor.set_temperature_unit(unit)
        self.weather_service.set_location(settings.get("location_name", "București"))
        self.weather_service.cached_weather = None
        self.refresh_weather()

    def open_help(self):
        QMessageBox.information(self, "Ajutor", "Încarcă orarul și apasă actualizare meteo.")

    def export_data(self):
        if not self.schedule_data: return
        fmt, ok = QInputDialog.getItem(self, "Export", "Alege format:", ["PDF", "CSV"], 0, False)
        if ok:
            entries = self.enriched_entries if self.enriched_entries else self.schedule_data.get("schedule", [])
            stats = self.data_processor.calculate_statistics(entries) if self.enriched_entries else None
            if fmt == "PDF": self.export_manager.export_to_pdf(entries, self.weather_data, stats)
            else: self.export_manager.export_to_csv(entries)

    def closeEvent(self, event):
        if self.weather_data: self.weather_service.save_weather_to_file(self.weather_data)
        event.accept()