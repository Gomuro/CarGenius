from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, 
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
import random # For mock data

class AnalyticsDialog(QDialog):
    def __init__(self, tracked_models_criteria, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Car Analytics")
        self.setMinimumSize(800, 600) # Set a default size
        self.tracked_models_criteria = tracked_models_criteria # Store the passed criteria

        self._create_ui()

    def _create_ui(self):
        main_layout = QVBoxLayout(self)

        # Tab Widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create and add the 'Average Prices' tab
        self.average_prices_tab = self._create_average_prices_tab()
        self.tab_widget.addTab(self.average_prices_tab, "Average Prices")

        # Add more tabs here in the future if needed
        # self.price_trends_tab = self._create_price_trends_tab()
        # self.tab_widget.addTab(self.price_trends_tab, "Price Trends")

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept) # self.accept() closes the dialog
        main_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

    def _create_average_prices_tab(self):
        tab_content_widget = QWidget()
        layout = QVBoxLayout(tab_content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        if not self.tracked_models_criteria:
            # Display a message if no models are being tracked
            info_label = QLabel("No models are currently being tracked. "
                                "Please add models to track from the main page filters.")
            info_label.setObjectName("info_label_analytics") # For potential styling
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
        else:
            # Create a table to display average prices for tracked models
            self.avg_prices_table = QTableWidget()
            self.avg_prices_table.setObjectName("analytics_table") # For styling
            # Define columns: Brand, Model, Year, Estimated Avg. Price
            column_headers = ["Brand", "Model", "Year", "Est. Avg. Price"]
            self.avg_prices_table.setColumnCount(len(column_headers))
            self.avg_prices_table.setHorizontalHeaderLabels(column_headers)
            self.avg_prices_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Read-only
            self.avg_prices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.avg_prices_table.setAlternatingRowColors(True)
            self.avg_prices_table.verticalHeader().setVisible(False) # Hide vertical row numbers

            # Populate table with tracked models and mock prices
            self.avg_prices_table.setRowCount(len(self.tracked_models_criteria))
            for row, criteria in enumerate(self.tracked_models_criteria):
                brand = criteria.get("brand", "N/A")
                model = criteria.get("model", "N/A")
                year = criteria.get("year", "N/A")
                
                # Mock estimated average price
                mock_price = f"€ {random.randint(10000, 80000):,}"

                self.avg_prices_table.setItem(row, 0, QTableWidgetItem(brand))
                self.avg_prices_table.setItem(row, 1, QTableWidgetItem(model))
                self.avg_prices_table.setItem(row, 2, QTableWidgetItem(year))
                self.avg_prices_table.setItem(row, 3, QTableWidgetItem(mock_price))
            
            # Adjust column widths
            header = self.avg_prices_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Stretch all columns initially
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Resize price column to contents

            layout.addWidget(self.avg_prices_table)
        
        layout.addStretch() # Pushes content to the top if table is small
        return tab_content_widget

    # Example for a future tab
    # def _create_price_trends_tab(self):
    #     widget = QWidget()
    #     layout = QVBoxLayout(widget)
    #     label = QLabel("Price Trends content will go here.")
    #     layout.addWidget(label)
    #     return widget

if __name__ == '__main__':
    # This is for testing the dialog directly
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = AnalyticsDialog([{"brand": "Toyota", "model": "Corolla", "year": "2020"}, {"brand": "Honda", "model": "Civic", "year": "2021"}])
    dialog.show()
    sys.exit(app.exec()) 