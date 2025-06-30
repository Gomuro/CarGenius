from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QCheckBox
from PyQt6.QtCore import Qt

class FilterOptions(QWidget):
    def __init__(self, show_tracking_option: bool = True, parent=None):
        super().__init__(parent)
        self._create_ui(show_tracking_option)

    def _create_ui(self, show_tracking_option: bool):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 5, 0, 0)

        if show_tracking_option:
            self.tracking_mode_checkbox = QCheckBox("Track Specific Models")
            self.tracking_mode_checkbox.setObjectName("filter_checkbox_light")
            self.tracking_mode_checkbox.setFixedHeight(32)
            layout.addWidget(self.tracking_mode_checkbox)
        
        self.analyze_button = QPushButton("⚡️ Analyze for Best Offer")
        self.analyze_button.setObjectName("dark_text_button")
        self.analyze_button.setFixedHeight(32)
        layout.addWidget(self.analyze_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("dark_text_button")
        self.reset_button.setFixedHeight(32)
        layout.addWidget(self.reset_button)
        
        layout.addStretch()

    # Add methods to connect signals if needed.
    # The main panel will connect to these widgets' signals. 