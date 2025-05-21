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
        layout.addWidget(message_label)
        
        # Set alignment based on sender
        self.setProperty("align", "right" if is_user else "left")


class LoadingBubble(MessageBubble):
    """Special message bubble showing loading animation"""
    
    def __init__(self, parent=None):
        super().__init__("", False, parent)
        
        # Remove existing widgets
        for i in reversed(range(self.layout().count())): 
            self.layout().itemAt(i).widget().setParent(None)
        
        # Add loading indicator
        loading_layout = QHBoxLayout()
        self.dots = []
        
        for i in range(3):
            dot = QLabel("•")
            dot.setObjectName("loading_dot")
            font = QFont("Arial", 18)
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
                dot.setStyleSheet("color: #5D94FB;") 
            else:
                dot.setStyleSheet("color: #AAAAAA;")
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
        chat_header = QLabel("AI Chat Assistant")
        chat_header.setObjectName("chat_header")
        chat_header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        chat_layout.addWidget(chat_header)
        
        # Create scroll area for messages
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        chat_layout.addWidget(scroll_area)
        
        # Container for messages
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setContentsMargins(0, 0, 0, 10)
        scroll_area.setWidget(self.messages_widget)
        
        # Welcome message
        self.add_message("Welcome to CarGenius AI Assistant. How can I help you today?", False)
        
        # Input area
        input_frame = QFrame()
        input_frame.setObjectName("input_frame")
        input_frame.setFrameShape(QFrame.Shape.StyledPanel)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        # Text area for input
        self.input_text = QTextEdit()
        self.input_text.setObjectName("input_text")
        self.input_text.setPlaceholderText("Type your message... (Press Enter to send)")
        self.input_text.setAcceptRichText(False)
        self.input_text.setMaximumHeight(100)
        
        # Handle enter key to send message
        self.input_text.installEventFilter(self)
        
        input_layout.addWidget(self.input_text)
        
        # Send button row
        send_row = QHBoxLayout()
        hint_label = QLabel("Press Enter to send")
        hint_label.setObjectName("hint_label")
        send_row.addWidget(hint_label)
        send_row.addStretch()
        
        # Send button
        send_button = QPushButton("Send")
        send_button.setObjectName("send_button")
        send_button.clicked.connect(self.send_message)
        send_row.addWidget(send_button)
        input_layout.addLayout(send_row)
        
        chat_layout.addWidget(input_frame)
        
        # Context sidebar
        context_panel = QWidget()
        context_panel.setObjectName("context_panel")
        context_panel.setMinimumWidth(200)
        context_layout = QVBoxLayout(context_panel)
        
        # Context panel header
        context_header = QLabel("Context & History")
        context_header.setObjectName("panel_header")
        context_header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        context_layout.addWidget(context_header)
        
        # System prompts section
        prompts_label = QLabel("System Prompts")
        prompts_label.setObjectName("section_header")
        context_layout.addWidget(prompts_label)
        
        # Example system prompts
        prompt_buttons = [
            "Car Buying Advisor",
            "Service Helper",
            "General Car Info"
        ]
        
        for prompt in prompt_buttons:
            btn = QPushButton(prompt)
            btn.setObjectName("prompt_button")
            context_layout.addWidget(btn)
        
        # History section
        history_label = QLabel("Conversation History")
        history_label.setObjectName("section_header")
        context_layout.addWidget(history_label)
        
        # Add spacer at the bottom
        context_layout.addStretch()
        
        # Add context panel to splitter
        splitter.addWidget(context_panel)
        
        # Set initial splitter sizes (80% chat, 20% context)
        splitter.setSizes([int(self.width() * 0.8), int(self.width() * 0.2)])
        
        self.scroll_area = scroll_area
        
    def eventFilter(self, obj, event):
        """Handle Enter key press in text input"""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        
        if obj == self.input_text and event.type() == QEvent.Type.KeyPress:
            key_event = QKeyEvent(event)
            if key_event.key() == Qt.Key.Key_Return and not key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
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