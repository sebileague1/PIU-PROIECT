from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox, QWidget
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from typing import List, Dict, Optional
from datetime import datetime

class NotificationManager(QObject):
    """
    Gestionează notificările pop-up pentru condiții meteo nefavorabile
    Folosește QSystemTrayIcon pentru notificări în system tray
    """
    
    # Semnale
    notification_clicked = pyqtSignal(dict)  # Emis când utilizatorul dă click pe notificare
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        
        # Creăm icon-ul pentru system tray
        self.tray_icon = None
        self.create_tray_icon()
        
        # Setări pentru notificări
        self.notifications_enabled = True
        self.check_interval = 3600000  # 1 oră în milisecunde
        
        # Timer pentru verificări automate
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.scheduled_check)
        
        # Păstrăm istoric de notificări pentru a nu trimite duplicate
        self.notification_history = []
        
    def create_tray_icon(self):
        """Creează icon-ul din system tray"""
        # Creăm un icon simplu pentru aplicație
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent
        
        painter = QPainter(pixmap)
        painter.setBrush(QColor(70, 130, 180))  # Albastru
        painter.setPen(QColor(30, 60, 90))
        painter.drawEllipse(8, 8, 48, 48)
        
        # Desenăm un simbol de soare/nor
        painter.setBrush(QColor(255, 200, 50))
        painter.drawEllipse(20, 20, 24, 24)
        painter.end()
        
        icon = QIcon(pixmap)
        
        # Creăm system tray icon-ul
        self.tray_icon = QSystemTrayIcon(icon, self.parent_widget)
        self.tray_icon.setToolTip("WeatherScheduler - Monitorizare meteo")
        
        # Creăm meniul pentru tray icon
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Arată aplicația")
        show_action.triggered.connect(self.show_main_window)
        
        tray_menu.addSeparator()
        
        check_action = tray_menu.addAction("Verifică meteo acum")
        check_action.triggered.connect(self.manual_check)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Ieșire")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Conectăm click-ul pe icon
        self.tray_icon.activated.connect(self.tray_icon_clicked)
        
        # Arătăm icon-ul
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()
        else:
            print("System tray nu este disponibil pe acest sistem")
            
    def tray_icon_clicked(self, reason):
        """Handler pentru click pe tray icon"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Click simplu - arată fereastra principală
            self.show_main_window()
            
    def show_main_window(self):
        """Arată fereastra principală a aplicației"""
        if self.parent_widget:
            self.parent_widget.show()
            self.parent_widget.activateWindow()
            self.parent_widget.raise_()
            
    def manual_check(self):
        """Verificare manuală declanșată de utilizator"""
        # Aici se va apela funcția de verificare meteo
        # Deocamdată arătăm un mesaj
        if self.tray_icon and QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                "WeatherScheduler",
                "Se verifică condițiile meteo...",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            
    def quit_application(self):
        """Închide aplicația"""
        if self.parent_widget:
            self.parent_widget.close()
            
    def check_rain_risk_and_notify(self, risky_entries: List[Dict]):
        """
        Verifică intrările cu risc de ploaie și trimite notificări
        
        Args:
            risky_entries: Lista cu intrări din orar care au risc de ploaie
        """
        if not self.notifications_enabled:
            return
            
        if not risky_entries:
            # Nu există risc de ploaie
            return
            
        # Filtrăm doar intrările pentru care nu am trimis deja notificare
        new_risky_entries = []
        for entry in risky_entries:
            entry_id = f"{entry.get('day', '')}_{entry.get('time', '')}_{entry.get('subject', '')}"
            
            if entry_id not in self.notification_history:
                new_risky_entries.append(entry)
                self.notification_history.append(entry_id)
                
        if not new_risky_entries:
            return
            
        # Construim mesajul de notificare
        if len(new_risky_entries) == 1:
            entry = new_risky_entries[0]
            weather = entry.get("weather_data", {})
            precip_prob = weather.get("precipitation_probability", 0)
            
            title = "⚠️ Risc de ploaie"
            message = (
                f"{entry.get('subject', 'Activitate')} - {entry.get('time', '')}\n"
                f"Probabilitate ploaie: {precip_prob}%\n"
                f"Nu uita umbrela!"
            )
        else:
            title = f"⚠️ Risc de ploaie la {len(new_risky_entries)} activități"
            message = f"Există risc de ploaie la {len(new_risky_entries)} activități mâine. Verifică detaliile în aplicație!"
            
        # Trimitem notificarea
        self.show_notification(title, message, QSystemTrayIcon.MessageIcon.Warning)
        
        # Opțional: arătăm și un QMessageBox dacă fereastra este vizibilă
        if self.parent_widget and self.parent_widget.isVisible():
            self.show_rain_warning_dialog(new_risky_entries)
            
    def show_notification(
        self, 
        title: str, 
        message: str, 
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        duration: int = 5000
    ):
        """
        Afișează o notificare în system tray
        
        Args:
            title: Titlul notificării
            message: Mesajul notificării
            icon: Tipul de icon (Information, Warning, Critical)
            duration: Durata afișării în milisecunde
        """
        if not self.tray_icon or not QSystemTrayIcon.isSystemTrayAvailable():
            print(f"Notificare (system tray indisponibil): {title} - {message}")
            return
            
        if not self.notifications_enabled:
            return
            
        self.tray_icon.showMessage(title, message, icon, duration)
        
    def show_rain_warning_dialog(self, risky_entries: List[Dict]):
        """
        Arată un dialog detaliat cu avertizare de ploaie
        
        Args:
            risky_entries: Lista cu intrări care au risc de ploaie
        """
        if not self.parent_widget:
            return
            
        # Construim mesajul detaliat
        message_parts = ["Există risc de ploaie pentru următoarele activități de mâine:\n"]
        
        for i, entry in enumerate(risky_entries, 1):
            weather = entry.get("weather_data", {})
            precip_prob = weather.get("precipitation_probability", 0)
            weather_desc = weather.get("weather_description", "Necunoscut")
            
            message_parts.append(
                f"{i}. {entry.get('subject', 'Activitate')} "
                f"({entry.get('time', '')})\n"
                f"   Condiții: {weather_desc} - {precip_prob}% șansă de ploaie"
            )
            
        message_parts.append("\n🌂 Recomandare: Nu uita să iei umbrela!")
        
        full_message = "\n".join(message_parts)
        
        msg_box = QMessageBox(self.parent_widget)
        msg_box.setWindowTitle("⚠️ Avertizare Meteo")
        msg_box.setText(full_message)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
    def start_automatic_checks(self, interval_minutes: int = 60):
        """
        Pornește verificările automate periodice
        
        Args:
            interval_minutes: Intervalul între verificări în minute
        """
        self.check_interval = interval_minutes * 60000  # Convertim în milisecunde
        self.check_timer.start(self.check_interval)
        
        print(f"Verificări automate pornite: la fiecare {interval_minutes} minute")
        
    def stop_automatic_checks(self):
        """Oprește verificările automate"""
        self.check_timer.stop()
        print("Verificări automate oprite")
        
    def scheduled_check(self):
        """
        Funcție apelată periodic de timer pentru verificări automate
        Aceasta va trebui conectată la logica principală de verificare meteo
        """
        print(f"Verificare automată la {datetime.now().strftime('%H:%M:%S')}")
        
        # Aici se va apela funcția de verificare din weather_service
        # care va returna lista cu intrări cu risc de ploaie
        # și apoi se va apela check_rain_risk_and_notify
        
        # Deocamdată trimitem o notificare de test
        if self.notifications_enabled:
            self.show_notification(
                "WeatherScheduler",
                "Verificare automată efectuată",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            
    def enable_notifications(self, enabled: bool):
        """Activează sau dezactivează notificările"""
        self.notifications_enabled = enabled
        
        if enabled:
            print("Notificări activate")
        else:
            print("Notificări dezactivate")
            
    def clear_notification_history(self):
        """Șterge istoricul de notificări"""
        self.notification_history.clear()
        print("Istoric notificări șters")
        
    def set_check_interval(self, minutes: int):
        """
        Setează intervalul pentru verificările automate
        
        Args:
            minutes: Intervalul în minute (minim 5, maxim 1440 = 24 ore)
        """
        minutes = max(5, min(1440, minutes))
        
        if self.check_timer.isActive():
            self.check_timer.stop()
            self.start_automatic_checks(minutes)
        else:
            self.check_interval = minutes * 60000
            
        print(f"Interval verificări setat la: {minutes} minute")
        
    def show_info_notification(self, message: str):
        """Trimite o notificare informativă simplă"""
        self.show_notification(
            "WeatherScheduler",
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
        
    def show_success_notification(self, message: str):
        """Trimite o notificare de succes"""
        self.show_notification(
            "✅ Succes",
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
        
    def show_error_notification(self, message: str):
        """Trimite o notificare de eroare"""
        self.show_notification(
            "❌ Eroare",
            message,
            QSystemTrayIcon.MessageIcon.Critical,
            5000
        )
        
    def cleanup(self):
        """Curăță resursele la închiderea aplicației"""
        if self.check_timer.isActive():
            self.check_timer.stop()
            
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()