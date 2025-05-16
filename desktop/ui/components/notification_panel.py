from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from . import BaseComponent

class NotificationPanel(BaseComponent):
    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        self.setObjectName("notification_panel")
        
        # Header with title and settings
        header_layout = QHBoxLayout()
        title = QLabel("Notifications")
        title.setObjectName("section_title")
        header_layout.addWidget(title)
        
        settings_button = QPushButton("Settings")
        settings_button.setObjectName("small_button")
        header_layout.addWidget(settings_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        main_layout.addLayout(header_layout)
        
        # Notification area
        notification_frame = QFrame()
        notification_frame.setObjectName("notification_frame")
        notification_layout = QVBoxLayout(notification_frame)
        
        self.notification_area = QLabel("New matches will appear here")
        self.notification_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        notification_layout.addWidget(self.notification_area)
        
        main_layout.addWidget(notification_frame) 