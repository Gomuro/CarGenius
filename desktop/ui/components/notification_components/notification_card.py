from PyQt6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QFrame, QWidget, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QFont

class NotificationCard(QFrame):
    def __init__(self, match_data, dismiss_callback, parent=None):
        super().__init__(parent)
        self.match_data = match_data
        self.dismiss_callback = dismiss_callback
        self._create_ui()

    def _create_ui(self):
        self.setObjectName("notification_toast")
        self.setProperty("type", self.match_data["type"])
        self.setMinimumWidth(250)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        header = QHBoxLayout()
        title = QLabel(self.match_data["title"])
        title.setObjectName("match_title")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        
        time_label = QLabel(self.match_data["time"])
        time_label.setObjectName("timestamp")

        dismiss_btn = QPushButton("×")
        dismiss_btn.setObjectName("dismiss_button_toast")
        dismiss_btn.setFixedSize(20, 20)
        dismiss_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        dismiss_btn.clicked.connect(self._handle_dismiss)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(time_label)
        header.addWidget(dismiss_btn)
        
        subtitle = QLabel(self.match_data["subtitle"])
        subtitle.setObjectName("match_subtitle")
        
        price_layout = QHBoxLayout()
        price = QLabel(self.match_data["price"])
        price.setObjectName("match_price")
        price.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        
        price_layout.addWidget(price)
        price_layout.addStretch()
        
        layout.addLayout(header)
        layout.addWidget(subtitle)
        layout.addLayout(price_layout)

        # Margin Indicator Section (reused from original panel)
        margin_section_widget = QWidget()
        margin_section_layout = QVBoxLayout(margin_section_widget)
        margin_section_layout.setContentsMargins(0, 8, 0, 0)
        margin_section_layout.setSpacing(4)

        bars_container = QWidget()
        bars_container_layout = QHBoxLayout(bars_container)
        bars_container_layout.setContentsMargins(0,0,0,0)
        bars_container_layout.setSpacing(3)

        num_total_bars = 5
        active_bars = self.match_data.get("margin_rating", 0)

        for i in range(num_total_bars):
            bar = QFrame()
            if i < active_bars:
                bar.setObjectName("margin_bar_filled")
            else:
                bar.setObjectName("margin_bar_empty")
            bars_container_layout.addWidget(bar)
        
        bars_container_layout.addStretch(1)
        margin_section_layout.addWidget(bars_container)

        margin_text_label = QLabel(self.match_data.get("margin_text", ""))
        margin_text_label.setObjectName("margin_text_label")
        margin_section_layout.addWidget(margin_text_label)

        margin_percentage_label = QLabel(self.match_data.get("margin_percentage_text", ""))
        margin_percentage_label.setObjectName("margin_percentage_label")
        margin_section_layout.addWidget(margin_percentage_label)

        layout.addWidget(margin_section_widget)

    def _handle_dismiss(self):
        self.dismiss_callback(self.match_data, self) 