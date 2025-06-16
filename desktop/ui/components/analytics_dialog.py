from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, 
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QRectF, QPointF
import random
import math

# Import the new graph widget
from .analytics_dialog_components.time_series_graph_widget import TimeSeriesLineGraphWidget
from desktop.services.main_api_service import APIService
from .result_table_components.car_listing_widget import CarListingWidget

class AnalyticsDialog(QDialog):
    def __init__(self, tracked_models_criteria, api_service: APIService, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Car Analytics & Price Trends")
        self.setMinimumSize(800, 600)
        self.tracked_models_criteria = tracked_models_criteria
        self.api_service = api_service
        self._create_ui()

    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.average_prices_tab_content = self._create_average_prices_tab()
        self.price_trends_tab_content = self._create_price_trends_tab()
        self.profitable_offers_tab_content = self._create_profitable_offers_tab()

        self.tab_widget.addTab(self.average_prices_tab_content, "Average Prices")
        self.tab_widget.addTab(self.price_trends_tab_content, "Price Trends")
        self.tab_widget.addTab(self.profitable_offers_tab_content, "Profitable Offers")

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

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

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Tracked Filters", "Avg Price", "Min Price", "Max Price", "Count", "Status"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        if not self.tracked_models_criteria:
            # Show message when no filters are tracked
            table.setRowCount(1)
            item = QTableWidgetItem("No tracked filters. Use the main page to add filters and track specific models.")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setSpan(0, 0, 1, 6)
            table.setItem(0, 0, item)
        else:
            # Show statistics for each tracked criteria
            table.setRowCount(len(self.tracked_models_criteria))
            
            for i, criteria in enumerate(self.tracked_models_criteria):
                # Create filter display text
                filter_parts = {}
                if criteria.get('price_from') and criteria.get('price_from') != None:
                    filter_parts['price_from'] = criteria.get('price_from')
                if criteria.get('price_to') and criteria.get('price_to') != None:
                    filter_parts['price_to'] = criteria.get('price_to')
                if criteria.get('brand') and criteria.get('brand') != None:
                    filter_parts['brand'] = criteria.get('brand')
                if criteria.get('model') and criteria.get('model') != None:
                    filter_parts['model'] = criteria.get('model')
                if criteria.get('year') and criteria.get('year') != None:
                    filter_parts['year'] = int(criteria.get('year'))
                
                filter_text = " | ".join(filter_parts) if filter_parts else "No filters"
                
                table.setItem(i, 0, QTableWidgetItem(filter_text))

                # Fetch statistics for this criteria
                try:
                    response = self.api_service.search_listings_sync(filter_parts)
                    if response and "Stats" in response:
                        stats = response["Stats"]
                        table.setItem(i, 1, QTableWidgetItem(f"{stats.get('avg_price', 0):,.2f} "))
                        table.setItem(i, 2, QTableWidgetItem(f"{stats.get('min_price', 0):,.2f} "))
                        table.setItem(i, 3, QTableWidgetItem(f"{stats.get('max_price', 0):,.2f} "))
                        table.setItem(i, 4, QTableWidgetItem(str(stats.get('count', 0))))
                        table.setItem(i, 5, QTableWidgetItem("✓ Data loaded"))
                    else:
                        table.setItem(i, 1, QTableWidgetItem("Error"))
                        table.setItem(i, 2, QTableWidgetItem("Error"))
                        table.setItem(i, 3, QTableWidgetItem("Error"))
                        table.setItem(i, 4, QTableWidgetItem("Error"))
                        table.setItem(i, 5, QTableWidgetItem("Error"))
                except Exception as e:
                    # Handle API errors
                    table.setItem(i, 1, QTableWidgetItem("Error"))
                    table.setItem(i, 2, QTableWidgetItem("Error"))
                    table.setItem(i, 3, QTableWidgetItem("Error"))
                    table.setItem(i, 4, QTableWidgetItem("Error"))
                    table.setItem(i, 5, QTableWidgetItem(f"✗ Error: {str(e)[:30]}..."))

        layout.addWidget(table)
        return widget

    def _create_price_trends_tab(self):
        # This tab will now hold a scrollable list of individual graphs
        scroll_widget = QWidget() # Widget to hold the layout of graphs
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(10,10,10,10)
        scroll_layout.setSpacing(20)

        if not self.tracked_models_criteria:
            info_label = QLabel("No models are currently tracked for price trends. "
                                "Add models using the main page filters and 'Track Specific Models' mode.")
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_label.setWordWrap(True)
            scroll_layout.addWidget(info_label)
        else:
            for criteria in self.tracked_models_criteria:
                model_name_parts = []
                if criteria.get("brand") and criteria.get("brand") != "N/A":
                    model_name_parts.append(criteria.get("brand"))
                if criteria.get("model") and criteria.get("model") != "N/A":
                    model_name_parts.append(criteria.get("model"))
                if criteria.get("year") and criteria.get("year") != "N/A":
                    model_name_parts.append(criteria.get("year"))
                model_display_name = " ".join(model_name_parts) if model_name_parts else "Unknown Model"

                # Graph Title (could also be part of the graph widget itself)
                # graph_title_label = QLabel(f"Price Trend: {model_display_name}")
                # graph_title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                # graph_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # scroll_layout.addWidget(graph_title_label)

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
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Mock data for profitable offers
        profitable_cars = [
            {
                "image": "🚗",
                "title": "Audi A6 3.0 TDI Quattro",
                "subtitle": "S-Line • Navi • Matrix LED • TOP DEAL",
                "price": "28,500 €",
                "price_tag": "Below Market",
                "year": "2019",
                "km": "55,000 km",
                "power": "210 kW (286 PS)",
                "fuel": "Diesel",
                "seller": "Premium Cars GmbH",
                "location": "80807 München",
                "margin_rating": 5,
                "margin_text": "Excellent Price",
                "margin_percentage_text": "Potential margin: 22%"
            },
            {
                "image": "🚗",
                "title": "BMW 520d Touring",
                "subtitle": "M Sport • HUD • Panorama • Laserlight",
                "price": "39,900 €",
                "price_tag": "Great Deal",
                "year": "2021",
                "km": "31,200 km",
                "power": "140 kW (190 PS)",
                "fuel": "Diesel",
                "seller": "BMW Niederlassung Hamburg",
                "location": "20537 Hamburg",
                "margin_rating": 5,
                "margin_text": "Very Good Price",
                "margin_percentage_text": "Potential margin: 19%"
            },
            {
                "image": "🚗",
                "title": "VW Golf VIII GTI",
                "subtitle": "Clubsport • DCC • Performance",
                "price": "36,800 €",
                "price_tag": "Hot Offer",
                "year": "2022",
                "km": "9,800 km",
                "power": "221 kW (300 PS)",
                "fuel": "Petrol",
                "seller": "Volkswagen Zentrum Berlin",
                "location": "10115 Berlin",
                "margin_rating": 4,
                "margin_text": "Good Price",
                "margin_percentage_text": "Potential margin: 15%"
            }
        ]

        if not profitable_cars:
            info_label = QLabel("No profitable offers found based on current criteria.")
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(info_label)
        else:
            for car_data in profitable_cars:
                listing_widget = CarListingWidget(car_data)
                layout.addWidget(listing_widget)

        layout.addStretch(1)

        # Create a scroll area to hold the listings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidget(container)

        return scroll_area

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