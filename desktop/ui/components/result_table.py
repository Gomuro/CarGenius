from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QHBoxLayout, QFrame)
# Removed QTableWidget, QTableWidgetItem, QScrollArea, QWidget, QGridLayout, QPushButton as they are encapsulated or not directly used
from PyQt6.QtCore import Qt # QSize removed
# from PyQt6.QtGui import QPixmap, QFont, QIcon # No longer directly used here
from . import BaseComponent
from .result_table_components.car_listing_widget import CarListingWidget # Import the new component

class ResultTable(BaseComponent):
    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        title_frame = QFrame()
        title_frame.setObjectName("results_header")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(20, 15, 20, 15)
        
        title = QLabel("Search Results")
        title.setObjectName("results_title")
        title_layout.addWidget(title)
        main_layout.addWidget(title_frame)
        
        listings_container = QFrame()
        listings_container.setObjectName("listings_container")
        self.listings_layout = QVBoxLayout(listings_container) # Made an attribute for potential dynamic updates
        self.listings_layout.setContentsMargins(0, 0, 0, 0)
        self.listings_layout.setSpacing(10)
        
        sample_cars = [
            {
                "image": "🚗",
                "title": "Mercedes-Benz CLA 200 d Shooting Brake",
                "subtitle": "CLA 200 d SB • AMG • CAMERA • AHK • MBUX • SHZ",
                "price": "35.980 €",
                "price_tag": "Seller price",
                "year": "2022",
                "km": "13.030 km",
                "power": "110 kW (150 PS)",
                "fuel": "Diesel",
                "seller": "STERNPARTNER SE & Co. KG",
                "location": "21465 Reinbek",
                "margin_rating": 5,
                "margin_text": "Very good price",
                "margin_percentage_text": "Potential margin: 18%"
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
                "location": "68789 Mannheim, Gartenstadt",
                "margin_rating": 3,
                "margin_text": "Fair price",
                "margin_percentage_text": "Potential margin: 8%"
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
                "location": "32105 Bad Salzuflen",
                "margin_rating": 4,
                "margin_text": "Good price",
                "margin_percentage_text": "Potential margin: 12%"
            }
        ]
        
        self.populate_listings(sample_cars) # Use a method to populate
            
        main_layout.addWidget(listings_container)
    
    def populate_listings(self, car_data_list):
        # Clear existing listings first if any (for dynamic updates)
        while self.listings_layout.count():
            child = self.listings_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for car_data in car_data_list:
            listing_widget = CarListingWidget(car_data)
            self.listings_layout.addWidget(listing_widget)
        
        # Potentially add a spacer or stretch if no results, or handle that in _create_ui
        self.listings_layout.addStretch(1) # Add stretch to push items to top if container is scrollable

    # _create_car_listing method is now encapsulated in CarListingWidget 