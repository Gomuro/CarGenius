from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLineEdit, QLabel, QFrame, QComboBox, 
                           QSizePolicy, QScrollArea)
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QPainterPath, QColor
from .toast_notification import ToastNotification

class MainWindow(QMainWindow):
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CarGenius")
        self.current_theme = "dark"  # Set dark theme as the only theme
        
        # Set minimum window size for usability
        self.setMinimumSize(800, 600)
        
        # Default size that maintains good proportions
        self.resize(1000, 750)
        
        self._create_ui()
        self._load_styles(self.current_theme)

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
        
        # Add AI chat button
        self.ai_chat_btn = QPushButton("Open AI Chat")
        self.ai_chat_btn.setObjectName("small_button")
        self.ai_chat_btn.clicked.connect(self.open_ai_chat)
        title_layout.addWidget(self.ai_chat_btn)
        
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

        # Filter panel with natural height
        from .filter_panel import FilterPanel
        self.filter_panel = FilterPanel()
        self.filter_panel.setObjectName("filter_panel")
        self.filter_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        main_layout.addWidget(self.filter_panel)

        # Results table with flexible sizing
        from .result_table import ResultTable
        self.result_table = ResultTable()
        self.result_table.setObjectName("result_table")
        # Remove minimum height requirement so it takes its natural size
        self.result_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        main_layout.addWidget(self.result_table)

        # Notification panel with natural height
        from .notification_panel import NotificationPanel
        self.notification_panel = NotificationPanel()
        self.notification_panel.setObjectName("notification_panel")
        self.notification_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        main_layout.addWidget(self.notification_panel)

    def open_ai_chat(self):
        # Import here to avoid circular imports
        from .ai_chat_window import AIChatWindow
        self.ai_chat_window = AIChatWindow()
        self.ai_chat_window.show()

    def show_test_notification(self):
        # Create and show a toast notification
        toast = ToastNotification(
            title="STAR",
            message="New match found: BMW X5 2021"
        )
        toast.show_notification()
    
    def show_multiple_notifications(self):
        # Show 3 notifications with different messages and avatars
        messages = [
            {"title": "STAR", "message": "Haxel: Looking good", "avatar": None},
            {"title": "STAR", "message": "Sally Ann: 😊😊😊", "avatar": None},
            {"title": "STAR", "message": "Haxel: Nice day in London!", "avatar": None}
        ]
        
        # Custom avatar colors for each notification
        avatar_colors = ["#4285F4", "#DB4437", "#0F9D58"]
        
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
        # Custom handling of resize events if needed
        super().resizeEvent(event) 