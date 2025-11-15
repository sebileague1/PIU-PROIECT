from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QLabel, QFileDialog, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
import json
from pathlib import Path

class MainWindow(QMainWindow):
    """Fereastra principală a aplicației WeatherScheduler"""
    
    # Semnale pentru comunicare între componente
    schedule_loaded = pyqtSignal(dict)
    weather_update_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_theme = "light"  # Tema curentă: light sau dark
        self.schedule_data = None
        self.weather_data = None
        
        self.init_ui()
        self.apply_theme()
        
    def init_ui(self):
        """Inițializează interfața utilizator"""
        self.setWindowTitle("WeatherScheduler - Planificator Meteo Orar")
        self.setGeometry(100, 100, 1200, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal vertical
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # ==== SECȚIUNEA HEADER ====
        header_layout = QHBoxLayout()
        
        # Label titlu
        title_label = QLabel("📅 WeatherScheduler")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Buton comutare dark/light mode
        self.theme_button = QPushButton("🌙 Mod Întunecat")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setFixedSize(150, 35)
        header_layout.addWidget(self.theme_button)
        
        main_layout.addLayout(header_layout)
        
        # ==== SECȚIUNEA CONTROALE ====
        controls_layout = QHBoxLayout()
        
        # Buton încărcare orar
        self.load_schedule_button = QPushButton("📂 Încarcă Orar")
        self.load_schedule_button.clicked.connect(self.load_schedule)
        self.load_schedule_button.setFixedSize(150, 40)
        controls_layout.addWidget(self.load_schedule_button)
        
        # Buton actualizare meteo
        self.refresh_weather_button = QPushButton("🔄 Actualizează Meteo")
        self.refresh_weather_button.clicked.connect(self.refresh_weather)
        self.refresh_weather_button.setEnabled(False)  # Activat doar după încărcarea orarului
        self.refresh_weather_button.setFixedSize(180, 40)
        controls_layout.addWidget(self.refresh_weather_button)
        
        controls_layout.addStretch()
        
        # Buton setări
        self.settings_button = QPushButton("⚙️ Setări")
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setFixedSize(120, 40)
        controls_layout.addWidget(self.settings_button)
        
        # Buton ajutor
        self.help_button = QPushButton("❓ Ajutor")
        self.help_button.clicked.connect(self.open_help)
        self.help_button.setFixedSize(120, 40)
        controls_layout.addWidget(self.help_button)
        
        # Buton export
        self.export_button = QPushButton("💾 Export")
        self.export_button.clicked.connect(self.export_data)
        self.export_button.setEnabled(False)
        self.export_button.setFixedSize(120, 40)
        controls_layout.addWidget(self.export_button)
        
        main_layout.addLayout(controls_layout)
        
        # ==== LABEL STATUS ====
        self.status_label = QLabel("Bine ai venit! Încarcă un orar pentru a începe.")
        self.status_label.setStyleSheet("padding: 10px; font-size: 14px;")
        main_layout.addWidget(self.status_label)
        
        # ==== TABELUL PRINCIPAL ====
        self.create_schedule_table()
        main_layout.addWidget(self.table)
        
        # ==== SECȚIUNEA GRAFICE ====
        # Aici va fi integrat widget-ul de grafice creat de Sebastian M.
        self.chart_placeholder = QLabel("Graficele vor apărea aici după actualizarea meteo")
        self.chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_placeholder.setStyleSheet("padding: 20px; border: 2px dashed gray;")
        self.chart_placeholder.setMinimumHeight(200)
        main_layout.addWidget(self.chart_placeholder)
        
    def create_schedule_table(self):
        """Creează tabelul pentru afișarea orarului și datelor meteo"""
        self.table = QTableWidget()
        
        # Definim coloanele tabelului
        columns = ["Zi", "Interval Orar", "Materie/Activitate", 
                   "🌡️ Temperatură", "☁️ Condiții", "💧 Precipitații", "💨 Vânt"]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Configurare aspect tabel
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Doar citire
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
            # Aici se va apela funcția de citire din schedule_manager.py (Sebastian D.)
            # Deocamdată simulăm încărcarea
            with open(file_path, 'r', encoding='utf-8') as f:
                self.schedule_data = json.load(f)
            
            self.populate_table_with_schedule()
            self.status_label.setText(f"✅ Orar încărcat cu succes din: {Path(file_path).name}")
            
            # Activează butoanele care necesită orar încărcat
            self.refresh_weather_button.setEnabled(True)
            self.export_button.setEnabled(True)
            
            # Emite semnal că orarul a fost încărcat
            self.schedule_loaded.emit(self.schedule_data)
            
        except Exception as e:
            QMessageBox.critical(self, "Eroare", f"Nu s-a putut încărca orarul:\n{str(e)}")
            
    def populate_table_with_schedule(self):
        """Populează tabelul cu datele din orar"""
        if not self.schedule_data:
            return
            
        # Presupunem că JSON-ul are structura: {"schedule": [{"day": "Luni", "time": "08:00-10:00", "subject": "PIU"}, ...]}
        schedule_entries = self.schedule_data.get("schedule", [])
        
        self.table.setRowCount(len(schedule_entries))
        
        for row, entry in enumerate(schedule_entries):
            # Ziua
            self.table.setItem(row, 0, QTableWidgetItem(entry.get("day", "")))
            # Interval orar
            self.table.setItem(row, 1, QTableWidgetItem(entry.get("time", "")))
            # Materie/Activitate
            self.table.setItem(row, 2, QTableWidgetItem(entry.get("subject", "")))
            
            # Coloanele meteo vor fi populate după actualizare
            self.table.setItem(row, 3, QTableWidgetItem("-"))
            self.table.setItem(row, 4, QTableWidgetItem("-"))
            self.table.setItem(row, 5, QTableWidgetItem("-"))
            self.table.setItem(row, 6, QTableWidgetItem("-"))
            
    def refresh_weather(self):
        """Actualizează datele meteo (apelează funcția lui Sebastian D.)"""
        self.status_label.setText("🔄 Se actualizează datele meteo...")
        
        # Aici se va apela weather_service.py pentru obținerea datelor
        # Deocamdată simulăm actualizarea
        self.status_label.setText("✅ Date meteo actualizate!")
        
        # Emite semnal pentru actualizare meteo
        self.weather_update_requested.emit()
        
        # Actualizează tabelul cu date meteo simulate
        self.update_weather_in_table()
        
    def update_weather_in_table(self):
        """Actualizează coloanele meteo în tabel cu date simulate"""
        # Aceasta este o funcție temporară până când Sebastian D. implementează logica reală
        for row in range(self.table.rowCount()):
            self.table.setItem(row, 3, QTableWidgetItem("18°C"))
            self.table.setItem(row, 4, QTableWidgetItem("Însorit"))
            self.table.setItem(row, 5, QTableWidgetItem("0%"))
            self.table.setItem(row, 6, QTableWidgetItem("10 km/h"))
            
    def toggle_theme(self):
        """Comută între tema light și dark"""
        if self.current_theme == "light":
            self.current_theme = "dark"
            self.theme_button.setText("☀️ Mod Luminos")
        else:
            self.current_theme = "light"
            self.theme_button.setText("🌙 Mod Întunecat")
            
        self.apply_theme()
        
    def apply_theme(self):
        """Aplică tema vizuală curentă"""
        if self.current_theme == "dark":
            # Tema întunecată
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
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
                }
                QHeaderView::section {
                    background-color: #4d4d4d;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #555555;
                }
            """)
        else:
            # Tema luminoasă
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QLabel {
                    color: #000000;
                }
                QPushButton {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #e8e8e8;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
                QPushButton:disabled {
                    background-color: #f0f0f0;
                    color: #999999;
                }
                QTableWidget {
                    background-color: #ffffff;
                    color: #000000;
                    gridline-color: #cccccc;
                }
                QHeaderView::section {
                    background-color: #e8e8e8;
                    color: #000000;
                    padding: 5px;
                    border: 1px solid #cccccc;
                }
            """)
            
    def open_settings(self):
        """Deschide dialogul de setări (implementat de Sebastian M.)"""
        # Aici se va deschide SettingsDialog
        QMessageBox.information(self, "Setări", "Dialogul de setări va fi implementat de Sebastian M.")
        
    def open_help(self):
        """Deschide dialogul de ajutor"""
        help_text = """
        <h2>Ghid utilizare WeatherScheduler</h2>
        <p><b>1. Încarcă Orar:</b> Selectează un fișier JSON sau CSV cu orarul tău.</p>
        <p><b>2. Actualizează Meteo:</b> Obține datele meteo pentru intervalele din orar.</p>
        <p><b>3. Setări:</b> Personalizează unități, sursa datelor și frecvența actualizării.</p>
        <p><b>4. Export:</b> Salvează raportul în format PDF sau CSV.</p>
        <p><b>5. Comutare teme:</b> Schimbă între modul luminos și întunecat.</p>
        
        <p><b>Format JSON orar:</b></p>
        <pre>
        {
            "schedule": [
                {
                    "day": "Luni",
                    "time": "08:00-10:00",
                    "subject": "Programare"
                }
            ]
        }
        </pre>
        """
        QMessageBox.information(self, "Ajutor", help_text)
        
    def export_data(self):
        """Exportă datele curente în PDF sau CSV (implementat de Sebastian M.)"""
        # Aici se va apela export_manager.py
        QMessageBox.information(self, "Export", "Funcția de export va fi implementată de Sebastian M.")