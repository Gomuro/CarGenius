# app/schemas/stats/analytics.py
from datetime import datetime, date
from pydantic import BaseModel, Field
from typing import List, Optional

"""Schemas for car technical details and equipment, used in the analytics module."""


class TechnicalDetailsSchema(BaseModel):
    damage_condition: Optional[str] = Field(None, description="damageCondition-item")  # Gebrauchtfahrzeug, Unfallfrei
    category: Optional[str] = Field(None, description="category-item")  # SUV / Geländewagen / Pickup
    trim_line: Optional[str] = Field(None, description="trimLine-item")  # Advanced
    sku: Optional[str] = Field(None, description="sku-item")  # Individual code
    country_version: Optional[str] = Field(None, description="countryVersion-item")  # Deutsche Ausführung
    power: Optional[int] = Field(None, description="power-item")  # 210 kW (286 PS)
    engine_type: Optional[str] = Field(None, description="envkv.engineType-item")  # Elektromotor
    other_energy_source: Optional[str] = Field(None, description="envkv.otherEnergySource-item")  # Strom
    battery: Optional[str] = Field(None, description="battery-item")  # z.B. "inklusive"
    battery_capacity: Optional[float] = Field(None, description="batteryCapacity-item")  # 82 kWh
    battery_certificate: Optional[str] = Field(None, description="batteryCertificate-item")  # Getestet vom Händler
    battery_range: Optional[int] = Field(None, description="batteryRange-item")  # 500 km
    num_seats: Optional[int] = Field(None, description="numSeats-item")  # 5
    door_count: Optional[int] = Field(None, description="doorCount-item")  # 4/5
    transmission: Optional[str] = Field(None, description="transmission-item")  # Automatik
    emissions_sticker: Optional[str] = Field(None, description="emissionsSticker-item")  # 4 (Grün)
    first_year_registration: Optional[int] = Field(None, description="firstRegistration-item")
    first_month_registration: Optional[int] = Field(None, description="firstRegistration-item")
    number_of_previous_owners: Optional[str] = Field(None, description="numberOfPreviousOwners-item")  # 1
    hu_year: Optional[int] = Field(None, description="hu-item")
    hu_month: Optional[int] = Field(None, description="hu-item")
    climatisation: Optional[str] = Field(None, description="climatisation-item")  # 3-Zonen-Klimaautomatik
    park_assists: Optional[str] = Field(None, description="parkAssists-item")  # Vorne, Hinten, Kamera
    airbags: Optional[str] = Field(None, description="airbag-item")  # Front-, Seiten- und weitere Airbags
    manufacturer_color_name: Optional[str] = Field(None,
                                                   description="manufacturerColorName-item")  # Navarrablau Metallic
    interior: Optional[str] = Field(None, description="interior-item")  # Teilleder, Schwarz
    trailer_load_braked: Optional[int] = Field(None, description="trailerLoadBraked-item")  # 1.200 kg
    trailer_load_unbraked: Optional[int] = Field(None, description="trailerLoadUnbraked-item")  # 750 kg
    net_weight: Optional[int] = Field(None, description="netWeight-item")  # 2.235 kg
    waranty_registration: Optional[str] = Field(None,
                                                description="warrantyRegistration-item")  # Garantie ab Erstzulassung\nNicht angegeben

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


"""Schemas for car equipment, used in the analytics module."""


class EquipmentSchema(BaseModel):
    abs: Optional[bool] = Field(None, description="Antiblockiersystem")
    adaptive_cruise_control: Optional[bool] = Field(None, description="Abstandstempomat")
    distance_warning: Optional[bool] = Field(None, description="Abstandswarner")
    all_wheel_drive: Optional[bool] = Field(None, description="Allradantrieb")
    ambient_lighting: Optional[bool] = Field(None, description="Ambiente-Beleuchtung")
    android_auto: Optional[bool] = Field(None, description="Android Auto")
    tow_bar_swiveling: Optional[bool] = Field(None, description="Anhängerkupplung schwenkbar")
    apple_carplay: Optional[bool] = Field(None, description="Apple CarPlay")
    armrest: Optional[bool] = Field(None, description="Armlehne")
    heated_windshield: Optional[bool] = Field(None, description="Beheizbare Frontscheibe")
    bluetooth: Optional[bool] = Field(None, description="Bluetooth")
    board_computer: Optional[bool] = Field(None, description="Bordcomputer")
    power_windows: Optional[bool] = Field(None, description="Elektr. Fensterheber")
    power_tailgate: Optional[bool] = Field(None, description="Elektr. Heckklappe")
    power_mirrors: Optional[bool] = Field(None, description="Elektr. Seitenspiegel")
    immobilizer: Optional[bool] = Field(None, description="Elektr. Wegfahrsperre")
    esp: Optional[bool] = Field(None, description="Elektron. Stabilitätsprogramm (ESP)")
    high_beam_assist: Optional[bool] = Field(None, description="Fernlichtassistent")
    hands_free: Optional[bool] = Field(None, description="Freisprecheinrichtung")
    warranty: Optional[bool] = Field(None, description="Garantie")
    speed_limiter: Optional[bool] = Field(None, description="Geschwindigkeitsbegrenzer")
    wireless_charging: Optional[bool] = Field(None, description="Induktionsladen für Smartphones")
    auto_dimming_mirror: Optional[bool] = Field(None, description="Innenspiegel autom. abblendend")
    isofix: Optional[bool] = Field(None, description="Isofix Kindersitzbefestigung")
    isofix_passenger: Optional[bool] = Field(None, description="Isofix Beifahrersitz")
    leather_steering_wheel: Optional[bool] = Field(None, description="Lederlenkrad")
    led_headlights: Optional[bool] = Field(None, description="LED-Scheinwerfer")
    led_daytime_running_lights: Optional[bool] = Field(None, description="LED-Tagfahrlicht")
    alloy_wheels: Optional[bool] = Field(None, description="Leichtmetallfelgen")
    light_sensor: Optional[bool] = Field(None, description="Lichtsensor")
    lumbar_support: Optional[bool] = Field(None, description="Lordosenstütze")
    drowsiness_warning: Optional[bool] = Field(None, description="Müdigkeitswarner")
    multi_function_steering_wheel: Optional[bool] = Field(None, description="Multifunktionslenkrad")
    music_streaming: Optional[bool] = Field(None, description="Musikstreaming integriert")
    navigation_system: Optional[bool] = Field(None, description="Navigationssystem")
    non_smoking_vehicle: Optional[bool] = Field(None, description="Nichtraucher-Fahrzeug")
    emergency_brake_assist: Optional[bool] = Field(None, description="Notbremsassistent")
    emergency_call_system: Optional[bool] = Field(None, description="Notrufsystem")
    dab_radio: Optional[bool] = Field(None, description="Radio DAB")
    rain_sensor: Optional[bool] = Field(None, description="Regensensor")
    tire_pressure_monitoring: Optional[bool] = Field(None, description="Reifendruckkontrolle")
    seat_heating: Optional[bool] = Field(None, description="Sitzheizung")
    sound_system: Optional[bool] = Field(None, description="Soundsystem")
    sport_package: Optional[bool] = Field(None, description="Sportpaket")
    sports_seats: Optional[bool] = Field(None, description="Sportsitze")
    voice_control: Optional[bool] = Field(None, description="Sprachsteuerung")
    lane_keep_assist: Optional[bool] = Field(None, description="Spurhalteassistent")
    touchscreen: Optional[bool] = Field(None, description="Touchscreen")
    traction_control: Optional[bool] = Field(None, description="Traktionskontrolle")
    radio: Optional[bool] = Field(None, description="Tuner/Radio")
    usb: Optional[bool] = Field(None, description="USB")
    traffic_sign_recognition: Optional[bool] = Field(None, description="Verkehrszeichenerkennung")
    digital_dashboard: Optional[bool] = Field(None, description="Volldigitales Kombiinstrument")
    wifi_hotspot: Optional[bool] = Field(None, description="WLAN / Wifi Hotspot")
    central_locking: Optional[bool] = Field(None, description="Zentralverriegelung")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


"""Schemas for json to fill the database with car listings."""


class ListingCreateRequestSchema(BaseModel):
    brand: str = Field(..., description="Brand of the car")
    model: str = Field(..., description="Model of the car")
    registration_year: int = Field(..., description="Year the car was registered")
    mileage: Optional[int] = Field(None, description="Mileage of the car in kilometers")
    city_or_postal_code: Optional[str] = Field(None, description="City or postal code where the car is located")
    color: Optional[str] = Field(None, description="Color of the car")
    price: int = Field(..., description="Price of the car in the specified currency")
    currency: Optional[str] = Field("EUR", description="Currency of the price, e.g., EUR")
    url: str = Field(..., description="URL of the car listing")
    technical_details: TechnicalDetailsSchema
    equipment: EquipmentSchema

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


"""Filtering scheme for GET requests with query parameters."""


class ListingSchema(BaseModel):
    brand: Optional[str] = Field(None, description="Filter by car brand")
    model: Optional[str] = Field(None, description="Filter by car model")
    registration_year: Optional[int] = Field(None, description="Filter by registration year")
    mileage: Optional[int] = Field(None, description="Filter by mileage")
    city_or_postal_code: Optional[str] = Field(None, description="Filter by city or postal code")
    color: Optional[str] = Field(None, description="Filter by car color")
    price_lte: Optional[int] = Field(None, description="Filter by maximum price")
    price_gte: Optional[int] = Field(None, description="Filter by minimum price")

    class Config:
        orm_mode = True


"""Schemas for car listings, used in the analytics module."""


class ListingOut(BaseModel):
    id: int = Field(..., description="Unique identifier for the car listing")
    created_at: datetime = Field(..., description="Timestamp when the car listing was created")
    brand: str = Field(..., description="Brand of the car")
    model: str = Field(..., description="Model of the car")
    registration_year: int = Field(..., description="Year the car was registered")
    mileage: Optional[int] = Field(None, description="Mileage of the car in kilometers")
    city_or_postal_code: Optional[str] = Field(None, description="City or postal code where the car is located")
    color: Optional[str] = Field(None, description="Color of the car")
    price: float = Field(..., description="Price of the car in the specified currency")
    currency: Optional[str] = Field(..., description="Currency of the price, e.g., EUR")
    url: str = Field(..., description="URL of the car listing")
    technical_details: Optional[TechnicalDetailsSchema]
    equipment: Optional[EquipmentSchema]

    class Config:
        orm_mode = True


class ListingStats(BaseModel):
    avg_price: Optional[float] = Field(None, description="Average price of the car listings")
    min_price: Optional[float] = Field(None, description="Minimum price of the car listings")
    max_price: Optional[float] = Field(None, description="Maximum price of the car listings")
    count: Optional[int] = Field(None, description="Total number of car listings found")

    class Config:
        orm_mode = True


class ListingFilteredResponse(BaseModel):
    Listings: List[ListingOut]
    Stats: ListingStats

    class Config:
        orm_mode = True


class AvgPriceByBrand(BaseModel):
    brand: str
    avg_price: float = Field(..., description="Average price of the car model")
    max_price: float = Field(..., description="Maximum price of the car model")
    min_price: float = Field(..., description="Minimum price of the car model")
    count: int = Field(..., description="Number of listings for the car model")
