from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QLabel, QFrame)
from PyQt6.QtGui import QIcon

class ChatInputArea(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("input_frame")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.input_text = QTextEdit()
        self.input_text.setObjectName("input_text")
        self.input_text.setPlaceholderText("Type your message...") # Removed (Press Enter to send) as it's now a hint label
        self.input_text.setAcceptRichText(False)
        self.input_text.setMinimumHeight(40)
        self.input_text.setMaximumHeight(100)
        input_row.addWidget(self.input_text)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("send_button")
        # Icon path will need to be correct relative to the main application execution or use a resource system
        self.send_button.setIcon(QIcon("desktop/ui/assets/send_icon.svg")) 
        self.send_button.setMinimumWidth(80)
        input_row.addWidget(self.send_button)

        layout.addLayout(input_row)

        hint_label = QLabel("Press Enter to send")
        hint_label.setObjectName("hint_label")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(hint_label)

    def get_text(self):
        return self.input_text.toPlainText().strip()

    def clear_text(self):
        self.input_text.clear()

    # The event filter for Enter key will be handled by the parent AIChatWindow
    # as it needs to call the send_message method of AIChatWindow. 