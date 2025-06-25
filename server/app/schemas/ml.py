# app/schemas/ml.py
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.stats.analytics import ListingOut, ListingStats, TechnicalDetailsSchema, EquipmentSchema


class CarFeatures(BaseModel):
    brand: Optional[str]
    model: Optional[str]
    registration_year: Optional[int]
    mileage: Optional[int]
    city_or_postal_code: Optional[str]
    color: Optional[str]
    price: Optional[float]
    damage_condition: Optional[str]
    category: Optional[str]
    trim_line: Optional[str]
    sku: Optional[str]
    country_version: Optional[str]
    power: Optional[int]
    engine_type: Optional[str]
    other_energy_source: Optional[str]
    battery: Optional[str]
    battery_capacity: Optional[float]
    battery_certificate: Optional[str]
    battery_range: Optional[float]
    num_seats: Optional[int]
    door_count: Optional[int]
    transmission: Optional[str]
    emissions_sticker: Optional[str]
    first_year_registration: Optional[int]
    first_month_registration: Optional[int]
    number_of_previous_owners: Optional[int]
    hu_year: Optional[int]
    hu_month: Optional[int]
    climatisation: Optional[str]
    park_assists: Optional[str]
    airbags: Optional[str]
    manufacturer_color_name: Optional[str]
    interior: Optional[str]
    trailer_load_braked: Optional[float]
    trailer_load_unbraked: Optional[float]
    net_weight: Optional[float]
    warranty_registration: Optional[str]

    abs: Optional[int]
    adaptive_cruise_control: Optional[int]
    distance_warning: Optional[int]
    all_wheel_drive: Optional[int]
    ambient_lighting: Optional[int]
    android_auto: Optional[int]
    tow_bar_swiveling: Optional[int]
    apple_carplay: Optional[int]
    armrest: Optional[int]
    heated_windshield: Optional[int]
    bluetooth: Optional[int]
    board_computer: Optional[int]
    power_windows: Optional[int]
    power_tailgate: Optional[int]
    power_mirrors: Optional[int]
    immobilizer: Optional[int]
    esp: Optional[int]
    high_beam_assist: Optional[int]
    hands_free: Optional[int]
    warranty: Optional[int]
    speed_limiter: Optional[int]
    wireless_charging: Optional[int]
    auto_dimming_mirror: Optional[int]
    isofix: Optional[int]
    isofix_passenger: Optional[int]
    leather_steering_wheel: Optional[int]
    led_headlights: Optional[int]
    led_daytime_running_lights: Optional[int]
    alloy_wheels: Optional[int]
    light_sensor: Optional[int]
    lumbar_support: Optional[int]
    drowsiness_warning: Optional[int]
    multi_function_steering_wheel: Optional[int]
    music_streaming: Optional[int]
    navigation_system: Optional[int]
    non_smoking_vehicle: Optional[int]
    emergency_brake_assist: Optional[int]
    emergency_call_system: Optional[int]
    dab_radio: Optional[int]
    rain_sensor: Optional[int]
    tire_pressure_monitoring: Optional[int]
    seat_heating: Optional[int]
    sound_system: Optional[int]
    sport_package: Optional[int]
    sports_seats: Optional[int]
    voice_control: Optional[int]
    lane_keep_assist: Optional[int]
    touchscreen: Optional[int]
    traction_control: Optional[int]
    radio: Optional[int]
    usb: Optional[int]
    traffic_sign_recognition: Optional[int]
    digital_dashboard: Optional[int]
    wifi_hotspot: Optional[int]
    central_locking: Optional[int]

    class Config:
        orm_mode = True


class ListingSchemaML(BaseModel):
    brand: Optional[str] = Field(None, description="Filter by car brand")
    model: Optional[str] = Field(None, description="Filter by car model")
    registration_year: Optional[int] = Field(None, description="Filter by registration year")
    mileage: Optional[int] = Field(None, description="Filter by mileage")
    city_or_postal_code: Optional[str] = Field(None, description="Filter by city or postal code")
    color: Optional[str] = Field(None, description="Filter by car color")
    price: Optional[int] = Field(None, description="Filter by exact price")
    technical_details: Optional[TechnicalDetailsSchema]
    equipment: Optional[EquipmentSchema]

    class Config:
        orm_mode = True


class ListingCreateRequestMLSchema(BaseModel):
    brand: Optional[str] = Field(None, description="Brand of the car")
    model: Optional[str] = Field(None, description="Model of the car")
    registration_year: Optional[int] = Field(None, description="Year the car was registered")
    mileage: Optional[int] = Field(None, description="Mileage of the car in kilometers")
    color: Optional[str] = Field(None, description="Color of the car")
    price: Optional[int] = Field(None, description="Price of the car in the specified currency")
    url: Optional[str] = Field(None, description="URL of the car listing")
    city_or_postal_code: Optional[str] = Field(None, description="City or postal code where the car is located")
    is_active: Optional[bool] = Field(True, description="Indicates if the listing is active")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class ListingFilterML(ListingCreateRequestMLSchema, TechnicalDetailsSchema, EquipmentSchema):
    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class PredictPriceRequest(BaseModel):
    registration_year: Optional[int]
    mileage: Optional[int]
    power: Optional[int]
    fuel_type: Optional[str]
    transmission: Optional[str]
    body_type: Optional[str]
    color: Optional[str]
    door_count: Optional[int]
    num_seats: Optional[int]
    number_of_previous_owners: Optional[int]
    climate_control: Optional[bool]
    navigation_system: Optional[bool]
    park_assist: Optional[bool]
    panoramic_roof: Optional[bool]
    leather_seats: Optional[bool]


class PricePredictionResponse(BaseModel):
    predicted_price: float
    actual_price: float
    difference: float
    is_profitable: bool
    similar_listings: list[ListingOut]
    stats: ListingStats
