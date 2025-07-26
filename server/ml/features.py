# server/ml/features.py
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CATEGORICAL_COLS = [
    "brand",
    "model",
    "engine_type",
]

NUMERIC_COLS = [
    "registration_year",
    "mileage",
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
        required_cols = ["registration_year", "brand", "model", "engine_type", "price", "mileage"]
    else:
        required_cols = ["registration_year", "brand", "model", "engine_type", "mileage"]

    df = df.dropna(subset=required_cols)
    if df.empty:
        raise ValueError("DataFrame is empty after preprocessing. Check your data or relax the dropna rules.")

    print("After dropna:", df.shape)

    df = pd.get_dummies(df, columns=CATEGORICAL_COLS)

    allowed_cols = [col for col in df.columns if col.startswith('brand_') 
                    or col.startswith('model_') 
                    or col.startswith('engine_type_')
                    or col.startswith('fuel_type_')
                    or col.startswith('price')
                    or col.startswith('registration_year')
                    or col.startswith('mileage')
                    or col in NUMERIC_COLS]
    df = df[allowed_cols]

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
