"""
Dialog pentru setările aplicației
Responsabil: Moscalu Sebastian
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QSpinBox, QGroupBox,
                             QCheckBox, QLineEdit, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
import json
from pathlib import Path

class SettingsDialog(QDialog):
    """
    Dialog pentru configurarea setărilor aplicației:
    - Unități de măsură (Celsius/Fahrenheit)
    - Frecvența actualizării datelor
    - Activare/dezactivare notificări
    - Locație pentru date meteo
    """
    
    # Semnal emis când setările sunt salvate
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.settings = self.load_settings()
        self.init_ui()
        self.load_current_settings()
        
    def init_ui(self):
        """Inițializează interfața dialogului"""
        self.setWindowTitle("⚙️ Setări WeatherScheduler")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # === SECȚIUNEA UNITĂȚI ===
        units_group = QGroupBox("🌡️ Unități de măsură")
        units_layout = QFormLayout()
        units_group.setLayout(units_layout)
        
        # Selector temperatură
        self.temp_unit_combo = QComboBox()
        self.temp_unit_combo.addItems(["Celsius (°C)", "Fahrenheit (°F)"])
        units_layout.addRow("Temperatură:", self.temp_unit_combo)
        
        # Selector viteză vânt
        self.wind_unit_combo = QComboBox()
        self.wind_unit_combo.addItems(["km/h", "m/s", "mph"])
        units_layout.addRow("Viteză vânt:", self.wind_unit_combo)
        
        layout.addWidget(units_group)
        
        # === SECȚIUNEA ACTUALIZARE DATE ===
        update_group = QGroupBox("🔄 Actualizare date")
        update_layout = QFormLayout()
        update_group.setLayout(update_layout)
        
        # Interval actualizare automată
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setMinimum(5)
        self.update_interval_spin.setMaximum(1440)  # 24 ore
        self.update_interval_spin.setValue(60)
        self.update_interval_spin.setSuffix(" minute")
        update_layout.addRow("Interval verificare:", self.update_interval_spin)
        
        # Checkbox pentru actualizare automată
        self.auto_update_check = QCheckBox("Activează verificarea automată")
        self.auto_update_check.setChecked(True)
        update_layout.addRow("", self.auto_update_check)
        
        # Durata cache
        self.cache_duration_spin = QSpinBox()
        self.cache_duration_spin.setMinimum(10)
        self.cache_duration_spin.setMaximum(120)
        self.cache_duration_spin.setValue(30)
        self.cache_duration_spin.setSuffix(" minute")
        update_layout.addRow("Durata cache:", self.cache_duration_spin)
        
        layout.addWidget(update_group)
        
        # === SECȚIUNEA NOTIFICĂRI ===
        notif_group = QGroupBox("🔔 Notificări")
        notif_layout = QVBoxLayout()
        notif_group.setLayout(notif_layout)
        
        self.notif_enabled_check = QCheckBox("Activează notificările")
        self.notif_enabled_check.setChecked(True)
        notif_layout.addWidget(self.notif_enabled_check)
        
        self.rain_alert_check = QCheckBox("Alertă pentru risc de ploaie (>30%)")
        self.rain_alert_check.setChecked(True)
        notif_layout.addWidget(self.rain_alert_check)
        
        self.extreme_weather_check = QCheckBox("Alertă pentru condiții extreme")
        self.extreme_weather_check.setChecked(True)
        notif_layout.addWidget(self.extreme_weather_check)
        
        # Prag minim pentru notificări ploaie
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Prag alertă ploaie:")
        self.rain_threshold_spin = QSpinBox()
        self.rain_threshold_spin.setMinimum(10)
        self.rain_threshold_spin.setMaximum(100)
        self.rain_threshold_spin.setValue(30)
        self.rain_threshold_spin.setSuffix("%")
        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.rain_threshold_spin)
        threshold_layout.addStretch()
        notif_layout.addLayout(threshold_layout)
        
        layout.addWidget(notif_group)
        
        # === SECȚIUNEA LOCAȚIE ===
        location_group = QGroupBox("📍 Locație")
        location_layout = QFormLayout()
        location_group.setLayout(location_layout)
        
        # Input latitudine
        self.latitude_input = QLineEdit()
        self.latitude_input.setPlaceholderText("ex: 44.4268")
        location_layout.addRow("Latitudine:", self.latitude_input)
        
        # Input longitudine
        self.longitude_input = QLineEdit()
        self.longitude_input.setPlaceholderText("ex: 26.1025")
        location_layout.addRow("Longitudine:", self.longitude_input)
        
        # Mesaj informativ
        info_label = QLabel("💡 Default: București (44.4268°N, 26.1025°E)")
        info_label.setStyleSheet("color: gray; font-size: 11px;")
        location_layout.addRow("", info_label)
        
        layout.addWidget(location_group)
        
        # === SECȚIUNEA AFIȘARE ===
        display_group = QGroupBox("🎨 Afișare")
        display_layout = QFormLayout()
        display_group.setLayout(display_layout)
        
        # Număr de zile afișate
        self.forecast_days_spin = QSpinBox()
        self.forecast_days_spin.setMinimum(1)
        self.forecast_days_spin.setMaximum(7)
        self.forecast_days_spin.setValue(7)
        self.forecast_days_spin.setSuffix(" zile")
        display_layout.addRow("Zile prognoză:", self.forecast_days_spin)
        
        # Checkbox pentru modul compact
        self.compact_mode_check = QCheckBox("Mod compact (mai puține detalii)")
        display_layout.addRow("", self.compact_mode_check)
        
        layout.addWidget(display_group)
        
        # === BUTOANE ===
        buttons_layout = QHBoxLayout()
        
        # Buton restaurare valori implicite
        self.reset_button = QPushButton("🔄 Restaurează valori implicite")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        buttons_layout.addWidget(self.reset_button)
        
        buttons_layout.addStretch()
        
        # Buton anulare
        self.cancel_button = QPushButton("Anulează")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        # Buton salvare
        self.save_button = QPushButton("💾 Salvează")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
        
    def load_current_settings(self):
        """Încarcă setările curente în interfață"""
        # Unități
        if self.settings.get("temperature_unit", "celsius") == "fahrenheit":
            self.temp_unit_combo.setCurrentIndex(1)
        else:
            self.temp_unit_combo.setCurrentIndex(0)
            
        wind_unit = self.settings.get("wind_unit", "km/h")
        wind_index = self.wind_unit_combo.findText(wind_unit)
        if wind_index >= 0:
            self.wind_unit_combo.setCurrentIndex(wind_index)
            
        # Actualizare
        self.update_interval_spin.setValue(self.settings.get("update_interval_minutes", 60))
        self.auto_update_check.setChecked(self.settings.get("auto_update_enabled", True))
        self.cache_duration_spin.setValue(self.settings.get("cache_duration_minutes", 30))
        
        # Notificări
        self.notif_enabled_check.setChecked(self.settings.get("notifications_enabled", True))
        self.rain_alert_check.setChecked(self.settings.get("rain_alert_enabled", True))
        self.extreme_weather_check.setChecked(self.settings.get("extreme_weather_alert", True))
        self.rain_threshold_spin.setValue(self.settings.get("rain_threshold", 30))
        
        # Locație
        self.latitude_input.setText(str(self.settings.get("latitude", 44.4268)))
        self.longitude_input.setText(str(self.settings.get("longitude", 26.1025)))
        
        # Afișare
        self.forecast_days_spin.setValue(self.settings.get("forecast_days", 7))
        self.compact_mode_check.setChecked(self.settings.get("compact_mode", False))
        
    def save_settings(self):
        """Salvează setările și emite semnalul de modificare"""
        try:
            # Validare coordonate
            try:
                latitude = float(self.latitude_input.text())
                longitude = float(self.longitude_input.text())
                
                if not (-90 <= latitude <= 90):
                    raise ValueError("Latitudinea trebuie să fie între -90 și 90")
                if not (-180 <= longitude <= 180):
                    raise ValueError("Longitudinea trebuie să fie între -180 și 180")
            except ValueError as e:
                QMessageBox.warning(
                    self,
                    "Date invalide",
                    f"Coordonatele introduse sunt invalide:\n{str(e)}"
                )
                return
                
            # Construim dicționarul cu noile setări
            new_settings = {
                # Unități
                "temperature_unit": "celsius" if self.temp_unit_combo.currentIndex() == 0 else "fahrenheit",
                "wind_unit": self.wind_unit_combo.currentText(),
                
                # Actualizare
                "update_interval_minutes": self.update_interval_spin.value(),
                "auto_update_enabled": self.auto_update_check.isChecked(),
                "cache_duration_minutes": self.cache_duration_spin.value(),
                
                # Notificări
                "notifications_enabled": self.notif_enabled_check.isChecked(),
                "rain_alert_enabled": self.rain_alert_check.isChecked(),
                "extreme_weather_alert": self.extreme_weather_check.isChecked(),
                "rain_threshold": self.rain_threshold_spin.value(),
                
                # Locație
                "latitude": latitude,
                "longitude": longitude,
                
                # Afișare
                "forecast_days": self.forecast_days_spin.value(),
                "compact_mode": self.compact_mode_check.isChecked()
            }
            
            # Salvăm în fișier
            self.settings = new_settings
            self.persist_settings()
            
            # Emitem semnalul
            self.settings_changed.emit(new_settings)
            
            # Închidem dialogul
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Eroare",
                f"Nu s-au putut salva setările:\n{str(e)}"
            )
            
    def reset_to_defaults(self):
        """Restaurează valorile implicite"""
        reply = QMessageBox.question(
            self,
            "Confirmare",
            "Sigur dorești să restaurezi toate setările la valorile implicite?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings = self.get_default_settings()
            self.load_current_settings()
            
    def load_settings(self) -> dict:
        """Încarcă setările din fișier"""
        settings_path = Path("resources/settings.json")
        
        try:
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Nu s-au putut încărca setările: {e}")
            
        return self.get_default_settings()
        
    def persist_settings(self):
        """Salvează setările în fișier"""
        settings_path = Path("resources/settings.json")
        
        try:
            # Creăm directorul dacă nu există
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Nu s-au putut salva setările: {e}")
            
    @staticmethod
    def get_default_settings() -> dict:
        """Returnează setările implicite"""
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
            "latitude": 44.4268,
            "longitude": 26.1025,
            "forecast_days": 7,
            "compact_mode": False
        }