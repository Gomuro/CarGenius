from PyQt6.QtCore import Qt, QSize, QTimer, QEvent, QRunnable, QThreadPool, pyqtSignal, QObject
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QLabel, QFrame, QScrollArea, 
                           QSizePolicy, QSpacerItem, QSplitter)
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QKeyEvent

from .ai_chat_components.message_bubbles import MessageBubble, LoadingBubble
from .ai_chat_components.chat_input_area import ChatInputArea
from .ai_chat_components.context_display_widget import ContextDisplayWidget
from .ai_chat_components.add_context_dialog import AddContextDialog
from desktop.services.main_api_service import APIService
from desktop.GLOBAL import GLOBAL

# Worker for running API calls in a separate thread
class GptWorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

class GptWorker(QRunnable):
    def __init__(self, api_service, user_id, prompt, context=None):
        super().__init__()
        self.api_service = api_service
        self.user_id = user_id
        self.prompt = prompt
        self.signals = GptWorkerSignals()
        self.context = context

    def run(self):
        try:
            if not self.user_id:
                raise ValueError("User ID is not set. Please ensure you have a valid license.")
            response = self.api_service.ask_gpt_sync(self.user_id, self.prompt, self.context)
            self.signals.finished.emit(response)
        except Exception as e:
            self.signals.error.emit(str(e))


class AIChatWindow(QWidget):
    """Main AI chat interface window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CarGenius AI Chat")
        self.resize(800, 600)
        self.setMinimumSize(400, 300)
        
        self.api_service = APIService()
        self.user_id = GLOBAL.LICENSE.get_license_key()
        self.threadpool = QThreadPool()
        self.chat_context = {}
        
        self._create_ui()
        
    def _create_ui(self):
        self.setObjectName("ai_chat_window")
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("chat_splitter")
        main_layout.addWidget(splitter)
        
        chat_widget = QWidget()
        chat_widget.setObjectName("chat_main_widget")
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(25, 25, 25, 25)
        chat_layout.setSpacing(20)
        splitter.addWidget(chat_widget)
        
        # Enhanced header with premium styling
        header_frame = QFrame()
        header_frame.setObjectName("chat_header_frame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        chat_header = QLabel("🤖 CarGenius AI Assistant")
        chat_header.setObjectName("chat_header")
        chat_header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header_layout.addWidget(chat_header)
        
        status_label = QLabel("● Online")
        status_label.setObjectName("chat_status")
        header_layout.addStretch()
        header_layout.addWidget(status_label)
        
        chat_layout.addWidget(header_frame)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("chat_scroll_area")
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
        
        self.add_message("🚗 Welcome to CarGenius AI Assistant! I'm here to help you find the perfect car. What can I assist you with today?", False)
        
        # Use the new premium ChatInputArea component
        self.chat_input_area = ChatInputArea()
        self.chat_input_area.send_button.clicked.connect(self.send_message)
        self.chat_input_area.add_context_button.clicked.connect(self.open_add_context_dialog)
        # Install event filter on the QTextEdit within ChatInputArea
        self.chat_input_area.input_text.installEventFilter(self)
        # Connect text change to update send button state
        self.chat_input_area.input_text.textChanged.connect(self._update_send_button_state)

        # Context display widget
        self.context_display = ContextDisplayWidget()
        self.context_display.clear_context_signal.connect(self.clear_context)
        chat_layout.addWidget(self.context_display)
        
        chat_layout.addWidget(self.chat_input_area)
        
        # Initialize send button state
        self._update_send_button_state()
        
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
        
        # Pass context to the worker and then clear it
        worker = GptWorker(self.api_service, self.user_id, message, self.chat_context)
        self.chat_context = {}  # Clear context after sending

        worker.signals.finished.connect(lambda response: self.receive_ai_response(loading_bubble, response))
        worker.signals.error.connect(lambda error: self.handle_ai_error(loading_bubble, error))
        self.threadpool.start(worker)
        
    def add_message(self, text, is_user=False):
        bubble = MessageBubble(text, is_user)

        # Create a container widget and layout to hold the bubble and spacer
        container_widget = QWidget()
        container_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        container_layout = QHBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        if is_user:
            # Add a spacer to push the bubble to the right
            container_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
            container_layout.addWidget(bubble)
        else:
            # Add the bubble to the left and a spacer to the right
            container_layout.addWidget(bubble)
            container_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))

        self.messages_layout.addWidget(container_widget)
            
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def add_loading(self):
        loading = LoadingBubble()

        container_widget = QWidget()
        container_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        container_layout = QHBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        container_layout.addWidget(loading)
        container_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))

        self.messages_layout.addWidget(container_widget)

        QTimer.singleShot(100, self.scroll_to_bottom)
        return loading
        
    def receive_ai_response(self, loading_bubble, response):
        if loading_bubble.parent() is not None:
            container = loading_bubble.parentWidget()
            container.setParent(None)
            container.deleteLater()
        
        if response and response.get("gpt_response"):
            ai_message = response["gpt_response"]
            self.add_message(ai_message, False)
        else:
            error_message = "Sorry, I couldn't get a valid response from the server."
            if response and "detail" in response:
                error_message += f"\nDetails: {response['detail']}"
            self.add_message(error_message, False)
        
    def handle_ai_error(self, loading_bubble, error_message):
        if loading_bubble.parent() is not None:
            container = loading_bubble.parentWidget()
            container.setParent(None)
            container.deleteLater()
        
        print(f"[AIChatWindow] Error from GPT API: {error_message}")
        self.add_message(f"An error occurred: {error_message}", False)
        
    def scroll_to_bottom(self):
        if hasattr(self, 'scroll_area') and self.scroll_area:
            scrollbar = self.scroll_area.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())
        
    def clear_context(self):
        """Clears the chat context and updates the UI."""
        self.chat_context = {}
        self.context_display.update_context(self.chat_context)
        print("Context cleared")
        
    def _update_send_button_state(self):
        """Update send button state based on input text"""
        if hasattr(self, 'chat_input_area'):
            has_text = bool(self.chat_input_area.get_text())
            self.chat_input_area.set_send_enabled(has_text)
        
    def open_add_context_dialog(self):
        dialog = AddContextDialog(self)
        dialog.add_car_context_signal.connect(self._on_context_car_selected)
        dialog.add_filters_context_signal.connect(self.add_filters_context)
        dialog.exec()

    def _on_context_car_selected(self, car_data: dict):
        """Handle car selection from the context dialog."""
        self.set_context('car', car_data)

    def set_context(self, context_type: str, data: dict):
        """
        Sets a specific type of context for the chat.
        This method updates the chat_context dictionary and refreshes the context display.
        """
        self.chat_context[context_type] = data
        self.context_display.update_context(self.chat_context)
        print(f"Context added: {context_type}")

    def add_car_context(self):
        # This method is now obsolete and will be replaced in Phase 3
        # Placeholder for Phase 3 - will be replaced with real data fetching
        self.set_context('car', {"id": "123", "name": "Audi A4"})

    def add_filters_context(self):
        # Placeholder for Phase 3 - will be replaced with real filter data
        self.set_context('filters', {"brand": "Audi", "price_max": 20000})
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'messages_widget') and self.messages_widget:
            self.scroll_to_bottom() 