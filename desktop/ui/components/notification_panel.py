from PyQt6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QFrame, QWidget, QComboBox)
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QTimer
from PyQt6.QtGui import QIcon, QCursor
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
        
        # Notification container setup
        self.notification_container = QWidget()
        self.notification_container.setFixedWidth(350)
        self.notification_container.setLayout(QVBoxLayout())
        self.notification_container.layout().setAlignment(Qt.AlignmentFlag.AlignBottom)
        main_layout.addWidget(self.notification_container)

    def show_notification(self, sender, message):
        toast = QFrame()
        toast.setFixedWidth(350)
        toast.setObjectName("notification_toast")
        
        # Toast layout
        layout = QHBoxLayout(toast)
        avatar = QLabel("👤")  # Placeholder
        layout.addWidget(avatar)
        
        text_layout = QVBoxLayout()
        header = QHBoxLayout()
        header.addWidget(QLabel(f"<b>{sender}</b>"))
        header.addWidget(QLabel("10:30 AM", objectName="timestamp"))
        header.addStretch()
        
        # Dismiss button
        close_btn = QPushButton("×", objectName="dismiss_button")
        close_btn.clicked.connect(lambda: self._dismiss_toast(toast))
        header.addWidget(close_btn)
        
        text_layout.addLayout(header)
        text_layout.addWidget(QLabel(message))
        layout.addLayout(text_layout)
        
        # Animation setup
        self._animate_toast(toast)
        self.notification_container.layout().addWidget(toast)

    def _animate_toast(self, toast):
        toast.move(QPoint(400, 0))
        anim = QPropertyAnimation(toast, b"pos")
        anim.setEndValue(QPoint(0, 0))
        anim.setDuration(200)
        anim.start()
        
        # Auto-dismiss after 5 seconds
        QTimer.singleShot(5000, lambda: self._dismiss_toast(toast))

    def _dismiss_toast(self, toast):
        anim = QPropertyAnimation(toast, b"pos")
        anim.setEndValue(QPoint(400, 0))
        anim.setDuration(200)
        anim.finished.connect(toast.deleteLater)
        anim.start() 