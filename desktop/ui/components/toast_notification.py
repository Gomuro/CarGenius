from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QFrame
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QTimer, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon, QColor, QPainter, QPainterPath, QPen
from datetime import datetime

# Keep track of active notifications for stacking
active_notifications = []
NOTIFICATION_GAP = 10  # Gap between stacked notifications

class ToastNotification(QFrame):
    def __init__(self, parent=None, title="", message="", avatar=None):
        super().__init__(parent)
        
        # Configure window flags to make it appear like a system notification
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Set window attributes to be transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Style setup
        self.setObjectName("notification_toast")
        self.setFixedWidth(350)
        self.setStyleSheet("""
            #notification_toast {
                background-color: rgba(255, 255, 255, 255);
                border-radius: 8px;
                padding: 12px;
            }
            #sender {
                font-weight: bold;
                color: #000000;
                font-size: 13px;
            }
            #message {
                color: #000000;
                font-size: 13px;
            }
            #timestamp {
                color: #666666;
                font-size: 12px;
            }
            #dismiss_button {
                background: transparent;
                border: none;
                color: #666666;
                font-size: 16px;
                padding: 0;
                font-weight: bold;
            }
            #dismiss_button:hover {
                color: #333333;
            }
        """)
        
        # Layout setup
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Avatar label with custom circular background
        avatar_label = QLabel()
        if avatar:
            pixmap = QPixmap(avatar)
        else:
            # Create a colored avatar
            size = 32
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw circular background
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            
            painter.fillRect(0, 0, size, size, QColor("#FF9F43"))  # Orange background
            
            # Draw text
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont('Arial', 15, QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "S")
            
            painter.end()
        
        # Make avatar circular
        pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        avatar_label.setPixmap(pixmap)
        avatar_label.setFixedSize(32, 32)
        main_layout.addWidget(avatar_label)
        
        # Content area
        content_layout = QVBoxLayout()
        main_layout.addLayout(content_layout)
        content_layout.setSpacing(2)
        
        # Header layout
        header_layout = QHBoxLayout()
        content_layout.addLayout(header_layout)
        
        # Sender name
        sender_label = QLabel(title)
        sender_label.setObjectName("sender")
        header_layout.addWidget(sender_label)
        
        # Time
        current_time = datetime.now().strftime("%H:%M")
        time_label = QLabel(current_time)
        time_label.setObjectName("timestamp")
        header_layout.addWidget(time_label)
        
        # Spacer to push dismiss button to the right
        header_layout.addStretch()
        
        # Dismiss button
        dismiss_button = QPushButton("×")
        dismiss_button.setObjectName("dismiss_button")
        dismiss_button.setCursor(Qt.CursorShape.PointingHandCursor)
        dismiss_button.clicked.connect(self.close_notification)
        header_layout.addWidget(dismiss_button)
        
        # Message text
        message_label = QLabel(message)
        message_label.setObjectName("message")
        message_label.setWordWrap(True)
        content_layout.addWidget(message_label)
        
        # Auto-dismiss timer
        QTimer.singleShot(5000, self.start_close_animation)
        
    def paintEvent(self, event):
        # Custom paint to add shadow and border
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create shadow
        shadow_color = QColor(0, 0, 0, 40)
        shadow_offset = 3
        for i in range(10):
            path = QPainterPath()
            path.addRoundedRect(shadow_offset - i/2, shadow_offset - i/2, 
                               self.width() - shadow_offset*2 + i, 
                               self.height() - shadow_offset*2 + i, 
                               8, 8)
            shadow_color.setAlpha(15 - i)
            painter.setPen(QPen(shadow_color, 1))
            painter.drawPath(path)
        
        # Draw notification background
        background_path = QPainterPath()
        background_path.addRoundedRect(0, 0, self.width(), self.height(), 8, 8)
        painter.fillPath(background_path, QColor(255, 255, 255, 255))
        
        # Draw border
        painter.setPen(QPen(QColor(220, 220, 220, 255), 1))
        painter.drawRoundedRect(0, 0, self.width()-1, self.height()-1, 8, 8)
        
    def show_notification(self):
        # Calculate position based on existing notifications
        screen_geometry = self.screen().geometry()
        self.adjustSize()
        
        # Add self to active notifications
        global active_notifications
        active_notifications.append(self)
        
        # Calculate Y position based on stack
        total_height = sum([n.height() + NOTIFICATION_GAP for n in active_notifications[:-1]])
        y_pos = screen_geometry.height() - self.height() - 20 - total_height
        
        # Set initial position (off-screen)
        self.move(
            screen_geometry.width() + 20, 
            y_pos
        )
        
        # Show the notification
        self.show()
        
        # Start entry animation
        self.entry_animation = QPropertyAnimation(self, b"pos")
        self.entry_animation.setDuration(200)
        end_pos = QPoint(
            screen_geometry.width() - self.width() - 20, 
            y_pos
        )
        self.entry_animation.setStartValue(self.pos())
        self.entry_animation.setEndValue(end_pos)
        self.entry_animation.start()
    
    def start_close_animation(self):
        # Exit animation
        screen_geometry = self.screen().geometry()
        self.exit_animation = QPropertyAnimation(self, b"pos")
        self.exit_animation.setDuration(200)
        start_pos = self.pos()
        end_pos = QPoint(
            screen_geometry.width() + 20, 
            self.y()
        )
        self.exit_animation.setStartValue(start_pos)
        self.exit_animation.setEndValue(end_pos)
        self.exit_animation.finished.connect(self.close_notification)
        self.exit_animation.start()
        
    def close_notification(self):
        # Remove from active notifications
        global active_notifications
        if self in active_notifications:
            idx = active_notifications.index(self)
            active_notifications.pop(idx)
            
            # Reposition remaining notifications
            self._reposition_notifications(idx)
        
        # Close the widget
        self.close()
        
    def _reposition_notifications(self, start_idx):
        """Reposition notifications after one is removed"""
        global active_notifications
        
        # No need to reposition if this was the last one
        if not active_notifications or start_idx >= len(active_notifications):
            return
            
        # Reposition each notification above the removed one
        screen_geometry = self.screen().geometry()
        for i in range(start_idx, len(active_notifications)):
            notification = active_notifications[i]
            
            # Calculate new position
            total_height = sum([n.height() + NOTIFICATION_GAP for n in active_notifications[:i]])
            new_y = screen_geometry.height() - notification.height() - 20 - total_height
            
            # Animate to new position
            anim = QPropertyAnimation(notification, b"pos")
            anim.setDuration(200)
            anim.setEndValue(QPoint(notification.x(), new_y))
            anim.start()
        
    def mousePressEvent(self, event):
        # Make the notification clickable
        if event.button() == Qt.MouseButton.LeftButton:
            self.close_notification()
        super().mousePressEvent(event) 