# app/shemas/car.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime

from pydantic.networks import HttpUrl


class CarBase(BaseModel):
    brand: str
    price: float
    currency: Optional[str] = "EUR"
    url: HttpUrl
    mileage: Optional[float] = None
    power: Optional[str] = None
    transmission: Optional[str] = None
    first_year_registration: Optional[int] = None
    first_mont_registration: Optional[int] = None
    number_of_previous_owners: Optional[str] = None
    battery_range: Optional[str] = None
    warranty_registration: Optional[str] = None


class CarCreate(CarBase):
    pass


class CarUpdate(CarBase):
    is_active: Optional[bool] = None


class CarOut(CarBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  # Enable ORM mode for compatibility with SQLAlchemy models
