from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QLabel, QFrame, QVBoxLayout, QHBoxLayout)
from PyQt6.QtGui import QFont

class MessageBubble(QFrame):
    """Widget representing a single chat message bubble"""
    
    def __init__(self, message, is_user=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setObjectName("user_bubble" if is_user else "ai_bubble")
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(0)
        
        sender = QLabel("You" if is_user else "AI")
        sender.setObjectName("sender_label")
        sender.setFont(QFont("Arial", 8))
        layout.addWidget(sender)
        
        message_label = QLabel(message)
        message_label.setObjectName("message_content")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(message_label)
        
        self.setProperty("align", "right" if is_user else "left")
        self.setMaximumWidth(500)


class LoadingBubble(MessageBubble):
    """Special message bubble showing loading animation"""
    
    def __init__(self, parent=None):
        super().__init__("", False, parent)
        
        for i in reversed(range(self.layout().count())): 
            self.layout().itemAt(i).widget().setParent(None)
        
        loading_layout = QHBoxLayout()
        loading_layout.setContentsMargins(15, 10, 15, 10)
        loading_layout.setSpacing(4)
        self.dots = []
        
        for i in range(3):
            dot = QLabel("•")
            dot.setObjectName("loading_dot")
            font = QFont("Segoe UI", 16)
            font.setBold(True)
            dot.setFont(font)
            self.dots.append(dot)
            loading_layout.addWidget(dot)
        
        self.layout().addLayout(loading_layout)
        
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animate_dots)
        self.animation_timer.start(300)
        self.animation_step = 0
    
    def _animate_dots(self):
        for i, dot in enumerate(self.dots):
            if i == self.animation_step % 3:
                dot.setStyleSheet("color: #5D94FB; margin-top: 0px;") 
            else:
                dot.setStyleSheet(f"color: #AAAAAA; margin-top: {5 if i == (self.animation_step + 1) % 3 else 2}px;")
        self.animation_step += 1 