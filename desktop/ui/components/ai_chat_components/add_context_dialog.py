from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QTabWidget, QWidget, 
                           QLabel, QHBoxLayout, QLineEdit, QListWidget)

class AddContextDialog(QDialog):
    """Dialog for adding different types of context to the AI chat."""

    add_car_context_signal = pyqtSignal(str)  # Pass a car ID or some identifier
    add_filters_context_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Context to Chat")
        self.setMinimumSize(500, 400) # Increased size for better layout

        main_layout = QVBoxLayout(self)
        
        # Tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Statistics Tab
        stats_tab = self._create_search_tab("stats")
        tab_widget.addTab(stats_tab, "Statistical Machines")

        # Auction Tab
        auction_tab = self._create_search_tab("auction")
        tab_widget.addTab(auction_tab, "Auction Machines")

        # Filters Tab
        filters_tab = self._create_search_tab("filters", has_add_button=True)
        tab_widget.addTab(filters_tab, "Filters")
        
    def _create_search_tab(self, search_type: str, has_add_button: bool = False) -> QWidget:
        """Helper method to create a standardized search tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText(f"Search {search_type}...")
        search_button = QPushButton("Search")
        
        search_layout.addWidget(search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        
        # Results list
        results_list = QListWidget()
        layout.addWidget(results_list)

        # Connect search button to a placeholder handler
        search_button.clicked.connect(lambda: self._on_search(search_type, search_input.text()))

        if has_add_button:
            add_filters_btn = QPushButton("Add Current Active Filters")
            add_filters_btn.clicked.connect(self.add_filters_context_signal.emit)
            add_filters_btn.clicked.connect(self.accept)
            layout.addWidget(add_filters_btn)

        return tab_widget

    def _on_search(self, search_type: str, query: str):
        """Placeholder method to handle search button clicks."""
        print(f"UI-only: Searching in '{search_type}' for query: '{query}'")
        # In the future, this will trigger the actual API call. 