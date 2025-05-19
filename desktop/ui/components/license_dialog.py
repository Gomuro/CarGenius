from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                           QPushButton, QHBoxLayout, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from desktop.GLOBAL import GLOBAL

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
        self.license_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        input_layout.addWidget(self.license_input)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(15)
        
        # Add spacer to push buttons to the right
        button_layout.addStretch()
        
        # Trial button
        self.trial_button = QPushButton("Continue with Trial")
        self.trial_button.setObjectName("secondary_button")
        button_layout.addWidget(self.trial_button)
        
        # Activate button
        self.activate_button = QPushButton("Activate License")
        self.activate_button.setObjectName("primary_button")
        button_layout.addWidget(self.activate_button)
        
        # Add buttons to input layout
        input_layout.addLayout(button_layout)
        
        # Add input frame to main layout
        main_layout.addWidget(input_frame)
        
        # Note at the bottom
        note = QLabel("Don't have a license key? Purchase at <a href='https://cargenius.com/purchase'>cargenius.com</a>")
        note.setObjectName("note_text")
        note.setOpenExternalLinks(True)
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(note)
        
    def _connect_signals(self):
        self.activate_button.clicked.connect(self._validate_license)
        self.trial_button.clicked.connect(self._continue_trial)
        
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
            QMessageBox.warning(self, "Invalid License", "Please enter a valid license key.")
            return
            
        # In a real app, this would validate with a server
        # For now, accept any non-empty key
        GLOBAL.LICENSE.save_license_key(license_key)
        self.license_validated.emit(True)
        self.accept()
        
    def _continue_trial(self):
        # User chooses to continue without a license
        self.license_validated.emit(False)
        self.accept() 