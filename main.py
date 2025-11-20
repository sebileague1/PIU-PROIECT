"""
WeatherScheduler - Aplicație desktop pentru vizualizare meteo pe orar personalizat
Autori: Danalache Emanuel, Danalache Sebastian, Moscalu Sebastian
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """Funcția principală care inițializează și rulează aplicația"""
    app = QApplication(sys.argv)
    
    # Setează numele aplicației
    app.setApplicationName("WeatherScheduler")
    app.setOrganizationName("PIU Project")
    
    # Creează și afișează fereastra principală
    window = MainWindow()
    window.show()
    
    # Rulează bucla evenimentelor Qt
    sys.exit(app.exec())

if __name__ == "__main__":
    main()