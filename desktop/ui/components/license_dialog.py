from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                           QPushButton, QHBoxLayout, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from desktop.GLOBAL import GLOBAL
import uuid
import requests

class LicenseDialog(QDialog):
    license_validated = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CarGenius - License Activation")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setMinimumSize(500, 300)
        self.setModal(True)
        self.setObjectName("LicenseDialog")
        
        self._create_ui()
        self._connect_signals()
        self._load_styles()
        
    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Header with app title
        title_label = QLabel("CarGenius")
        title_label.setObjectName("app_title")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle = QLabel("License Activation")
        subtitle.setObjectName("license_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)
        
        # License input frame
        input_frame = QFrame()
        input_frame.setObjectName("license_frame")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(15)
        
        # Instructions
        instructions = QLabel("Please enter your license key to activate CarGenius:")
        instructions.setObjectName("instructions")
        input_layout.addWidget(instructions)
        
        # License key input
        self.license_input = QLineEdit()
        self.license_input.setObjectName("license_input")
        self.license_input.setPlaceholderText("XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX")
        input_layout.addWidget(self.license_input)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(15)
        
        # Add spacer to push buttons to the right
        button_layout.addStretch()
        
        # Activate button
        self.activate_button = QPushButton("Activate License")
        self.activate_button.setObjectName("primary_button")
        button_layout.addWidget(self.activate_button)
        
        # Add buttons to input layout
        input_layout.addLayout(button_layout)
        
        # Add input frame to main layout
        main_layout.addWidget(input_frame)
        
    def _connect_signals(self):
        self.activate_button.clicked.connect(self._validate_license)
        
    def _load_styles(self):
        # Use the same theme as the main application
        try:
            theme = GLOBAL.get_settings().get("theme", "light")
            style_file = f"desktop/ui/themes/{theme}.qss"
            with open(style_file, 'r') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            pass
            
    def _validate_license(self):
        license_key = self.license_input.text().strip()
        
        if not license_key:
            QMessageBox.warning(self, "Invalid License", "Please enter a license key.")
            return
            
        try:
            uuid_obj = uuid.UUID(license_key, version=4)
            if str(uuid_obj) != license_key:
                raise ValueError("Invalid UUID format")
                
        except ValueError:
            QMessageBox.warning(self, "Invalid License", 
                "Please enter a valid license key in the format:\n"
                "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX")
            return
            
        # API validation
        try:
            response = requests.post(
                f"{GLOBAL.API_BASE_URL}{GLOBAL.LICENSE_VALIDATE_ENDPOINT}",
                json={
                    "key": license_key,
                    "client_info": "string"
                },
                timeout=5
            )
            
            if response.status_code == 200:
                is_valid = response.json().get("is_valid", False)
                if is_valid:
                    GLOBAL.LICENSE.save_license_key(license_key)
                    self.license_validated.emit(True)
                    self.accept()
                    return
                else:
                    QMessageBox.warning(self, "Invalid License", 
                        "This license key is not valid or has expired")
            else:
                QMessageBox.critical(self, "Validation Error", 
                    f"License server error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Connection Error",
                f"Could not connect to license server: {str(e)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"An unexpected error occurred: {str(e)}") 