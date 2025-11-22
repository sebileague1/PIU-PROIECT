from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QSpinBox, QGroupBox,
                             QCheckBox, QLineEdit, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
import json
from pathlib import Path

class SettingsDialog(QDialog):
    """
    Dialog pentru configurarea setarilor aplicatiei:
    - Unitati de masura (Celsius/Fahrenheit)
    - Frecventa actualizarii datelor
    - Activare/dezactivare notificari
    - Locatie pentru date meteo
    """
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.settings = self.load_settings()
        self.init_ui()
        self.load_current_settings()
        
    def init_ui(self):
        """Initializeaza interfata dialogului"""
        self.setWindowTitle("⚙️ Setari WeatherScheduler")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        units_group = QGroupBox("🌡️ Unitati de masura")
        units_layout = QFormLayout()
        units_group.setLayout(units_layout)
        
        self.temp_unit_combo = QComboBox()
        self.temp_unit_combo.addItems(["Celsius (°C)", "Fahrenheit (°F)"])
        units_layout.addRow("Temperatura:", self.temp_unit_combo)
        
        self.wind_unit_combo = QComboBox()
        self.wind_unit_combo.addItems(["km/h", "m/s", "mph"])
        units_layout.addRow("Viteza vant:", self.wind_unit_combo)
        
        layout.addWidget(units_group)
        
        update_group = QGroupBox("🔄 Actualizare date")
        update_layout = QFormLayout()
        update_group.setLayout(update_layout)
        
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setMinimum(5)
        self.update_interval_spin.setMaximum(1440)
        self.update_interval_spin.setValue(60)
        self.update_interval_spin.setSuffix(" minute")
        update_layout.addRow("Interval verificare:", self.update_interval_spin)
        
        self.auto_update_check = QCheckBox("Activeaza verificarea automata")
        self.auto_update_check.setChecked(True)
        update_layout.addRow("", self.auto_update_check)
        
        self.cache_duration_spin = QSpinBox()
        self.cache_duration_spin.setMinimum(10)
        self.cache_duration_spin.setMaximum(120)
        self.cache_duration_spin.setValue(30)
        self.cache_duration_spin.setSuffix(" minute")
        update_layout.addRow("Durata cache:", self.cache_duration_spin)
        
        layout.addWidget(update_group)
        
        notif_group = QGroupBox("🔔 Notificari")
        notif_layout = QVBoxLayout()
        notif_group.setLayout(notif_layout)
        
        self.notif_enabled_check = QCheckBox("Activeaza notificarile")
        self.notif_enabled_check.setChecked(True)
        notif_layout.addWidget(self.notif_enabled_check)
        
        self.rain_alert_check = QCheckBox("Alerta pentru risc de ploaie (>30%)")
        self.rain_alert_check.setChecked(True)
        notif_layout.addWidget(self.rain_alert_check)
        
        self.extreme_weather_check = QCheckBox("Alerta pentru conditii extreme")
        self.extreme_weather_check.setChecked(True)
        notif_layout.addWidget(self.extreme_weather_check)
        
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Prag alerta ploaie:")
        self.rain_threshold_spin = QSpinBox()
        self.rain_threshold_spin.setMinimum(10)
        self.rain_threshold_spin.setMaximum(100)
        self.rain_threshold_spin.setValue(30)
        self.rain_threshold_spin.setSuffix("%")
        self.rain_threshold_spin.setMinimumWidth(80)
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.rain_threshold_spin)
        threshold_layout.addStretch()
        notif_layout.addLayout(threshold_layout)
        
        layout.addWidget(notif_group)
        
        location_group = QGroupBox("📍 Locatie")
        location_layout = QFormLayout()
        location_group.setLayout(location_layout)
        
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("ex: Iasi, Bacau, Bucuresti")
        location_layout.addRow("Nume Oras:", self.location_input)
        
        layout.addWidget(location_group)
        
        display_group = QGroupBox("🎨 Afisare")
        display_layout = QFormLayout()
        display_group.setLayout(display_layout)
        
        self.forecast_days_spin = QSpinBox()
        self.forecast_days_spin.setMinimum(1)
        self.forecast_days_spin.setMaximum(7)
        self.forecast_days_spin.setValue(7)
        self.forecast_days_spin.setSuffix(" zile")
        display_layout.addRow("Zile prognoza:", self.forecast_days_spin)
        
        self.compact_mode_check = QCheckBox("Mod compact (mai putine detalii)")
        display_layout.addRow("", self.compact_mode_check)
        
        layout.addWidget(display_group)
        

        buttons_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("🔄 Restaureaza valori implicite")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        buttons_layout.addWidget(self.reset_button)
        
        buttons_layout.addStretch()
        
        self.cancel_button = QPushButton("Anuleaza")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("💾 Salveaza")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
        
    def load_current_settings(self):
        """Incarca setarile curente in interfata"""

        if self.settings.get("temperature_unit", "celsius") == "fahrenheit":
            self.temp_unit_combo.setCurrentIndex(1)
        else:
            self.temp_unit_combo.setCurrentIndex(0)
            
        wind_unit = self.settings.get("wind_unit", "km/h")
        wind_index = self.wind_unit_combo.findText(wind_unit)
        if wind_index >= 0:
            self.wind_unit_combo.setCurrentIndex(wind_index)
            
        self.update_interval_spin.setValue(self.settings.get("update_interval_minutes", 60))
        self.auto_update_check.setChecked(self.settings.get("auto_update_enabled", True))
        self.cache_duration_spin.setValue(self.settings.get("cache_duration_minutes", 30))
        
        self.notif_enabled_check.setChecked(self.settings.get("notifications_enabled", True))
        self.rain_alert_check.setChecked(self.settings.get("rain_alert_enabled", True))
        self.extreme_weather_check.setChecked(self.settings.get("extreme_weather_alert", True))
        self.rain_threshold_spin.setValue(self.settings.get("rain_threshold", 30))
        
        self.location_input.setText(self.settings.get("location_name", "București"))
        
        self.forecast_days_spin.setValue(self.settings.get("forecast_days", 7))
        self.compact_mode_check.setChecked(self.settings.get("compact_mode", False))
        
    def save_settings(self):
        """Salveaza setarile si emite semnalul de modificare"""
        try:
            new_settings = {
                "temperature_unit": "celsius" if self.temp_unit_combo.currentIndex() == 0 else "fahrenheit",
                "wind_unit": self.wind_unit_combo.currentText(),
                
                "update_interval_minutes": self.update_interval_spin.value(),
                "auto_update_enabled": self.auto_update_check.isChecked(),
                "cache_duration_minutes": self.cache_duration_spin.value(),
                
                "notifications_enabled": self.notif_enabled_check.isChecked(),
                "rain_alert_enabled": self.rain_alert_check.isChecked(),
                "extreme_weather_alert": self.extreme_weather_check.isChecked(),
                "rain_threshold": self.rain_threshold_spin.value(),
                
                "location_name": self.location_input.text().strip(),
                
                "forecast_days": self.forecast_days_spin.value(),
                "compact_mode": self.compact_mode_check.isChecked()
            }
            
            self.settings = new_settings
            self.persist_settings()
            
            self.settings_changed.emit(new_settings)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Eroare",
                f"Nu s-au putut salva setarile:\n{str(e)}"
            )
            
    def reset_to_defaults(self):
        """Restaureaza valorile implicite"""
        reply = QMessageBox.question(
            self,
            "Confirmare",
            "Sigur doresti sa restaurezi toate setarile la valorile implicite?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings = self.get_default_settings()
            self.load_current_settings()
            
    def load_settings(self) -> dict:
        """Incarca setarile din fisier"""
        settings_path = Path("resources/settings.json")
        
        try:
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Nu s-au putut incarca setarile: {e}")
            
        return self.get_default_settings()
        
    def persist_settings(self):
        """Salveaza setarile in fisier"""
        settings_path = Path("resources/settings.json")
        
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Nu s-au putut salva setarile: {e}")
            
    @staticmethod
    def get_default_settings() -> dict:
        """Returneaza setarile implicite"""
        return {
            "temperature_unit": "celsius",
            "wind_unit": "km/h",
            "update_interval_minutes": 60,
            "auto_update_enabled": True,
            "cache_duration_minutes": 30,
            "notifications_enabled": True,
            "rain_alert_enabled": True,
            "extreme_weather_alert": True,
            "rain_threshold": 30,
            "location_name": "București",
            "forecast_days": 7,
            "compact_mode": False
        }