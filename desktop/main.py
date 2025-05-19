import sys
import os
from PyQt6.QtWidgets import QApplication
from desktop.ui.components.main_window import MainWindow
from desktop.ui.components.license_dialog import LicenseDialog
from desktop.GLOBAL import GLOBAL

if __name__ == "__main__":
    # Ensure application data directory exists
    os.makedirs(GLOBAL.PATH.APPLICATION_ROOT, exist_ok=True)
    
    # Initialize application
    app = QApplication(sys.argv)
    
    # Write startup log
    GLOBAL.LOG.write_log("Application started")
    
    # Check for license key
    license_key = GLOBAL.LICENSE.get_license_key()
    
    # Create main window but don't show it yet
    window = MainWindow()
    
    # If no license is found, show the license dialog
    if not license_key:
        license_dialog = LicenseDialog()
        
        # Show the license dialog and wait for user's action
        if license_dialog.exec():
            # License dialog was accepted
            GLOBAL.LOG.write_log("License dialog closed with license: " + 
                               ("valid" if GLOBAL.LICENSE.get_license_key() else "trial"))
        else:
            # User closed the dialog without accepting
            GLOBAL.LOG.write_log("License dialog was closed without activation")
            sys.exit(0)
    
    # Show the main window
    window.show()
    
    # Execute application
    sys.exit(app.exec())
