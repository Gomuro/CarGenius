from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, 
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QRectF, QPointF
import random
import math

# Import the new graph widget
from .analytics_dialog_components.time_series_graph_widget import TimeSeriesLineGraphWidget

class AnalyticsDialog(QDialog):
    def __init__(self, tracked_models_criteria, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Car Analytics & Price Trends")
        self.setMinimumSize(800, 600)
        self.tracked_models_criteria = tracked_models_criteria
        self._create_ui()

    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.average_prices_tab_content = self._create_average_prices_tab()
        self.tab_widget.addTab(self.average_prices_tab_content, "Price Trends") # Renamed tab for clarity

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

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # Sample tracked models for testing the dialog directly
    sample_tracked = [
        {"brand": "Toyota", "model": "Camry", "year": "2021"},
        {"brand": "Honda", "model": "CR-V", "year": "2022"},
        {"brand": "BMW", "model": "X5"}, # Year might be None
    ]
    dialog = AnalyticsDialog(sample_tracked)
    dialog.show()
    sys.exit(app.exec()) 