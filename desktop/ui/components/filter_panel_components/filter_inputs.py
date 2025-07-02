from PyQt6.QtWidgets import (
    QComboBox, QLineEdit, QGridLayout, QLabel, QPushButton, QWidget, QFrame, 
    QHBoxLayout, QVBoxLayout, QSizePolicy, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QSettings, QPropertyAnimation, QParallelAnimationGroup, pyqtSignal, QTimer, QThreadPool, QRunnable, QObject
from desktop.services.main_api_service import APIService

class CountWorkerSignals(QObject):
    finished = pyqtSignal(int)

class CountWorker(QRunnable):
    def __init__(self, api_service, filters):
        super().__init__()
        self.api_service = api_service
        self.filters = filters
        self.signals = CountWorkerSignals()

    def run(self):
        count = self.api_service.get_listings_count_sync(self.filters)
        self.signals.finished.emit(count)

class RetryComboBox(QComboBox):
    """A QComboBox that can enter an error state and allow retrying."""
    retry_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_error_state = False
        self._is_no_data_state = False

    def mousePressEvent(self, event):
        if self._is_error_state and self.isEnabled():
            # When in error state, a click should trigger a retry
            self.retry_requested.emit()
        else:
            # Default behavior for a normal state
            super().mousePressEvent(event)

    def set_error_state(self, message: str):
        """Set the combobox to an error state, showing a message."""
        self.blockSignals(True)
        self._is_error_state = True
        self._is_no_data_state = False
        self.clear()
        self.addItem(message)
        self.setCurrentIndex(0)
        self.setEnabled(True)  # Ensure it's clickable for retry
        self.setToolTip("An error occurred. Click to retry loading.")
        self.setStyleSheet("QComboBox { color: #E53935; font-style: italic; }")
        self.blockSignals(False)

    def set_no_data_state(self, message: str):
        """Set the combobox to a state indicating no data is available."""
        self.blockSignals(True)
        self._is_error_state = False
        self._is_no_data_state = True
        self.clear()
        self.addItem(message)
        self.setCurrentIndex(0)
        self.setEnabled(False) # Not interactive
        self.setToolTip("No available options for the current selection.")
        self.setStyleSheet("QComboBox { color: #9E9E9E; font-style: italic; }")
        self.blockSignals(False)
        
    def clear_special_state(self):
        """Reset the combobox from an error or no-data state."""
        if self._is_error_state or self._is_no_data_state:
            self.blockSignals(True)
            self._is_error_state = False
            self._is_no_data_state = False
            self.setStyleSheet("") # Reset stylesheet
            self.setToolTip("")
            self.setEnabled(True)
            self.clear()
            self.blockSignals(False)

class FilterInputs(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("CarGenius", "App")
        self.api_service_instance = APIService()
        self.filter_options = {}  # Store all filter options
        self.original_search_button_text = "Loading..."
        self.is_loading = True
        self.auto_update_button_text = True  # Flag to control automatic button text updates
        
        self.count_threadpool = QThreadPool()
        self.count_timer = QTimer(self)
        self.count_timer.setSingleShot(True)
        self.count_timer.setInterval(500) # 500ms delay
        self.count_timer.timeout.connect(self._trigger_count_update)

        self._create_ui()
        self._setup_cascading_behavior()
        self._load_filter_options()

    # =============================================================================
    # БЛОК 1: ІНІЦІАЛІЗАЦІЯ ТА ЗАВАНТАЖЕННЯ ДАНИХ
    # =============================================================================
    
    def _load_filter_options(self):
        """Load all available filter options efficiently without loading full dataset"""
        self.is_loading = True
        self.brand_input.clear_special_state()
        self._update_loading_state()
        
        try:
            # Get all filter options in one efficient call
            self.filter_options = self.api_service_instance.get_filter_options_sync()
            if self.filter_options and self.filter_options.get("brands"):
                # Get total count of listings for button text
                total_brands = len(self.filter_options.get("brands", []))
                total_models = len(self.filter_options.get("models", []))
                self.original_search_button_text = f"Search {total_brands} brands, {total_models} models"
            else:
                raise ConnectionError("API did not return valid filter options.")
        except Exception as e:
            print(f"Error loading filter options: {e}")
            self.filter_options = {}
            self.original_search_button_text = "Error loading filters"
            self.brand_input.set_error_state("Failed to load brands - Retry")
        finally:
            self.is_loading = False
            if not self.brand_input._is_error_state:
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
        """Create the entire UI, including the new UX enhancements."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        # 1. Help Panel
        self._create_help_panel(main_layout)

        # 2. Filter Grid Layout
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(10)
        grid_layout.setVerticalSpacing(12)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Row 1: Brand -> Model -> Year -> Color
        self._create_primary_filters(grid_layout)
        
        # Row 2: Mileage, Location, Price, Search Button
        self._create_secondary_filters(grid_layout)

        main_layout.addLayout(grid_layout)

    def _create_help_panel(self, parent_layout):
        self.help_panel = QFrame()
        self.help_panel.setObjectName("help_panel")
        self.help_panel.setStyleSheet("""
            #help_panel {
                background-color: rgba(0, 0, 0, 0.1);
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        help_layout = QHBoxLayout(self.help_panel)
        help_layout.setContentsMargins(5, 5, 5, 5)
        help_layout.setSpacing(10)
        
        icon_label = QLabel("💡")
        help_layout.addWidget(icon_label)
        
        text_label = QLabel("<b>Pro Tip:</b> Filters are linked. Start with Brand, and other options will update automatically.")
        text_label.setWordWrap(True)
        help_layout.addWidget(text_label, 1)
        
        close_button = QPushButton("×")
        close_button.setObjectName("close_help_button")
        close_button.setFixedSize(20, 20)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setStyleSheet("""
            #close_help_button {
                border: none;
                font-weight: bold;
                font-size: 16px;
            }
            #close_help_button:hover {
                color: #E53935;
            }
        """)
        close_button.clicked.connect(self._hide_help_panel)
        help_layout.addWidget(close_button)

        parent_layout.addWidget(self.help_panel)
        
        if self.settings.value("hide_filter_help", False, type=bool):
            self.help_panel.hide()

    def _hide_help_panel(self):
        self.help_panel.hide()
        self.settings.setValue("hide_filter_help", True)

    def _create_primary_filters(self, grid_layout):
        """First row: Brand, Model, Year, Color."""
        # --- Headers (at row 0) ---
        headers = ["Brand", "Model", "Registration date", "Color"]
        for i, header_text in enumerate(headers):
            label = QLabel(header_text)
            label.setObjectName("filter_header_light")
            grid_layout.addWidget(label, 0, i)

        # --- Inputs (at row 1) ---
        self.brand_input = self._create_combobox()
        self.model_input = self._create_combobox()
        self.reg_date_input = self._create_combobox()
        self.color_input = self._create_combobox()

        grid_layout.addWidget(self.brand_input, 1, 0)
        grid_layout.addWidget(self.model_input, 1, 1)
        grid_layout.addWidget(self.reg_date_input, 1, 2)
        grid_layout.addWidget(self.color_input, 1, 3)

    def _create_secondary_filters(self, grid_layout):
        """Second row: Mileage, Location, Price, Search Button."""
        # --- Headers (at row 2) ---
        grid_layout.addWidget(QLabel("Kilometers up to"), 2, 0)
        grid_layout.addWidget(QLabel("City or postal code"), 2, 1)
        grid_layout.addWidget(QLabel("Price up to"), 2, 2)
        # Empty label for search button alignment
        grid_layout.addWidget(QLabel(""), 2, 3)
        
        for i in [0, 1, 2, 3]:
             if grid_layout.itemAtPosition(2,i):
                grid_layout.itemAtPosition(2, i).widget().setObjectName("filter_header_light")

        # --- Inputs (at row 3) ---
        self.mileage_input = self._create_combobox()
        
        self.location_input = QLineEdit()
        self.location_input.setObjectName("dark_filter_input")
        self.location_input.setPlaceholderText("Enter location")
        self.location_input.setFixedHeight(38)
        
        self.price_input = self._create_combobox()
        if isinstance(self.price_input, RetryComboBox): # price is static
            price_combo = QComboBox()
            price_combo.setObjectName("dark_filter_input")
            price_combo.setFixedHeight(38)
            self.price_input.deleteLater()
            self.price_input = price_combo
            
        self.price_input.addItems(["Any price", "€10,000", "€20,000", "€30,000", "€50,000", "€100,000"])
        
        self.search_button = QPushButton(self.original_search_button_text)
        self.search_button.setObjectName("search_button_red")
        self.search_button.setFixedHeight(38)
        
        grid_layout.addWidget(self.mileage_input, 3, 0)
        grid_layout.addWidget(self.location_input, 3, 1)
        grid_layout.addWidget(self.price_input, 3, 2)
        grid_layout.addWidget(self.search_button, 3, 3)
        
        # --- Column Stretching ---
        grid_layout.setColumnStretch(0, 4) # Brand / Mileage
        grid_layout.setColumnStretch(1, 4) # Model / Location
        grid_layout.setColumnStretch(2, 3) # Year / Price
        grid_layout.setColumnStretch(3, 3) # Color / Search

    def _create_combobox(self):
        """Create standard combobox"""
        combo = RetryComboBox()
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
        
        # Connect retry signals
        self.brand_input.retry_requested.connect(self._load_filter_options)
        self.model_input.retry_requested.connect(self._populate_models)
        self.reg_date_input.retry_requested.connect(self._populate_years)
        self.color_input.retry_requested.connect(self._populate_colors)
        
        # Add updates for other filters
        self.location_input.textChanged.connect(self._update_search_button_count)
        self.price_input.currentTextChanged.connect(self._update_search_button_count)
        self.color_input.currentTextChanged.connect(self._update_search_button_count)
        self.mileage_input.currentTextChanged.connect(self._update_search_button_count)

    def _initialize_filters(self):
        """Initialize all filters after loading data"""
        if not self.is_loading and self.filter_options:
            self._populate_brands()
            # Year and Color are now independent, so populate them at the start
            self._populate_years()
            self._populate_colors()
            # Reset dependent filters to their initial "Any" state
            self._reset_dropdown(self.model_input, "Any Model", is_loading=False)
            self._populate_mileages() # mileage is static, just populate
            # Set initial enabled/disabled states and tooltips
            self._update_filter_states_and_tooltips()

    def _on_brand_changed(self):
        """When brand changes → update models."""
        self._update_search_button_count()
        # Directly populate models without animation for a simpler, faster response
        self._populate_models()
        
    def _on_model_changed(self):
        """When model changes, we only need to update the search count."""
        self._update_search_button_count()
        # No longer triggers updates for other filters

    def _on_year_changed(self):
        """When year changes, we only need to update the search count."""
        self._update_search_button_count()
        # No longer triggers updates for other filters

    def _run_cascade_animation(self, widgets: list, logic_callback: callable):
        """Generic function to run fade-out -> logic -> fade-in animation."""
        effects = [w.graphicsEffect() for w in widgets]

        # Fade out
        fade_out_group = QParallelAnimationGroup(self)
        for effect in effects:
            if not effect: continue
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(150)
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            fade_out_group.addAnimation(anim)

        def on_fade_out_finished():
            logic_callback()

            # Fade in
            fade_in_group = QParallelAnimationGroup(self)
            for effect in effects:
                if not effect: continue
                anim = QPropertyAnimation(effect, b"opacity")
                anim.setDuration(250)
                anim.setStartValue(0.0)
                anim.setEndValue(1.0)
                fade_in_group.addAnimation(anim)
            
            # Start the fade-in and let it self-manage
            fade_in_group.start()

        # Connect the finished signal and start the animation
        fade_out_group.finished.connect(on_fade_out_finished)
        fade_out_group.start()

    # =============================================================================
    # БЛОК 4: МЕТОДИ ЗАПОВНЕННЯ ФІЛЬТРІВ
    # =============================================================================
    
    def _populate_brands(self):
        """Populate brands list"""
        brands = self.filter_options.get("brands", [])
        self._populate_dropdown(self.brand_input, brands, "Any Brand")

    def _populate_models(self):
        """Populate models list for selected brand using efficient API call"""
        self.model_input.clear_special_state()
        selected_brand = self.brand_input.currentText()
        
        # Don't try to load if brand is invalid or not selected
        if selected_brand in ["Any Brand", ""] or self.brand_input._is_error_state:
            self._populate_dropdown(self.model_input, self.filter_options.get("models", []), "Any Model")
            self._update_filter_states_and_tooltips()
            return
            
        self._reset_dropdown(self.model_input, "Loading models...", is_loading=True)

        try:
            models = self.api_service_instance.get_models_for_brand_sync(selected_brand)
            if models is None: # API error
                raise ConnectionError("API did not return model data.")

            if not models: # Empty list
                self.model_input.set_no_data_state("No models for this brand")
            else:
                self._populate_dropdown(self.model_input, models, "Any Model")
        except Exception as e:
            print(f"Error loading models for brand {selected_brand}: {e}")
            self.model_input.set_error_state("Failed to load - Retry")
        finally:
            self._update_filter_states_and_tooltips()

    def _populate_years(self):
        """Populate years list from initially loaded options."""
        self.reg_date_input.clear_special_state()
        self._reset_dropdown(self.reg_date_input, "Loading years...", is_loading=True)
        try:
            years = self.filter_options.get("years", [])
            if not years:
                self.reg_date_input.set_no_data_state("No years available")
            else:
                years_str = sorted([str(year) for year in years], reverse=True)
                self._populate_dropdown(self.reg_date_input, years_str, "Any Year")
        except Exception as e:
            print(f"Error preparing years list: {e}")
            self.reg_date_input.set_error_state("Processing error - Retry")
        finally:
            self._update_filter_states_and_tooltips()

    def _populate_mileages(self):
        """Populate mileage list"""
        # The "> 150,000 km" option is removed as it cannot be supported by the backend API
        mileage_ranges = ["Any Mileage", "< 10,000 km", "< 50,000 km", "< 100,000 km", "< 150,000 km"]
        
        # Ensure mileage_input is a standard QComboBox
        if isinstance(self.mileage_input, RetryComboBox):
            mileage_combo = QComboBox()
            mileage_combo.setObjectName("dark_filter_input")
            mileage_combo.setFixedHeight(38)
            # Replace in layout
            self.mileage_input.parentWidget().layout().replaceWidget(self.mileage_input, mileage_combo)
            self.mileage_input.deleteLater()
            self.mileage_input = mileage_combo
            # Reconnect signal if needed
            self.mileage_input.currentTextChanged.connect(self._update_search_button_count)

        self.mileage_input.clear()
        self.mileage_input.addItems(mileage_ranges)

    def _populate_colors(self):
        """Populate colors list from initially loaded options."""
        self.color_input.clear_special_state()
        self._reset_dropdown(self.color_input, "Loading colors...", is_loading=True)
        try:
            colors = self.filter_options.get("colors", [])
            if not colors:
                self.color_input.set_no_data_state("No colors available")
            else:
                self._populate_dropdown(self.color_input, sorted(colors), "Any Color")
        except Exception as e:
            print(f"Error preparing colors list: {e}")
            self.color_input.set_error_state("Processing error - Retry")
        finally:
            self._update_filter_states_and_tooltips()

    def _populate_dropdown(self, dropdown, items, default_text):
        """Universal method for populating dropdown list, ensuring special states are cleared."""
        # dropdown is an instance of RetryComboBox
        dropdown.clear_special_state()
        dropdown.setStyleSheet("") # Reset any temporary styles (e.g., from loading)
        
        is_blocked = dropdown.signalsBlocked()
        if not is_blocked:
            dropdown.blockSignals(True)

        dropdown.clear()
        dropdown.addItem(default_text)
        if items:
            dropdown.addItems(items)

        if not is_blocked:
            dropdown.blockSignals(False)

    def _update_search_button_count(self):
        """Debounce the count update."""
        if self.is_loading or not self.auto_update_button_text:
            return
        
        self.search_button.setText("Updating...")
        self.count_timer.start() # Restart the timer every time a filter changes

    def _trigger_count_update(self):
        """Fetch the count of listings based on current filters."""
        criteria = self.get_criteria()

        # When no filters are selected, use the initial text with total counts.
        if not criteria:
            if self.original_search_button_text != "Error loading filters":
                 self.search_button.setText(self.original_search_button_text)
            else:
                 self.search_button.setText("Search")
            return

        worker = CountWorker(self.api_service_instance, criteria)
        worker.signals.finished.connect(self._on_count_finished)
        self.count_threadpool.start(worker)

    def _on_count_finished(self, count):
        """Update the search button text with the fetched count."""
        if count > 0:
            self.search_button.setText(f"Search {count} listings")
        elif count == 0:
            self.search_button.setText("No listings found")
        else: # count == -1, an error occurred
            self.search_button.setText("Error updating count")

    # =============================================================================
    # БЛОК 5: МЕТОДИ СКИДАННЯ ФІЛЬТРІВ
    # =============================================================================
    
    def _reset_dropdown(self, dropdown, default_text, is_loading: bool):
        """Reset dropdown to a default or loading state."""
        # dropdown is an instance of RetryComboBox
        dropdown.clear_special_state()
        dropdown.clear()
        dropdown.addItem(default_text)
        dropdown.setEnabled(not is_loading)
        if is_loading:
            dropdown.setStyleSheet("QComboBox { color: #9E9E9E; }")

    # =============================================================================
    # БЛОК 7: ПУБЛІЧНЕ API
    # =============================================================================
    
    def get_criteria(self) -> dict:
        """Gathers all filter criteria into a single dictionary."""
        criteria = {}
        
        # Brand
        brand = self.brand_input.currentText()
        if brand != "Any Brand" and not self.brand_input._is_error_state:
            criteria['brand'] = brand

        # Model
        model = self.model_input.currentText()
        if model != "Any Model" and not self.model_input._is_error_state and not self.model_input._is_no_data_state:
            criteria['model'] = model

        # Registration Year
        reg_date_text = self.reg_date_input.currentText()
        if reg_date_text != "Any Year" and not self.reg_date_input._is_error_state and not self.reg_date_input._is_no_data_state:
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
        if color_text != "Any Color" and not self.color_input._is_error_state and not self.color_input._is_no_data_state:
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
        """Resets all inputs to their default state."""
        if self.is_loading:
            return  # Don't reset during loading
            
        self.auto_update_button_text = True
        
        # Block signals to prevent cascade triggers during reset
        self.brand_input.blockSignals(True)
        
        # Reset dropdowns and clear inputs
        self.brand_input.setCurrentIndex(0)
        self.location_input.clear()
        self.price_input.setCurrentIndex(0)
        self.mileage_input.setCurrentIndex(0)
        self.reg_date_input.setCurrentIndex(0)
        self.color_input.setCurrentIndex(0)
        
        self.brand_input.blockSignals(False)

        # Manually trigger updates for dependent filters and UI state
        self._populate_models()
        self._update_filter_states_and_tooltips()
        self._update_search_button_count()

    def _update_filter_states_and_tooltips(self):
        """Enable/disable filters based on selections and update their tooltips."""
        # Do not change state if the combo itself is in a special state
        if self.brand_input._is_error_state or self.brand_input._is_no_data_state:
            self.model_input.setEnabled(False)
            self.reg_date_input.setEnabled(False)
            self.color_input.setEnabled(False)
            return

        is_brand_selected = self.brand_input.currentText() not in ["Any Brand", ""]
        
        # --- State Logic ---
        self.model_input.setEnabled(is_brand_selected and not self.model_input._is_error_state)
        # Year and Color are now independent, so their state only depends on if they loaded correctly
        self.reg_date_input.setEnabled(not self.reg_date_input._is_error_state and not self.reg_date_input._is_no_data_state)
        self.color_input.setEnabled(not self.color_input._is_error_state and not self.color_input._is_no_data_state)

        # --- Tooltip Logic ---
        if self.brand_input._is_error_state or self.brand_input._is_no_data_state: return

        self.brand_input.setToolTip("Select a brand to see available models.")

        if not self.model_input.isEnabled() and not self.model_input._is_error_state:
            self.model_input.setToolTip("Select a Brand to enable this filter.")
        elif not self.model_input._is_error_state:
            self.model_input.setToolTip("Available models depend on the selected brand.")

        # Year and Color tooltips are now static since they are independent
        if not self.reg_date_input._is_error_state:
            self.reg_date_input.setToolTip("Select the vehicle registration year.")
        
        if not self.color_input._is_error_state:
            self.color_input.setToolTip("Select the vehicle color.")

        self.mileage_input.setToolTip("Select the maximum vehicle mileage.")