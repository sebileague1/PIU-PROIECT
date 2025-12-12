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

# Import componente create de ceilalți membri
from core.schedule_manager import ScheduleManager
from core.weather_service import WeatherService
from core.data_processor import DataProcessor
from widgets.weather_chart import WeatherChartWidget
from widgets.notification_manager import NotificationManager
from utils.export_manager import ExportManager
from ui.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    """Fereastra principală a aplicației WeatherScheduler"""
    
    schedule_loaded = pyqtSignal(dict)
    weather_update_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.schedule_data = None
        self.weather_data = None
        self.enriched_entries = []
        
        # === INIȚIALIZARE COMPONENTE ===
        
        self.schedule_manager = ScheduleManager()
        
        self.weather_service = WeatherService()
        self.weather_service.weather_data_ready.connect(self.on_weather_data_received)
        self.weather_service.weather_error.connect(self.on_weather_error)
        
        self.data_processor = DataProcessor()
        self.notification_manager = NotificationManager(self)
        self.notification_manager.start_automatic_checks(60)
        self.export_manager = ExportManager(self)
        
        self.init_ui()
        self.apply_theme() # Aplicăm tema întunecată o singură dată
        
        cached_weather = self.weather_service.load_weather_from_file()
        if cached_weather:
            self.weather_data = cached_weather
            print("Date meteo încărcate din cache")
        
    def init_ui(self):
        """Inițializează interfața utilizator"""
        self.setWindowTitle("WeatherScheduler - Planificator Meteo Orar")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # ==== SECȚIUNEA HEADER ====
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📅 WeatherScheduler")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # ==== SECȚIUNEA CONTROALE ====
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
        controls_layout.addWidget(self.export_button)
        
        main_layout.addLayout(controls_layout)
        
        # ==== LABEL STATUS ====
        self.status_label = QLabel("✅ Bine ai venit! Încarcă un orar pentru a începe.")
        self.status_label.setStyleSheet("padding: 10px; font-size: 14px;")
        main_layout.addWidget(self.status_label)
        
        # ==== TABELUL PRINCIPAL ====
        self.create_schedule_table()
        main_layout.addWidget(self.table, 3) 
        
        # ==== WIDGET GRAFICE (Sebastian M.) ====
        self.weather_chart = WeatherChartWidget(self)
        main_layout.addWidget(self.weather_chart, 2)
        
    def create_schedule_table(self):
        """Creează tabelul pentru afișarea orarului și datelor meteo"""
        self.table = QTableWidget()
        
        columns = ["Zi", "Interval Orar", "Materie/Activitate", 
                   "🌡️ Temperatură", "☁️ Condiții", "💧 Precipitații", "💨 Vânt"]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
    def load_schedule(self):
        """Încarcă orarul din fișier JSON sau CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selectează fișierul cu orarul",
            "",
            "Fișiere JSON (*.json);;Fișiere CSV (*.csv);;Toate fișierele (*.*)"
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
            self.status_label.setText(f"✅ Orar încărcat cu succes: {num_entries} intrări din {Path(file_path).name}")
            
            self.refresh_weather_button.setEnabled(True)
            self.export_button.setEnabled(True)
            
            self.notification_manager.show_success_notification(f"Orar încărcat: {num_entries} intrări")
            
            if self.weather_data:
                self.update_schedule_with_cached_weather()
            
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Eroare la încărcarea orarului:\n{str(e)}")
            
    def populate_table_with_schedule(self):
        """Populează tabelul cu datele din orar"""
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
        """Actualizează tabelul cu datele meteo din cache"""
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
        """Actualizează datele meteo de la API"""
        if not self.schedule_data:
            QMessageBox.warning(self, "Atenție", "Încarcă mai întâi un orar!")
            return
            
        self.status_label.setText("🔄 Se actualizează datele meteo de la API Open-Meteo...")
        self.refresh_weather_button.setEnabled(False)
        
        self.weather_service.fetch_weather_data(days=7)
        
    def on_weather_data_received(self, weather_data: dict):
        """Handler apelat când datele meteo sunt primite de la API"""
        self.weather_data = weather_data
        
        if not self.schedule_data:
            self.status_label.setText("✅ Date meteo primite! Încarcă un orar pentru a le combina.")
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
        """Handler apelat când apare o eroare la obținerea datelor meteo"""
        self.status_label.setText(f"❌ Eroare la obținerea datelor meteo: {error_message}")
        self.refresh_weather_button.setEnabled(True)
        self.notification_manager.show_error_notification(f"Eroare meteo: {error_message}")
        
        QMessageBox.warning(
            self,
            "Eroare API meteo",
            f"Nu s-au putut obține datele meteo:\n{error_message}\n\n"
            "Verifică conexiunea la internet și încearcă din nou."
        )
        
    def update_table_with_weather_data(self, enriched_entries: list):
        """Actualizează tabelul cu datele meteo îmbogățite"""
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
        """Aplică tema vizuală întunecată (singura temă)"""
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
        """Deschide dialogul de setări"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.apply_new_settings)
        dialog.exec()

    def apply_new_settings(self, settings: dict):
        """Aplică noile setări după salvare"""
        unit = settings.get("temperature_unit", "celsius")
        
        self.weather_service.set_temperature_unit(unit)
        
        # CORECȚIE: Setăm unitatea și în DataProcessor pentru formatare
        self.data_processor.set_temperature_unit(unit)
        
        self.weather_service.set_location(settings.get("location_name", "București"))
        
        self.notification_manager.enable_notifications(settings.get("notifications_enabled", True))
        self.notification_manager.set_check_interval(settings.get("update_interval_minutes", 60))
        
        if settings.get("auto_update_enabled", True):
            self.notification_manager.start_automatic_checks(settings.get("update_interval_minutes", 60))
        else:
            self.notification_manager.stop_automatic_checks()
        
        # Invalidează cache-ul și forțează o reîmprospătare cu noua unitate
        self.weather_service.cached_weather = None
        self.refresh_weather()
        
        self.status_label.setText("✅ Setări aplicate cu succes!")
        self.notification_manager.show_success_notification("Setări actualizate!")
        
    def open_help(self):
        """Deschide dialogul de ajutor"""
        help_text = """
        <h2>📚 Ghid de utilizare WeatherScheduler</h2>
        
        <h3>1️⃣ Încarcă Orar</h3>
        <p>Click pe <b>"📂 Încarcă Orar"</b> și selectează un fișier JSON sau CSV cu orarul tău.</p>
        
        <h3>2️⃣ Actualizează Meteo</h3>
        <p>Click pe <b>"🔄 Actualizează Meteo"</b> pentru a obține date meteo de la API-ul Open-Meteo.</p>
        
        <h3>3️⃣ Vizualizează</h3>
        <p>• <b>Tabelul</b> arată orarul tău cu date meteo pentru fiecare interval</p>
        <p>• <b>Graficele</b> arată evoluția temperaturii și precipitațiilor</p>
        
        <h3>5️⃣ Setări</h3>
        <p>Personalizează aplicația din <b>"⚙️ Setări"</b>:</p>
        <p>• Schimbă între Celsius și Fahrenheit</p>
        <p>• Configurează locația (după nume)</p>
        <p>• Ajustează frecvența actualizărilor</p>
        
        <h3>6️⃣ Export</h3>
        <p>Exportă raportul în <b>PDF</b> sau <b>CSV</b>.</p>
        
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
        """Exportă datele curente în PDF sau CSV"""
        if not self.schedule_data:
            QMessageBox.warning(self, "Atenție", "Nu există date de exportat. Încarcă mai întâi un orar.")
            return
        
        formats = ["PDF", "CSV"]
        format_choice, ok = QInputDialog.getItem(
            self,
            "Selectează formatul",
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
        else:  # CSV
            success = self.export_manager.export_to_csv(export_entries)
        
        if success:
            self.notification_manager.show_success_notification(f"Date exportate în format {format_choice}")
            
    def closeEvent(self, event):
        """Handler apelat când aplicația se închide"""
        self.notification_manager.cleanup()
        
        if self.weather_data:
            self.weather_service.save_weather_to_file(self.weather_data)
        
        event.accept()