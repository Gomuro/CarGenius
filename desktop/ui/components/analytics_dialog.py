from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, 
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame, QHBoxLayout, QGridLayout, QSpacerItem, QSizePolicy, QProgressBar, QDateEdit)
from PyQt6.QtCore import Qt, QRectF, QPointF, QThread, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QFont, QPalette
import random
import math
from datetime import datetime, timedelta

# Import the new graph widget
from .analytics_dialog_components.time_series_graph_widget import TimeSeriesLineGraphWidget
from desktop.services.main_api_service import APIService
from .result_table_components.car_listing_widget import CarListingWidget
from desktop.GLOBAL import GLOBAL
from desktop.services.cargurus_api_service import CargurusAPIService

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
        
        # Date range for trends tab
        self.trends_start_date = QDate.currentDate().addYears(-1)
        self.trends_end_date = QDate.currentDate()
        
        # Error notification state
        self.last_error_message = None
        self.error_shown = False
        
        # Hot deals state management
        self.ml_worker = None
        self.hot_deals_widget = None
        self.hot_deals_loaded = False
        self.hot_deals_cache = None
        self.cache_timer = QTimer()
        self.cache_timer.timeout.connect(self._clear_hot_deals_cache)
        
        # Price trends state management
        self.trends_worker = None
        self.trends_widget = None
        self.trends_loaded = False
        
        self._load_tracked_filters_from_api()
        self._load_analytics_styles()
        self._create_ui()
        
    def closeEvent(self, event):
        """Clean up resources when dialog is closed."""
        # Stop and cleanup ML worker
        if self.ml_worker and self.ml_worker.isRunning():
            self.ml_worker.terminate()
            self.ml_worker.wait()
            
        # Stop and cleanup trends worker
        if self.trends_worker and self.trends_worker.isRunning():
            self.trends_worker.terminate()
            self.trends_worker.wait()
            
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
        
        # Reset trends loading state
        self.trends_loaded = False
        if self.trends_worker and self.trends_worker.isRunning():
            self.trends_worker.terminate()
            self.trends_worker.wait()
        
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
        current_time = datetime.now()
        
        for i in range(num_points):
            # Calculate timestamp for each point (going backwards in time)
            days_ago = (num_points - 1 - i) * 7  # Weekly intervals going backwards
            timestamp_date = current_time - timedelta(days=days_ago)
            timestamp = int(timestamp_date.timestamp() * 1000)  # Convert to milliseconds
            
            data.append((i, current_price, timestamp))
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
        # Store reference to the widget for updating
        self.trends_widget = QWidget()
        layout = QVBoxLayout(self.trends_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header with refresh button
        header_layout = QHBoxLayout()
        header_label = QLabel("📈 Price Trends Analysis")
        header_label.setObjectName("section_title")
        header_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Start Date
        start_label = QLabel("From:")
        start_label.setObjectName("date_label")
        header_layout.addWidget(start_label)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setObjectName("date_picker")
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(self.trends_start_date)
        self.start_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.start_date_edit.setMinimumWidth(120)
        self._configure_calendar_widget(self.start_date_edit)
        header_layout.addWidget(self.start_date_edit)

        # End Date
        end_label = QLabel("To:")
        end_label.setObjectName("date_label")
        header_layout.addWidget(end_label)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setObjectName("date_picker")
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(self.trends_end_date)
        self.end_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.end_date_edit.setMinimumWidth(120)
        self._configure_calendar_widget(self.end_date_edit)
        header_layout.addWidget(self.end_date_edit)

        # Preset buttons
        preset_layout = QHBoxLayout()
        
        last_month_btn = QPushButton("1M")
        last_month_btn.setObjectName("preset_button")
        last_month_btn.setToolTip("Last 30 days")
        last_month_btn.clicked.connect(lambda: self._set_preset_range(30))
        preset_layout.addWidget(last_month_btn)
        
        last_3_months_btn = QPushButton("3M")
        last_3_months_btn.setObjectName("preset_button")
        last_3_months_btn.setToolTip("Last 3 months")
        last_3_months_btn.clicked.connect(lambda: self._set_preset_range(90))
        preset_layout.addWidget(last_3_months_btn)
        
        last_6_months_btn = QPushButton("6M")
        last_6_months_btn.setObjectName("preset_button")
        last_6_months_btn.setToolTip("Last 6 months")
        last_6_months_btn.clicked.connect(lambda: self._set_preset_range(180))
        preset_layout.addWidget(last_6_months_btn)
        
        last_year_btn = QPushButton("1Y")
        last_year_btn.setObjectName("preset_button")
        last_year_btn.setToolTip("Last year")
        last_year_btn.clicked.connect(lambda: self._set_preset_range(365))
        preset_layout.addWidget(last_year_btn)
        

            
        header_layout.addLayout(preset_layout)
        
        # Apply button
        apply_button = QPushButton("Apply")
        apply_button.setObjectName("action_button")
        apply_button.clicked.connect(self._apply_date_range)
        header_layout.addWidget(apply_button)
        
        # Refresh button
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.setObjectName("small_button")
        refresh_button.clicked.connect(self._refresh_price_trends)
        refresh_button.setToolTip("Refresh price trends data")
        header_layout.addWidget(refresh_button)
        
        layout.addLayout(header_layout)
        
        # Content container that we'll replace based on state
        self.trends_content = QWidget()
        self.trends_content_layout = QVBoxLayout(self.trends_content)
        self.trends_content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.trends_content)
        
        # Load initial content
        self._load_price_trends_content()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidget(self.trends_widget)

        return scroll_area

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
        
    def _load_price_trends_content(self):
        """Load the appropriate content for price trends tab based on state."""
        # Clear existing content
        while self.trends_content_layout.count():
            child = self.trends_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Check if no tracked filters
        if not self.tracked_models_criteria:
            self._show_trends_empty_state()
            return
            
        # Check if already loading
        if self.trends_worker and self.trends_worker.isRunning():
            return  # Already loading
            
        # Start loading from API
        self._show_trends_loading_state()
        self._start_trends_loading()
        
    def _show_trends_empty_state(self):
        """Show empty state when no tracked filters."""
        empty_widget = EmptyStateWidget(
            "No price trends available",
            "Add tracked filters to see price trend analysis over time."
        )
        self.trends_content_layout.addWidget(empty_widget)
        
    def _show_trends_loading_state(self):
        """Show loading indicator while fetching trends data."""
        loading_widget = QWidget()
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.setSpacing(15)
        
        # Loading indicator
        loading_label = QLabel("📈 Loading price trends...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setFont(QFont("Segoe UI", 14))
        loading_layout.addWidget(loading_label)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate
        progress_bar.setMaximumWidth(300)
        loading_layout.addWidget(progress_bar)
        
        loading_text = QLabel("Fetching CarGurus data and generating trend graphs for your tracked filters...")
        loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_text.setWordWrap(True)
        loading_text.setObjectName("empty_state_action")
        loading_layout.addWidget(loading_text)
        
        self.trends_content_layout.addWidget(loading_widget)
        
    def _show_trends_error_state(self, error_message):
        """Show error state with retry option."""
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_layout.setSpacing(15)
        
        # Error icon and message
        error_label = QLabel("❌ Failed to load price trends")
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
        retry_button.clicked.connect(self._refresh_price_trends)
        retry_button.setMaximumWidth(150)
        error_layout.addWidget(retry_button)
        
        self.trends_content_layout.addWidget(error_widget)
        
    def _display_trends_graphs(self, graphs_data):
        """Display the loaded trend graphs."""
        for i, graph_data in enumerate(graphs_data):
            graph_widget = TimeSeriesLineGraphWidget(graph_data['data'], graph_data['title'])
            self.trends_content_layout.addWidget(graph_widget)
            
            # Stagger the animation start for a cascading effect
            def start_delayed_animation(widget, delay_ms, index):
                def trigger():
                    print(f"[Analytics] Starting animation for graph {index} with delay {delay_ms}ms")
                    widget.startDrawingAnimation()
                # Use QTimer to delay animation start
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(delay_ms, trigger)
            
            # Start animations with 400ms delays between each graph
            start_delayed_animation(graph_widget, i * 400, i)
        
        # Add stretch
        self.trends_content_layout.addStretch(1)
        
    def _start_trends_loading(self):
        """Start the trends worker thread to load graph data."""
        start_date_ts = int(datetime(self.trends_start_date.year(), self.trends_start_date.month(), self.trends_start_date.day()).timestamp() * 1000)
        end_date_ts = int(datetime(self.trends_end_date.year(), self.trends_end_date.month(), self.trends_end_date.day(), 23, 59, 59).timestamp() * 1000)
        
        self.trends_worker = TrendsDataWorker(self.tracked_models_criteria, start_date_ts, end_date_ts)
        self.trends_worker.finished.connect(self._on_trends_loaded)
        self.trends_worker.error.connect(self._on_trends_error)
        self.trends_worker.start()
        
    def _on_trends_loaded(self, graphs_data):
        """Handle successful trends loading."""
        try:
            self.trends_loaded = True
            
            # Clear existing content
            while self.trends_content_layout.count():
                child = self.trends_content_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Display graphs
            self._display_trends_graphs(graphs_data)
            
            print(f"[AnalyticsDialog] Loaded {len(graphs_data)} trend graphs")
            
        except Exception as e:
            print(f"[AnalyticsDialog] Error processing trends data: {e}")
            self._on_trends_error(f"Error processing data: {str(e)}")
            
    def _on_trends_error(self, error_message):
        """Handle trends loading error."""
        print(f"[AnalyticsDialog] Trends loading error: {error_message}")
        
        # Clear existing content
        while self.trends_content_layout.count():
            child = self.trends_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Show error state
        self._show_trends_error_state(error_message)
        
    def _refresh_price_trends(self):
        """Manually refresh price trends data."""
        print("[AnalyticsDialog] Manual price trends refresh triggered")
        self.trends_loaded = False
        if self.trends_worker and self.trends_worker.isRunning():
            self.trends_worker.terminate()
            self.trends_worker.wait()
        self._load_price_trends_content()

    def _load_analytics_styles(self):
        """Load external analytics stylesheet."""
        try:
            import os
            style_path = os.path.join(os.path.dirname(__file__), "..", "themes", "analytics_styles.qss")
            
            with open(style_path, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
                print("[AnalyticsDialog] Loaded analytics styles successfully")
        except Exception as e:
            print(f"[AnalyticsDialog] Failed to load analytics styles: {e}")
    
    def _configure_calendar_widget(self, date_edit):
        """Configure calendar widget properties."""
        calendar = date_edit.calendarWidget()
        if calendar:
            calendar.setMinimumSize(380, 320)
            calendar.setGridVisible(True)
            calendar.setVerticalHeaderFormat(calendar.VerticalHeaderFormat.NoVerticalHeader)
            calendar.setHorizontalHeaderFormat(calendar.HorizontalHeaderFormat.ShortDayNames)
            calendar.setNavigationBarVisible(True)
            calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
            
    def _apply_date_range(self):
        """Apply the selected date range and refresh the trends tab."""
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        
        # Clear any previous error styling
        self._clear_date_validation_errors()
        
        if start_date >= end_date:
            # Show validation error
            self._show_date_validation_error("Start date must be before end date")
            return
            
        # Check if date range is too large (more than 5 years)
        if start_date.daysTo(end_date) > 1825:  # 5 years
            self._show_date_validation_error("Date range cannot exceed 5 years")
            return
            
        # Check if dates are too far in the future
        if end_date > QDate.currentDate():
            self._show_date_validation_error("End date cannot be in the future")
            return
            
        self.trends_start_date = start_date
        self.trends_end_date = end_date
        
        print(f"[AnalyticsDialog] Applying new date range: {self.trends_start_date.toString('yyyy-MM-dd')} to {self.trends_end_date.toString('yyyy-MM-dd')}")
        self._refresh_price_trends()
        
    def _show_date_validation_error(self, message):
        """Show date validation error styling and user notification."""
        # Prevent duplicate error notifications
        if self.error_shown and self.last_error_message == message:
            return
            
        error_style = """
        QDateEdit {
            background-color: #4A2B2B;
            border: 2px solid #E74C3C;
            border-radius: 6px;
            padding: 6px 10px;
            color: #E0E0E0;
            font-size: 11px;
            font-weight: 500;
        }
        """
        
        # Apply error styling to both date edits
        self.start_date_edit.setStyleSheet(error_style)
        self.end_date_edit.setStyleSheet(error_style)
        
        # Show tooltip with error message
        self.start_date_edit.setToolTip(message)
        self.end_date_edit.setToolTip(message)
        
        # Show user-friendly notification
        self._show_date_error_notification(message)
        
        # Track error state
        self.last_error_message = message
        self.error_shown = True
        
        print(f"[AnalyticsDialog] Date validation error: {message}")
    
    def _show_date_error_notification(self, message):
        """Show a temporary notification to the user about date validation error."""
        # Import required modules
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore import QTimer
        
        # Create error notification label
        if not hasattr(self, 'error_notification'):
            self.error_notification = QLabel()
            self.error_notification.setObjectName("date_error_notification")
            self.error_notification.setWordWrap(True)
            
            # Find the main trends widget layout to insert the error notification
            trends_widget_layout = self.trends_widget.layout()
            if trends_widget_layout:
                trends_widget_layout.insertWidget(1, self.error_notification)  # Insert after header
        
        # Set error message and show
        self.error_notification.setText(f"⚠️ {message}")
        self.error_notification.show()
        
        # Auto-hide after 4 seconds
        if not hasattr(self, 'error_timer'):
            self.error_timer = QTimer()
            self.error_timer.setSingleShot(True)
            self.error_timer.timeout.connect(self._hide_date_error_notification)
        
        self.error_timer.start(4000)  # 4 seconds
    
    def _hide_date_error_notification(self):
        """Hide the date error notification."""
        if hasattr(self, 'error_notification'):
            self.error_notification.hide()
        
        # Reset error state when hiding notification
        self.error_shown = False
        
    def _clear_date_validation_errors(self):
        """Clear date validation error styling."""
        # Clear inline styles to restore QSS styles
        self.start_date_edit.setStyleSheet("")
        self.end_date_edit.setStyleSheet("")
        
        # Clear tooltips
        self.start_date_edit.setToolTip("")
        self.end_date_edit.setToolTip("")
        
        # Hide error notification
        self._hide_date_error_notification()
        
        # Reset error state
        self.last_error_message = None
        self.error_shown = False
        
    def _set_preset_range(self, days):
        """Set date range to a preset number of days from today."""
        end_date = QDate.currentDate()
        start_date = end_date.addDays(-days)
        
        self.start_date_edit.setDate(start_date)
        self.end_date_edit.setDate(end_date)
        
        # Automatically apply the preset range
        self._apply_date_range()

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

# Worker thread for loading trends data
class TrendsDataWorker(QThread):
    """Worker thread for loading price trends data from CarGurus API"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, tracked_criteria, start_date, end_date):
        super().__init__()
        self.tracked_criteria = tracked_criteria
        self.start_date = start_date
        self.end_date = end_date
        
    def run(self):
        """Fetch and process data for all tracked models."""
        cargurus_api_service = CargurusAPIService()
        graphs_data = []

        try:
            # First, get the general CarGurus data which contains all brand/model mappings
            general_data = cargurus_api_service.get_cargurus_data_sync(entity_ids=[])
            if not general_data:
                self.error.emit("Could not load initial data from CarGurus.")
                return

            for criteria in self.tracked_criteria:
                label_name = criteria.get('brand') or criteria.get('model')
                if not label_name:
                    continue

                # Find the entity_id for the current brand/model
                entity_id = cargurus_api_service.get_entity_id_by_label(label_name, general_data)

                # Fallback: if not found in general data, query server DB
                if not entity_id:
                    server_data = cargurus_api_service.get_label_from_server(label_name)
                    if server_data and isinstance(server_data, list) and server_data:
                        entity_id = server_data[0].get('entity_id')

                if not entity_id:
                    print(f"Could not find entity_id for {label_name}")
                    # Create a mock graph with an error message
                    mock_graph_data = self._generate_mock_time_series()
                    graphs_data.append({
                        "title": f"{label_name} (Not Found)",
                        "data": mock_graph_data
                    })
                    continue

                # Fetch detailed price data for this entity
                if isinstance(self.start_date, QDate):
                    start_timestamp = int(self.start_date.toPyDateTime().timestamp() * 1000)
                else:
                    start_timestamp = self.start_date

                if isinstance(self.end_date, QDate):
                    end_timestamp = int(self.end_date.toPyDateTime().timestamp() * 1000)
                else:
                    end_timestamp = self.end_date

                specific_data = cargurus_api_service.get_cargurus_data_sync(
                    entity_ids=[entity_id],
                    start_date=start_timestamp,
                    end_date=end_timestamp
                )
                
                if specific_data:
                    graph_data = cargurus_api_service.format_price_trends_for_graph(specific_data)
                    graphs_data.append({
                        "title": label_name,
                        "data": graph_data
                    })
                else:
                    # Handle case where specific data fails
                    mock_graph_data = self._generate_mock_time_series()
                    graphs_data.append({
                        "title": f"{label_name} (Data Error)",
                        "data": mock_graph_data
                    })
            
            self.finished.emit(graphs_data)
        except Exception as e:
            self.error.emit(f"An unexpected error occurred: {e}")
    
    def _generate_mock_time_series(self, num_points=10, base_price=30000, volatility=5000):
        """Generate mock time series data for fallback"""
        import random
        from datetime import datetime, timedelta
        
        data = []
        current_price = base_price + random.uniform(-volatility/2, volatility/2)
        current_time = datetime.now()
        
        for i in range(num_points):
            # Calculate timestamp for each point (going backwards in time)
            days_ago = (num_points - 1 - i) * 7  # Weekly intervals going backwards
            timestamp_date = current_time - timedelta(days=days_ago)
            timestamp = int(timestamp_date.timestamp() * 1000)  # Convert to milliseconds
            
            data.append((i, current_price, timestamp))
            current_price += random.uniform(-volatility * 0.3, volatility * 0.3)
            current_price = max(5000, current_price)  # Ensure price doesn't go too low
        return data

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