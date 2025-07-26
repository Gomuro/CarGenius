# server/ml/model_utils.py
import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # ml/
MODEL_PATH = os.path.join(BASE_DIR, "model", "price_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "model", "scaler.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "model", "model_features.pkl")

def load_model():
    """
    Loads the trained model, features, scaler, and imputers/indicator for preprocessing.
    Returns: model, features, scaler, num_imputer, cat_imputer, missing_indicator
    """
    model = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)
    scaler = joblib.load(SCALER_PATH)
   
    return model, features, scaler,


def get_ml_model():
    model, features, scaler = load_model()
    return model
