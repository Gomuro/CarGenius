from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QHBoxLayout, QFrame)
# Removed QTableWidget, QTableWidgetItem, QScrollArea, QWidget, QGridLayout, QPushButton as they are encapsulated or not directly used
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QRunnable, QThreadPool
# from PyQt6.QtGui import QPixmap, QFont, QIcon # No longer directly used here
from . import BaseComponent
from .result_table_components.car_listing_widget import CarListingWidget # Import the new component
from desktop.services.main_api_service import APIService

# Worker for loading car data in background
class CarDataWorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

class CarDataWorker(QRunnable):
    def __init__(self, api_service):
        super().__init__()
        self.api_service = api_service
        self.signals = CarDataWorkerSignals()

    def run(self):
        try:
            # Fetch all listings with empty criteria to get a general overview
            response = self.api_service.search_listings_sync({})
            self.signals.finished.emit(response)
        except Exception as e:
            self.signals.error.emit(str(e))

class ResultTable(BaseComponent):
    car_context_signal = pyqtSignal(dict)

    def __init__(self, *args, **kwargs):
        self.api_service = APIService()
        self.threadpool = QThreadPool()
        super().__init__(*args, **kwargs)

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
        self.listings_layout = QVBoxLayout(listings_container)
        self.listings_layout.setContentsMargins(0, 0, 0, 0)
        self.listings_layout.setSpacing(10)
        
        # Add loading indicator
        self.loading_label = QLabel("Loading car listings...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setObjectName("loading_label")
        self.listings_layout.addWidget(self.loading_label)
        
        main_layout.addWidget(listings_container)
        
        # Load real data
        self._load_car_data()

    def _load_car_data(self):
        """Load car data from the API in a background thread."""
        worker = CarDataWorker(self.api_service)
        worker.signals.finished.connect(self._on_data_loaded)
        worker.signals.error.connect(self._on_data_error)
        self.threadpool.start(worker)

    def _on_data_loaded(self, response):
        """Handle successful data loading."""
        self.loading_label.hide()
        
        if response and "Listings" in response:
            listings_data = response.get("Listings", [])
            if listings_data:
                # Convert API data to widget format and populate
                converted_data = [self._convert_api_data_to_widget_format(car) for car in listings_data]
                self.populate_listings(converted_data)
            else:
                self._show_no_results()
        else:
            self._show_error("Invalid server response. Please try again later.")

    def _on_data_error(self, error_message):
        """Handle data loading error."""
        self.loading_label.hide()
        self._show_error(f"Failed to load car listings: {error_message}")

    def _convert_api_data_to_widget_format(self, api_data):
        """Convert API car data to CarListingWidget expected format."""
        return {
            "image": "🚗",
            "title": f"{api_data.get('brand', 'Unknown')} {api_data.get('model', 'Unknown')}",
            "subtitle": f"{api_data.get('registration_year', 'N/A')} • {api_data.get('mileage', 'N/A')} km",
            "price": f"{api_data.get('price', 0):,} €",
            "price_tag": "Market price",
            "year": str(api_data.get('registration_year', 'N/A')),
            "km": f"{api_data.get('mileage', 0):,} km",
            "power": api_data.get('technical_details', {}).get('power', 'N/A'),
            "fuel": api_data.get('technical_details', {}).get('engine_type', 'N/A'),
            "seller": "Market data",
            "location": api_data.get('city_or_postal_code', 'N/A'),
            "margin_rating": 3,  # Default value - could be enhanced with real ML predictions
            "margin_text": "Market analysis",
            "margin_percentage_text": "Statistical data",
            # Store original API data for context
            "_api_data": api_data
        }

    def _show_no_results(self):
        """Show no results message."""
        no_results_label = QLabel("📭 No car listings available at the moment.\nPlease try again later.")
        no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_results_label.setObjectName("no_results_label")
        self.listings_layout.addWidget(no_results_label)

    def _show_error(self, error_message):
        """Show error message."""
        error_label = QLabel(f"❌ {error_message}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setObjectName("error_label")
        error_label.setStyleSheet("""
            color: #D32F2F; 
            background-color: rgba(211, 47, 47, 0.1);
            border: 1px solid #D32F2F;
            border-radius: 4px;
            padding: 15px;
            font-size: 14px;
        """)
        self.listings_layout.addWidget(error_label)
    
    def populate_listings(self, car_data_list):
        # Clear existing listings first if any (for dynamic updates)
        while self.listings_layout.count():
            child = self.listings_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for car_data in car_data_list:
            listing_widget = CarListingWidget(car_data)
            listing_widget.send_to_ai_signal.connect(self._on_car_context_selected)
            self.listings_layout.addWidget(listing_widget)
        
        # Add stretch to push items to top if container is scrollable
        self.listings_layout.addStretch(1)

    def _on_car_context_selected(self, car_data: dict):
        """Receives car data from a listing and emits it upward."""
        self.car_context_signal.emit(car_data)

    # _create_car_listing method is now encapsulated in CarListingWidget 