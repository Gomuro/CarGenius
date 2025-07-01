from PyQt6.QtWidgets import QComboBox, QLineEdit, QGridLayout, QLabel, QPushButton, QWidget
from desktop.services.main_api_service import APIService

class FilterInputs(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_service_instance = APIService()
        self.filter_options = {}  # Store all filter options
        self.original_search_button_text = "Loading..."
        self.is_loading = True
        self.auto_update_button_text = True  # Flag to control automatic button text updates
        
        self._create_ui()  # Create UI first with "Loading..." text
        self._load_filter_options()  # Then load filter options efficiently
        self._setup_cascading_behavior()

    # =============================================================================
    # БЛОК 1: ІНІЦІАЛІЗАЦІЯ ТА ЗАВАНТАЖЕННЯ ДАНИХ
    # =============================================================================
    
    def _load_filter_options(self):
        """Load all available filter options efficiently without loading full dataset"""
        self.is_loading = True
        self._update_loading_state()
        
        try:
            # Get all filter options in one efficient call
            self.filter_options = self.api_service_instance.get_filter_options_sync()
            if self.filter_options:
                # Get total count of listings for button text
                total_brands = len(self.filter_options.get("brands", []))
                total_models = len(self.filter_options.get("models", []))
                self.original_search_button_text = f"Search {total_brands} brands, {total_models} models"
            else:
                self.filter_options = {"brands": [], "models": [], "colors": [], "years": []}
                self.original_search_button_text = "Search listings"
        except Exception as e:
            print(f"Error loading filter options: {e}")
            self.filter_options = {"brands": [], "models": [], "colors": [], "years": []}
            self.original_search_button_text = "Error loading filters"
        finally:
            self.is_loading = False
            self._initialize_filters()
            self._update_loading_state()

    def _update_loading_state(self):
        """Update the loading state of the UI"""
        if self.is_loading:
            self.search_button.setText("Loading...")
            self.search_button.setEnabled(False)
            # Disable all filters during loading
            self._set_filters_enabled(False)
        else:
            self.search_button.setText(self.original_search_button_text)
            self.search_button.setEnabled(True)
            # Enable filters after loading
            self._set_filters_enabled(True)

    def _set_filters_enabled(self, enabled: bool):
        """Enable/disable all filters"""
        self.brand_input.setEnabled(enabled)
        self.model_input.setEnabled(enabled)
        self.reg_date_input.setEnabled(enabled)
        self.mileage_input.setEnabled(enabled)
        self.location_input.setEnabled(enabled)
        self.color_input.setEnabled(enabled)
        self.price_input.setEnabled(enabled)

    # =============================================================================
    # БЛОК 2: СТВОРЕННЯ ІНТЕРФЕЙСУ
    # =============================================================================
    
    def _create_ui(self):
        """Create interface with all elements"""
        layout = QGridLayout(self)
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # Headers and elements of the first row
        self._create_row1_elements(layout)
        # Headers and elements of the second row  
        self._create_row2_elements(layout)
        
        # Don't initialize filters here - this will be done after loading data

    def _create_row1_elements(self, layout):
        """First row: Brand, Model, Year, Mileage"""
        headers = ["Brand", "Model", "Registration date", "Kilometers up to"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setObjectName("filter_header_light")
            layout.addWidget(label, 0, col)

        # Create dropdown lists
        self.brand_input = self._create_combobox()
        self.model_input = self._create_combobox()
        self.reg_date_input = self._create_combobox()
        self.mileage_input = self._create_combobox()
        
        layout.addWidget(self.brand_input, 1, 0)
        layout.addWidget(self.model_input, 1, 1)
        layout.addWidget(self.reg_date_input, 1, 2)
        layout.addWidget(self.mileage_input, 1, 3)

    def _create_row2_elements(self, layout):
        """Second row: Location, Color, Price, Search"""
        headers = ["City or postal code", "Color", "Price up to", ""]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setObjectName("filter_header_light")
            layout.addWidget(label, 2, col)

        # Create elements
        self.location_input = QLineEdit()
        self.location_input.setObjectName("dark_filter_input")
        self.location_input.setPlaceholderText("Enter location")
        self.location_input.setFixedHeight(38)
        
        self.color_input = self._create_combobox()
        
        self.price_input = self._create_combobox()
        self.price_input.addItems(["Any price", "€10,000", "€20,000", "€30,000", "€50,000", "€100,000"])
        
        self.search_button = QPushButton(self.original_search_button_text)
        self.search_button.setObjectName("search_button_red")
        self.search_button.setFixedHeight(38)
        
        layout.addWidget(self.location_input, 3, 0)
        layout.addWidget(self.color_input, 3, 1)
        layout.addWidget(self.price_input, 3, 2)
        layout.addWidget(self.search_button, 3, 3)
        
        # Configure column stretching
        for i in range(4):
            layout.setColumnStretch(i, 1)

    def _create_combobox(self):
        """Create standard combobox"""
        combo = QComboBox()
        combo.setObjectName("dark_filter_input")
        combo.setFixedHeight(38)
        return combo

    # =============================================================================
    # БЛОК 3: КАСКАДНА ЛОГІКА ФІЛЬТРАЦІЇ
    # =============================================================================
    
    def _setup_cascading_behavior(self):
        """Setup cascading behavior of filters"""
        self.brand_input.currentTextChanged.connect(self._on_brand_changed)
        self.model_input.currentTextChanged.connect(self._on_model_changed)
        self.reg_date_input.currentTextChanged.connect(self._on_year_changed)
        # Add updates for other filters
        self.location_input.textChanged.connect(self._update_search_button_count)
        self.price_input.currentTextChanged.connect(self._update_search_button_count)
        self.color_input.currentTextChanged.connect(self._update_search_button_count)
        self.mileage_input.currentTextChanged.connect(self._update_search_button_count)

    def _initialize_filters(self):
        """Initialize all filters after loading data"""
        if not self.is_loading and self.filter_options:
            self._populate_brands()
            self._reset_dependent_filters()

    def _on_brand_changed(self):
        """When brand changes → update models"""
        self._populate_models()
        self._reset_years_and_below()
        self._update_search_button_count()

    def _on_model_changed(self):
        """When model changes → update years"""
        self._populate_years()
        self._reset_colors_and_mileages()
        self._update_search_button_count()

    def _on_year_changed(self):
        """When year changes → update mileage and colors"""
        self._populate_mileages()
        self._populate_colors()
        self._update_search_button_count()

    # =============================================================================
    # БЛОК 4: МЕТОДИ ЗАПОВНЕННЯ ФІЛЬТРІВ
    # =============================================================================
    
    def _populate_brands(self):
        """Populate brands list"""
        brands = self.filter_options.get("brands", [])
        self._populate_dropdown(self.brand_input, brands, "Any Brand")

    def _populate_models(self):
        """Populate models list for selected brand using efficient API call"""
        selected_brand = self.brand_input.currentText()
        try:
            # Use efficient API call to get models for specific brand
            if selected_brand == "Any Brand":
                models = self.filter_options.get("models", [])
            else:
                models = self.api_service_instance.get_models_for_brand_sync(selected_brand)
                if models is None:
                    models = []
            self._populate_dropdown(self.model_input, models, "Any Model")
        except Exception as e:
            print(f"Error loading models for brand {selected_brand}: {e}")
            self._populate_dropdown(self.model_input, [], "Any Model")

    def _populate_years(self):
        """Populate years list"""
        years = self.filter_options.get("years", [])
        years_str = [str(year) for year in years]
        self._populate_dropdown(self.reg_date_input, years_str, "Any Year")

    def _populate_mileages(self):
        """Populate mileage list"""
        # The "> 150,000 km" option is removed as it cannot be supported by the backend API
        mileage_ranges = ["Any Mileage", "< 10,000 km", "< 50,000 km", "< 100,000 km", "< 150,000 km"]
        self.mileage_input.clear()
        self.mileage_input.addItems(mileage_ranges)

    def _populate_colors(self):
        """Populate colors list for current filters using efficient API call"""
        selected_brand = self.brand_input.currentText()
        selected_model = self.model_input.currentText()
        selected_year_text = self.reg_date_input.currentText()
        
        try:
            # Convert year to int if not "Any Year"
            selected_year = None
            if selected_year_text != "Any Year":
                try:
                    selected_year = int(selected_year_text)
                except ValueError:
                    pass
            
            # Use efficient API call to get colors for current filters
            colors = self.api_service_instance.get_colors_for_filters_sync(
                brand=selected_brand if selected_brand != "Any Brand" else None,
                model=selected_model if selected_model != "Any Model" else None,
                registration_year=selected_year
            )
            if colors is None:
                colors = []
            self._populate_dropdown(self.color_input, colors, "Any Color")
        except Exception as e:
            print(f"Error loading colors: {e}")
            self._populate_dropdown(self.color_input, [], "Any Color")

    def _populate_dropdown(self, dropdown, items, default_text):
        """Universal method for populating dropdown list"""
        dropdown.clear()
        dropdown.addItem(default_text)
        if items:
            dropdown.addItems(items)

    def _update_search_button_count(self):
        """Update button text according to current filters"""
        if self.is_loading or not self.auto_update_button_text:
            return  # Don't update during loading or if auto-update is disabled
            
        # For now, just show current filter state since we don't load all data
        criteria = self.get_criteria()
        if criteria:
            filter_count = len([v for v in criteria.values() if v])
            self.search_button.setText(f"Search with {filter_count} filters")
        else:
            self.search_button.setText(self.original_search_button_text)

    # =============================================================================
    # БЛОК 5: МЕТОДИ СКИДАННЯ ФІЛЬТРІВ
    # =============================================================================
    
    def _reset_dependent_filters(self):
        """Reset all dependent filters"""
        self._reset_dropdown(self.model_input, "Any Model")
        self._reset_dropdown(self.reg_date_input, "Any Year")
        self._reset_dropdown(self.mileage_input, "Any Mileage")
        self._reset_dropdown(self.color_input, "Any Color")

    def _reset_years_and_below(self):
        """Reset years and everything below"""
        self._reset_dropdown(self.reg_date_input, "Any Year")
        self._reset_colors_and_mileages()

    def _reset_colors_and_mileages(self):
        """Reset colors and mileage"""
        self._reset_dropdown(self.mileage_input, "Any Mileage")
        self._reset_dropdown(self.color_input, "Any Color")

    def _reset_dropdown(self, dropdown, default_text):
        """Reset dropdown to initial state"""
        dropdown.clear()
        dropdown.addItem(default_text)

    # =============================================================================
    # БЛОК 7: ПУБЛІЧНЕ API
    # =============================================================================
    
    def get_criteria(self) -> dict:
        """Gathers all filter criteria into a single dictionary."""
        criteria = {}
        
        # Brand
        brand = self.brand_input.currentText()
        if brand != "Any Brand":
            criteria['brand'] = brand

        # Model
        model = self.model_input.currentText()
        if model != "Any Model":
            criteria['model'] = model

        # Registration Year
        reg_date_text = self.reg_date_input.currentText()
        if reg_date_text != "Any Year":
            try:
                criteria['registration_year'] = int(reg_date_text)
            except (ValueError, TypeError):
                print(f"Warning: Could not parse year value '{reg_date_text}'")
            
        # Price
        price_text = self.price_input.currentText()
        if price_text != "Any price":
            try:
                price_value = int(price_text.replace('€', '').replace(',', ''))
                criteria['price_lte'] = price_value
            except (ValueError, TypeError):
                print(f"Warning: Could not parse price value '{price_text}'")

        # Mileage
        mileage_text = self.mileage_input.currentText()
        if mileage_text != "Any Mileage":
            try:
                # Backend expects a single 'mileage' parameter, treated as 'less than or equal to'
                mileage_str = mileage_text.replace('<', '').replace('>', '').replace(',', '').replace('km', '').strip()
                mileage_value = int(mileage_str)
                if '<' in mileage_text:
                    criteria['mileage'] = mileage_value
            except (ValueError, TypeError):
                print(f"Warning: Could not parse mileage value '{mileage_text}'")

        # Location
        location_text = self.location_input.text()
        if location_text:
            criteria['city_or_postal_code'] = location_text

        # Color
        color_text = self.color_input.currentText()
        if color_text != "Any Color":
            criteria['color'] = color_text
                
        return criteria

    def set_search_button_text(self, text):
        """Set text for search button (for tracking mode)"""
        self.search_button.setText(text)
        # Disable auto-updates when custom text is set
        self.auto_update_button_text = False

    def restore_auto_button_updates(self):
        """Restore automatic text updates for the button"""
        self.auto_update_button_text = True
        self._update_search_button_count()  # Update to current count

    def reset_inputs(self):
        """Reset all filters to initial state"""
        if self.is_loading:
            return  # Don't reset during loading
            
        # Re-enable auto-updates when resetting
        self.auto_update_button_text = True
        
        self.brand_input.setCurrentIndex(0)  # "Any Brand"
        self._on_brand_changed()  # Cascade reset everything else
        self.location_input.clear()
        self.price_input.setCurrentIndex(0)
        self.search_button.setText(self.original_search_button_text) 