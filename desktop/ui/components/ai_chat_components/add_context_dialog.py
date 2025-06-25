import os
from PyQt6.QtCore import pyqtSignal, Qt, QObject, QRunnable, QThreadPool
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QTabWidget, QWidget, 
                           QLabel, QHBoxLayout, QLineEdit, QListWidget, QScrollArea, QListWidgetItem, QMessageBox)
from ..filter_panel_components.filter_inputs import FilterInputs
from ..filter_panel_components.filter_options import FilterOptions
from ..result_table_components.car_listing_widget import CarListingWidget
from desktop.services.main_api_service import APIService

# Worker for running search in a separate thread
class SearchWorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str, str)  # error_type, error_message

class SearchWorker(QRunnable):
    def __init__(self, api_service, criteria):
        super().__init__()
        self.api_service = api_service
        self.criteria = criteria
        self.signals = SearchWorkerSignals()

    def run(self):
        try:
            response = self.api_service.search_listings_sync(self.criteria)
            if response is None:
                # API returned None, likely a network or server issue
                self.signals.error.emit("network", "Could not connect to the server. Please check your internet connection and try again.")
            else:
                self.signals.finished.emit(response)
        except ConnectionError as e:
            self.signals.error.emit("network", "Network connection failed. Please check your internet connection and try again.")
        except TimeoutError as e:
            self.signals.error.emit("timeout", "Request timed out. The server might be busy. Please try again in a moment.")
        except Exception as e:
            error_message = str(e)
            if "connection" in error_message.lower() or "network" in error_message.lower():
                self.signals.error.emit("network", "Network connection failed. Please check your internet connection and try again.")
            elif "timeout" in error_message.lower():
                self.signals.error.emit("timeout", "Request timed out. Please try again in a moment.")
            elif "server" in error_message.lower() or "500" in error_message:
                self.signals.error.emit("server", "Server error occurred. Please try again later.")
            elif "404" in error_message:
                self.signals.error.emit("server", "Service not found. Please contact support if this persists.")
            else:
                self.signals.error.emit("unknown", f"An unexpected error occurred: {error_message}")

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
        self.threadpool = QThreadPool()

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
            
            # Add a loading indicator (a simple label)
            self.loading_label = QLabel("Searching, please wait...")
            self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.loading_label.setHidden(True) # Initially hidden
            layout.addWidget(self.loading_label)

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
        """Handle search with detailed filters using a background thread."""
        criteria = filter_inputs.get_criteria()
        print(f"Searching {search_type} with criteria: {criteria}")
        
        # Show loading indicator and disable button
        self.loading_label.setHidden(False)
        filter_inputs.search_button.setEnabled(False)
        self._clear_results()

        # Run search in a background thread
        worker = SearchWorker(self.api_service, criteria)
        worker.signals.finished.connect(
            lambda response: self._on_search_finished(response, filter_inputs)
        )
        worker.signals.error.connect(
            lambda error_type, error_msg: self._on_search_error(error_type, error_msg, filter_inputs)
        )
        self.threadpool.start(worker)

    def _on_search_finished(self, response, filter_inputs):
        """Handle successful search completion."""
        self.loading_label.setHidden(True)
        filter_inputs.search_button.setEnabled(True)

        if response and "Listings" in response:
            listings_data = response.get("Listings", [])
            if listings_data:
                self._display_car_listings(listings_data)
            else:
                self._display_no_results()
        else:
            # Response exists but doesn't have expected format
            self._display_error_message("Invalid server response. Please try again or contact support.")

    def _on_search_error(self, error_type, error_message, filter_inputs):
        """Handle search error with specific error types."""
        self.loading_label.setHidden(True)
        filter_inputs.search_button.setEnabled(True)
        print(f"Search error ({error_type}): {error_message}")
        
        # Show error in the results area
        self._display_error_message(error_message)
        
        # For critical errors, also show a popup
        if error_type in ["network", "server"]:
            self._show_error_popup("Search Error", error_message)

    def _display_error_message(self, error_message):
        """Display an error message in the results area."""
        self._clear_results()
        error_label = QLabel(f"❌ {error_message}")
        error_label.setStyleSheet("""
            color: #D32F2F; 
            background-color: rgba(211, 47, 47, 0.1);
            border: 1px solid #D32F2F;
            border-radius: 4px;
            padding: 15px;
            font-size: 14px;
        """)
        error_label.setWordWrap(True)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(error_label)

    def _show_error_popup(self, title, message):
        """Show an error popup dialog."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

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
        no_results_label = QLabel("📭 No cars found matching your search criteria.\nTry adjusting your filters or search terms.")
        no_results_label.setStyleSheet("""
            color: #666; 
            background-color: rgba(102, 102, 102, 0.1);
            border: 1px solid #666;
            border-radius: 4px;
            padding: 15px;
            font-size: 14px;
        """)
        no_results_label.setWordWrap(True)
        no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

        try:
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
        except Exception as e:
            list_widget.clear()
            error_item = QListWidgetItem(f"❌ Error loading filters: {str(e)}")
            error_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it non-selectable
            list_widget.addItem(error_item)
            print(f"Error fetching filters: {e}")

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