from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLineEdit, QLabel, QFrame, QComboBox, 
                           QSizePolicy, QScrollArea)
from PyQt6.QtGui import QIcon, QFont

class MainWindow(QMainWindow):
    theme_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CarGenius")
        self.current_theme = "light"
        
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
        
        # Theme switcher
        self.theme_button = QPushButton("Switch to Dark Theme")
        self.theme_button.setObjectName("theme_button")
        self.theme_button.clicked.connect(self._toggle_theme)
        title_layout.addWidget(self.theme_button, alignment=Qt.AlignmentFlag.AlignRight)
        header_layout.addLayout(title_layout)
        
        # Server settings with better adaptive layout
        server_layout = QHBoxLayout()
        server_layout.setSpacing(10)
        
        server_label = QLabel("Server URL:")
        server_label.setFixedWidth(80)
        server_layout.addWidget(server_label)
        
        self.server_url = QLineEdit("https://api.cargenius.com")
        self.server_url.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        server_layout.addWidget(self.server_url, 3)
        
        api_label = QLabel("API Key:")
        api_label.setFixedWidth(60)
        server_layout.addWidget(api_label)
        
        self.api_key = QLineEdit()
        self.api_key.setPlaceholderText("Enter your API key")
        self.api_key.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        server_layout.addWidget(self.api_key, 2)
        
        header_layout.addLayout(server_layout)
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

    def _toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        button_text = "Switch to Light Theme" if self.current_theme == "dark" else "Switch to Dark Theme"
        self.theme_button.setText(button_text)
        self._load_styles(self.current_theme)

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