import sys
import os
from PyQt6.QtWidgets import QApplication
from desktop.ui.components.main_window import MainWindow
from desktop.GLOBAL import GLOBAL

if __name__ == "__main__":
    # Ensure application data directory exists
    os.makedirs(GLOBAL.PATH.APPLICATION_ROOT, exist_ok=True)
    
    # Initialize application
    app = QApplication(sys.argv)
    
    # Write startup log
    GLOBAL.LOG.write_log("Application started")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Execute application
    sys.exit(app.exec())
