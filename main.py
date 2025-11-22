import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """Functia principala care initializeaza si ruleaza aplicatia"""
    app = QApplication(sys.argv)
    
    app.setApplicationName("WeatherScheduler")
    app.setOrganizationName("PIU Project")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()