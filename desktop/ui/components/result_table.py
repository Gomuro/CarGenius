from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QVBoxLayout, QLabel, 
                           QHBoxLayout, QFrame, QScrollArea, QWidget, QGridLayout, QPushButton)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon
from . import BaseComponent

class ResultTable(BaseComponent):
    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Section title with background header
        title_frame = QFrame()
        title_frame.setObjectName("results_header")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(20, 15, 20, 15)
        
        title = QLabel("Search Results")
        title.setObjectName("results_title")
        title_layout.addWidget(title)
        
        main_layout.addWidget(title_frame)
        
        # Container for listings
        listings_container = QFrame()
        listings_container.setObjectName("listings_container")
        listings_layout = QVBoxLayout(listings_container)
        listings_layout.setContentsMargins(0, 0, 0, 0)
        listings_layout.setSpacing(10)  # Gap between listings
        
        # Create sample listings
        sample_cars = [
            {
                "image": "🚗",  # Replace with real image loading
                "title": "Mercedes-Benz CLA 200 d Shooting Brake",
                "subtitle": "CLA 200 d SB • AMG • CAMERA • AHK • MBUX • SHZ",
                "price": "35.980 €",
                "price_tag": "Seller price",
                "year": "2022",
                "km": "13.030 km",
                "power": "110 kW (150 PS)",
                "fuel": "Diesel",
                "seller": "STERNPARTNER SE & Co. KG",
                "location": "21465 Reinbek"
            },
            {
                "image": "🚗",
                "title": "Mercedes-Benz S 450 4MATIC",
                "subtitle": "S 450 4MATIC • Schwarz Matt Foliert",
                "price": "117.499 €",
                "price_tag": "Without warranty",
                "year": "2024",
                "km": "800 km",
                "power": "270 kW (367 PS)",
                "fuel": "Diesel",
                "seller": "",
                "location": "68789 Mannheim, Gartenstadt"
            },
            {
                "image": "🚗",
                "title": "Mercedes-Benz Vito Kombi Tourer Pro 116 CDI",
                "subtitle": "Vito Kombi Tourer Pro 116 CDI Lang 9G-Tronic",
                "price": "42.390 €",
                "price_tag": "Dealer price",
                "year": "2023",
                "km": "24.159 km",
                "power": "120 kW (163 PS)",
                "fuel": "Diesel",
                "seller": "Die Autohaui Bad Salzuflen KG. der Deal",
                "location": "32105 Bad Salzuflen"
            }
        ]
        
        for car in sample_cars:
            listing = self._create_car_listing(car)
            listings_layout.addWidget(listing)
            
        # Add listings container to main layout
        main_layout.addWidget(listings_container)
    
    def _create_car_listing(self, car_data):
        # Create listing frame
        listing_frame = QFrame()
        listing_frame.setObjectName("car_listing")
        listing_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Use grid layout for fixed proportions
        layout = QGridLayout(listing_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setHorizontalSpacing(15)
        
        # Left side - Car image (column 0)
        image_frame = QFrame()
        image_frame.setObjectName("car_image_container")
        image_frame.setFixedSize(278, 190)  # Fixed size from design spec
        
        image_layout = QVBoxLayout(image_frame)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        # For now using emoji, in real app this would be QPixmap loading
        image_label = QLabel(car_data["image"])
        image_label.setObjectName("car_image")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setFont(QFont("Arial", 72))
        image_layout.addWidget(image_label)
        
        # Right side - Car details (column 1)
        details_frame = QFrame()
        details_frame.setObjectName("car_details")
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)
        
        # Car title and subtitle
        title_label = QLabel(car_data["title"])
        title_label.setObjectName("car_title")
        subtitle_label = QLabel(car_data["subtitle"])
        subtitle_label.setObjectName("car_subtitle")
        
        # Price information
        price_layout = QHBoxLayout()
        price_layout.setContentsMargins(0, 0, 0, 0)
        price_layout.setSpacing(5)
        
        price_label = QLabel(car_data["price"])
        price_label.setObjectName("car_price")
        price_tag = QLabel(car_data["price_tag"])
        price_tag.setObjectName("price_tag")
        
        price_layout.addWidget(price_label)
        price_layout.addWidget(price_tag)
        price_layout.addStretch()
        
        # Car specifications
        specs_layout = QHBoxLayout()
        specs_layout.setContentsMargins(0, 0, 0, 0)
        specs_layout.setSpacing(15)
        
        # Create spec items with consistent spacing
        specs_items = [
            f"{car_data['year']}",
            f"{car_data['km']}",
            f"{car_data['power']}",
            f"{car_data['fuel']}"
        ]
        
        for spec in specs_items:
            spec_label = QLabel(spec)
            spec_label.setObjectName("car_spec")
            specs_layout.addWidget(spec_label)
        
        specs_layout.addStretch()
        
        # Seller information
        seller_layout = QHBoxLayout()
        seller_layout.setContentsMargins(0, 0, 0, 0)
        
        if car_data["seller"]:
            seller_label = QLabel(car_data["seller"])
            seller_label.setObjectName("car_seller")
            seller_layout.addWidget(seller_label)
            
        location_label = QLabel(car_data["location"])
        location_label.setObjectName("car_location")
        seller_layout.addStretch()
        seller_layout.addWidget(location_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        contact_btn = QPushButton("Contact")
        contact_btn.setObjectName("contact_button")
        
        share_btn = QPushButton("Share")
        share_btn.setObjectName("share_button")
        
        button_layout.addWidget(contact_btn)
        button_layout.addWidget(share_btn)
        
        # Add all elements to the details layout
        details_layout.addWidget(title_label)
        details_layout.addWidget(subtitle_label)
        details_layout.addLayout(price_layout)
        details_layout.addLayout(specs_layout)
        details_layout.addStretch()
        details_layout.addLayout(seller_layout)
        details_layout.addLayout(button_layout)
        
        # Add both sides to the grid
        layout.addWidget(image_frame, 0, 0)
        layout.addWidget(details_frame, 0, 1)
        
        # Set column stretching
        layout.setColumnStretch(0, 0)  # First column fixed width
        layout.setColumnStretch(1, 1)  # Second column stretches
        
        return listing_frame 