# server/app/models/car.py
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, Date, func, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.db_mixins import TimestampMixin


class ListingMobileDe(TimestampMixin, Base):
    """Represents a car listing in the database."""
    __tablename__ = "listing_mobilede"

    id = Column(Integer, primary_key=True, index=True)
    # Relationships
    technical_details = relationship("TechnicalDetails", uselist=False, back_populates="listing_mobilede",
                                     passive_deletes=True)  # One-to-one relationship with TechnicalDetails    (uselist=False means this is a single object, not a list.)
    equipment = relationship("Equipment", uselist=False, back_populates="listing_mobilede",
                             passive_deletes=True)  # One-to-one relationship with Equipment

    is_active = Column(Boolean, default=True, index=True)
    # Basic Info
    brand = Column(String, index=True, nullable=False)
    model = Column(String, index=True, nullable=False)
    registration_year = Column(Integer, index=True, nullable=False)
    mileage = Column(Integer, index=True, nullable=True)
    city_or_postal_code = Column(String, index=True, nullable=True)
    color = Column(String, index=True, nullable=True)
    price = Column(Integer, index=True, nullable=False)
    currency = Column(String, default='EUR')
    url = Column(Text, unique=True, nullable=False)


class TechnicalDetails(Base):
    __tablename__ = "technical_details"

    id = Column(Integer, primary_key=True, index=True)
    # Relationships
    listing_id = Column(Integer, ForeignKey("listing_mobilede.id", ondelete="CASCADE"),
                        unique=True)  # One-to-one relationship with ListingMobileDe
    listing_mobilede = relationship("ListingMobileDe",
                                    back_populates="technical_details")  # Back-reference to ListingMobileDe

    damage_condition = Column(String, index=True, nullable=True)
    category = Column(String, index=True, nullable=True)
    trim_line = Column(String, nullable=True)
    sku = Column(String, unique=True, nullable=True)  # Individual code
    country_version = Column(String, nullable=True)  # Deutsche Ausführung
    power = Column(Integer, nullable=True)  # 210 kW (286 PS)
    engine_type = Column(String, index=True, nullable=True)  # Elektromotor
    other_energy_source = Column(String, nullable=True)  # Strom
    battery = Column(String, nullable=True)  # z.B. "inklusive"
    battery_capacity = Column(Float, nullable=True)  # 82 kWh
    battery_certificate = Column(String, nullable=True)  # Getestet vom Händler
    battery_range = Column(Integer, nullable=True)  # 500 km
    num_seats = Column(Integer, nullable=True)  # 5
    door_count = Column(Integer, nullable=True)  # 4/5
    transmission = Column(String, index=True, nullable=True)  # Automatik
    emissions_sticker = Column(String, nullable=True)  # 4 (Grün)
    first_year_registration = Column(Integer, index=True, nullable=True)
    first_month_registration = Column(Integer, index=True, nullable=True)
    number_of_previous_owners = Column(String, nullable=True)  # 1
    hu_year = Column(Integer, nullable=True)
    hu_month = Column(Integer, nullable=True)
    climatisation = Column(String, nullable=True)  # 3-Zonen-Klimaautomatik
    park_assists = Column(String, nullable=True)  # Vorne, Hinten, Kamera
    airbags = Column(String, nullable=True)  # Front-, Seiten- und weitere Airbags
    manufacturer_color_name = Column(String, nullable=True)  # Navarrablau Metallic
    interior = Column(String, nullable=True)  # Teilleder, Schwarz
    trailer_load_braked = Column(Integer, nullable=True)  # 1.200 kg
    trailer_load_unbraked = Column(Integer, nullable=True)  # 750 kg
    net_weight = Column(Integer, nullable=True)  # 2.235 kg
    waranty_registration = Column(String, nullable=True)  # Garantie ab Erstzulassung


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    # Relationships
    listing_id = Column(Integer, ForeignKey("listing_mobilede.id", ondelete="CASCADE"),
                        unique=True)  # One-to-one relationship with ListingMobileDe (uselist=False means this is a single object, not a list.)
    listing_mobilede = relationship("ListingMobileDe", back_populates="equipment",
                                    uselist=False)  # Back-reference to ListingMobileDe

    abs = Column(Boolean, default=False)
    adaptive_cruise_control = Column(Boolean, default=False)
    distance_warning = Column(Boolean, default=False)
    all_wheel_drive = Column(Boolean, default=False)
    ambient_lighting = Column(Boolean, default=False)
    android_auto = Column(Boolean, default=False)
    tow_bar_swiveling = Column(Boolean, default=False)
    apple_carplay = Column(Boolean, default=False)
    armrest = Column(Boolean, default=False)
    heated_windshield = Column(Boolean, default=False)
    bluetooth = Column(Boolean, default=False)
    board_computer = Column(Boolean, default=False)
    power_windows = Column(Boolean, default=False)
    power_tailgate = Column(Boolean, default=False)
    power_mirrors = Column(Boolean, default=False)
    immobilizer = Column(Boolean, default=False)
    esp = Column(Boolean, default=False)
    high_beam_assist = Column(Boolean, default=False)
    hands_free = Column(Boolean, default=False)
    warranty = Column(Boolean, default=False)
    speed_limiter = Column(Boolean, default=False)
    wireless_charging = Column(Boolean, default=False)
    auto_dimming_mirror = Column(Boolean, default=False)
    isofix = Column(Boolean, default=False)
    isofix_passenger = Column(Boolean, default=False)
    leather_steering_wheel = Column(Boolean, default=False)
    led_headlights = Column(Boolean, default=False)
    led_daytime_running_lights = Column(Boolean, default=False)
    alloy_wheels = Column(Boolean, default=False)
    light_sensor = Column(Boolean, default=False)
    lumbar_support = Column(Boolean, default=False)
    drowsiness_warning = Column(Boolean, default=False)
    multi_function_steering_wheel = Column(Boolean, default=False)
    music_streaming = Column(Boolean, default=False)
    navigation_system = Column(Boolean, default=False)
    non_smoking_vehicle = Column(Boolean, default=False)
    emergency_brake_assist = Column(Boolean, default=False)
    emergency_call_system = Column(Boolean, default=False)
    dab_radio = Column(Boolean, default=False)
    rain_sensor = Column(Boolean, default=False)
    tire_pressure_monitoring = Column(Boolean, default=False)
    seat_heating = Column(Boolean, default=False)
    sound_system = Column(Boolean, default=False)
    sport_package = Column(Boolean, default=False)
    sports_seats = Column(Boolean, default=False)
    voice_control = Column(Boolean, default=False)
    lane_keep_assist = Column(Boolean, default=False)
    touchscreen = Column(Boolean, default=False)
    traction_control = Column(Boolean, default=False)
    radio = Column(Boolean, default=False)
    usb = Column(Boolean, default=False)
    traffic_sign_recognition = Column(Boolean, default=False)
    digital_dashboard = Column(Boolean, default=False)
    wifi_hotspot = Column(Boolean, default=False)
    central_locking = Column(Boolean, default=False)
