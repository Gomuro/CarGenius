# app/routers/stats/analytics.py
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.car import ListingMobileDe, TechnicalDetails, Equipment
from app.models.license import LicenseKey
from app.schemas.ml import ListingFilterML, ListingCreateRequestMLSchema, ListingSchemaML
from app.schemas.stats.analytics import AvgPriceByBrand, ListingSchema, TechnicalDetailsSchema, \
    EquipmentSchema, ListingCreateRequestSchema, ListingFilteredResponse
from app.services.license import get_license_by_key
from app.services.stats.analytics import get_avg_price_by_brand, get_filtered, listings_json_to_db, get_filtered2, \
    get_filtered_from_license_key, get_filtered3
import json

from ml.predict import predict_price

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


@router.get("/filter-search", response_model=ListingFilteredResponse)
async def search_listings(
        db: AsyncSession = Depends(get_db),
        listing_filters: ListingSchema = Depends(),
        tech_filters: TechnicalDetailsSchema = Depends(),
        equipment_filters: EquipmentSchema = Depends()
) -> {ListingFilteredResponse}:
    """
    Search for car listings based on various filters.
    """
    return await get_filtered(
        db=db,
        listing_filters=listing_filters,
        tech_filters=tech_filters,
        equipment_filters=equipment_filters
    )

async def flatten_listing_ml(listings: list[ListingSchemaML]) -> list[dict]:
    flat_listings = []

    for listing in listings:
        listing_dict = listing.dict()
        # print("!!!!!!#########Flattening listings for ML model...", listing_dict)
        # print('!!!!!!!!!!listing', listing_dict)
        flat_listing = ({k: v for k, v in listing_dict.items() if k not in ["technical_details", "equipment"]})
        # print("#########Flat listing without details:", flat_listing)

        technical_details = listing_dict.get("technical_details", {}) or {}
        equipment = listing_dict.get("equipment", {}) or {}

        flat_listing.update(technical_details)
        flat_listing.update(equipment)

        for k, v in flat_listing.items():
            if isinstance(v, bool):
                flat_listing[k] = int(v)
        flat_listings.append(flat_listing)
    return flat_listings


@router.get("/filter-search2", response_model=dict)
async def search_listings2(key: str, db: AsyncSession = Depends(get_db)):
    license_obj = await get_license_by_key(db, key)
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    listings = await get_filtered3(db=db, license_key=license_obj)
    print("!!!!!!!!!!#########Flattening listings for ML model...", listings)
    flat_listings = await flatten_listing_ml(listings)  # [{'brand': ..., 'mileage': ..., ...}, {...}, ...]
    if not flat_listings:
        return {"detail": "No listings found"}

    valid_indexes = []
    input_for_model = []

    for i, features in enumerate(flat_listings):
        try:
            features = dict(features)
            features.pop('price', None)  # 🛑 не подаємо на вхід target
            features = {
                k: (0 if v is None else v)
                for k, v in features.items()
            }
            input_for_model.append(features)
            valid_indexes.append(i)
        except Exception as e:
            print(f"⚠️ Skip listing #{i} due to error: {e}")
    # Робимо прогноз тільки по валідним
    predicted_prices = predict_price(input_for_model)
    # print("Len listings:", len(listings))
    # print("Len flat_listings:", len(flat_listings))
    # print("Len predicted_prices:", len(predicted_prices))

    best_offer = None
    max_saving = float("-inf")

    for model_index, original_index in enumerate(valid_indexes):
        listing = listings[original_index]
        predicted = predicted_prices[model_index]
        actual = listing.price
        saving = predicted - actual

        if saving > max_saving:
            max_saving = saving
            best_offer = {
                "actual_price": actual,
                "predicted_price": predicted,
                "saving": saving,
            }
    print("✅ Model input columns:", list(input_for_model[0].keys()))
    print("✅ Model predicted prices:", predicted_prices)

    return {
        "best_offer": best_offer,
        "listings_count": len(flat_listings),
    }

@router.get("/average_price", response_model=list[AvgPriceByBrand])
async def get_average_price(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """
    Get average price, max price, min price, and count of car listings grouped by title.
    """
    return await get_avg_price_by_brand(limit, db)
