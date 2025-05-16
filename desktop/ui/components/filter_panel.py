from PyQt6.QtWidgets import (QLineEdit, QComboBox, 
                           QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QPushButton, QFrame, QToolButton)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from . import BaseComponent

class FilterPanel(BaseComponent):
    def _create_ui(self):
        # Main container layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left sidebar with vehicle icons
        sidebar = QFrame()
        sidebar.setObjectName("vehicle_sidebar")
        sidebar.setFixedWidth(60)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(16)
        sidebar_layout.setContentsMargins(5, 20, 5, 10)
        
        car_icon = self._create_vehicle_button("🚗", "Cars", True)
        moto_icon = self._create_vehicle_button("🏍️", "Motorcycles")
        bike_icon = self._create_vehicle_button("🚲", "Bicycles")
        van_icon = self._create_vehicle_button("🚐", "Vans")
        truck_icon = self._create_vehicle_button("🚚", "Trucks")
        
        sidebar_layout.addWidget(car_icon)
        sidebar_layout.addWidget(moto_icon)
        sidebar_layout.addWidget(bike_icon)
        sidebar_layout.addWidget(van_icon)
        sidebar_layout.addWidget(truck_icon)
        sidebar_layout.addStretch()
        
        main_layout.addWidget(sidebar)
        
        # Right content area
        content = QFrame()
        content.setObjectName("filter_content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 15, 20, 15)
        content_layout.setSpacing(15)
        
        # Filter section frame with background
        filter_frame = QFrame()
        filter_frame.setObjectName("filter_frame")
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
            label.setObjectName("filter_header")
            filter_grid.addWidget(label, 0, col)
        
        # Create filter inputs - Second row
        self.brand_input = QComboBox()
        self.brand_input.setObjectName("filter_input")
        self.brand_input.addItems(["Any Brand", "Audi", "BMW", "Mercedes", "Tesla", "Toyota", "Volkswagen"])
        
        self.model_input = QComboBox()
        self.model_input.setObjectName("filter_input")
        self.model_input.addItems(["Any Model"])
        
        self.reg_date = QComboBox()
        self.reg_date.setObjectName("filter_input")
        self.reg_date.addItems(["Any year", "2023", "2022", "2021", "2020", "2019", "2018"])
        
        self.mileage = QComboBox()
        self.mileage.setObjectName("filter_input")
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
        headers_row2 = ["City or postal code", "Payment method", "Price up to", ""]
        for col, header in enumerate(headers_row2):
            label = QLabel(header)
            label.setObjectName("filter_header")
            filter_grid.addWidget(label, 2, col)
        
        # Create second row of inputs
        self.location = QLineEdit()
        self.location.setObjectName("filter_input")
        self.location.setPlaceholderText("Enter location")
        self.location.setFixedHeight(uniform_height)
        
        # Payment method buttons
        payment_frame = QFrame()
        payment_frame.setObjectName("payment_method_frame")
        payment_frame.setFixedHeight(uniform_height)
        payment_layout = QHBoxLayout(payment_frame)
        payment_layout.setContentsMargins(0, 0, 0, 0)
        payment_layout.setSpacing(0)
        
        self.buy_button = QPushButton("Buy")
        self.buy_button.setObjectName("payment_option_selected")
        self.buy_button.setCheckable(True)
        self.buy_button.setChecked(True)
        
        self.rent_button = QPushButton("Rent")
        self.rent_button.setObjectName("payment_option")
        self.rent_button.setCheckable(True)
        
        payment_layout.addWidget(self.buy_button)
        payment_layout.addWidget(self.rent_button)
        
        self.price = QComboBox()
        self.price.setObjectName("filter_input")
        self.price.addItems(["Any price", "€10,000", "€20,000", "€30,000", "€50,000", "€100,000"])
        self.price.setFixedHeight(uniform_height)
        
        self.search_btn = QPushButton("165 178 listings")
        self.search_btn.setObjectName("search_button")
        self.search_btn.setFixedHeight(uniform_height)
        
        # Add to grid
        filter_grid.addWidget(self.location, 3, 0)
        filter_grid.addWidget(payment_frame, 3, 1)
        filter_grid.addWidget(self.price, 3, 2)
        filter_grid.addWidget(self.search_btn, 3, 3)
        
        # Make columns stretch equally
        for i in range(4):
            filter_grid.setColumnStretch(i, 1)
        
        filter_layout.addLayout(filter_grid)
        
        # Bottom row for checkbox options - make them the same size too
        options_row = QHBoxLayout()
        options_row.setSpacing(15)
        options_row.setContentsMargins(0, 5, 0, 0)
        
        option_buttons = [
            ("Electric vehicles only", "filter_option", True),
            ("Online purchase", "filter_option", True),
            ("Additional filters", "text_button", False),
            ("Reset", "text_button", False)
        ]
        
        for text, obj_name, checkable in option_buttons:
            btn = QPushButton(text)
            btn.setObjectName(obj_name)
            if checkable:
                btn.setCheckable(True)
            btn.setFixedHeight(32)  # Uniform height for option buttons
            options_row.addWidget(btn)
        
        options_row.addStretch()
        filter_layout.addLayout(options_row)
        
        # Add filter frame to content layout
        content_layout.addWidget(filter_frame)
        
        # Add spacing at the bottom to ensure the filter panel is properly spaced
        content_layout.addStretch(1)
        
        main_layout.addWidget(content, 1)

    def _create_vehicle_button(self, icon, tooltip, selected=False):
        btn = QToolButton()
        btn.setObjectName("vehicle_button" if not selected else "vehicle_button_selected")
        btn.setToolTip(tooltip)
        btn.setText(icon)
        btn.setFixedSize(QSize(45, 45))  # Uniform size for vehicle buttons
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        return btn 