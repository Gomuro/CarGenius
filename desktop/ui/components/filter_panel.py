from PyQt6.QtWidgets import (QLineEdit, QComboBox, 
                           QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QPushButton, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from . import BaseComponent

class FilterPanel(BaseComponent):
    def _create_ui(self):
        # Main container layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Content area
        content = QFrame()
        content.setObjectName("filter_content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 15, 20, 15)
        content_layout.setSpacing(15)
        
        # Filter section frame with background - make it darker
        filter_frame = QFrame()
        filter_frame.setObjectName("dark_filter_frame")
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(15)
        
        # Create filter grid with precisely 4 columns of equal width
        filter_grid = QGridLayout()
        filter_grid.setHorizontalSpacing(20)  # Increased spacing between columns
        filter_grid.setVerticalSpacing(12)    # Increased spacing between rows
        filter_grid.setContentsMargins(0, 0, 0, 0)
        
        # Create filter headers - First row
        headers = ["Brand", "Model", "Registration date", "Kilometers up to"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setObjectName("filter_header_light")
            filter_grid.addWidget(label, 0, col)
        
        # Create filter inputs - Second row
        self.brand_input = QComboBox()
        self.brand_input.setObjectName("dark_filter_input")
        self.brand_input.addItems(["Any Brand", "Audi", "BMW", "Mercedes", "Tesla", "Toyota", "Volkswagen"])
        
        self.model_input = QComboBox()
        self.model_input.setObjectName("dark_filter_input")
        self.model_input.addItems(["Any Model"])
        
        self.reg_date = QComboBox()
        self.reg_date.setObjectName("dark_filter_input")
        self.reg_date.addItems(["Any year", "2023", "2022", "2021", "2020", "2019", "2018"])
        
        self.mileage = QComboBox()
        self.mileage.setObjectName("dark_filter_input")
        self.mileage.addItems(["Any mileage", "10,000 km", "25,000 km", "50,000 km", "100,000 km"])
        
        # Set uniform heights for all filter inputs
        uniform_height = 38  # Slightly reduced height
        self.brand_input.setFixedHeight(uniform_height)
        self.model_input.setFixedHeight(uniform_height)
        self.reg_date.setFixedHeight(uniform_height)
        self.mileage.setFixedHeight(uniform_height)
        
        # Add to grid
        filter_grid.addWidget(self.brand_input, 1, 0)
        filter_grid.addWidget(self.model_input, 1, 1)
        filter_grid.addWidget(self.reg_date, 1, 2)
        filter_grid.addWidget(self.mileage, 1, 3)
        
        # Create second row of headers
        headers_row2 = ["City or postal code", "Color", "Price up to", ""]
        for col, header in enumerate(headers_row2):
            label = QLabel(header)
            label.setObjectName("filter_header_light")
            filter_grid.addWidget(label, 2, col)
        
        # Create second row of inputs
        self.location = QLineEdit()
        self.location.setObjectName("dark_filter_input")
        self.location.setPlaceholderText("Enter location")
        self.location.setFixedHeight(uniform_height)
        
        # Color selection combo box
        self.color_combo = QComboBox()
        self.color_combo.setObjectName("dark_filter_input")
        self.color_combo.addItems(["Any color", "White", "Black", "Silver", "Red", "Blue", "Gray"])
        self.color_combo.setFixedHeight(uniform_height)
        
        self.price = QComboBox()
        self.price.setObjectName("dark_filter_input")
        self.price.addItems(["Any price", "€10,000", "€20,000", "€30,000", "€50,000", "€100,000"])
        self.price.setFixedHeight(uniform_height)
        
        self.search_btn = QPushButton("165 178 listings")
        self.search_btn.setObjectName("search_button_red")
        self.search_btn.setFixedHeight(uniform_height)
        
        # Add to grid
        filter_grid.addWidget(self.location, 3, 0)
        filter_grid.addWidget(self.color_combo, 3, 1)
        filter_grid.addWidget(self.price, 3, 2)
        filter_grid.addWidget(self.search_btn, 3, 3)
        
        # Make columns stretch equally
        for i in range(4):
            filter_grid.setColumnStretch(i, 1)
        
        filter_layout.addLayout(filter_grid)
        
        # Bottom row for checkbox options
        options_row = QHBoxLayout()
        options_row.setSpacing(15)
        options_row.setContentsMargins(0, 5, 0, 0)
        
        # Create bottom row buttons with appropriate styles
        electric_btn = QPushButton("Electric vehicles only")
        electric_btn.setObjectName("dark_filter_option")
        electric_btn.setCheckable(True)
        electric_btn.setFixedHeight(32)
        options_row.addWidget(electric_btn)
        
        online_btn = QPushButton("Online purchase")
        online_btn.setObjectName("dark_filter_option")
        online_btn.setCheckable(True)
        online_btn.setFixedHeight(32)
        options_row.addWidget(online_btn)
        
        additional_btn = QPushButton("Additional filters")
        additional_btn.setObjectName("dark_text_button")
        additional_btn.setFixedHeight(32)
        options_row.addWidget(additional_btn)
        
        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("dark_text_button")
        reset_btn.setFixedHeight(32)
        options_row.addWidget(reset_btn)
        
        options_row.addStretch()
        filter_layout.addLayout(options_row)
        
        # Add filter frame to content layout
        content_layout.addWidget(filter_frame)
        
        # Add spacing at the bottom to ensure the filter panel is properly spaced
        content_layout.addStretch(1)
        
        main_layout.addWidget(content, 1) 