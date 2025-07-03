from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, 
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame, QHBoxLayout, QGridLayout, QSpacerItem, QSizePolicy, QProgressBar)
from PyQt6.QtCore import Qt, QRectF, QPointF, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette
import random
import math

# Import the new graph widget
from .analytics_dialog_components.time_series_graph_widget import TimeSeriesLineGraphWidget
from desktop.services.main_api_service import APIService
from .result_table_components.car_listing_widget import CarListingWidget
from desktop.GLOBAL import GLOBAL

class FilterSummaryCard(QFrame):
    """Custom widget for displaying filter information in a card format"""
    
    def __init__(self, criteria, stats, index, parent_dialog):
        super().__init__()
        self.criteria = criteria
        self.stats = stats
        self.index = index
        self.parent_dialog = parent_dialog
        self.setObjectName("filter_summary_card")
        self._create_ui()
    
    def _create_ui(self):
        self.setFrameStyle(QFrame.Shape.Box)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Header with filter name and remove button
        header_layout = QHBoxLayout()
        
        # Filter title
        filter_title = self._create_filter_title()
        title_label = QLabel(filter_title)
        title_label.setObjectName("filter_card_title")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Remove button
        remove_btn = QPushButton("✕")
        remove_btn.setObjectName("filter_remove_btn")
        remove_btn.setFixedSize(24, 24)
        remove_btn.clicked.connect(self._remove_filter)
        remove_btn.setToolTip("Remove this filter")
        header_layout.addWidget(remove_btn)
        
        layout.addLayout(header_layout)
        
        # Filter details
        details_layout = QHBoxLayout()
        details_text = self._create_filter_details()
        details_label = QLabel(details_text)
        details_label.setObjectName("filter_card_details")
        details_label.setWordWrap(True)
        details_layout.addWidget(details_label)
        layout.addLayout(details_layout)
        
        # Statistics grid
        if self.stats and "Stats" in self.stats:
            stats_data = self.stats["Stats"]
            stats_layout = QGridLayout()
            stats_layout.setSpacing(8)
            
            # Price statistics
            self._add_stat_item(stats_layout, 0, 0, "Average Price", f"€{stats_data.get('avg_price', 0):,.0f}")
            self._add_stat_item(stats_layout, 0, 1, "Min Price", f"€{stats_data.get('min_price', 0):,.0f}")
            self._add_stat_item(stats_layout, 1, 0, "Max Price", f"€{stats_data.get('max_price', 0):,.0f}")
            self._add_stat_item(stats_layout, 1, 1, "Total Count", str(stats_data.get('count', 0)))
            
            layout.addLayout(stats_layout)
            
            # Status indicator
            status_label = QLabel("✓ Data loaded successfully")
            status_label.setObjectName("filter_card_status_success")
            layout.addWidget(status_label)
        else:
            # Error state
            error_label = QLabel("⚠ No data available")
            error_label.setObjectName("filter_card_status_error")
            layout.addWidget(error_label)
    
    def _create_filter_title(self):
        """Create a concise title for the filter"""
        parts = []
        if self.criteria.get('brand'):
            parts.append(self.criteria['brand'])
        if self.criteria.get('model'):
            parts.append(self.criteria['model'])
        if self.criteria.get('registration_year'):
            parts.append(str(self.criteria['registration_year']))
        
        return " ".join(parts) if parts else "Custom Filter"
    
    def _create_filter_details(self):
        """Create detailed filter information"""
        details = []
        if self.criteria.get('price_lte'):
            details.append(f"Max Price: €{self.criteria['price_lte']:,}")
        if self.criteria.get('city_or_postal_code'):
            details.append(f"Location: {self.criteria['city_or_postal_code']}")
        if self.criteria.get('color'):
            details.append(f"Color: {self.criteria['color']}")
        
        return " • ".join(details) if details else "No additional filters"
    
    def _add_stat_item(self, layout, row, col, label, value):
        """Add a statistic item to the grid"""
        label_widget = QLabel(label)
        label_widget.setObjectName("stat_label")
        
        value_widget = QLabel(value)
        value_widget.setObjectName("stat_value")
        value_widget.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        item_layout = QVBoxLayout()
        item_layout.setSpacing(2)
        item_layout.addWidget(label_widget)
        item_layout.addWidget(value_widget)
        
        item_widget = QWidget()
        item_widget.setLayout(item_layout)
        item_widget.setObjectName("stat_item")
        
        layout.addWidget(item_widget, row, col)
    
    def _remove_filter(self):
        """Remove this filter from tracking"""
        self.parent_dialog.remove_tracked_filter(self.index)

class EmptyStateWidget(QWidget):
    """Widget to show when there are no tracked filters"""
    
    def __init__(self, message, action_text=None):
        super().__init__()
        self.message = message
        self.action_text = action_text
        self._create_ui()
    
    def _create_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Empty state icon
        icon_label = QLabel("📊")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setObjectName("empty_state_message")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Segoe UI", 14))
        layout.addWidget(message_label)
        
        if self.action_text:
            action_label = QLabel(self.action_text)
            action_label.setObjectName("empty_state_action")
            action_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            action_label.setWordWrap(True)
            layout.addWidget(action_label)

class AnalyticsDialog(QDialog):
    def __init__(self, tracked_models_criteria, api_service: APIService, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Car Analytics & Price Trends")
        self.setMinimumSize(900, 700)
        self.resize(1200, 800)
        self.tracked_models_criteria = tracked_models_criteria.copy() if tracked_models_criteria else []
        self.api_service = api_service
        self.license_key = GLOBAL.LICENSE.get_license_key()
        
        # Hot deals state management
        self.ml_worker = None
        self.hot_deals_widget = None
        self.hot_deals_loaded = False
        self.hot_deals_cache = None
        self.cache_timer = QTimer()
        self.cache_timer.timeout.connect(self._clear_hot_deals_cache)
        
        self._load_tracked_filters_from_api()
        self._create_ui()
        
    def closeEvent(self, event):
        """Clean up resources when dialog is closed."""
        # Stop and cleanup ML worker
        if self.ml_worker and self.ml_worker.isRunning():
            self.ml_worker.terminate()
            self.ml_worker.wait()
            
        # Stop cache timer
        if hasattr(self, 'cache_timer'):
            self.cache_timer.stop()
            
        super().closeEvent(event)

    def _load_tracked_filters_from_api(self):
        """Load tracked filters from the API for the current license"""
        if not self.license_key:
            print("[AnalyticsDialog] No license key found, using local tracked filters only")
            return
            
        try:
            # The API is the source of truth, so we clear the list first.
            self.tracked_models_criteria.clear()
            response = self.api_service.get_tracked_filters_sync(self.license_key)
            
            if response is not None:
                self.tracked_models_criteria.extend(response)
                print(f"[AnalyticsDialog] Loaded {len(self.tracked_models_criteria)} filters from API")
            else:
                print("[AnalyticsDialog] No filters found in API response")
        except Exception as e:
            print(f"[AnalyticsDialog] Error loading filters from API: {e}")
            self.tracked_models_criteria.clear() # Ensure list is empty on error

    def _save_tracked_filters_to_api(self):
        """Save current tracked filters to the API"""
        if not self.license_key:
            print("[AnalyticsDialog] No license key found, cannot save filters")
            return False
            
        try:
            response = self.api_service.update_tracked_filters_sync(self.license_key, self.tracked_models_criteria)
            if response is not None:
                print(f"[AnalyticsDialog] Successfully saved {len(self.tracked_models_criteria)} filters to API")
                return True
            else:
                print("[AnalyticsDialog] Failed to save filters to API")
                return False
        except Exception as e:
            print(f"[AnalyticsDialog] Error saving filters to API: {e}")
            return False

    def add_tracked_filter(self, criteria):
        """Add a new filter to tracking list and save to API"""
        if criteria not in self.tracked_models_criteria:
            self.tracked_models_criteria.append(criteria)
            print(f"[AnalyticsDialog] Added filter to tracking: {criteria}")
            
            # Save to API
            if self._save_tracked_filters_to_api():
                self._refresh_tabs()
            else:
                print("[AnalyticsDialog] Filter added locally but failed to save to API")
        else:
            print(f"[AnalyticsDialog] Filter already tracked: {criteria}")

    def remove_tracked_filter(self, index):
        """Remove a filter from tracking list and save to API"""
        if 0 <= index < len(self.tracked_models_criteria):
            removed_filter = self.tracked_models_criteria.pop(index)
            print(f"[AnalyticsDialog] Removed filter from tracking: {removed_filter}")
            
            # Save to API
            if self._save_tracked_filters_to_api():
                self._refresh_tabs()
            else:
                print("[AnalyticsDialog] Filter removed locally but failed to save to API")

    def clear_all_tracked_filters(self):
        """Clear all tracked filters and update API"""
        if not self.license_key:
            print("[AnalyticsDialog] No license key found, cannot clear filters")
            return
            
        try:
            response = self.api_service.clear_tracked_filters_sync(self.license_key)
            if response is not None:
                self.tracked_models_criteria.clear()
                print("[AnalyticsDialog] Successfully cleared all filters")
                self._refresh_tabs()
            else:
                print("[AnalyticsDialog] Failed to clear filters from API")
        except Exception as e:
            print(f"[AnalyticsDialog] Error clearing filters: {e}")

    def _refresh_tabs(self):
        """Refresh all tab contents after filter changes"""
        # Save current tab index
        current_index = self.tab_widget.currentIndex()
        
        # Clear hot deals cache when filters change
        self._clear_hot_deals_cache()
        
        # Remove all tabs
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        
        # Recreate tabs
        self.average_prices_tab_content = self._create_average_prices_tab()
        self.price_trends_tab_content = self._create_price_trends_tab()
        self.profitable_offers_tab_content = self._create_profitable_offers_tab()

        self.tab_widget.addTab(self.average_prices_tab_content, "📊 Price Overview")
        self.tab_widget.addTab(self.price_trends_tab_content, "📈 Trends")
        self.tab_widget.addTab(self.profitable_offers_tab_content, "💰 Hot Deals")
        
        # Restore current tab
        if current_index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(current_index)
            
    def _clear_hot_deals_cache(self):
        """Clear the hot deals cache to force refresh."""
        self.hot_deals_cache = None
        self.hot_deals_loaded = False
        print("[AnalyticsDialog] Hot deals cache cleared")
        
    def _convert_ml_offer_to_widget_format(self, ml_offer):
        """Convert ML API response to CarListingWidget format."""
        try:
            # Calculate margin percentage for rating
            predicted = ml_offer.get('predicted_price', 0)
            actual = ml_offer.get('actual_price', 0)
            saving = ml_offer.get('saving', 0)
            
            margin_percentage = (saving / predicted * 100) if predicted > 0 else 0
            
            # Determine rating and text based on savings
            if saving > 5000:
                margin_rating = 5
                margin_text = "Excellent Deal"
            elif saving > 3000:
                margin_rating = 4
                margin_text = "Very Good Deal"
            elif saving > 1500:
                margin_rating = 3
                margin_text = "Good Deal"
            elif saving > 500:
                margin_rating = 2
                margin_text = "Fair Deal"
            else:
                margin_rating = 1
                margin_text = "Below Average"
                
            # Handle mileage (API has typo "meleage")
            mileage = ml_offer.get('meleage', ml_offer.get('mileage', 0))
            
            return {
                "image": "🚗",
                "title": f"{ml_offer.get('brand', 'Unknown')} {ml_offer.get('model', 'Unknown')}",
                "subtitle": f"{ml_offer.get('registration_year', 'N/A')} • {mileage:,} km • ML Recommended",
                "price": f"€{actual:,.0f}",
                "price_tag": f"Save €{saving:,.0f}",
                "year": str(ml_offer.get('registration_year', 'N/A')),
                "km": f"{mileage:,} km",
                "power": "N/A",  # Not available in ML API response
                "fuel": ml_offer.get('color', 'N/A'),  # Using color as secondary info
                "seller": "Market Analysis",
                "location": "Germany",
                "margin_rating": margin_rating,
                "margin_text": margin_text,
                "margin_percentage_text": f"Potential savings: €{saving:,.0f} ({margin_percentage:.1f}%)",
                "_api_data": {
                    "url": ml_offer.get('url', ''),
                    "brand": ml_offer.get('brand', 'Unknown'),
                    "model": ml_offer.get('model', 'Unknown'),
                    "registration_year": ml_offer.get('registration_year', 'N/A'),
                    "price": actual
                }
            }
        except Exception as e:
            print(f"[AnalyticsDialog] Error converting ML offer: {e}")
            return None

    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Title and subtitle
        title_layout = QVBoxLayout()
        title_label = QLabel("Analytics Dashboard")
        title_label.setObjectName("analytics_title")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Track and analyze car market trends")
        subtitle_label.setObjectName("analytics_subtitle")
        subtitle_label.setFont(QFont("Segoe UI", 12))
        title_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("analytics_tabs")
        main_layout.addWidget(self.tab_widget)

        self.average_prices_tab_content = self._create_average_prices_tab()
        self.price_trends_tab_content = self._create_price_trends_tab()
        self.profitable_offers_tab_content = self._create_profitable_offers_tab()

        self.tab_widget.addTab(self.average_prices_tab_content, "📊 Price Overview")
        self.tab_widget.addTab(self.price_trends_tab_content, "📈 Trends")
        self.tab_widget.addTab(self.profitable_offers_tab_content, "💰 Hot Deals")

        # Bottom buttons layout
        button_layout = QHBoxLayout()
        
        # Clear All Filters button
        clear_all_button = QPushButton("🗑 Clear All Filters")
        clear_all_button.setObjectName("danger_button")
        clear_all_button.clicked.connect(self.clear_all_tracked_filters)
        button_layout.addWidget(clear_all_button)
        
        # Add spacer
        button_layout.addStretch()
        
        # Close button
        close_button = QPushButton("Close")
        close_button.setObjectName("primary_button")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)

    def _generate_mock_time_series(self, num_points=10, base_price=30000, volatility=5000):
        data = []
        current_price = base_price + random.uniform(-volatility/2, volatility/2)
        for i in range(num_points):
            data.append((i, current_price))
            current_price += random.uniform(-volatility * 0.3, volatility * 0.3)
            current_price = max(5000, current_price) # Ensure price doesn't go too low
        return data

    def _create_average_prices_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        if not self.tracked_models_criteria:
            # Show empty state
            empty_widget = EmptyStateWidget(
                "No tracked filters yet",
                "Use the main page to add filters and track specific car models for analysis."
            )
            layout.addWidget(empty_widget)
        else:
            # Create scroll area for filter cards
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.Shape.NoFrame)
            
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setContentsMargins(0, 0, 0, 0)
            scroll_layout.setSpacing(15)
            
            # Show statistics for each tracked criteria
            for i, criteria in enumerate(self.tracked_models_criteria):
                # Fetch statistics for this criteria
                try:
                    response = self.api_service.search_listings_sync(criteria)
                    stats = response if response else None
                except Exception as e:
                    print(f"Error fetching stats for filter {i}: {e}")
                    stats = None
                
                # Create filter card
                filter_card = FilterSummaryCard(criteria, stats, i, self)
                scroll_layout.addWidget(filter_card)
            
            scroll_layout.addStretch()
            scroll_area.setWidget(scroll_widget)
            layout.addWidget(scroll_area)

        return widget

    def _create_price_trends_tab(self):
        # This tab will now hold a scrollable list of individual graphs
        scroll_widget = QWidget() # Widget to hold the layout of graphs
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(30)

        if not self.tracked_models_criteria:
            empty_widget = EmptyStateWidget(
                "No price trends available",
                "Add tracked filters to see price trend analysis over time."
            )
            scroll_layout.addWidget(empty_widget)
        else:
            for criteria in self.tracked_models_criteria:
                model_name_parts = []
                if criteria.get("brand") and criteria.get("brand") != "N/A":
                    model_name_parts.append(criteria.get("brand"))
                if criteria.get("model") and criteria.get("model") != "N/A":
                    model_name_parts.append(criteria.get("model"))
                if criteria.get("registration_year") and criteria.get("registration_year") != "N/A":
                    model_name_parts.append(str(criteria.get("registration_year")))
                model_display_name = " ".join(model_name_parts) if model_name_parts else "Unknown Model"

                # Generate mock data for this model
                # Adjust base_price and volatility based on criteria if desired
                mock_data = self._generate_mock_time_series(num_points=random.randint(5,12), base_price=random.randint(15000, 60000))
                
                graph_widget = TimeSeriesLineGraphWidget(mock_data, model_display_name)
                scroll_layout.addWidget(graph_widget)
        
        scroll_layout.addStretch(1) # Add stretch at the end of the vertical layout

        # Put the scroll_widget inside a QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidget(scroll_widget)

        return scroll_area # The tab now gets the scroll_area

    def _create_profitable_offers_tab(self):
        # Store reference to the widget for updating
        self.hot_deals_widget = QWidget()
        layout = QVBoxLayout(self.hot_deals_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header with refresh button
        header_layout = QHBoxLayout()
        header_label = QLabel("💰 ML-Powered Best Deals")
        header_label.setObjectName("section_title")
        header_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.setObjectName("small_button")
        refresh_button.clicked.connect(self._refresh_hot_deals)
        refresh_button.setToolTip("Refresh ML recommendations")
        header_layout.addWidget(refresh_button)
        
        layout.addLayout(header_layout)
        
        # Content container that we'll replace based on state
        self.hot_deals_content = QWidget()
        self.hot_deals_content_layout = QVBoxLayout(self.hot_deals_content)
        self.hot_deals_content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.hot_deals_content)
        
        # Load initial content
        self._load_hot_deals_content()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidget(self.hot_deals_widget)
        
        return scroll_area
        
    def _load_hot_deals_content(self):
        """Load the appropriate content for hot deals tab based on state."""
        # Clear existing content
        while self.hot_deals_content_layout.count():
            child = self.hot_deals_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Check license first
        if not self.license_key:
            self._show_no_license_state()
            return
            
        # Check if we have cached data
        if self.hot_deals_cache:
            self._display_cached_offers()
            return
            
        # Check if already loading
        if self.ml_worker and self.ml_worker.isRunning():
            return  # Already loading
            
        # Start loading from API
        self._show_loading_state()
        self._start_ml_loading()
        
    def _show_no_license_state(self):
        """Show state when no license key is available."""
        no_license_widget = EmptyStateWidget(
            "License Required",
            "Please ensure you have a valid license to access ML-powered recommendations."
        )
        self.hot_deals_content_layout.addWidget(no_license_widget)
        
    def _show_loading_state(self):
        """Show loading indicator while fetching ML data."""
        loading_widget = QWidget()
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.setSpacing(15)
        
        # Loading indicator
        loading_label = QLabel("🔄 Analyzing market data...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setFont(QFont("Segoe UI", 14))
        loading_layout.addWidget(loading_label)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate
        progress_bar.setMaximumWidth(300)
        loading_layout.addWidget(progress_bar)
        
        loading_text = QLabel("Our ML model is finding the best deals based on your tracked filters...")
        loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_text.setWordWrap(True)
        loading_text.setObjectName("empty_state_action")
        loading_layout.addWidget(loading_text)
        
        self.hot_deals_content_layout.addWidget(loading_widget)
        
    def _show_error_state(self, error_message):
        """Show error state with retry option."""
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_layout.setSpacing(15)
        
        # Error icon and message
        error_label = QLabel("❌ Failed to load recommendations")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        error_layout.addWidget(error_label)
        
        # Error details
        details_label = QLabel(f"Error: {error_message}")
        details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_label.setWordWrap(True)
        details_label.setObjectName("empty_state_action")
        error_layout.addWidget(details_label)
        
        # Retry button
        retry_button = QPushButton("🔄 Retry")
        retry_button.setObjectName("action_button")
        retry_button.clicked.connect(self._refresh_hot_deals)
        retry_button.setMaximumWidth(150)
        error_layout.addWidget(retry_button)
        
        self.hot_deals_content_layout.addWidget(error_widget)
        
    def _show_empty_state(self):
        """Show state when no good deals are found."""
        empty_widget = EmptyStateWidget(
            "No exceptional deals found right now",
            "Our ML analysis didn't find any below-market offers matching your tracked filters. Check back later or adjust your filters!"
        )
        self.hot_deals_content_layout.addWidget(empty_widget)
        
    def _display_cached_offers(self):
        """Display cached ML offers."""
        if not self.hot_deals_cache or not self.hot_deals_cache.get('top_offers'):
            self._show_empty_state()
            return
            
        top_offers = self.hot_deals_cache['top_offers']
        listings_count = self.hot_deals_cache.get('listings_count', 0)
        
        # Info header
        info_label = QLabel(f"📊 Found {len(top_offers)} exceptional deals from {listings_count} analyzed listings")
        info_label.setObjectName("empty_state_action")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hot_deals_content_layout.addWidget(info_label)
        
        # Display offers
        for offer in top_offers:
            # Only show offers with positive savings
            if offer.get('saving', 0) > 0:
                widget_data = self._convert_ml_offer_to_widget_format(offer)
                if widget_data:
                    listing_widget = CarListingWidget(widget_data)
                    self.hot_deals_content_layout.addWidget(listing_widget)
        
        # Add stretch
        self.hot_deals_content_layout.addStretch(1)
        
    def _start_ml_loading(self):
        """Start the ML worker thread to load best offers."""
        self.ml_worker = MLBestOffersWorker(self.api_service, self.license_key)
        self.ml_worker.finished.connect(self._on_ml_offers_loaded)
        self.ml_worker.error.connect(self._on_ml_offers_error)
        self.ml_worker.start()
        
    def _on_ml_offers_loaded(self, result):
        """Handle successful ML offers loading."""
        try:
            # Cache the result for 10 minutes
            self.hot_deals_cache = result
            self.hot_deals_loaded = True
            
            # Set cache expiry timer
            self.cache_timer.stop()
            self.cache_timer.start(10 * 60 * 1000)  # 10 minutes
            
            # Update UI
            self._load_hot_deals_content()
            
            print(f"[AnalyticsDialog] Loaded {len(result.get('top_offers', []))} ML offers")
            
        except Exception as e:
            print(f"[AnalyticsDialog] Error processing ML offers: {e}")
            self._on_ml_offers_error(f"Error processing data: {str(e)}")
            
    def _on_ml_offers_error(self, error_message):
        """Handle ML offers loading error."""
        print(f"[AnalyticsDialog] ML offers error: {error_message}")
        
        # Clear existing content
        while self.hot_deals_content_layout.count():
            child = self.hot_deals_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Show error state
        self._show_error_state(error_message)
        
    def _refresh_hot_deals(self):
        """Manually refresh hot deals data."""
        print("[AnalyticsDialog] Manual hot deals refresh triggered")
        self._clear_hot_deals_cache()
        self._load_hot_deals_content()

# Worker thread for loading ML data
class MLBestOffersWorker(QThread):
    """Worker thread for loading best offers from ML API"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, api_service, license_key):
        super().__init__()
        self.api_service = api_service
        self.license_key = license_key
        
    def run(self):
        try:
            if not self.license_key:
                self.error.emit("No license key available")
                return
                
            result = self.api_service.get_best_offer_sync(self.license_key)
            if result:
                self.finished.emit(result)
            else:
                self.error.emit("No response from server")
        except Exception as e:
            self.error.emit(str(e))

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    from desktop.services.main_api_service import APIService

    app = QApplication(sys.argv)
    # Sample tracked models for testing the dialog directly
    sample_tracked = [
        {"brand": "Toyota", "model": "Camry", "year": "2021"},
        {"brand": "Honda", "model": "CR-V", "year": "2022"},
        {"brand": "BMW", "model": "X5"}, # Year might be None
    ]
    api = APIService()
    dialog = AnalyticsDialog(sample_tracked, api)
    dialog.show()
    sys.exit(app.exec()) 