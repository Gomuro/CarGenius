from PyQt6.QtWidgets import QComboBox, QLineEdit, QGridLayout, QLabel, QPushButton, QWidget

class FilterInputs(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_search_button_text = "165 178 listings"
        self._create_ui()

    def _create_ui(self):
        layout = QGridLayout(self)
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        headers_row1 = ["Brand", "Model", "Registration date", "Kilometers up to"]
        for col, header in enumerate(headers_row1):
            label = QLabel(header)
            label.setObjectName("filter_header_light")
            layout.addWidget(label, 0, col)

        self.brand_input = QComboBox()
        self.brand_input.setObjectName("dark_filter_input")
        self.brand_input.addItems(["Any Brand", "Audi", "BMW", "Mercedes", "Tesla", "Toyota", "Volkswagen"])
        
        self.model_input = QComboBox()
        self.model_input.setObjectName("dark_filter_input")
        self.model_input.addItems(["Any Model"])
        
        self.reg_date_input = QComboBox() # Renamed to avoid conflict with a potential QDate object
        self.reg_date_input.setObjectName("dark_filter_input")
        self.reg_date_input.addItems(["Any year", "2023", "2022", "2021", "2020", "2019", "2018"])
        
        self.mileage_input = QComboBox() # Renamed for clarity
        self.mileage_input.setObjectName("dark_filter_input")
        self.mileage_input.addItems(["Any mileage", "10,000 km", "25,000 km", "50,000 km", "100,000 km"])
        
        uniform_height = 38
        self.brand_input.setFixedHeight(uniform_height)
        self.model_input.setFixedHeight(uniform_height)
        self.reg_date_input.setFixedHeight(uniform_height)
        self.mileage_input.setFixedHeight(uniform_height)
        
        layout.addWidget(self.brand_input, 1, 0)
        layout.addWidget(self.model_input, 1, 1)
        layout.addWidget(self.reg_date_input, 1, 2)
        layout.addWidget(self.mileage_input, 1, 3)
        
        headers_row2 = ["City or postal code", "Color", "Price up to", ""]
        for col, header in enumerate(headers_row2):
            label = QLabel(header)
            label.setObjectName("filter_header_light")
            layout.addWidget(label, 2, col)
        
        self.location_input = QLineEdit() # Renamed
        self.location_input.setObjectName("dark_filter_input")
        self.location_input.setPlaceholderText("Enter location")
        self.location_input.setFixedHeight(uniform_height)
        
        self.color_input = QComboBox() # Renamed
        self.color_input.setObjectName("dark_filter_input")
        self.color_input.addItems(["Any color", "White", "Black", "Silver", "Red", "Blue", "Gray"])
        self.color_input.setFixedHeight(uniform_height)
        
        self.price_input = QComboBox() # Renamed
        self.price_input.setObjectName("dark_filter_input")
        self.price_input.addItems(["Any price", "€10,000", "€20,000", "€30,000", "€50,000", "€100,000"])
        self.price_input.setFixedHeight(uniform_height)
        
        self.search_button = QPushButton(self.original_search_button_text) # Renamed
        self.search_button.setObjectName("search_button_red")
        self.search_button.setFixedHeight(uniform_height)
        
        layout.addWidget(self.location_input, 3, 0)
        layout.addWidget(self.color_input, 3, 1)
        layout.addWidget(self.price_input, 3, 2)
        layout.addWidget(self.search_button, 3, 3)
        
        for i in range(4):
            layout.setColumnStretch(i, 1)

    def get_criteria(self):
        return {
            "brand": self.brand_input.currentText() if self.brand_input.currentText() != "Any Brand" else None,
            "model": self.model_input.currentText() if self.model_input.currentText() != "Any Model" else None,
            "year": self.reg_date_input.currentText() if self.reg_date_input.currentText() != "Any year" else None,
            "mileage": self.mileage_input.currentText() if self.mileage_input.currentText() != "Any mileage" else None,
            "location": self.location_input.text() if self.location_input.text() else None,
            "color": self.color_input.currentText() if self.color_input.currentText() != "Any color" else None,
            "price": self.price_input.currentText() if self.price_input.currentText() != "Any price" else None,
        }

    def set_search_button_text(self, text):
        self.search_button.setText(text)

    def reset_inputs(self):
        self.brand_input.setCurrentIndex(0)
        self.model_input.setCurrentIndex(0)
        self.reg_date_input.setCurrentIndex(0)
        self.mileage_input.setCurrentIndex(0)
        self.location_input.clear()
        self.color_input.setCurrentIndex(0)
        self.price_input.setCurrentIndex(0)
        self.search_button.setText(self.original_search_button_text)

    # Add methods to connect signals if needed, e.g., search_button.clicked
    # For now, the main panel will connect to this button's clicked signal. 