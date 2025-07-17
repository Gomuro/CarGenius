from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QLabel, QFrame, QVBoxLayout, QHBoxLayout, QSizePolicy, QTextEdit)
from PyQt6.QtGui import QFont, QTextOption
import markdown

class MessageBubble(QFrame):
    """Widget representing a single chat message bubble"""
    
    def __init__(self, message, is_user=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setObjectName("user_bubble" if is_user else "ai_bubble")
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        # Set proper size policies for the bubble
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        sender = QLabel("You" if is_user else "AI")
        sender.setObjectName("sender_label")
        sender.setFont(QFont("Arial", 8))
        sender.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(sender)
        
        # Use QLabel with RichText for simple, reliable text display without scrolling
        message_label = QLabel()
        message_label.setObjectName("message_content")
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)
        message_label.setOpenExternalLinks(True)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.LinksAccessibleByMouse)
        message_label.setFont(QFont("Segoe UI", 10))
        message_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        message_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        
        # Convert Markdown to HTML for better formatting
        html_message = markdown.markdown(message, extensions=["extra", "nl2br"])
        message_label.setText(html_message)
        
        # Ensure the label can grow to fit all content
        message_label.setMinimumHeight(20)  # Start with minimum height
        message_label.adjustSize()  # Let it size itself based on content
        
        layout.addWidget(message_label)
        
        self.setProperty("align", "right" if is_user else "left")
        self.setMaximumWidth(500)
        self.setMinimumWidth(100)  # Add minimum width to prevent over-compression
        
        # Ensure the bubble adjusts its height based on content
        self.adjustSize()


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