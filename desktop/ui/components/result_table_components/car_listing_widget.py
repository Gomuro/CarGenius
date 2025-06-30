from PyQt6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, QFrame, QWidget, QGridLayout, QPushButton, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont # QPixmap, QIcon removed as they are not used directly here but in parent/data
import webbrowser

class CarListingWidget(QFrame):
    send_to_ai_signal = pyqtSignal(dict)

    def __init__(self, car_data, parent=None):
        super().__init__(parent)
        self.car_data = car_data
        self.setObjectName("car_listing")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._create_ui()

    def _create_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setHorizontalSpacing(15)
        
        # Left side - Car image
        image_frame = QFrame()
        image_frame.setObjectName("car_image_container")
        image_frame.setFixedSize(278, 190)
        image_layout = QVBoxLayout(image_frame)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        image_label = QLabel(self.car_data["image"])
        image_label.setObjectName("car_image")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setFont(QFont("Arial", 72))
        image_layout.addWidget(image_label)
        
        # Right side - Car details
        details_frame = QFrame()
        details_frame.setObjectName("car_details")
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)
        
        title_label = QLabel(self.car_data["title"])
        title_label.setObjectName("car_title")
        subtitle_label = QLabel(self.car_data["subtitle"])
        subtitle_label.setObjectName("car_subtitle")
        
        price_layout = QHBoxLayout()
        price_layout.setContentsMargins(0, 0, 0, 0)
        price_layout.setSpacing(5)
        price_label = QLabel(self.car_data["price"])
        price_label.setObjectName("car_price")
        price_tag = QLabel(self.car_data["price_tag"])
        price_tag.setObjectName("price_tag")
        price_layout.addWidget(price_label)
        price_layout.addWidget(price_tag)
        price_layout.addStretch()
        
        # Margin Indicator Section
        margin_section_widget = QWidget()
        margin_section_layout = QVBoxLayout(margin_section_widget)
        margin_section_layout.setContentsMargins(0, 8, 0, 5)
        margin_section_layout.setSpacing(4)

        bars_container = QWidget()
        bars_container_layout = QHBoxLayout(bars_container)
        bars_container_layout.setContentsMargins(0,0,0,0)
        bars_container_layout.setSpacing(3)
        num_total_bars = 5
        active_bars = self.car_data.get("margin_rating", 0)
        for i in range(num_total_bars):
            bar = QFrame()
            if i < active_bars:
                bar.setObjectName("margin_bar_filled")
            else:
                bar.setObjectName("margin_bar_empty")
            bars_container_layout.addWidget(bar)
        bars_container_layout.addStretch(1)
        margin_section_layout.addWidget(bars_container)

        margin_text_label = QLabel(self.car_data.get("margin_text", ""))
        margin_text_label.setObjectName("margin_text_label")
        margin_section_layout.addWidget(margin_text_label)

        margin_percentage_label = QLabel(self.car_data.get("margin_percentage_text", ""))
        margin_percentage_label.setObjectName("margin_percentage_label")
        margin_section_layout.addWidget(margin_percentage_label)

        details_layout.addWidget(margin_section_widget) # Add margin section to details
        
        specs_layout = QHBoxLayout()
        specs_layout.setContentsMargins(0, 0, 0, 0)
        specs_layout.setSpacing(15)
        specs_items = [
            f"{self.car_data['year']}",
            f"{self.car_data['km']}",
            f"{self.car_data['power']}",
            f"{self.car_data['fuel']}"
        ]
        for spec in specs_items:
            spec_label = QLabel(spec)
            spec_label.setObjectName("car_spec")
            specs_layout.addWidget(spec_label)
        specs_layout.addStretch()
        
        seller_layout = QHBoxLayout()
        seller_layout.setContentsMargins(0, 0, 0, 0)
        if self.car_data["seller"]:
            seller_label = QLabel(self.car_data["seller"])
            seller_label.setObjectName("car_seller")
            seller_layout.addWidget(seller_label)
        location_label = QLabel(self.car_data["location"])
        location_label.setObjectName("car_location")
        seller_layout.addStretch()
        seller_layout.addWidget(location_label)
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        button_layout.addStretch()
        view_listing_btn = QPushButton("Open on Website")
        view_listing_btn.setObjectName("view_listing_button")
        view_listing_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_listing_btn.clicked.connect(self._open_on_website)

        self.share_btn = QPushButton("Share")
        self.share_btn.setObjectName("share_button")
        self.share_btn.clicked.connect(self._share_car_details)

        ask_ai_btn = QPushButton("Ask AI")
        ask_ai_btn.setObjectName("ask_ai_button")
        ask_ai_btn.clicked.connect(self._on_ask_ai_clicked)

        button_layout.addWidget(view_listing_btn)
        button_layout.addWidget(self.share_btn)
        button_layout.addWidget(ask_ai_btn)
        
        details_layout.addWidget(title_label)
        details_layout.addWidget(subtitle_label)
        details_layout.addLayout(price_layout)
        # Margin section already added above title/subtitle
        details_layout.addLayout(specs_layout)
        details_layout.addStretch()
        details_layout.addLayout(seller_layout)
        details_layout.addLayout(button_layout)
        
        layout.addWidget(image_frame, 0, 0)
        layout.addWidget(details_frame, 0, 1)
        
        layout.setColumnStretch(0, 0) 
        layout.setColumnStretch(1, 1) 

    def _open_on_website(self):
        """Opens the car's URL in the default web browser."""
        url = self.car_data.get("_api_data", {}).get("url")
        if url:
            webbrowser.open(url)
            print(f"Opening URL: {url}")
        else:
            print("No URL found for this listing.")
            
    def _share_car_details(self):
        """Formats car details and copies them to the clipboard."""
        api_data = self.car_data.get('_api_data', {})
        
        details_to_share = (
            f"Check out this car I found with CarGenius:\n"
            f"Make: {api_data.get('brand', 'N/A')}\n"
            f"Model: {api_data.get('model', 'N/A')}\n"
            f"Year: {api_data.get('registration_year', 'N/A')}\n"
            f"Price: {self.car_data.get('price', 'N/A')}\n"
            f"URL: {api_data.get('url', 'N/A')}"
        )
        
        clipboard = QApplication.clipboard()
        clipboard.setText(details_to_share)
        
        # Provide user feedback
        original_text = self.share_btn.text()
        self.share_btn.setText("Copied!")
        QTimer.singleShot(2000, lambda: self.share_btn.setText(original_text))
        print("Car details copied to clipboard.")

    def _on_ask_ai_clicked(self):
        """Emits the car data when the Ask AI button is clicked."""
        self.send_to_ai_signal.emit(self.car_data)
        print(f"UI: Emitting car data for AI context: {self.car_data.get('title')}") 