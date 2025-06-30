from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QHBoxLayout, QFrame, QPushButton, QComboBox, QSpacerItem, QSizePolicy)
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
    def __init__(self, api_service, page=1, page_size=20):
        super().__init__()
        self.api_service = api_service
        self.page = page
        self.page_size = page_size
        self.signals = CarDataWorkerSignals()

    def run(self):
        try:
            # Fetch listings with pagination parameters
            response = self.api_service.search_listings_sync({}, self.page, self.page_size)
            self.signals.finished.emit(response)
        except Exception as e:
            self.signals.error.emit(str(e))

class ResultTable(BaseComponent):
    car_context_signal = pyqtSignal(dict)

    def __init__(self, *args, **kwargs):
        self.api_service = APIService()
        self.threadpool = QThreadPool()
        
        # Pagination state
        self.current_page = 1
        self.page_size = 20
        self.total_pages = 1
        self.total_results = 0
        
        super().__init__(*args, **kwargs)

    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Title and results count header
        title_frame = QFrame()
        title_frame.setObjectName("results_header")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(20, 15, 20, 15)
        
        self.title_label = QLabel("Search Results")
        self.title_label.setObjectName("results_title")
        title_layout.addWidget(self.title_label)
        
        # Results count (will be updated dynamically)
        self.results_count_label = QLabel("")
        self.results_count_label.setObjectName("results_count")
        self.results_count_label.setStyleSheet("color: #666; font-size: 12px;")
        title_layout.addWidget(self.results_count_label)
        
        title_layout.addStretch(1)
        main_layout.addWidget(title_frame)
        
        # Page size selector frame
        page_size_frame = QFrame()
        page_size_frame.setObjectName("page_size_frame")
        page_size_layout = QHBoxLayout(page_size_frame)
        page_size_layout.setContentsMargins(20, 10, 20, 10)
        
        page_size_layout.addStretch(1)
        
        page_size_label = QLabel("Results per page:")
        page_size_label.setStyleSheet("color: #666; font-size: 12px;")
        page_size_layout.addWidget(page_size_label)
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "20", "50"])
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.setMinimumWidth(60)
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        page_size_layout.addWidget(self.page_size_combo)
        
        main_layout.addWidget(page_size_frame)
        
        # Loading indicator (separate from listings to avoid deletion)
        self.loading_label = QLabel("Loading car listings...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setObjectName("loading_label")
        main_layout.addWidget(self.loading_label)
        
        # Listings container
        listings_container = QFrame()
        listings_container.setObjectName("listings_container")
        self.listings_layout = QVBoxLayout(listings_container)
        self.listings_layout.setContentsMargins(0, 0, 0, 0)
        self.listings_layout.setSpacing(10)
        
        main_layout.addWidget(listings_container)
        
        # Pagination controls frame
        pagination_frame = QFrame()
        pagination_frame.setObjectName("pagination_frame")
        pagination_layout = QHBoxLayout(pagination_frame)
        pagination_layout.setContentsMargins(20, 15, 20, 15)
        
        # Previous button
        self.prev_button = QPushButton("← Previous")
        self.prev_button.setEnabled(False)  # Disabled by default
        self.prev_button.clicked.connect(self._on_previous_page)
        self.prev_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #333;
                color: white;
            }
            QPushButton:hover:enabled {
                background-color: #444;
            }
            QPushButton:disabled {
                background-color: #222;
                color: #666;
                border-color: #333;
            }
        """)
        pagination_layout.addWidget(self.prev_button)
        
        # Spacer
        pagination_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Page indicator
        self.page_indicator = QLabel("Page 1 of 1")
        self.page_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_indicator.setStyleSheet("color: #666; font-size: 12px; font-weight: bold;")
        pagination_layout.addWidget(self.page_indicator)
        
        # Spacer
        pagination_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Next button
        self.next_button = QPushButton("Next →")
        self.next_button.setEnabled(False)  # Disabled by default
        self.next_button.clicked.connect(self._on_next_page)
        self.next_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #333;
                color: white;
            }
            QPushButton:hover:enabled {
                background-color: #444;
            }
            QPushButton:disabled {
                background-color: #222;
                color: #666;
                border-color: #333;
            }
        """)
        pagination_layout.addWidget(self.next_button)
        
        main_layout.addWidget(pagination_frame)
        
        # Load real data
        self._load_car_data()

    def _on_page_size_changed(self, new_size_text):
        """Handle page size change."""
        new_size = int(new_size_text)
        if new_size != self.page_size:
            self.page_size = new_size
            self.current_page = 1  # Reset to first page
            print(f"[ResultTable] Page size changed to {new_size}, resetting to page 1")
            self._load_car_data()

    def _on_previous_page(self):
        """Handle previous page button click."""
        if self.current_page > 1:
            self.current_page -= 1
            print(f"[ResultTable] Going to previous page: {self.current_page}")
            self._load_car_data()

    def _on_next_page(self):
        """Handle next page button click."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            print(f"[ResultTable] Going to next page: {self.current_page}")
            self._load_car_data()

    def _update_pagination_ui(self):
        """Update pagination controls based on current state."""
        # Update page indicator
        self.page_indicator.setText(f"Page {self.current_page} of {self.total_pages}")
        
        # Update button states
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)
        
        # Update results count
        start_result = (self.current_page - 1) * self.page_size + 1
        end_result = min(self.current_page * self.page_size, self.total_results)
        
        if self.total_results > 0:
            self.results_count_label.setText(f"Showing {start_result}-{end_result} of {self.total_results} results")
        else:
            self.results_count_label.setText("No results found")

    def _load_car_data(self):
        """Load car data from the API in a background thread."""
        # Show loading indicator
        self.loading_label.show()
        self.loading_label.setText(f"Loading page {self.current_page}...")
        
        # Disable pagination controls while loading
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        
        worker = CarDataWorker(self.api_service, self.current_page, self.page_size)
        worker.signals.finished.connect(self._on_data_loaded)
        worker.signals.error.connect(self._on_data_error)
        self.threadpool.start(worker)

    def _on_data_loaded(self, response):
        """Handle successful data loading."""
        self.loading_label.hide()
        
        if response and "Listings" in response:
            listings_data = response.get("Listings", [])
            
            # Use pagination data from server response
            self.total_results = response.get("Stats", {}).get("count", len(listings_data))
            self.total_pages = response.get("total", 1)
            
            # Fallback calculation if server doesn't provide pagination metadata
            if "total" not in response:
                self.total_results = len(listings_data)
                self.total_pages = max(1, (self.total_results + self.page_size - 1) // self.page_size)
            
            # Server already returns paginated data, so use it directly
            page_data = listings_data
            
            if page_data:
                # Convert API data to widget format and populate
                converted_data = [self._convert_api_data_to_widget_format(car) for car in page_data]
                self.populate_listings(converted_data)
            else:
                self._show_no_results()
                
            # Update pagination UI
            self._update_pagination_ui()
        else:
            self._show_error("Invalid server response. Please try again later.")
            self._update_pagination_ui()

    def _on_data_error(self, error_message):
        """Handle data loading error."""
        self.loading_label.hide()
        self._show_error(f"Failed to load car listings: {error_message}")
        
        # Reset pagination state on error
        self.total_results = 0
        self.total_pages = 1
        self._update_pagination_ui()

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