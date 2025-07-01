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
    def __init__(self, api_service, search_criteria, page=1, page_size=20):
        super().__init__()
        self.api_service = api_service
        self.search_criteria = search_criteria
        self.page = page
        self.page_size = page_size
        self.signals = CarDataWorkerSignals()

    def run(self):
        try:
            # Add pagination parameters to the search criteria
            request_data = self.search_criteria.copy()
            request_data['page'] = self.page
            request_data['size'] = self.page_size

            # Use the combined criteria for the API call
            response = self.api_service.search_listings_sync(request_data)
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
        
        # Search state
        self.current_search_criteria = {}
        self.has_searched = False
        
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
        self.loading_label = QLabel("")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setObjectName("loading_label")
        self.loading_label.hide()  # Initially hidden
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
        
        # Initial state - show "ready to search" message (after all UI elements are created)
        self._show_ready_to_search()

    def search_with_criteria(self, search_criteria: dict):
        """Public method to trigger search with given criteria"""
        self.current_search_criteria = search_criteria
        self.current_page = 1  # Reset to first page for new search
        self.has_searched = True
        print(f"[ResultTable] Starting search with criteria: {search_criteria}")
        self._load_car_data()

    def _show_ready_to_search(self):
        """Show initial state message"""
        self._clear_listings()
        ready_label = QLabel("🔍 Use the filters above to search for cars")
        ready_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ready_label.setObjectName("ready_search_label")
        ready_label.setStyleSheet("""
            color: #888; 
            font-size: 16px;
            padding: 40px;
            border: 2px dashed #444;
            border-radius: 8px;
            background-color: rgba(68, 68, 68, 0.1);
        """)
        self.listings_layout.addWidget(ready_label)
        
        # Update UI state for no search
        self.results_count_label.setText("")
        self.page_indicator.setText("Page 1 of 1")
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)

    def _on_page_size_changed(self, new_size_text):
        """Handle page size change."""
        new_size = int(new_size_text)
        if new_size != self.page_size:
            self.page_size = new_size
            self.current_page = 1  # Reset to first page
            print(f"[ResultTable] Page size changed to {new_size}, resetting to page 1")
            if self.has_searched:  # Only reload if we've already searched
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
        if not self.has_searched:
            return  # Don't load if no search has been performed
            
        # Show loading indicator
        self.loading_label.show()
        self.loading_label.setText(f"Searching page {self.current_page}...")
        
        # Disable pagination controls while loading
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        
        worker = CarDataWorker(self.api_service, self.current_search_criteria, self.current_page, self.page_size)
        worker.signals.finished.connect(self._on_data_loaded)
        worker.signals.error.connect(self._on_data_error)
        self.threadpool.start(worker)

    def _on_data_loaded(self, response):
        """Handle successful data loading."""
        self.loading_label.hide()
        
        if response and "Listings" in response and "Stats" in response:
            listings_data = response.get("Listings", [])
            stats = response.get("Stats", {})
            
            # Use real pagination data from the API response
            self.total_results = stats.get("count", 0)
            self.total_pages = response.get("total", 0)
            
            if listings_data:
                # Data is already paginated by the backend
                converted_data = [self._convert_api_data_to_widget_format(car) for car in listings_data]
                self.populate_listings(converted_data)
            else:
                self._show_no_results()
                
            # Update pagination UI with correct data
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
        self._clear_listings()
        no_results_label = QLabel("📭 No cars found matching your search criteria.\nTry adjusting your filters and search again.")
        no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_results_label.setObjectName("no_results_label")
        no_results_label.setStyleSheet("""
            color: #888; 
            font-size: 14px;
            padding: 30px;
            border: 2px solid #666;
            border-radius: 8px;
            background-color: rgba(102, 102, 102, 0.1);
        """)
        self.listings_layout.addWidget(no_results_label)

    def _show_error(self, error_message):
        """Show error message."""
        self._clear_listings()
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

    def _clear_listings(self):
        """Clear existing listings"""
        while self.listings_layout.count():
            child = self.listings_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def populate_listings(self, car_data_list):
        # Clear existing listings first if any (for dynamic updates)
        self._clear_listings()

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