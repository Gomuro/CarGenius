# # app/routers/ml.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.stats.analytics import ListingSchema, TechnicalDetailsSchema, EquipmentSchema, ListingOut, ListingStats
from app.services.ml import evaluate_offer
from app.services.stats.analytics import get_filterd

router = APIRouter()

def create_listing_filter_from_input(data: dict) -> ListingSchema:
    return ListingSchema(
        registration_year=data.get("registration_year"),
        mileage=data.get("mileage"),
    )

def create_tech_filter_from_input(data: dict) -> TechnicalDetailsSchema:
    return TechnicalDetailsSchema(
        power=data.get("power"),
        fuel_type=data.get("fuel_type"),
    )

def create_equipment_filter_from_input(data: dict) -> EquipmentSchema:
    return EquipmentSchema(
        navigation_system=data.get("navigation_system"),
        climate_control=data.get("climate_control"),
    )

from pydantic import BaseModel
from typing import Optional

class PredictPriceRequest(BaseModel):
    registration_year: Optional[int]
    mileage: Optional[int]
    power: Optional[int]
    fuel_type: Optional[str]
    transmission: Optional[str]
    body_type: Optional[str]
    color: Optional[str]
    door_count: Optional[int]
    num_seats: Optional[int]
    number_of_previous_owners: Optional[int]
    climate_control: Optional[bool]
    navigation_system: Optional[bool]
    park_assist: Optional[bool]
    panoramic_roof: Optional[bool]
    leather_seats: Optional[bool]

# 📁 app/schemas/ml.py

from typing import List
from pydantic import BaseModel


class PricePredictionResponse(BaseModel):
    predicted_price: float
    actual_price: float
    difference: float
    is_profitable: bool
    similar_listings: list[ListingOut]
    stats: ListingStats


@router.post("/ml/suggest-price", response_model=PricePredictionResponse)
async def suggest_price(
    payload: PredictPriceRequest,
    db: AsyncSession = Depends(get_db)
):

    predicted_price = evaluate_offer(payload.dict())

    listing_filters = create_listing_filter_from_input(payload.dict())
    tech_filters = create_tech_filter_from_input(payload.dict())
    equipment_filters = create_equipment_filter_from_input(payload.dict())

    response = await get_filterd(
        db=db,
        listing_filters=listing_filters,
        tech_filters=tech_filters,
        equipment_filters=equipment_filters
    )

    return {
        "predicted_price": predicted_price,
        "similar_listings": response.Listings,
        "stats": response.Stats
    }
