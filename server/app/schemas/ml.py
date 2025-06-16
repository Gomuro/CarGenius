# app/schemas/ml.py
from typing import Any, Dict
from pydantic import BaseModel


class MLInput(BaseModel):
    data: Dict[str, Any]

class PricePredictionRequest(BaseModel):
    data: Dict

class PricePrediction(BaseModel):
    predicted_price: float