from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QLabel, QFrame)
from PyQt6.QtGui import QIcon, QFont
import os

class ChatInputArea(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("premium_input_frame")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._create_ui()

    def _create_ui(self):
        # Main container layout should be vertical
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Input row with enhanced design
        input_container = QFrame()
        input_container.setObjectName("input_container")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(4, 4, 4, 4)
        input_layout.setSpacing(12)
        
        # Add context button
        self.add_context_button = QPushButton("+")
        self.add_context_button.setObjectName("add_context_button")
        self.add_context_button.setFixedSize(48, 48) # Adjusted size
        self.add_context_button.setFont(QFont("Segoe UI", 16))
        input_layout.addWidget(self.add_context_button)

        # Enhanced text input
        self.input_text = QTextEdit()
        self.input_text.setObjectName("premium_input_text")
        self.input_text.setPlaceholderText("💬 Type your message here...") 
        self.input_text.setAcceptRichText(False)
        self.input_text.setMinimumHeight(48)
        self.input_text.setMaximumHeight(120)
        self.input_text.setFont(QFont("Segoe UI", 14))
        self.input_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        input_layout.addWidget(self.input_text)

        # Premium send button with SVG icon
        self.send_button = QPushButton()
        self.send_button.setObjectName("premium_send_button")
        
        # Set up the icon with proper path handling
        icon_path = os.path.join(os.path.dirname(__file__), "../../assets/send_icon.svg")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            # Fallback path if the above doesn't work
            icon = QIcon("desktop/ui/assets/send_icon.svg")
        
        self.send_button.setIcon(icon)
        self.send_button.setIconSize(QSize(20, 20))
        self.send_button.setFixedSize(56, 56)  # Perfect circle button
        self.send_button.setToolTip("Send message (Enter)")
        input_layout.addWidget(self.send_button)

        main_layout.addWidget(input_container)

        # Enhanced hint section
        hint_container = QHBoxLayout()
        hint_container.setContentsMargins(16, 0, 16, 4)
        
        # Character counter (optional)
        # self.char_counter = QLabel("0")
        # self.char_counter.setObjectName("char_counter")
        # hint_container.addWidget(self.char_counter)
        
        hint_container.addStretch()
        
        # Hint label with better styling
        hint_label = QLabel("✨ Press Enter to send • Shift+Enter for new line")
        hint_label.setObjectName("premium_hint_label")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        hint_container.addWidget(hint_label)

        main_layout.addLayout(hint_container)
        
        # Connect character counter
        # self.input_text.textChanged.connect(self._update_char_counter)

    # def _update_char_counter(self):
    #     """Update character counter"""
    #     text_length = len(self.input_text.toPlainText())
    #     self.char_counter.setText(f"{text_length}")
        
    #     # Change color based on length
    #     if text_length > 500:
    #         self.char_counter.setObjectName("char_counter_warning")
    #     elif text_length > 300:
    #         self.char_counter.setObjectName("char_counter_caution")
    #     else:
    #         self.char_counter.setObjectName("char_counter")
        
    #     # Refresh style
    #     self.char_counter.style().unpolish(self.char_counter)
    #     self.char_counter.style().polish(self.char_counter)

    def get_text(self):
        return self.input_text.toPlainText().strip()

    def clear_text(self):
        self.input_text.clear()
        # self._update_char_counter()

    def set_send_enabled(self, enabled):
        """Enable/disable send button with visual feedback"""
        self.send_button.setEnabled(enabled)
        if enabled:
            self.send_button.setObjectName("premium_send_button")
        else:
            self.send_button.setObjectName("premium_send_button_disabled")
        
        # Refresh style
        self.send_button.style().unpolish(self.send_button)
        self.send_button.style().polish(self.send_button)

    # The event filter for Enter key will be handled by the parent AIChatWindow
    # as it needs to call the send_message method of AIChatWindow. 