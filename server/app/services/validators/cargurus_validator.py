"""
CarGurus API Data Validator

Converts data from CarGurus API format to our internal database models format.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re
import logging
import requests

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation process"""
    success: bool
    listing_data: Optional[Dict[str, Any]] = None
    technical_data: Optional[Dict[str, Any]] = None
    equipment_data: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CarGurusValidator:
    """
    Validates and converts CarGurus API response to our model format
    """
    
    # Mapping for equipment options from CarGurus to our database fields
    EQUIPMENT_MAPPING = {
        # Navigation & Technology
        'Navigation System': 'navigation_system',
        'Bluetooth': 'bluetooth',
        'Apple CarPlay': 'apple_carplay',
        'Android Auto': 'android_auto',
        'USB': 'usb',
        'Touchscreen': 'touchscreen',
        'WiFi Hotspot': 'wifi_hotspot',
        'Voice Control': 'voice_control',
        'Music Streaming': 'music_streaming',
        'Digital Dashboard': 'digital_dashboard',
        'Board Computer': 'board_computer',
        
        # Safety & Driver Assistance
        'Backup Camera': 'backup_camera',
        'Parking Sensors': 'parking_sensors',
        'Blind Spot Monitoring': 'blind_spot_monitoring',
        'Adaptive Cruise Control': 'adaptive_cruise_control',
        'Lane Keep Assist': 'lane_keep_assist',
        'Traffic Sign Recognition': 'traffic_sign_recognition',
        'Emergency Brake Assist': 'emergency_brake_assist',
        'Emergency Call System': 'emergency_call_system',
        'ABS Brakes': 'abs',
        'ESP': 'esp',
        'Traction Control': 'traction_control',
        'Tire Pressure Monitoring': 'tire_pressure_monitoring',
        'Drowsiness Warning': 'drowsiness_warning',
        'Distance Warning': 'distance_warning',
        'High Beam Assist': 'high_beam_assist',
        'Immobilizer': 'immobilizer',
        
        # Comfort & Convenience
        'Heated Seats': 'seat_heating',
        'Multi Zone Climate Control': 'multi_zone_climate',
        'Power Mirror Package': 'power_mirrors',
        'Power Windows': 'power_windows',
        'Power Liftgate': 'power_tailgate',
        'Central Locking': 'central_locking',
        'Remote Keyless Entry': 'remote_keyless_entry',
        'Auto-dimming Mirrors': 'auto_dimming_mirror',
        'Rain Sensing Wipers': 'rain_sensor',
        'Light Sensor': 'light_sensor',
        'Ambient Lighting': 'ambient_lighting',
        'Armrest': 'armrest',
        'Lumbar Support': 'lumbar_support',
        'Hands Free': 'hands_free',
        'Wireless Charging': 'wireless_charging',
        'Speed Limiter': 'speed_limiter',
        'Warranty': 'warranty',
        
        # Audio & Entertainment
        'Sound System': 'sound_system',
        'Radio': 'radio',
        'DAB Radio': 'dab_radio',
        
        # Exterior & Wheels
        'Premium Wheels': 'alloy_wheels',
        'Alloy Wheels': 'alloy_wheels',
        'LED Headlights': 'led_headlights',
        'LED Daytime Running Lights': 'led_daytime_running_lights',
        
        # Interior & Seats
        'Leather Seats': 'leather_interior',
        'Sports Seats': 'sports_seats',
        'Heated Front Seats': 'seat_heating',
        'Multi-Function Steering Wheel': 'multi_function_steering_wheel',
        'Leather Steering Wheel': 'leather_steering_wheel',
        
        # Packages
        'Sport Package': 'sport_package',
        'Technology Package': 'technology_package',
        'Premium Package': 'premium_package',
        'Heat Package': 'heat_package',
        'Suspension Package': 'suspension_package',
        'SE Package': 'se_package',
        
        # Drivetrain
        'All-Wheel Drive': 'all_wheel_drive',
        
        # Other
        'Sunroof/Moonroof': 'sunroof',
        'Non-Smoking Vehicle': 'non_smoking_vehicle',
        'ISOFIX': 'isofix',
        'Tow Bar': 'tow_bar_swiveling',
    }
    
    def __init__(self):
        self.logger = logger
    
    def validate_from_url(self, url: str) -> ValidationResult:
        """
        Fetches data from a URL, then validates and converts it.

        Args:
            url: The URL to fetch CarGurus data from.

        Returns:
            ValidationResult with converted data or errors.
        """
        result = ValidationResult(success=False)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            cargurus_data = response.json()
            return self.validate_and_convert(cargurus_data)
        except requests.exceptions.RequestException as e:
            result.errors.append(f"Failed to fetch data from URL: {e}")
            self.logger.error(f"URL fetch failed for {url}: {e}")
            return result
        except Exception as e:
            result.errors.append(f"An unexpected error occurred: {e}")
            self.logger.error(f"An unexpected error occurred for {url}: {e}")
            return result
    
    def validate_and_convert(self, cargurus_data: Dict[str, Any]) -> ValidationResult:
        """
        Main validation method that converts CarGurus data to our format
        
        Args:
            cargurus_data: Raw JSON response from CarGurus API
            
        Returns:
            ValidationResult with converted data or errors
        """
        result = ValidationResult(success=False)
        
        try:
            # Extract main sections
            listing = cargurus_data.get('listing', {})
            auto_entity_info = cargurus_data.get('autoEntityInfo', {})
            seller = cargurus_data.get('seller', {})
            
            if not listing:
                result.errors.append("Missing 'listing' section in CarGurus data")
                return result
            
            # Convert listing data
            listing_data = self._convert_listing_data(listing, auto_entity_info, seller)
            if listing_data:
                result.listing_data = listing_data
            
            # Convert technical details
            technical_data = self._convert_technical_data(listing, auto_entity_info)
            if technical_data:
                result.technical_data = technical_data
            
            # Convert equipment data
            equipment_data = self._convert_equipment_data(listing)
            if equipment_data:
                result.equipment_data = equipment_data
            
            result.success = True
            self.logger.info("Successfully validated and converted CarGurus data")
            
        except Exception as e:
            result.errors.append(f"Validation error: {str(e)}")
            self.logger.error(f"CarGurus validation failed: {e}")
        
        return result
    
    def _convert_listing_data(self, listing: Dict, auto_entity: Dict, seller: Dict) -> Dict[str, Any]:
        """Convert basic listing information"""
        
        # Extract city from seller address
        city_or_postal_code = None
        seller_address = seller.get('address', {})
        if seller_address:
            city = seller_address.get('city', '')
            postal_code = seller_address.get('postalCode', '')
            city_or_postal_code = f"{city}, {postal_code}" if city and postal_code else city or postal_code
        
        data = {
            'brand': auto_entity.get('make') or listing.get('makeName', ''),
            'model': auto_entity.get('model') or listing.get('modelName', ''),
            'registration_year': auto_entity.get('year') or listing.get('year'),
            'mileage': listing.get('mileage'),
            'city_or_postal_code': city_or_postal_code,
            'color': listing.get('localizedExteriorColor'),
            'price': listing.get('price'),
            'currency': 'USD',  # CarGurus is primarily US-based
            'url': self._construct_listing_url(listing.get('id')),
            'is_active': listing.get('status') == 'OPEN'
        }
        
        # Clean up None values for required fields
        if not data['brand'] or not data['model'] or not data['registration_year'] or not data['price']:
            self.logger.warning("Missing required fields in listing data")
            return {}
        
        return data
    
    def _convert_technical_data(self, listing: Dict, auto_entity: Dict) -> Dict[str, Any]:
        """Convert technical details"""
        
        # Extract power from engine display name (e.g., "210 kW (286 PS) Electric")
        power = self._extract_power_from_engine(listing.get('localizedEngineDisplayName', ''))
        
        # Extract seats and doors from detail stats
        num_seats, door_count = self._extract_seats_and_doors(listing)
        
        # Extract battery info for electric vehicles
        ev_battery = listing.get('evBatteryDto', {})
        battery_capacity = None
        battery_range = None
        
        if ev_battery:
            # Extract capacity (e.g., "75 kWh" -> 75.0)
            capacity_str = ev_battery.get('capacity', '')
            if 'kwh' in capacity_str.lower():
                battery_capacity = self._extract_float_from_string(capacity_str)
            
            # Extract range (e.g., "238 mi" -> 238)
            range_str = ev_battery.get('range', '')
            if 'mi' in range_str.lower():
                battery_range = self._extract_int_from_string(range_str)
        
        data = {
            'damage_condition': listing.get('vehicleCondition'),
            'category': auto_entity.get('bodyStyle'),
            'trim_line': auto_entity.get('trim') or listing.get('trimName'),
            'sku': listing.get('vin'),
            'country_version': 'US',  # CarGurus is US-based
            'power': power,
            'engine_type': listing.get('localizedEngineDisplayName'),
            'other_energy_source': listing.get('localizedFuelType'),
            'battery': 'included' if ev_battery else None,
            'battery_capacity': battery_capacity,
            'battery_range': battery_range,
            'num_seats': num_seats,
            'door_count': door_count,
            'transmission': listing.get('localizedTransmission'),
            'first_year_registration': listing.get('year'),
            'manufacturer_color_name': listing.get('localizedExteriorColor'),
            'interior': listing.get('localizedInteriorColor'),
        }
        
        return {k: v for k, v in data.items() if v is not None}
    
    def _convert_equipment_data(self, listing: Dict) -> Dict[str, Any]:
        """Convert equipment/options data"""
        
        # Initialize all equipment fields as False
        equipment_data = {field: False for field in self.EQUIPMENT_MAPPING.values()}
        
        # Process options list
        options = listing.get('options', [])
        for option in options:
            if option in self.EQUIPMENT_MAPPING:
                db_field = self.EQUIPMENT_MAPPING[option]
                equipment_data[db_field] = True
        
        # Process detailed options from listingDetailStatsSectionDto
        detail_stats = listing.get('listingDetailStatsSectionDto', [])
        for section in detail_stats:
            if section.get('categoryName') == 'Safety':
                safety_options = section.get('optionsList', [])
                for option in safety_options:
                    option_name = option.get('name', '')
                    if option_name in self.EQUIPMENT_MAPPING:
                        db_field = self.EQUIPMENT_MAPPING[option_name]
                        equipment_data[db_field] = True
            
            elif section.get('categoryName') == 'Options':
                options_list = section.get('optionsList', [])
                for option in options_list:
                    option_name = option.get('name', '')
                    if option_name in self.EQUIPMENT_MAPPING:
                        db_field = self.EQUIPMENT_MAPPING[option_name]
                        equipment_data[db_field] = True
        
        return equipment_data
    
    def _construct_listing_url(self, listing_id: Optional[int]) -> str:
        """Construct CarGurus listing URL"""
        if listing_id:
            return f"https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?sourceContext=carGurusHomePage&entitySelectingHelper.selectedEntity={listing_id}"
        return ""
    
    def _extract_power_from_engine(self, engine_str: str) -> Optional[int]:
        """Extract power in kW from engine description"""
        if not engine_str:
            return None
        
        # Look for patterns like "210 kW" or "286 PS"
        kw_match = re.search(r'(\d+)\s*kW', engine_str, re.IGNORECASE)
        if kw_match:
            return int(kw_match.group(1))
        
        # Convert PS to kW if only PS is available (1 PS ≈ 0.735 kW)
        ps_match = re.search(r'(\d+)\s*PS', engine_str, re.IGNORECASE)
        if ps_match:
            ps_value = int(ps_match.group(1))
            return int(ps_value * 0.735)
        
        return None
    
    def _extract_seats_and_doors(self, listing: Dict) -> tuple[Optional[int], Optional[int]]:
        """Extract number of seats and doors from listing details"""
        num_seats = None
        door_count = None
        
        # Check localized number of doors
        doors_str = listing.get('localizedNumberOfDoors', '')
        if doors_str:
            door_count = self._extract_int_from_string(doors_str)
        
        # Check detail stats for more info
        detail_stats = listing.get('listingDetailStatsSectionDto', [])
        for section in detail_stats:
            if section.get('categoryName') == 'Measurements':
                items = section.get('items', [])
                for item in items:
                    if item.get('key') == 'numberOfDoors':
                        door_count = self._extract_int_from_string(item.get('displayValue', ''))
        
        # Estimate seats based on vehicle type and doors
        if door_count:
            if door_count == 2:
                num_seats = 2  # Sports cars typically
            elif door_count in [4, 5]:
                num_seats = 5  # Most sedans/SUVs
        
        return num_seats, door_count
    
    def _extract_int_from_string(self, text: str) -> Optional[int]:
        """Extract first integer from string"""
        if not text:
            return None
        
        match = re.search(r'\d+', text)
        return int(match.group()) if match else None
    
    def _extract_float_from_string(self, text: str) -> Optional[float]:
        """Extract first float from string"""
        if not text:
            return None
        
        match = re.search(r'(\d+\.?\d*)', text)
        return float(match.group()) if match else None


def validate_cargurus_json(cargurus_json: Dict[str, Any]) -> ValidationResult:
    """
    Convenience function to validate CarGurus data from a JSON object.

    Args:
        cargurus_json: Raw JSON response from CarGurus API
        
    Returns:
        ValidationResult with converted data
    """
    validator = CarGurusValidator()
    return validator.validate_and_convert(cargurus_json)


def validate_cargurus_url(url: str) -> ValidationResult:
    """
    Convenience function to validate CarGurus data from a URL.

    Args:
        url: The URL to fetch and validate.

    Returns:
        ValidationResult with converted data.
    """
    validator = CarGurusValidator()
    return validator.validate_from_url(url) 