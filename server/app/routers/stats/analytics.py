# app/routers/stats/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.stats.analytics import AvgPriceByBrand, ListingOut, ListingSchema, TechnicalDetailsSchema, \
    EquipmentSchema, ListingCreateRequestSchema
from app.services.stats.analytics import get_avg_price_by_brand, get_filterd, listings_json_to_db
from app.services.stats.filter_mobilde import filtered_listings
import json

router = APIRouter()


@router.post("/json-to-db")
async def save_listing_to_db(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Save a car listing to the database.
    """

    file_path = "car_data_Audi_1.json"
    try:
        with open(file_path, "r", encoding="utf8") as file:
            data = json.load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{file_path} not found")

    if isinstance(data, list):
        listing_data = data
    elif isinstance(data, dict):
        listing_data = [data]
    else:
        raise HTTPException(status=400, detail="Invalid data format. Expected a list or a dictionary.")
    created = 0
    for item in listing_data:
        try:
            combined_data = {
                **item.get("listing", {}),
                "technical_details": item.get("technical_details", {}),
                "equipment": item.get("equipment", {})
            }

            listing = ListingCreateRequestSchema(**combined_data)
            await listings_json_to_db(db=db, data=listing)
            created += 1
        except Exception as e:
            print(f"Error processing item {item}: {e}")

    return {"message": f"Successfully saved {created} listings to the database."}




@router.get("/filter-search", response_model=list[ListingOut])
async def search_listings(
        db: AsyncSession = Depends(get_db),
        listing_filters: ListingSchema = Depends(),
        tech_filters: TechnicalDetailsSchema = Depends(),
        equipment_filters: EquipmentSchema = Depends()
) -> list[ListingOut]:
    """
    Search for car listings based on various filters.
    """
    return await get_filterd(
        db=db,
        listing_filters=listing_filters,
        tech_filters=tech_filters,
        equipment_filters=equipment_filters
    )


@router.get("/average_price", response_model=list[AvgPriceByBrand])
async def get_average_price(limit: int=20, db: AsyncSession = Depends(get_db)):
    """
    Get average price, max price, min price, and count of car listings grouped by title.
    """
    return await get_avg_price_by_brand(limit, db)
