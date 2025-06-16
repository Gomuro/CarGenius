# server/ml/features.py
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CATEGORICAL_COLS = [
    "brand",
    "model",
    "color",
    "city_or_postal_code",
    "currency",
    "url",
    "is_active",
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
    print("!!!!!!", df.columns)

    df[NUMERIC_COLS] = df[NUMERIC_COLS].apply(pd.to_numeric, errors='coerce')

    print("Before dropna:", df.shape)
    # df = df.dropna(subset=NUMERIC_COLS + ["price"])
    REQUIRED_COLS = ["price", "mileage", "power", "registration_year"]
    df = df.dropna(subset=REQUIRED_COLS)
    if df.empty:
        raise ValueError("DataFrame is empty after preprocessing. Check your data or relax the dropna rules.")

    print("After dropna:", df.shape)
    print("$$$$$$$$$$$$$", df[NUMERIC_COLS + ["price"]].isna().sum())

    df = pd.get_dummies(df, columns=CATEGORICAL_COLS)

    if fit:
        scaler = StandardScaler()
        df[NUMERIC_COLS] = df[NUMERIC_COLS].fillna(0)

        scaled = scaler.fit_transform(df[NUMERIC_COLS])
    else:
        scaled = scaler.transform(df[NUMERIC_COLS])

    df[NUMERIC_COLS] = scaled

    return df, scaler

