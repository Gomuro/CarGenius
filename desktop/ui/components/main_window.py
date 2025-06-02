from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QSize
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLineEdit, QLabel, QFrame, QComboBox, 
                           QSizePolicy, QScrollArea, QToolTip)
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QPainterPath, QColor, QCursor
from .toast_notification import ToastNotification
from .analytics_dialog import AnalyticsDialog

class MainWindow(QMainWindow):
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CarGenius")
        self.current_theme = "dark"  # Set dark theme as the only theme
        self.tracked_models_criteria = [] # Initialize list for tracked models
        
        # Set minimum window size for usability
        self.setMinimumSize(800, 600)
        
        # Default size that maintains good proportions
        self.resize(1000, 750)
        
        # Initialize AI chat window reference
        self.ai_chat_window = None
        
        self._create_ui()
        self._load_styles(self.current_theme)
        self._add_floating_chat_button()

    def _create_ui(self):
        # Create scroll area as central widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setCentralWidget(scroll_area)
        
        # Content widget that holds all app components
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        
        # Main layout for all components
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header section
        header_frame = QFrame()
        header_frame.setObjectName("header_frame")
        header_layout = QVBoxLayout(header_frame)
        
        # App title
        title_layout = QHBoxLayout()
        app_title = QLabel("CarGenius")
        app_title.setObjectName("app_title")
        app_title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_layout.addWidget(app_title)
        
        # Add test notification button
        self.test_notification_btn = QPushButton("Test Toast")
        self.test_notification_btn.setObjectName("small_button")
        self.test_notification_btn.clicked.connect(self.show_test_notification)
        title_layout.addWidget(self.test_notification_btn)
        
        # Add multiple notifications test button
        self.multi_notification_btn = QPushButton("Test Multiple")
        self.multi_notification_btn.setObjectName("small_button")
        self.multi_notification_btn.clicked.connect(self.show_multiple_notifications)
        title_layout.addWidget(self.multi_notification_btn)
        
        # Add Analytics Dialog button
        self.analytics_btn = QPushButton("Open Analytics")
        self.analytics_btn.setObjectName("small_button")
        self.analytics_btn.clicked.connect(self._open_analytics_dialog)
        title_layout.addWidget(self.analytics_btn)
        
        # Add spacer to push title to the left
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        
        # Add header to main layout
        main_layout.addWidget(header_frame)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("separator")
        main_layout.addWidget(separator)
        
        # Notification panel with natural height
        from .notification_panel import NotificationPanel
        self.notification_panel = NotificationPanel()
        self.notification_panel.setObjectName("notification_panel")
        self.notification_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        main_layout.addWidget(self.notification_panel)

        # Filter panel with natural height
        from .filter_panel import FilterPanel
        self.filter_panel = FilterPanel()
        self.filter_panel.setObjectName("filter_panel")
        self.filter_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        # Connect to the filter panel's signal for model tracking
        self.filter_panel.model_tracking_requested.connect(self._handle_model_tracking_request)
        main_layout.addWidget(self.filter_panel)

        # Results table with flexible sizing
        from .result_table import ResultTable
        self.result_table = ResultTable()
        self.result_table.setObjectName("result_table")
        # Remove minimum height requirement so it takes its natural size
        self.result_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        main_layout.addWidget(self.result_table)

    def _add_floating_chat_button(self):
        """Add a floating action button for opening the AI chat"""
        self.chat_fab = QPushButton(self)
        self.chat_fab.setObjectName("chat_fab")
        self.chat_fab.setCheckable(True)  # Make the button checkable for toggle state
        
        # Set size and make it round
        self.chat_fab.setFixedSize(56, 56)
        self.chat_fab.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Add stars icon
        stars_icon = QIcon("ui/assets/chat/chat-icon.svg")
        self.chat_fab.setIcon(stars_icon)
        self.chat_fab.setIconSize(QSize(28, 28))
        
        # Connect click event
        self.chat_fab.clicked.connect(self.toggle_ai_chat)
        
        # Add tooltip
        self.chat_fab.setToolTip("Open AI Chat")
        
        # Position in bottom-right corner (will be updated on resize)
        self._update_fab_position()

    def _update_fab_position(self):
        """Update the floating button position"""
        margin = 20
        self.chat_fab.move(
            self.width() - self.chat_fab.width() - margin,
            self.height() - self.chat_fab.height() - margin
        )

    def toggle_ai_chat(self):
        """Toggle the AI chat window open/closed state"""
        if self.ai_chat_window and self.ai_chat_window.isVisible():
            # Close window if it exists and is visible
            self.ai_chat_window.close()
            self.chat_fab.setChecked(False)
            self.chat_fab.setToolTip("Open AI Chat")
            self.chat_fab.setObjectName("chat_fab")
        else:
            # Open window
            self.open_ai_chat()
            self.chat_fab.setChecked(True)
            self.chat_fab.setToolTip("Close AI Chat")
            self.chat_fab.setObjectName("chat_fab_active")
        
        # Update styles
        self.chat_fab.style().unpolish(self.chat_fab)
        self.chat_fab.style().polish(self.chat_fab)

    def open_ai_chat(self):
        """Open the AI chat window"""
        # Import here to avoid circular imports
        from .ai_chat_window import AIChatWindow
        
        # Create a new window if it doesn't exist
        if not self.ai_chat_window:
            self.ai_chat_window = AIChatWindow()
            # Connect close event to update button state
            self.ai_chat_window.closeEvent = self.handle_chat_close
        
        # Show the window
        self.ai_chat_window.show()
        self.ai_chat_window.activateWindow()
    
    def _handle_model_tracking_request(self, criteria):
        """Handles the request to track a new model based on criteria."""
        # Basic check for duplicates to avoid adding the exact same criteria multiple times
        if criteria not in self.tracked_models_criteria:
            self.tracked_models_criteria.append(criteria)
            print(f"[MainWindow] Added to tracked models: {criteria}")
            print(f"[MainWindow] Current tracked list: {self.tracked_models_criteria}")
            # Optionally, provide feedback to the user (e.g., a toast notification)
            # self.show_toast_notification("Model Added", f"'{criteria.get('brand','')} {criteria.get('model','')}' added to tracking.")
        else:
            print(f"[MainWindow] Model criteria {criteria} already tracked.")

    def _open_analytics_dialog(self):
        """Opens the Car Analytics dialog."""
        # Pass the list of tracked models and self as parent
        dialog = AnalyticsDialog(self.tracked_models_criteria, parent=self) 
        dialog.exec() # Show as a modal dialog
    
    def handle_chat_close(self, event):
        """Handle the chat window close event to update button state"""
        self.chat_fab.setChecked(False)
        self.chat_fab.setToolTip("Open AI Chat")
        self.chat_fab.setObjectName("chat_fab")
        self.chat_fab.style().unpolish(self.chat_fab)
        self.chat_fab.style().polish(self.chat_fab)
        event.accept()  # Allow the window to close

    def show_test_notification(self):
        # Create and show a toast notification
        toast = ToastNotification(
            title="New Match",
            message="BMW X5 2021 matches your search criteria"
        )
        toast.show_notification()
    
    def show_multiple_notifications(self):
        # Show 3 notifications with different car matches
        messages = [
            {
                "title": "New Match",
                "message": "Mercedes-Benz CLA 200 d Shooting Brake - 35.980 €",
                "avatar": None
            },
            {
                "title": "Price Drop",
                "message": "BMW 3 Series 320d - Price reduced by 2.500 €",
                "avatar": None
            },
            {
                "title": "New Match",
                "message": "Audi A4 Avant 2.0 TDI - Just arrived in your area",
                "avatar": None
            }
        ]
        
        # Custom avatar colors for each notification
        avatar_colors = ["#4CAF50", "#2196F3", "#FF9800"]
        
        # Show notifications with a small delay between them
        for i, msg in enumerate(messages):
            QTimer.singleShot(i * 500, lambda m=msg, i=i: self._show_delayed_notification(
                m["title"], 
                m["message"], 
                avatar_colors[i]
            ))
    
    def _show_delayed_notification(self, title, message, avatar_color=None):
        toast = ToastNotification(title=title, message=message)
        
        # Customize avatar if color provided
        if avatar_color:
            # Access the avatar label and update it with custom color
            for child in toast.children():
                if isinstance(child, QLabel) and child.width() == 32 and child.height() == 32:
                    size = 32
                    pixmap = QPixmap(size, size)
                    pixmap.fill(Qt.GlobalColor.transparent)
                    
                    painter = QPainter(pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    
                    # Draw circular background
                    path = QPainterPath()
                    path.addEllipse(0, 0, size, size)
                    painter.setClipPath(path)
                    
                    painter.fillRect(0, 0, size, size, QColor(avatar_color))
                    
                    # Draw initial
                    painter.setPen(Qt.GlobalColor.white)
                    painter.setFont(QFont('Arial', 15, QFont.Weight.Bold))
                    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, title[0])
                    
                    painter.end()
                    
                    child.setPixmap(pixmap)
                    break
        
        toast.show_notification()

    def _load_styles(self, theme):
        style_file = f"ui/themes/{theme}.qss"
        try:
            with open(style_file, 'r') as f:
                self.setStyleSheet(f.read())
            self.theme_changed.emit(theme)
        except FileNotFoundError:
            print(f"Style file {style_file} not found")
            
    def resizeEvent(self, event):
        # Update floating button position when window is resized
        self._update_fab_position()
        super().resizeEvent(event) 