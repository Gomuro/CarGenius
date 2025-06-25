# app/schemas/license.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from .stats.analytics import ListingSchema, TechnicalDetailsSchema, EquipmentSchema


class LicenseCreateRequest(BaseModel):
    client_info: Optional[str] = None

    class Config:
        orm_mode = True


class LicenseValidateRequest(BaseModel):
    key: str
    device_id: Optional[str] = None
    client_info: str

    class Config:
        orm_mode = True


class LicenseValidateResponse(BaseModel):
    is_valid: bool
    message: Optional[str] = None

    class Config:
        orm_mode = True


class ListingFilter(ListingSchema, TechnicalDetailsSchema, EquipmentSchema):
    # This class inherits all fields from the other schemas.
    # Pydantic will ensure all fields are optional by default when they are defined with Optional[...]
    # or have a default value in the parent schemas.
    # We can add a Config class if we need to override behavior.
    class Config:
        allow_population_by_field_name = True
        orm_mode = True
        extra = "forbid"  # This will reject any fields not defined in the schema


class LicenseCreateResponse(BaseModel):
    key: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    client_info: Optional[str]
    filters: Optional[List[ListingFilter]] = []

    class Config:
        orm_mode = True


class ListingMlOut(BaseModel):
    id: int
    brand: str
    model: str
    price: int
    mileage: int
    registration_year: int

    class Config:
        orm_mode = True
