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
    """Fereastra principala a aplicatiei WeatherScheduler"""
    
    schedule_loaded = pyqtSignal(dict)
    weather_update_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.schedule_data = None
        self.weather_data = None
        self.enriched_entries = []
        
        self.schedule_manager = ScheduleManager()
        
        self.weather_service = WeatherService()
        self.weather_service.weather_data_ready.connect(self.on_weather_data_received)
        self.weather_service.weather_error.connect(self.on_weather_error)
        
        self.data_processor = DataProcessor()
        self.notification_manager = NotificationManager(self)
        self.notification_manager.start_automatic_checks(60)
        self.export_manager = ExportManager(self)
        
        self.init_ui()
        self.apply_theme()
        
        cached_weather = self.weather_service.load_weather_from_file()
        if cached_weather:
            self.weather_data = cached_weather
            print("Date meteo incarcate din cache")
        
    def init_ui(self):
        """Initializeaza interfata utilizator"""
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
        
        self.load_schedule_button = QPushButton("📂 Incarca Orar")
        self.load_schedule_button.clicked.connect(self.load_schedule)
        self.load_schedule_button.setFixedSize(150, 40)
        controls_layout.addWidget(self.load_schedule_button)
        
        self.refresh_weather_button = QPushButton("🔄 Actualizeaza Meteo")
        self.refresh_weather_button.clicked.connect(self.refresh_weather)
        self.refresh_weather_button.setEnabled(False)
        self.refresh_weather_button.setFixedSize(180, 40)
        controls_layout.addWidget(self.refresh_weather_button)
        
        controls_layout.addStretch()
        
        self.settings_button = QPushButton("⚙️ Setari")
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
    
        self.status_label = QLabel("✅ Bine ai venit! Incarca un orar pentru a incepe.")
        self.status_label.setStyleSheet("padding: 10px; font-size: 14px;")
        main_layout.addWidget(self.status_label)
        
        self.create_schedule_table()
        main_layout.addWidget(self.table, 3) 
        
        self.weather_chart = WeatherChartWidget(self)
        main_layout.addWidget(self.weather_chart, 2)
        
    def create_schedule_table(self):
        """Creeaza tabelul pentru afisarea orarului si datelor meteo"""
        self.table = QTableWidget()
        
        columns = ["Zi", "Interval Orar", "Materie/Activitate", 
                   "🌡️ Temperatura", "☁️ Conditii", "💧 Precipitatii", "💨 Vant"]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
    def load_schedule(self):
        """Incarca orarul din fisier JSON sau CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecteaza fisierul cu orarul",
            "",
            "Fisiere JSON (*.json);;Fisiere CSV (*.csv);;Toate fisierele (*.*)"
        )
        
        if not file_path:
            return
            
        try:
            if file_path.endswith('.json'):
                result = self.schedule_manager.load_from_json(file_path)
            else:
                result = self.schedule_manager.load_from_csv(file_path)
                
            if result["status"] == "error":
                QMessageBox.critical(self, "Eroare", result["message"])
                return
                
            self.schedule_data = {"schedule": result["schedule"]}
            self.populate_table_with_schedule()
            
            num_entries = len(result["schedule"])
            self.status_label.setText(f"✅ Orar incarcat cu succes: {num_entries} intrari din {Path(file_path).name}")
            
            self.refresh_weather_button.setEnabled(True)
            self.export_button.setEnabled(True)
            
            self.notification_manager.show_success_notification(f"Orar incarcat: {num_entries} intrari")
            
            if self.weather_data:
                self.update_schedule_with_cached_weather()
            
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare la incarcarea orarului:\n{str(e)}")
            
    def populate_table_with_schedule(self):
        """Populeaza tabelul cu datele din orar"""
        if not self.schedule_data:
            return
            
        schedule_entries = self.schedule_data.get("schedule", [])
        self.table.setRowCount(len(schedule_entries))
        
        for row, entry in enumerate(schedule_entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.get("day", "")))
            self.table.setItem(row, 1, QTableWidgetItem(entry.get("time", "")))
            self.table.setItem(row, 2, QTableWidgetItem(entry.get("subject", "")))
            self.table.setItem(row, 3, QTableWidgetItem("-"))
            self.table.setItem(row, 4, QTableWidgetItem("-"))
            self.table.setItem(row, 5, QTableWidgetItem("-"))
            self.table.setItem(row, 6, QTableWidgetItem("-"))
            
    def update_schedule_with_cached_weather(self):
        """Actualizeaza tabelul cu datele meteo din cache"""
        if not self.schedule_data or not self.weather_data:
            return
            
        schedule_entries = self.schedule_data.get("schedule", [])
        self.enriched_entries = self.data_processor.merge_schedule_with_weather(
            schedule_entries,
            self.weather_data
        )
        
        self.update_table_with_weather_data(self.enriched_entries)
        self.weather_chart.update_charts(self.weather_data, self.enriched_entries)
        
        stats = self.data_processor.calculate_statistics(self.enriched_entries)
        avg_temp = stats['avg_temperature']
        temp_str = f"{avg_temp:.1f}°C" if avg_temp is not None else "N/A"
        
        self.status_label.setText(
            f"✅ Date meteo din cache aplicate | "
            f"Temp medie: {temp_str} | "
            f"Perioade cu ploaie: {stats['rainy_periods']}"
        )
            
    def refresh_weather(self):
        """Actualizeaza datele meteo de la API"""
        if not self.schedule_data:
            QMessageBox.warning(self, "Atentie", "Incarca mai intai un orar!")
            return
            
        self.status_label.setText("🔄 Se actualizeaza datele meteo de la API Open-Meteo...")
        self.refresh_weather_button.setEnabled(False)
        
        self.weather_service.fetch_weather_data(days=7)
        
    def on_weather_data_received(self, weather_data: dict):
        """Handler apelat cand datele meteo sunt primite de la API"""
        self.weather_data = weather_data
        
        if not self.schedule_data:
            self.status_label.setText("✅ Date meteo primite! Incarca un orar pentru a le combina.")
            self.refresh_weather_button.setEnabled(True)
            return
        
        schedule_entries = self.schedule_data.get("schedule", [])
        self.enriched_entries = self.data_processor.merge_schedule_with_weather(
            schedule_entries,
            weather_data
        )
        
        self.update_table_with_weather_data(self.enriched_entries)
        self.weather_chart.update_charts(weather_data, self.enriched_entries)
        
        tomorrow_entries = self.data_processor.get_entries_for_tomorrow(self.enriched_entries)
        risky_entries = []
        
        for entry in tomorrow_entries:
            weather_info = entry.get("weather")
            if weather_info:
                is_rainy, severity = self.data_processor.detect_rain_conditions(weather_info)
                if is_rainy:
                    entry["weather_data"] = weather_info
                    risky_entries.append(entry)
        
        if risky_entries:
            self.notification_manager.check_rain_risk_and_notify(risky_entries)
        
        stats = self.data_processor.calculate_statistics(self.enriched_entries)
        avg_temp = stats['avg_temperature']
        temp_str = f"{avg_temp:.1f}°C" if avg_temp is not None else "N/A"
        
        self.status_label.setText(
            f"✅ Date meteo actualizate! "
            f"Temp medie: {temp_str} | "
            f"Perioade cu ploaie: {stats['rainy_periods']}"
        )
        
        self.refresh_weather_button.setEnabled(True)
        self.notification_manager.show_success_notification("Date meteo actualizate cu succes!")

    def on_weather_error(self, error_message: str):
        """Handler apelat cand apare o eroare la obtinerea datelor meteo"""
        self.status_label.setText(f"❌ Eroare la obtinerea datelor meteo: {error_message}")
        self.refresh_weather_button.setEnabled(True)
        self.notification_manager.show_error_notification(f"Eroare meteo: {error_message}")
        
        QMessageBox.warning(
            self,
            "Eroare API meteo",
            f"Nu s-au putut obtine datele meteo:\n{error_message}\n\n"
            "Verifica conexiunea la internet si incearca din nou."
        )
        
    def update_table_with_weather_data(self, enriched_entries: list):
        """Actualizeaza tabelul cu datele meteo imbogatite"""
        self.table.setRowCount(len(enriched_entries))
        
        for row, entry in enumerate(enriched_entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.get("day", "")))
            self.table.setItem(row, 1, QTableWidgetItem(entry.get("time", "")))
            self.table.setItem(row, 2, QTableWidgetItem(entry.get("subject", "")))
            
            weather = entry.get("weather")
            if weather:
                formatted = self.data_processor.format_weather_for_table(weather)
                self.table.setItem(row, 3, QTableWidgetItem(formatted["temperature"]))
                self.table.setItem(row, 4, QTableWidgetItem(formatted["conditions"]))
                self.table.setItem(row, 5, QTableWidgetItem(formatted["precipitation"]))
                self.table.setItem(row, 6, QTableWidgetItem(formatted["wind"]))
                
                is_rainy, severity = self.data_processor.detect_rain_conditions(weather)
                if is_rainy:
                    if severity == "heavy":
                        color = QColor(255, 200, 200)
                    elif severity == "moderate":
                        color = QColor(255, 240, 200)
                    else:
                        color = QColor(230, 240, 255)
                        
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(color)
            else:
                for col in range(3, 7):
                    self.table.setItem(row, col, QTableWidgetItem("-"))
            
    def apply_theme(self):
        """Aplica tema vizuala intunecata (singura tema)"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QPushButton:disabled {
                background-color: #1d1d1d;
                color: #666666;
            }
            QTableWidget {
                background-color: #3d3d3d;
                color: #ffffff;
                gridline-color: #555555;
                font-size: 14px;
            }
            QTableWidget::item:selected {
                background-color: #555555;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #4d4d4d;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #555555;
            }
            
            /* STIL PENTRU SCROLLBAR (DARK) */
            QScrollBar:vertical {
                border: 1px solid #555555;
                background: #3d3d3d;
                width: 15px;
                margin: 20px 0 20px 0;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                min-height: 20px;
                border-radius: 7px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 20px;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
            
    def open_settings(self):
        """Deschide dialogul de setari"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.apply_new_settings)
        dialog.exec()

    def apply_new_settings(self, settings: dict):
        """Aplica noile setari dupa salvare"""
        self.weather_service.set_temperature_unit(settings.get("temperature_unit", "celsius"))
        
        self.weather_service.set_location(settings.get("location_name", "Bucuresti"))
        
        self.notification_manager.enable_notifications(settings.get("notifications_enabled", True))
        self.notification_manager.set_check_interval(settings.get("update_interval_minutes", 60))
        
        if settings.get("auto_update_enabled", True):
            self.notification_manager.start_automatic_checks(settings.get("update_interval_minutes", 60))
        else:
            self.notification_manager.stop_automatic_checks()
        
        self.weather_service.cached_weather = None
        
        self.status_label.setText("✅ Setari aplicate cu succes!")
        self.notification_manager.show_success_notification("Setari actualizate!")
        
    def open_help(self):
        """Deschide dialogul de ajutor"""
        help_text = """
        <h2>📚 Ghid de utilizare WeatherScheduler</h2>
        
        <h3>1️⃣ Incarca Orar</h3>
        <p>Click pe <b>"📂 Incarca Orar"</b> și selectează un fișier JSON sau CSV cu orarul tău.</p>
        
        <h3>2️⃣ Actualizeaza Meteo</h3>
        <p>Click pe <b>"🔄 Actualizeaza Meteo"</b> pentru a obține date meteo de la API-ul Open-Meteo.</p>
        
        <h3>3️⃣ Vizualizeaza</h3>
        <p>• <b>Tabelul</b> arata orarul tau cu date meteo pentru fiecare interval</p>
        <p>• <b>Graficele</b> arata evolutia temperaturii si precipitatiilor</p>
        
        <h3>5️⃣ Setari</h3>
        <p>Personalizeaza aplicatia din <b>"⚙️ Setari"</b>:</p>
        <p>• Schimba intre Celsius si Fahrenheit</p>
        <p>• Configureaza locatia (dupa nume)</p>
        <p>• Ajusteaza frecventa actualizarilor</p>
        
        <h3>6️⃣ Export</h3>
        <p>Exporta raportul in <b>PDF</b> sau <b>CSV</b>.</p>
        
        <hr>
        <p><b>💡 Sursa datelor:</b> API Open-Meteo</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Ajutor WeatherScheduler")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
        
    def export_data(self):
        """Exporta datele curente in PDF sau CSV"""
        if not self.schedule_data:
            QMessageBox.warning(self, "Atentie", "Nu exista date de exportat. Incarca mai intai un orar.")
            return
        
        formats = ["PDF", "CSV"]
        format_choice, ok = QInputDialog.getItem(
            self,
            "Selecteaza formatul",
            "Alege formatul de export:",
            formats,
            0,
            False
        )
        
        if not ok:
            return
        
        if self.enriched_entries:
            export_entries = self.enriched_entries
            statistics = self.data_processor.calculate_statistics(self.enriched_entries)
        else:
            export_entries = self.schedule_data.get("schedule", [])
            statistics = None
        
        if format_choice == "PDF":
            success = self.export_manager.export_to_pdf(
                export_entries,
                self.weather_data,
                statistics
            )
        else:
            success = self.export_manager.export_to_csv(export_entries)
        
        if success:
            self.notification_manager.show_success_notification(f"Date exportate în format {format_choice}")
            
    def closeEvent(self, event):
        """Handler apelat cand aplicatia se inchide"""
        self.notification_manager.cleanup()
        
        if self.weather_data:
            self.weather_service.save_weather_to_file(self.weather_data)
        
        event.accept()