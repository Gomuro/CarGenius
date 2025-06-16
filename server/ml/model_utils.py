# server/ml/model_utils.py
import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # ml/
MODEL_PATH = os.path.join(BASE_DIR, "model", "price_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "model", "scaler.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "model", "model_features.pkl")

def load_model():
    model = joblib.load(MODEL_PATH)         # Load the trained model ["RandomForestRegressor"]
    features = joblib.load(FEATURES_PATH)   # Load the features used in training ["price", "mileage", "power", "registration_year", ...]
    return model, features
