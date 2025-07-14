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

        # Add an icon for better visual distinction
        self.icon_label = QLabel("ℹ️")
        self.icon_label.setFont(QFont("Segoe UI Emoji", 11))
        
        self.context_label = QLabel()
        self.context_label.setFont(QFont("Segoe UI", 9, italic=True))
        
        self.clear_button = QPushButton("✕")
        self.clear_button.setObjectName("clear_context_button")
        self.clear_button.setFixedSize(20, 20)
        self.clear_button.clicked.connect(self.clear_context_signal.emit)
        
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.context_label)
        self.layout.addStretch()
        self.layout.addWidget(self.clear_button)
        
        self.setVisible(False)

    def update_context(self, context: dict):
        """Updates the display based on the provided context with more detail."""
        if not context:
            self.setVisible(False)
            return
            
        display_parts = []
        
        # Handle car context
        if 'car' in context and isinstance(context.get('car'), dict):
            car_info = context['car']
            
            # Try to get brand and model from _api_data first (most reliable)
            api_data = car_info.get('_api_data', {})
            brand = api_data.get('brand', '')
            model = api_data.get('model', '')
            
            # If not found in _api_data, try direct fields
            if not brand or not model:
                brand = brand or car_info.get('brand', '')
                model = model or car_info.get('model', '')
            
            # If still not found, use the title as fallback
            if not brand and not model:
                title = car_info.get('title', '')
                if title:
                    display_parts.append(f"Car: {title}")
            else:
                display_parts.append(f"Car: {brand} {model}".strip())
        
        # Handle filters context
        if 'filters' in context and isinstance(context.get('filters'), dict):
            summary = self._summarize_filter_for_display(context['filters'])
            if summary:
                display_parts.append(f"Filters: {summary}")

        if not display_parts:
            self.setVisible(False)
            return
            
        display_text = "Context: " + " | ".join(display_parts)
        self.context_label.setText(display_text)
        self.setVisible(True) 

    def _summarize_filter_for_display(self, filter_data: dict) -> str:
        """Creates a readable summary of a filter dictionary for the context display."""
        parts = []
        
        brand = filter_data.get('brand')
        if brand and brand != 'Any Brand':
            parts.append(brand)
            
        model = filter_data.get('model')
        if model and model != 'Any Model':
            parts.append(model)
            
        price = filter_data.get('price_to')
        if price:
            try:
                parts.append(f"up to €{int(price):,}")
            except (ValueError, TypeError):
                pass 
        
        return ", ".join(parts) 