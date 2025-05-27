from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QLabel, QFrame, QScrollArea, 
                           QSizePolicy, QSpacerItem, QSplitter)
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette


class MessageBubble(QFrame):
    """Widget representing a single chat message bubble"""
    
    def __init__(self, message, is_user=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setObjectName("user_bubble" if is_user else "ai_bubble")
        
        # Set frame properties
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(0)  # Reduce spacing between sender and message
        
        # Show who sent the message
        sender = QLabel("You" if is_user else "AI")
        sender.setObjectName("sender_label")
        sender.setFont(QFont("Arial", 8))
        layout.addWidget(sender)
        
        # Message content
        message_label = QLabel(message)
        message_label.setObjectName("message_content")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(message_label)
        
        # Set alignment based on sender
        self.setProperty("align", "right" if is_user else "left")
        
        # Set maximum width
        self.setMaximumWidth(500)


class LoadingBubble(MessageBubble):
    """Special message bubble showing loading animation"""
    
    def __init__(self, parent=None):
        super().__init__("", False, parent)
        
        # Remove existing widgets
        for i in reversed(range(self.layout().count())): 
            self.layout().itemAt(i).widget().setParent(None)
        
        # Add loading indicator
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
        
        # Start animation
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


class AIChatWindow(QWidget):
    """Main AI chat interface window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CarGenius AI Chat")
        self.resize(800, 600)
        self.setMinimumSize(400, 300)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Chat area (main content)
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(15, 15, 15, 15)
        splitter.addWidget(chat_widget)
        
        # Chat header with title
        header_layout = QHBoxLayout()
        chat_header = QLabel("AI Chat Assistant")
        chat_header.setObjectName("chat_header")
        chat_header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(chat_header)
        
        # Add spacer and optional button in header
        header_layout.addStretch()
        chat_layout.addLayout(header_layout)
        
        # Create scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        chat_layout.addWidget(self.scroll_area)
        
        # Container for messages
        self.messages_widget = QWidget()
        self.messages_widget.setObjectName("messages_container")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setContentsMargins(0, 10, 0, 10)
        self.scroll_area.setWidget(self.messages_widget)
        
        # Welcome message
        self.add_message("Welcome to CarGenius AI Assistant. How can I help you today?", False)
        
        # Input area
        input_frame = QFrame()
        input_frame.setObjectName("input_frame")
        input_frame.setFrameShape(QFrame.Shape.StyledPanel)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 12, 15, 12)
        
        # Create a horizontal layout for the input field and send button
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        
        # Text area for input
        self.input_text = QTextEdit()
        self.input_text.setObjectName("input_text")
        self.input_text.setPlaceholderText("Type your message... (Press Enter to send)")
        self.input_text.setAcceptRichText(False)
        self.input_text.setMinimumHeight(40)
        self.input_text.setMaximumHeight(100)
        
        # Handle enter key to send message
        self.input_text.installEventFilter(self)
        
        # Add input field to horizontal layout
        input_row.addWidget(self.input_text)
        
        # Send button with icon
        send_button = QPushButton("Send")
        send_button.setObjectName("send_button")
        send_button.setIcon(QIcon("desktop/ui/assets/send_icon.svg"))
        send_button.clicked.connect(self.send_message)
        send_button.setMinimumWidth(80)
        
        # Add send button to horizontal layout
        input_row.addWidget(send_button)
        
        # Add the input row to the main input layout
        input_layout.addLayout(input_row)
        
        # Add hint text below the input field
        hint_label = QLabel("Press Enter to send")
        hint_label.setObjectName("hint_label")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        input_layout.addWidget(hint_label)
        
        chat_layout.addWidget(input_frame)
        
        # Set initial splitter sizes (80% chat, 20% context)
        splitter.setSizes([int(self.width() * 0.8), int(self.width() * 0.2)])
        
    def eventFilter(self, obj, event):
        """Handle Enter key press in text input"""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        
        if obj == self.input_text and event.type() == QEvent.Type.KeyPress:
            # Check if the event is a QKeyEvent
            if isinstance(event, QKeyEvent):
                if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)
        
    def send_message(self):
        """Send user message and get AI response"""
        message = self.input_text.toPlainText().strip()
        if not message:
            return
            
        # Add user message
        self.add_message(message, True)
        
        # Clear input
        self.input_text.clear()
        
        # Show loading indicator
        loading_bubble = self.add_loading()
        
        # Simulate AI response after delay
        # In a real app, this would call an actual AI API
        QTimer.singleShot(1500, lambda: self.receive_ai_response(loading_bubble))
        
    def add_message(self, text, is_user=False):
        """Add a new message bubble to the chat"""
        bubble = MessageBubble(text, is_user)
        self.messages_layout.addWidget(bubble)
        
        # Align based on sender
        if is_user:
            self.messages_layout.setAlignment(bubble, Qt.AlignmentFlag.AlignRight)
        else:
            self.messages_layout.setAlignment(bubble, Qt.AlignmentFlag.AlignLeft)
            
        # Auto scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def add_loading(self):
        """Add a loading indicator bubble"""
        loading = LoadingBubble()
        self.messages_layout.addWidget(loading)
        self.messages_layout.setAlignment(loading, Qt.AlignmentFlag.AlignLeft)
        
        # Auto scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
        return loading
        
    def receive_ai_response(self, loading_bubble):
        """Replace loading bubble with AI response"""
        # Remove loading bubble
        loading_bubble.setParent(None)
        
        # Add AI response
        responses = [
            "I can help you with that. Let me find some information for you.",
            "Based on your interest, I'd recommend looking at the latest sedan models with hybrid options.",
            "Great question! The average lifespan of modern car batteries is typically 3-5 years, depending on usage and climate conditions.",
            "I found several SUV options that match your criteria. Would you like me to compare their features?"
        ]
        
        import random
        response = random.choice(responses)
        self.add_message(response, False)
        
    def scroll_to_bottom(self):
        """Scroll the message area to the bottom"""
        if hasattr(self, 'scroll_area') and self.scroll_area:
            scrollbar = self.scroll_area.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())
        
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        if hasattr(self, 'messages_widget') and self.messages_widget:
            self.scroll_to_bottom() 