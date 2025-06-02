from PyQt6.QtCore import Qt, QSize, QTimer, QEvent
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QLabel, QFrame, QScrollArea, 
                           QSizePolicy, QSpacerItem, QSplitter)
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QKeyEvent

from .ai_chat_components.message_bubbles import MessageBubble, LoadingBubble
from .ai_chat_components.chat_input_area import ChatInputArea
import random # For generating random AI responses


class AIChatWindow(QWidget):
    """Main AI chat interface window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CarGenius AI Chat")
        self.resize(800, 600)
        self.setMinimumSize(400, 300)
        
        self._create_ui()
        
    def _create_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(15, 15, 15, 15)
        splitter.addWidget(chat_widget)
        
        header_layout = QHBoxLayout()
        chat_header = QLabel("AI Chat Assistant")
        chat_header.setObjectName("chat_header")
        chat_header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(chat_header)
        header_layout.addStretch()
        chat_layout.addLayout(header_layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        chat_layout.addWidget(self.scroll_area)
        
        self.messages_widget = QWidget()
        self.messages_widget.setObjectName("messages_container")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setContentsMargins(0, 10, 0, 10)
        self.scroll_area.setWidget(self.messages_widget)
        
        self.add_message("Welcome to CarGenius AI Assistant. How can I help you today?", False)
        
        # Use the new ChatInputArea component
        self.chat_input_area = ChatInputArea()
        self.chat_input_area.send_button.clicked.connect(self.send_message)
        # Install event filter on the QTextEdit within ChatInputArea
        self.chat_input_area.input_text.installEventFilter(self) 
        chat_layout.addWidget(self.chat_input_area)
        
        splitter.setSizes([int(self.width() * 0.8), int(self.width() * 0.2)])
        
    def eventFilter(self, obj, event):
        if obj == self.chat_input_area.input_text and event.type() == QEvent.Type.KeyPress:
            if isinstance(event, QKeyEvent):
                if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)
        
    def send_message(self):
        message = self.chat_input_area.get_text()
        if not message:
            return
            
        self.add_message(message, True)
        self.chat_input_area.clear_text()
        
        loading_bubble = self.add_loading()
        
        QTimer.singleShot(1500, lambda: self.receive_ai_response(loading_bubble))
        
    def add_message(self, text, is_user=False):
        bubble = MessageBubble(text, is_user)
        self.messages_layout.addWidget(bubble)
        
        if is_user:
            self.messages_layout.setAlignment(bubble, Qt.AlignmentFlag.AlignRight)
        else:
            self.messages_layout.setAlignment(bubble, Qt.AlignmentFlag.AlignLeft)
            
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def add_loading(self):
        loading = LoadingBubble()
        self.messages_layout.addWidget(loading)
        self.messages_layout.setAlignment(loading, Qt.AlignmentFlag.AlignLeft)
        QTimer.singleShot(100, self.scroll_to_bottom)
        return loading
        
    def receive_ai_response(self, loading_bubble):
        if loading_bubble.parent() is not None: # Check if bubble hasn't been removed elsewhere
            loading_bubble.setParent(None)
            loading_bubble.deleteLater() # Ensure it's properly deleted
        
        responses = [
            "I can help you with that. Let me find some information for you.",
            "Based on your interest, I'd recommend looking at the latest sedan models with hybrid options.",
            "Great question! The average lifespan of modern car batteries is typically 3-5 years, depending on usage and climate conditions.",
            "I found several SUV options that match your criteria. Would you like me to compare their features?"
        ]
        
        response = random.choice(responses)
        self.add_message(response, False)
        
    def scroll_to_bottom(self):
        if hasattr(self, 'scroll_area') and self.scroll_area:
            scrollbar = self.scroll_area.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'messages_widget') and self.messages_widget:
            self.scroll_to_bottom() 