import re
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class CarDataValidator:
    """Validates and transforms raw scraped car data to match database schema"""
    
    def __init__(self):
        self.equipment_mapping = {
            # German -> English mapping for equipment
            "ABS": "abs",
            "Abstandstempomat": "adaptive_cruise_control", 
            "Abstandswarner": "distance_warning",
            "Allradantrieb": "all_wheel_drive",
            "Ambiente-Beleuchtung": "ambient_lighting",
            "Android Auto": "android_auto",
            "Anhängerkupplung schwenkbar": "tow_bar_swiveling",
            "Apple CarPlay": "apple_carplay",
            "Armlehne": "armrest",
            "Beheizbare Frontscheibe": "heated_windshield",
            "Bluetooth": "bluetooth",
            "Bordcomputer": "board_computer",
            "Elektr. Fensterheber": "power_windows",
            "Elektr. Heckklappe": "power_tailgate",
            "Elektr. Seitenspiegel": "power_mirrors",
            "Elektr. Wegfahrsperre": "immobilizer",
            "ESP": "esp",
            "Fernlichtassistent": "high_beam_assist",
            "Freisprecheinrichtung": "hands_free",
            "Garantie": "warranty",
            "Geschwindigkeitsbegrenzer": "speed_limiter",
            "Induktionsladen für Smartphones": "wireless_charging",
            "Innenspiegel autom. abblendend": "auto_dimming_mirror",
            "Isofix": "isofix",
            "Isofix Beifahrersitz": "isofix_passenger",
            "Lederlenkrad": "leather_steering_wheel",
            "LED-Scheinwerfer": "led_headlights",
            "LED-Tagfahrlicht": "led_daytime_running_lights",
            "Leichtmetallfelgen": "alloy_wheels",
            "Lichtsensor": "light_sensor",
            "Lordosenstütze": "lumbar_support",
            "Müdigkeitswarner": "drowsiness_warning",
            "Multifunktionslenkrad": "multi_function_steering_wheel",
            "Musikstreaming integriert": "music_streaming",
            "Navigationssystem": "navigation_system",
            "Nichtraucher-Fahrzeug": "non_smoking_vehicle",
            "Notbremsassistent": "emergency_brake_assist",
            "Notrufsystem": "emergency_call_system",
            "Radio DAB": "dab_radio",
            "Regensensor": "rain_sensor",
            "Reifendruckkontrolle": "tire_pressure_monitoring",
            "Sitzheizung": "seat_heating",
            "Soundsystem": "sound_system",
            "Sportpaket": "sport_package",
            "Sportsitze": "sports_seats",
            "Sprachsteuerung": "voice_control",
            "Spurhalteassistent": "lane_keep_assist",
            "Touchscreen": "touchscreen",
            "Traktionskontrolle": "traction_control",
            "Tuner/Radio": "radio",
            "USB": "usb",
            "Verkehrszeichenerkennung": "traffic_sign_recognition",
            "Volldigitales Kombiinstrument": "digital_dashboard",
            "WLAN / Wifi Hotspot": "wifi_hotspot",
            "Zentralverriegelung": "central_locking"
        }

    def validate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main validation method that transforms raw data"""
        try:
            validated_data = {
                'listing': self._validate_listing(raw_data),
                'technical_details': self._validate_technical_details(raw_data),
                'equipment': self._validate_equipment(raw_data)
            }
            logger.info("✅ Data validation completed successfully")
            return validated_data
        except Exception as e:
            logger.error(f"❌ Validation failed: {str(e)}")
            raise

    def _validate_listing(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate main listing data"""
        basic_info = raw_data.get('basic_info', {})
        key_features = raw_data.get('key_features', {})
        
        # Extract brand and model from title
        brand = basic_info.get('brand', '')
        model = basic_info.get('model', '')
        
        # Extract price (remove € symbol and convert to int)
        price_str = basic_info.get('price', '0')
        price = self._parse_price(price_str)
        
        # Extract registration year from first_registration
        registration_str = key_features.get('first_registration', '')
        registration_year = self._parse_registration_year(registration_str)
        
        # Extract mileage from mileage string
        mileage_str = key_features.get('mileage', '')
        mileage = self._parse_mileage(mileage_str)
        
        # Extract city/postal code from location
        location = basic_info.get('location', '')
        city_postal = self._parse_location(location)
        
        return {
            'brand': brand,
            'model': model,
            'registration_year': registration_year,
            'mileage': mileage,
            'city_or_postal_code': city_postal,
            'color': self._extract_color(raw_data),
            'price': price,
            'currency': 'EUR',
            'url': basic_info.get('url', ''),
            'is_active': True
        }

    def _validate_technical_details(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate technical details data"""
        tech_data = raw_data.get('technical_data', {})
        key_features = raw_data.get('key_features', {})
        
        # Parse first registration into separate year and month
        first_reg_str = key_features.get('first_registration', '')
        first_year, first_month = self._parse_date_components(first_reg_str)
        
        # Parse HU date into separate year and month
        hu_str = tech_data.get('hu-item', '') or key_features.get('hu', '')
        hu_year, hu_month = self._parse_hu_date_components(hu_str)
        
        return {
            'damage_condition': tech_data.get('damageCondition-item'),
            'category': tech_data.get('category-item'),
            'trim_line': tech_data.get('trimLine-item'),
            'country_version': tech_data.get('countryVersion-item'),
            'power': self._parse_power(tech_data.get('power-item', key_features.get('power', ''))),
            'engine_type': tech_data.get('envkv.engineType-item'),
            'battery_capacity': self._parse_battery_capacity(tech_data.get('batteryCapacity-item', '')),
            'battery_range': self._parse_battery_range(key_features.get('battery_range', '')),
            'num_seats': self._parse_int(tech_data.get('numSeats-item')),
            'door_count': self._parse_door_count(tech_data.get('doorCount-item')),
            'transmission': self._parse_transmission(key_features.get('transmission', '')),
            'emissions_sticker': tech_data.get('emissionsSticker-item'),
            'first_year_registration': first_year,
            'first_month_registration': first_month,
            'number_of_previous_owners': self._parse_int(key_features.get('number_of_previous_owners', '')),
            'hu_year': hu_year,
            'hu_month': hu_month,
            'climatisation': tech_data.get('climatisation-item'),
            'park_assists': tech_data.get('parkAssists-item'),
            'airbags': tech_data.get('airbag-item'),
            'manufacturer_color_name': tech_data.get('manufacturerColorName-item'),
            'interior': tech_data.get('interior-item'),
            'trailer_load_braked': self._parse_weight(tech_data.get('trailerLoadBraked-item', '')),
            'trailer_load_unbraked': self._parse_weight(tech_data.get('trailerLoadUnbraked-item', '')),
            'net_weight': self._parse_weight(tech_data.get('netWeight-item', '')),
            'waranty_registration': key_features.get('warranty_registration')
        }

    def _validate_equipment(self, raw_data: Dict[str, Any]) -> Dict[str, bool]:
        """Validate equipment data"""
        equipment_data = raw_data.get('equipment', {})
        validated_equipment = {}
        
        # Initialize all equipment fields to False
        for english_name in self.equipment_mapping.values():
            validated_equipment[english_name] = False
        
        # Set True for present equipment
        for german_name, present in equipment_data.items():
            if german_name in self.equipment_mapping and present:
                english_name = self.equipment_mapping[german_name]
                validated_equipment[english_name] = True
        
        return validated_equipment

    # Parsing helper methods
    def _parse_price(self, price_str: str) -> int:
        """Extract price as integer from price string"""
        if not price_str:
            return 0
        # Remove everything except digits
        numbers = re.findall(r'\d+', price_str.replace('.', '').replace(',', ''))
        return int(''.join(numbers)) if numbers else 0

    def _parse_registration_year(self, reg_str: str) -> Optional[int]:
        """Extract year from registration string like 'Erstzulassung\n03/2018'"""
        if not reg_str:
            return None
        year_match = re.search(r'(\d{4})', reg_str)
        return int(year_match.group(1)) if year_match else None

    def _parse_mileage(self, mileage_str: str) -> Optional[int]:
        """Extract mileage as integer from string like 'Kilometerstand\n78.378 km'"""
        if not mileage_str:
            return None
        numbers = re.findall(r'\d+', mileage_str.replace('.', '').replace(',', ''))
        return int(''.join(numbers)) if numbers else None

    def _parse_location(self, location: str) -> Optional[str]:
        """Extract city/postal code from location string"""
        if not location:
            return None
        # Extract postal code and city from format like "Tolkewitzer Straße 83 DE-01279 Dresden"
        match = re.search(r'DE-(\d{5})\s+([^,]+)', location)
        if match:
            postal_code, city = match.groups()
            return f"{postal_code} {city.strip()}"
        return location

    def _parse_power(self, power_str: str) -> Optional[int]:
        """Extract power in kW from string like 'Leistung\n185 kW (252 PS)'"""
        if not power_str:
            return None
        kw_match = re.search(r'(\d+)\s*kW', power_str)
        return int(kw_match.group(1)) if kw_match else None

    def _parse_battery_capacity(self, capacity_str: str) -> Optional[float]:
        """Extract battery capacity from string"""
        if not capacity_str:
            return None
        match = re.search(r'(\d+(?:\.\d+)?)\s*kWh', capacity_str)
        return float(match.group(1)) if match else None

    def _parse_battery_range(self, range_str: str) -> Optional[int]:
        """Extract battery range from string"""
        if not range_str or range_str == "Not found":
            return None
        numbers = re.findall(r'(\d+)', range_str)
        return int(numbers[0]) if numbers else None

    def _parse_transmission(self, trans_str: str) -> Optional[str]:
        """Extract transmission from string like 'Getriebe\nAutomatik'"""
        if not trans_str:
            return None
        lines = trans_str.split('\n')
        return lines[-1].strip() if len(lines) > 1 else trans_str.strip()

    def _parse_first_registration(self, reg_str: str) -> Optional[str]:
        """Convert registration to YYYY-MM-DD format"""
        if not reg_str:
            return None
        # Extract MM/YYYY format
        match = re.search(r'(\d{2})/(\d{4})', reg_str)
        if match:
            month, year = match.groups()
            from datetime import datetime
            return datetime(int(year), int(month), 1).strftime("%m/%Y")
        return None

    def _parse_door_count(self, door_str: str) -> Optional[int]:
        """Extract door count from string like '4/5'"""
        if not door_str:
            return None
        match = re.search(r'(\d+)', door_str)
        return int(match.group(1)) if match else None

    def _parse_weight(self, weight_str: str) -> Optional[int]:
        """Extract weight in kg from string"""
        if not weight_str:
            return None
        numbers = re.findall(r'(\d+)', weight_str.replace('.', '').replace(',', ''))
        return int(''.join(numbers)) if numbers else None

    def _parse_int(self, value: str) -> Optional[int]:
        """Safely parse integer from string"""
        if not value or value == "Not found":
            return None
        numbers = re.findall(r'\d+', str(value))
        return int(numbers[0]) if numbers else None

    def _extract_color(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract color from technical data"""
        tech_data = raw_data.get('technical_data', {})
        color = tech_data.get('color-item') or tech_data.get('manufacturerColorName-item')
        return color.replace(' Metallic', '').strip() if color else None

    def _parse_date_components(self, date_str: str) -> tuple[Optional[int], Optional[int]]:
        """Extract year and month from registration string like 'Erstzulassung\n03/2018'"""
        if not date_str:
            return None, None
        # Look for MM/YYYY pattern
        match = re.search(r'(\d{2})/(\d{4})', date_str)
        if match:
            month, year = match.groups()
            return int(year), int(month)
        # Fallback: look for just year
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            return int(year_match.group(1)), None
        return None, None

    def _parse_hu_date_components(self, hu_str: str) -> tuple[Optional[int], Optional[int]]:
        """Extract year and month from HU string like 'HU\n12/2025' or similar formats"""
        if not hu_str:
            return None, None
        # Look for MM/YYYY pattern
        match = re.search(r'(\d{2})/(\d{4})', hu_str)
        if match:
            month, year = match.groups()
            return int(year), int(month)
        # Look for YYYY-MM pattern
        match = re.search(r'(\d{4})-(\d{2})', hu_str)
        if match:
            year, month = match.groups()
            return int(year), int(month)
        # Fallback: look for just year
        year_match = re.search(r'(\d{4})', hu_str)
        if year_match:
            return int(year_match.group(1)), None
        return None, None 