from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox, QWidget
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from typing import List, Dict, Optional
from datetime import datetime

class NotificationManager(QObject):
    """
    Gestioneaza notificarile pop-up pentru conditii meteo nefavorabile
    Foloseste QSystemTrayIcon pentru notificari in system tray
    """
    
    notification_clicked = pyqtSignal(dict)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        
        self.tray_icon = None
        self.create_tray_icon()
        
        self.notifications_enabled = True
        self.check_interval = 3600000 
        
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.scheduled_check)
        
        self.notification_history = []
        
    def create_tray_icon(self):
        """Creeaza icon-ul din system tray"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))  
        
        painter = QPainter(pixmap)
        painter.setBrush(QColor(70, 130, 180))
        painter.setPen(QColor(30, 60, 90))
        painter.drawEllipse(8, 8, 48, 48)
        
        painter.setBrush(QColor(255, 200, 50))
        painter.drawEllipse(20, 20, 24, 24)
        painter.end()
        
        icon = QIcon(pixmap)

        self.tray_icon = QSystemTrayIcon(icon, self.parent_widget)
        self.tray_icon.setToolTip("WeatherScheduler - Monitorizare meteo")

        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Arata aplicatia")
        show_action.triggered.connect(self.show_main_window)
        
        tray_menu.addSeparator()
        
        check_action = tray_menu.addAction("Verifica meteo acum")
        check_action.triggered.connect(self.manual_check)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Iesire")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        self.tray_icon.activated.connect(self.tray_icon_clicked)
        
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()
        else:
            print("System tray nu este disponibil pe acest sistem")
            
    def tray_icon_clicked(self, reason):
        """Handler pentru click pe tray icon"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_main_window()
            
    def show_main_window(self):
        """Arata fereastra principala a aplicatiei"""
        if self.parent_widget:
            self.parent_widget.show()
            self.parent_widget.activateWindow()
            self.parent_widget.raise_()
            
    def manual_check(self):
        """Verificare manuala declansata de utilizator"""
        if self.tray_icon and QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                "WeatherScheduler",
                "Se verifica conditiile meteo...",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            
    def quit_application(self):
        """Inchide aplicatia"""
        if self.parent_widget:
            self.parent_widget.close()
            
    def check_rain_risk_and_notify(self, risky_entries: List[Dict]):
        """
        Verifica intrarile cu risc de ploaie si trimite notificari
        
        Args:
            risky_entries: Lista cu intrari din orar care au risc de ploaie
        """
        if not self.notifications_enabled:
            return
            
        if not risky_entries:
            return
            
        new_risky_entries = []
        for entry in risky_entries:
            entry_id = f"{entry.get('day', '')}_{entry.get('time', '')}_{entry.get('subject', '')}"
            
            if entry_id not in self.notification_history:
                new_risky_entries.append(entry)
                self.notification_history.append(entry_id)
                
        if not new_risky_entries:
            return
            
        if len(new_risky_entries) == 1:
            entry = new_risky_entries[0]
            weather = entry.get("weather_data", {})
            precip_prob = weather.get("precipitation_probability", 0)
            
            title = "⚠️ Risc de ploaie"
            message = (
                f"{entry.get('subject', 'Activitate')} - {entry.get('time', '')}\n"
                f"Probabilitate ploaie: {precip_prob}%\n"
            )
        else:
            title = f"⚠️ Risc de ploaie la {len(new_risky_entries)} activitati"
            message = f"Exista risc de ploaie la {len(new_risky_entries)} activitati maine. Verifica detaliile in aplicatie!"
            
        self.show_notification(title, message, QSystemTrayIcon.MessageIcon.Warning)
        
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
        Afiseaza o notificare in system tray
        
        Args:
            title: Titlul notificarii
            message: Mesajul notificarii
            icon: Tipul de icon (Information, Warning, Critical)
            duration: Durata afisarii in milisecunde
        """
        if not self.tray_icon or not QSystemTrayIcon.isSystemTrayAvailable():
            print(f"Notificare (system tray indisponibil): {title} - {message}")
            return
            
        if not self.notifications_enabled:
            return
            
        self.tray_icon.showMessage(title, message, icon, duration)
        
    def show_rain_warning_dialog(self, risky_entries: List[Dict]):
        """
        Arata un dialog detaliat cu avertizare de ploaie
        
        Args:
            risky_entries: Lista cu intrari care au risc de ploaie
        """
        if not self.parent_widget:
            return
            
        message_parts = ["Exista risc de ploaie pentru urmatoarele activitati de maine:\n"]
        
        for i, entry in enumerate(risky_entries, 1):
            weather = entry.get("weather_data", {})
            precip_prob = weather.get("precipitation_probability", 0)
            weather_desc = weather.get("weather_description", "Necunoscut")
            
            message_parts.append(
                f"{i}. {entry.get('subject', 'Activitate')} "
                f"({entry.get('time', '')})\n"
                f"   Conditii: {weather_desc} - {precip_prob}% sansa de ploaie"
            )
            
        message_parts.append("\n🌂 Recomandare: Nu uita sa iei umbrela!")
        
        full_message = "\n".join(message_parts)
        
        msg_box = QMessageBox(self.parent_widget)
        msg_box.setWindowTitle("⚠️ Avertizare Meteo")
        msg_box.setText(full_message)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
    def start_automatic_checks(self, interval_minutes: int = 60):
        """
        Porneste verificarile automate periodice
        
        Args:
            interval_minutes: Intervalul intre verificari in minute
        """
        self.check_interval = interval_minutes * 60000 
        self.check_timer.start(self.check_interval)
        
        print(f"Verificari automate pornite: la fiecare {interval_minutes} minute")
        
    def stop_automatic_checks(self):
        """Opreste verificarile automate"""
        self.check_timer.stop()
        print("Verificari automate oprite")
        
    def scheduled_check(self):
        """
        Functie apelata periodic de timer pentru verificari automate
        Aceasta va trebui conectata la logica principala de verificare meteo
        """
        print(f"Verificare automata la {datetime.now().strftime('%H:%M:%S')}")

        if self.notifications_enabled:
            self.show_notification(
                "WeatherScheduler",
                "Verificare automata efectuata",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            
    def enable_notifications(self, enabled: bool):
        """Activeaza sau dezactiveaza notificarile"""
        self.notifications_enabled = enabled
        
        if enabled:
            print("Notificari activate")
        else:
            print("Notificari dezactivate")
            
    def clear_notification_history(self):
        """Sterge istoricul de notificari"""
        self.notification_history.clear()
        print("Istoric notificari sters")
        
    def set_check_interval(self, minutes: int):
        """
        Seteaza intervalul pentru verificarile automate
        
        Args:
            minutes: Intervalul in minute (minim 5, maxim 1440 = 24 ore)
        """
        minutes = max(5, min(1440, minutes))
        
        if self.check_timer.isActive():
            self.check_timer.stop()
            self.start_automatic_checks(minutes)
        else:
            self.check_interval = minutes * 60000
            
        print(f"Interval verificari setat la: {minutes} minute")
        
    def show_info_notification(self, message: str):
        """Trimite o notificare informativa simpla"""
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
        """Curata resursele la inchiderea aplicatiei"""
        if self.check_timer.isActive():
            self.check_timer.stop()
            
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()