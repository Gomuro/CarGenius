# app/utils.py
from app.models.car import ListingMobileDe, TechnicalDetails, Equipment
from app.models.license import LicenseKey
from app.schemas.stats.analytics import ListingOut, ListingSchema


def flatten_listing(listing: ListingOut) -> dict:
    base = listing.dict()   # Convert Pydantic model to dict
    technical = base.pop("technical_details", {}) or {}   # Use empty dict if None
    equipment = base.pop("equipment", {}) or {}           # Use empty dict if None

    # if technical or equipment are Pydantic models, convert them to dict
    if hasattr(technical, "dict"):
        technical = technical.dict()
    if hasattr(equipment, "dict"):
        equipment = equipment.dict()

    return {**base, **technical, **equipment}   # Merge all dictionaries into one

def clean_filter_dict(raw: dict) -> dict:
    return {
        k: v for k, v in raw.items()
        if v not in ("string", 0, 0.0, None, "")
    }


def flatten_listing_mobilede(listing: ListingMobileDe) -> dict:
    base_fields = {
        "brand": listing.brand,
        "model": listing.model,
        "registration_year": listing.registration_year,
        "mileage": listing.mileage,
        "city_or_postal_code": listing.city_or_postal_code,
        "color": listing.color,
        "price": listing.price,
    }

    tech_fields = {}
    if listing.technical_details:
        tech_fields = {
            k: getattr(listing.technical_details, k)
            for k in TechnicalDetails.__table__.columns.keys()
            if k not in ("id", "listing_id")
        }

    eq_fields = {}
    if listing.equipment:
        eq_fields = {
            k: getattr(listing.equipment, k)
            for k in Equipment.__table__.columns.keys()
            if k not in ("id", "listing_id")
        }
    print("%%%%%%%%%%%%%%%%%", {**base_fields, **tech_fields, **eq_fields})
    return {**base_fields, **tech_fields, **eq_fields}


def flatten_listing_ml(obj) -> dict:
    if obj is None:
        return {}

    if hasattr(obj, "dict"):
        return obj.dict()

    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
        if hasattr(obj, column.name)
    }