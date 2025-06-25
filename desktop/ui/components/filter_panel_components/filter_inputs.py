from PyQt6.QtWidgets import QComboBox, QLineEdit, QGridLayout, QLabel, QPushButton, QWidget
from desktop.services.main_api_service import APIService

class FilterInputs(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_service_instance = APIService()
        self.all_listings = []
        self.original_search_button_text = "Loading..."
        self.is_loading = True
        self.auto_update_button_text = True  # Flag to control automatic button text updates
        
        self._create_ui()  # Створюємо UI спочатку з текстом "Loading..."
        self._load_data()  # Потім завантажуємо дані
        self._setup_cascading_behavior()

    # =============================================================================
    # БЛОК 1: ІНІЦІАЛІЗАЦІЯ ТА ЗАВАНТАЖЕННЯ ДАНИХ
    # =============================================================================
    
    def _load_data(self):
        """Завантажуємо всі дані один раз для фільтрації"""
        self.is_loading = True
        self._update_loading_state()
        
        try:
            cars_data = self.api_service_instance.search_listings_sync({})
            if cars_data and 'Listings' in cars_data:
                self.all_listings = cars_data['Listings']
                # Використовуємо Stats.count для точної кількості записів
                if 'Stats' in cars_data and cars_data['Stats'] and 'count' in cars_data['Stats']:
                    total_count = cars_data['Stats']['count']
                    self.original_search_button_text = f"{total_count} listings"
                else:
                    # Fallback до підрахунку довжини масиву
                    self.original_search_button_text = f"{len(self.all_listings)} listings"
            else:
                self.all_listings = []
                self.original_search_button_text = "0 listings"
        except Exception as e:
            print(f"Error loading data: {e}")
            self.all_listings = []
            self.original_search_button_text = "Error loading data"
        finally:
            self.is_loading = False
            self._initialize_filters()
            self._update_loading_state()

    def _update_loading_state(self):
        """Оновлюємо стан завантаження UI"""
        if self.is_loading:
            self.search_button.setText("Loading...")
            self.search_button.setEnabled(False)
            # Вимикаємо всі фільтри під час завантаження
            self._set_filters_enabled(False)
        else:
            self.search_button.setText(self.original_search_button_text)
            self.search_button.setEnabled(True)
            # Вмикаємо фільтри після завантаження
            self._set_filters_enabled(True)

    def _set_filters_enabled(self, enabled: bool):
        """Вмикаємо/вимикаємо всі фільтри"""
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
        """Створюємо інтерфейс з усіма елементами"""
        layout = QGridLayout(self)
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # Заголовки та елементи першого ряду
        self._create_row1_elements(layout)
        # Заголовки та елементи другого ряду  
        self._create_row2_elements(layout)
        
        # НЕ ініціалізуємо фільтри тут - це буде зроблено після завантаження даних

    def _create_row1_elements(self, layout):
        """Перший ряд: Brand, Model, Year, Mileage"""
        headers = ["Brand", "Model", "Registration date", "Kilometers up to"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setObjectName("filter_header_light")
            layout.addWidget(label, 0, col)

        # Створюємо випадаючі списки
        self.brand_input = self._create_combobox()
        self.model_input = self._create_combobox()
        self.reg_date_input = self._create_combobox()
        self.mileage_input = self._create_combobox()
        
        layout.addWidget(self.brand_input, 1, 0)
        layout.addWidget(self.model_input, 1, 1)
        layout.addWidget(self.reg_date_input, 1, 2)
        layout.addWidget(self.mileage_input, 1, 3)

    def _create_row2_elements(self, layout):
        """Другий ряд: Location, Color, Price, Search"""
        headers = ["City or postal code", "Color", "Price up to", ""]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setObjectName("filter_header_light")
            layout.addWidget(label, 2, col)

        # Створюємо елементи
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
        
        # Налаштовуємо розтягування колонок
        for i in range(4):
            layout.setColumnStretch(i, 1)

    def _create_combobox(self):
        """Створюємо стандартний combobox"""
        combo = QComboBox()
        combo.setObjectName("dark_filter_input")
        combo.setFixedHeight(38)
        return combo

    # =============================================================================
    # БЛОК 3: КАСКАДНА ЛОГІКА ФІЛЬТРАЦІЇ
    # =============================================================================
    
    def _setup_cascading_behavior(self):
        """Налаштовуємо каскадну поведінку фільтрів"""
        self.brand_input.currentTextChanged.connect(self._on_brand_changed)
        self.model_input.currentTextChanged.connect(self._on_model_changed)
        self.reg_date_input.currentTextChanged.connect(self._on_year_changed)
        # Додаємо оновлення для інших фільтрів
        self.location_input.textChanged.connect(self._update_search_button_count)
        self.price_input.currentTextChanged.connect(self._update_search_button_count)
        self.color_input.currentTextChanged.connect(self._update_search_button_count)
        self.mileage_input.currentTextChanged.connect(self._update_search_button_count)

    def _initialize_filters(self):
        """Ініціалізуємо всі фільтри після завантаження даних"""
        if not self.is_loading and self.all_listings:
            self._populate_brands()
            self._reset_dependent_filters()

    def _on_brand_changed(self):
        """Коли змінюється бренд → оновлюємо моделі"""
        self._populate_models()
        self._reset_years_and_below()
        self._update_search_button_count()

    def _on_model_changed(self):
        """Коли змінюється модель → оновлюємо роки"""
        self._populate_years()
        self._reset_colors_and_mileages()
        self._update_search_button_count()

    def _on_year_changed(self):
        """Коли змінюється рік → оновлюємо пробіг та кольори"""
        self._populate_mileages()
        self._populate_colors()
        self._update_search_button_count()

    # =============================================================================
    # БЛОК 4: МЕТОДИ ЗАПОВНЕННЯ ФІЛЬТРІВ
    # =============================================================================
    
    def _populate_brands(self):
        """Заповнюємо список брендів"""
        brands = {listing.get("brand") for listing in self.all_listings if listing.get("brand")}
        self._populate_dropdown(self.brand_input, sorted(brands), "Any Brand")

    def _populate_models(self):
        """Заповнюємо список моделей для обраного бренду"""
        filtered_data = self._filter_by_brand()
        models = {listing.get("model") for listing in filtered_data if listing.get("model")}
        self._populate_dropdown(self.model_input, sorted(models), "Any Model")

    def _populate_years(self):
        """Заповнюємо список років для обраного бренду та моделі"""
        filtered_data = self._filter_by_brand_and_model()
        years = {listing.get("registration_year") for listing in filtered_data if listing.get("registration_year")}
        years_str = [str(year) for year in sorted(years)]
        self._populate_dropdown(self.reg_date_input, years_str, "Any Year")

    def _populate_mileages(self):
        """Заповнюємо список пробігу"""
        # The "> 150,000 km" option is removed as it cannot be supported by the backend API
        mileage_ranges = ["Any Mileage", "< 10,000 km", "< 50,000 km", "< 100,000 km", "< 150,000 km"]
        self.mileage_input.clear()
        self.mileage_input.addItems(mileage_ranges)

    def _populate_colors(self):
        """Заповнюємо список кольорів для поточних фільтрів"""
        filtered_data = self._get_current_filtered_data()
        colors = {listing.get("color") for listing in filtered_data if listing.get("color")}
        self._populate_dropdown(self.color_input, sorted(colors), "Any Color")

    def _populate_dropdown(self, dropdown, items, default_text):
        """Універсальний метод заповнення випадаючого списку"""
        dropdown.clear()
        dropdown.addItem(default_text)
        if items:
            dropdown.addItems(items)

    def _update_search_button_count(self):
        """Оновлюємо текст кнопки згідно з поточними фільтрами"""
        if self.is_loading or not self.auto_update_button_text:
            return  # Не оновлюємо під час завантаження або якщо вимкнено автооновлення
            
        filtered_data = self._get_current_filtered_data()
        count = len(filtered_data)
        self.search_button.setText(f"{count} listings")

    # =============================================================================
    # БЛОК 5: МЕТОДИ ФІЛЬТРАЦІЇ ДАНИХ
    # =============================================================================
    
    def _filter_by_brand(self):
        """Фільтруємо дані за брендом"""
        selected_brand = self.brand_input.currentText()
        if selected_brand == "Any Brand":
            return self.all_listings
        return [l for l in self.all_listings if l.get("brand") == selected_brand]

    def _filter_by_brand_and_model(self):
        """Фільтруємо дані за брендом та моделлю"""
        filtered_data = self._filter_by_brand()
        selected_model = self.model_input.currentText()
        if selected_model == "Any Model":
            return filtered_data
        return [l for l in filtered_data if l.get("model") == selected_model]

    def _get_current_filtered_data(self):
        """Отримуємо відфільтровані дані на основі поточних налаштувань"""
        # Починаємо з повного списку або з попередньо відфільтрованих даних
        filtered_data = self._filter_by_brand_and_model() # Включає фільтрацію за брендом і моделлю

        # Фільтрація за роком
        selected_year = self.reg_date_input.currentText()
        if selected_year != "Any Year":
            try:
                year_val = int(selected_year)
                filtered_data = [l for l in filtered_data if l.get("registration_year") == year_val]
            except ValueError:
                pass

        # Фільтрація за ціною
        selected_price = self.price_input.currentText()
        if selected_price != "Any price":
            try:
                price_val = int(selected_price.replace("€", "").replace(",", ""))
                filtered_data = [l for l in filtered_data if l.get("price", 0) <= price_val]
            except ValueError:
                pass

        # Фільтрація за пробігом
        selected_mileage = self.mileage_input.currentText()
        if selected_mileage != "Any Mileage":
            if "< 10,000" in selected_mileage:
                filtered_data = [l for l in filtered_data if l.get("mileage", 0) < 10000]
            elif "< 50,000" in selected_mileage:
                filtered_data = [l for l in filtered_data if l.get("mileage", 0) < 50000]
            elif "< 100,000" in selected_mileage:
                filtered_data = [l for l in filtered_data if l.get("mileage", 0) < 100000]
            elif "< 150,000" in selected_mileage:
                filtered_data = [l for l in filtered_data if l.get("mileage", 0) < 150000]
                
        # Фільтрація за локацією (місто або поштовий індекс)
        location_text = self.location_input.text().strip().lower()
        if location_text:
            filtered_data = [
                l for l in filtered_data 
                if l.get("city_or_postal_code") and location_text in l["city_or_postal_code"].lower()
            ]

        # Фільтрація за кольором
        selected_color = self.color_input.currentText()
        if selected_color != "Any Color":
            filtered_data = [l for l in filtered_data if l.get("color") == selected_color]
            
        return filtered_data

    # =============================================================================
    # БЛОК 6: МЕТОДИ СКИДАННЯ ФІЛЬТРІВ
    # =============================================================================
    
    def _reset_dependent_filters(self):
        """Скидаємо всі залежні фільтри"""
        self._reset_dropdown(self.model_input, "Any Model")
        self._reset_dropdown(self.reg_date_input, "Any Year")
        self._reset_dropdown(self.mileage_input, "Any Mileage")
        self._reset_dropdown(self.color_input, "Any Color")

    def _reset_years_and_below(self):
        """Скидаємо роки та все що нижче"""
        self._reset_dropdown(self.reg_date_input, "Any Year")
        self._reset_colors_and_mileages()

    def _reset_colors_and_mileages(self):
        """Скидаємо кольори та пробіг"""
        self._reset_dropdown(self.mileage_input, "Any Mileage")
        self._reset_dropdown(self.color_input, "Any Color")

    def _reset_dropdown(self, dropdown, default_text):
        """Скидаємо випадаючий список до початкового стану"""
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
        """Встановлюємо текст для кнопки пошуку (для режиму відстеження)"""
        self.search_button.setText(text)
        # Disable auto-updates when custom text is set
        self.auto_update_button_text = False

    def restore_auto_button_updates(self):
        """Відновлюємо автоматичне оновлення тексту кнопки"""
        self.auto_update_button_text = True
        self._update_search_button_count()  # Update to current count

    def reset_inputs(self):
        """Скидаємо всі фільтри до початкового стану"""
        if self.is_loading:
            return  # Не скидаємо під час завантаження
            
        # Re-enable auto-updates when resetting
        self.auto_update_button_text = True
        
        self.brand_input.setCurrentIndex(0)  # "Any Brand"
        self._on_brand_changed()  # Каскадно скидаємо все інше
        self.location_input.clear()
        self.price_input.setCurrentIndex(0)
        self.search_button.setText(self.original_search_button_text) 