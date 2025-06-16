# # app/routers/ml.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.routers.stats.analytics import get_listings_by_filters
from app.schemas.license import ListingFilter
from app.schemas.stats.analytics import ListingSchema, TechnicalDetailsSchema, EquipmentSchema, ListingOut, ListingStats
from app.services.license import get_license_by_key
from app.services.ml import evaluate_offer, rank_listings_by_price
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





@router.get("/{license_key}/best-price", response_model=List[ListingFilter])
async def get_best_price_listings(
    license_key: str,
    db: AsyncSession = Depends(get_db),
):
    # Step 1: Get License and filters
    license_obj = await get_license_by_key(db, license_key)
    if not license_obj:
        raise HTTPException(status_code=404, detail="License key not found")

    filters = license_obj.filters or []
    if not filters:
        raise HTTPException(status_code=400, detail="No filters saved for this license key")

    # Step 2: Query listings applying filters
    listings = await get_listings_by_filters(db, filters)
    if not listings:
        return []  # no matches

    # Step 3: Rank listings with ML or heuristic
    ranked_listings = rank_listings_by_price(listings)

    # Step 4: Return top N results (e.g., top 10)
    top_results = ranked_listings[:10]
    return top_results