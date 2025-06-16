# server/ml/predict.py
import pandas as pd
from .model_utils import load_model


def predict_price(input_data: dict) -> float:
    model, features = load_model()

    df = pd.DataFrame([input_data])

    # One-hot encoding
    df = pd.get_dummies(df)

    for col in features:
        if col not in df.columns:
            df[col] = 0

    df = df[features]   # Sort columns to match the model's training order

    prediction = model.predict(df)[0]
    return round(prediction, 2)
