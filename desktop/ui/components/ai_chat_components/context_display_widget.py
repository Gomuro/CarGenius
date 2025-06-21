from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtGui import QFont

class ContextDisplayWidget(QFrame):
    """A widget to display and clear the current AI chat context."""
    
    clear_context_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("context_display_widget")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(10)
        
        self.context_label = QLabel()
        self.context_label.setFont(QFont("Segoe UI", 9, italic=True))
        
        self.clear_button = QPushButton("✕")
        self.clear_button.setObjectName("clear_context_button")
        self.clear_button.setFixedSize(20, 20)
        self.clear_button.clicked.connect(self.clear_context_signal.emit)
        
        self.layout.addWidget(self.context_label)
        self.layout.addStretch()
        self.layout.addWidget(self.clear_button)
        
        self.setVisible(False)

    def update_context(self, context: dict):
        """Updates the display based on the provided context."""
        if not context:
            self.setVisible(False)
            return
            
        context_keys = [key.capitalize() for key in context.keys()]
        display_text = f"Context: {', '.join(context_keys)}"
        self.context_label.setText(display_text)
        self.setVisible(True) 