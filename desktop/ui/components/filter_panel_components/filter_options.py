from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QCheckBox
from PyQt6.QtCore import Qt

class FilterOptions(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()

    def _create_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 5, 0, 0)

        self.additional_filters_button = QPushButton("Additional filters")
        self.additional_filters_button.setObjectName("dark_text_button")
        self.additional_filters_button.setFixedHeight(32)
        layout.addWidget(self.additional_filters_button)
        
        self.tracking_mode_checkbox = QCheckBox("Track Specific Models")
        self.tracking_mode_checkbox.setObjectName("filter_checkbox_light")
        self.tracking_mode_checkbox.setFixedHeight(32)
        layout.addWidget(self.tracking_mode_checkbox)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("dark_text_button")
        self.reset_button.setFixedHeight(32)
        layout.addWidget(self.reset_button)
        
        layout.addStretch()

    # Add methods to connect signals if needed.
    # The main panel will connect to these widgets' signals. 