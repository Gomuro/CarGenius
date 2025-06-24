import os
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QTabWidget, QWidget, 
                           QLabel, QHBoxLayout, QLineEdit, QListWidget, QScrollArea, QListWidgetItem)
from ..filter_panel_components.filter_inputs import FilterInputs
from ..filter_panel_components.filter_options import FilterOptions
from ..result_table_components.car_listing_widget import CarListingWidget
from desktop.services.main_api_service import APIService

class AddContextDialog(QDialog):
    """Dialog for adding different types of context to the AI chat."""

    add_car_context_signal = pyqtSignal(dict)  # Pass car data
    add_filters_context_signal = pyqtSignal(dict)

    def __init__(self, license_key: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Context to Chat")
        self.setMinimumSize(800, 700) # Increased size significantly
        self.license_key = license_key
        self.api_service = APIService()

        main_layout = QVBoxLayout(self)
        
        # Tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Statistics Tab
        stats_tab = self._create_search_tab("stats", use_detailed_filters=True)
        tab_widget.addTab(stats_tab, "Statistical Machines")

        # Auction Tab
        auction_tab = self._create_search_tab("auction")
        tab_widget.addTab(auction_tab, "Auction Machines")

        # Filters Tab
        filters_tab = self._create_search_tab("filters")
        tab_widget.addTab(filters_tab, "Filters")
        
        self._load_styles()

    def _load_styles(self):
        """Loads the application's stylesheet."""
        theme_path = os.path.join(os.path.dirname(__file__), '..', '..', 'themes', 'dark.qss')
        try:
            with open(theme_path, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Stylesheet not found at {theme_path}")

    def _create_search_tab(self, search_type: str, use_detailed_filters: bool = False) -> QWidget:
        """Helper method to create a standardized search tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        if use_detailed_filters:
            # Use the advanced filter panel UI
            filter_inputs = FilterInputs()
            filter_options = FilterOptions(show_tracking_option=False) # Hide tracking checkbox
            
            # Connect the search button from the filter inputs
            filter_inputs.search_button.clicked.connect(
                lambda: self._on_detailed_search(search_type, filter_inputs)
            )

            layout.addWidget(filter_inputs)
            layout.addWidget(filter_options)
            
            # Create scrollable results area for car listings
            results_scroll = QScrollArea()
            results_scroll.setWidgetResizable(True)
            results_widget = QWidget()
            self.results_layout = QVBoxLayout(results_widget)
            self.results_layout.setContentsMargins(0, 0, 0, 0)
            self.results_layout.setSpacing(10)
            results_scroll.setWidget(results_widget)
            layout.addWidget(results_scroll)
            
        elif search_type == "filters":
            # Special layout for the Filters tab
            layout.addWidget(QLabel("Select a saved filter to add as context:"))
            
            saved_filters_list = QListWidget()
            self._fetch_and_display_filters(saved_filters_list) # Fetch real data
            layout.addWidget(saved_filters_list)

            add_selected_btn = QPushButton("Add Selected Filter")
            add_selected_btn.setEnabled(False)
            layout.addWidget(add_selected_btn)
            
            # Enable the button only when an item is selected
            saved_filters_list.itemSelectionChanged.connect(lambda: add_selected_btn.setEnabled(bool(saved_filters_list.currentItem())))
            
            # Connect the button to the new handler
            add_selected_btn.clicked.connect(lambda: self._on_add_selected_filter(saved_filters_list))
            
        else:
            # Use the simple search bar for other tabs like 'auction'
            search_layout = QHBoxLayout()
            search_input = QLineEdit()
            search_input.setPlaceholderText(f"Search {search_type}...")
            search_button = QPushButton("Search")
            
            search_layout.addWidget(search_input)
            search_layout.addWidget(search_button)
            layout.addLayout(search_layout)
            
            # Connect search button to a placeholder handler
            search_button.clicked.connect(lambda: self._on_search(search_type, search_input.text()))

            # Results list (for simple search)
            results_list = QListWidget()
            layout.addWidget(results_list)

        return tab_widget

    def _on_detailed_search(self, search_type: str, filter_inputs):
        """Handle search with detailed filters using real API."""
        criteria = filter_inputs.get_criteria()
        print(f"Searching {search_type} with criteria: {criteria}")
        
        # Call the real API
        response = self.api_service.search_listings_sync(criteria)

        listings_data = response.get("Listings", [])
        
        if response:
            self._display_car_listings(listings_data)
        else:
            print("No results or error in API response")
            self._display_no_results()

    def _display_car_listings(self, listings_data):
        """Display car listings using CarListingWidget."""
        # Clear existing results
        self._clear_results()
        # listings_data {"Listings": [{...}, {...}, ...], "Stats": {...}}
        show_only_one_listing = True
        for car_data in listings_data:
            # Convert API data to CarListingWidget format
            widget_data = self._convert_api_data_to_widget_format(car_data)
            if show_only_one_listing:
                print(f"car_data: {car_data}")
                show_only_one_listing = False

            car_widget = CarListingWidget(widget_data)
            car_widget.send_to_ai_signal.connect(self._on_car_selected)
            self.results_layout.addWidget(car_widget)

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
            "margin_rating": 3,  # Default value
            "margin_text": "Market analysis",
            "margin_percentage_text": "Statistical data",
            # Store original API data for context
            "_api_data": api_data
        }

    def _on_car_selected(self, car_data):
        """Handle when a car is selected for AI context."""
        # Use the original API data if available, otherwise use the widget data
        context_data = car_data.get('_api_data', car_data)
        self.add_car_context_signal.emit(context_data)
        self.accept()

    def _on_add_selected_filter(self, list_widget: QListWidget):
        """Emits the selected filter data and closes the dialog."""
        current_item = list_widget.currentItem()
        if current_item:
            filter_data = current_item.data(Qt.ItemDataRole.UserRole)
            self.add_filters_context_signal.emit(filter_data)
            self.accept()

    def _clear_results(self):
        """Clear existing search results."""
        if hasattr(self, 'results_layout'):
            while self.results_layout.count():
                child = self.results_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

    def _display_no_results(self):
        """Display no results message."""
        self._clear_results()
        no_results_label = QLabel("No results found. Try adjusting your search criteria.")
        no_results_label.setStyleSheet("color: #666; text-align: center; padding: 20px;")
        self.results_layout.addWidget(no_results_label)

    def _on_search(self, search_type: str, query: str):
        """Placeholder method to handle search button clicks."""
        print(f"UI-only: Searching in '{search_type}' for query: '{query}'")
        # In the future, this will trigger the actual API call.

    def _fetch_and_display_filters(self, list_widget: QListWidget):
        """Fetches tracked filters from the API and populates the list widget."""
        if not self.license_key:
            list_widget.addItem("No license key found.")
            return

        filters = self.api_service.get_tracked_filters_sync(self.license_key)
        
        list_widget.clear()
        if filters:
            for f in filters:
                item_text = self._summarize_filter(f)
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, f)
                list_widget.addItem(list_item)
        else:
            list_widget.addItem("No saved filters found.")

    def _summarize_filter(self, filter_data: dict) -> str:
        """Creates a readable summary of a filter dictionary."""
        parts = []
        if 'brand' in filter_data:
            parts.append(f"Brand: {filter_data['brand']}")
        if 'model' in filter_data:
            parts.append(f"Model: {filter_data['model']}")
        if 'price_to' in filter_data:
            parts.append(f"Price up to: {filter_data['price_to']}")
        
        summary = ", ".join(parts)
        return summary if summary else "Unnamed Filter" 