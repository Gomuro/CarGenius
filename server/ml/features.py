# server/ml/features.py
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CATEGORICAL_COLS = [
    "brand",
    "model",
    "color",
    "city_or_postal_code",
    "damage_condition",
    "category",
    "trim_line",
    "country_version",
    "engine_type",
    "transmission",
    "emissions_sticker",
    "climatisation",
    "park_assists",
    "airbags",
    "manufacturer_color_name",
    "interior",
    "warranty_registration",
    "sku",
    "other_energy_source",
    "battery",
    "battery_certificate",
    "abs",
    "adaptive_cruise_control",
    "distance_warning",
    "all_wheel_drive",
    "ambient_lighting",
    "android_auto",
    "tow_bar_swiveling",
    "apple_carplay",
    "armrest",
    "heated_windshield",
    "bluetooth",
    "board_computer",
    "power_windows",
    "power_tailgate",
    "power_mirrors",
    "immobilizer",
    "esp",
    "high_beam_assist",
    "hands_free",
    "warranty",
    "speed_limiter",
    "wireless_charging",
    "auto_dimming_mirror",
    "isofix",
    "isofix_passenger",
    "leather_steering_wheel",
    "led_headlights",
    "led_daytime_running_lights",
    "alloy_wheels",
    "light_sensor",
    "lumbar_support",
    "drowsiness_warning",
    "multi_function_steering_wheel",
    "music_streaming",
    "navigation_system",
    "non_smoking_vehicle",
    "emergency_brake_assist",
    "emergency_call_system",
    "dab_radio",
    "rain_sensor",
    "tire_pressure_monitoring",
    "seat_heating",
    "sound_system",
    "sport_package",
    "sports_seats",
    "voice_control",
    "lane_keep_assist",
    "touchscreen",
    "traction_control",
    "radio",
    "usb",
    "traffic_sign_recognition",
    "digital_dashboard",
    "wifi_hotspot",
    "central_locking",
]

NUMERIC_COLS = [
    "registration_year",
    "mileage",
    "power",
    "battery_capacity",
    "battery_range",
    "num_seats",
    "door_count",
    "first_year_registration",
    "first_month_registration",
    "number_of_previous_owners",
    "hu_year",
    "hu_month",
    "trailer_load_braked",
    "trailer_load_unbraked",
    "net_weight",
]


def preprocess_data(df: pd.DataFrame, fit=False, scaler=None):
    df = df.copy()
    df = df.drop(columns=df.select_dtypes(include=["datetime", "datetimetz"]).columns, errors="ignore")

    df[NUMERIC_COLS] = df[NUMERIC_COLS].apply(pd.to_numeric, errors='coerce')
    for col in CATEGORICAL_COLS:
        if col not in df.columns:
            df[col] = np.nan

    print("Before dropna:", df.shape)
    if fit:
        required_cols = ["price", "mileage", "power", "registration_year"]
    else:
        required_cols = ["mileage", "power", "registration_year"]

    df = df.dropna(subset=required_cols)
    if df.empty:
        raise ValueError("DataFrame is empty after preprocessing. Check your data or relax the dropna rules.")

    print("After dropna:", df.shape)

    df = pd.get_dummies(df, columns=CATEGORICAL_COLS)

    if fit:
        scaler = StandardScaler()
        df[NUMERIC_COLS] = df[NUMERIC_COLS].fillna(0)
        scaled = scaler.fit_transform(df[NUMERIC_COLS])
    if not fit and "price" in df.columns:
        print("❌ Error: price remained in df after preprocessing!")

    else:
        if scaler is None:
            raise ValueError("Scaler must be provided when fit=False")
        scaled = scaler.transform(df[NUMERIC_COLS])

    df[NUMERIC_COLS] = scaled

    return df, scaler
