# server/ml/predict.py
from typing import List
import pandas as pd
from .features import preprocess_data
from .model_utils import load_model


def predict_price(input_data_list: List[dict]) -> List[float]:
    """ Predict car prices based on input data."""
    model, features, scaler = load_model()  # Load the model, features, scaler, imputers, indicator
    df = pd.DataFrame(input_data_list).drop(columns=["price"], errors="ignore")

    # Check for complex types in columns
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
            raise ValueError(f"Column '{col}' contains non-scalar values")

    # Invoke preprocess_data from scaler (fit=False)
    df, _ = preprocess_data(df, fit=False, scaler=scaler)

    # We ensure the correct order of columns (fill in missing 0)
    df = df.reindex(columns=features, fill_value=0)

    # Forecast
    return model.predict(df).tolist()
