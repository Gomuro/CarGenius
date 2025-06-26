# app/routers/stats/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.car import ListingMobileDe
from app.schemas.stats.analytics import AvgPriceByBrand, ListingSchema, TechnicalDetailsSchema, \
    EquipmentSchema, ListingCreateRequestSchema, ListingFilteredResponse
from app.services.license import get_license_by_key
from app.services.stats.analytics import get_avg_price_by_brand, get_filtered, listings_json_to_db, get_filtered_for_ml
import json
from app.utils import flatten_listing_ml
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
            data = json.load(file)  # Load JSON data from the file
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{file_path} not found")

    if isinstance(data, list):
        listing_data = data
    elif isinstance(data, dict):
        listing_data = [data]
    else:
        raise HTTPException(status_code=400, detail="Invalid data format. Expected a list or a dictionary.")
    created = 0
    skipped = 0
    for item in listing_data:
        try:
            combined_data = {
                **item.get("listing", {}),
                "technical_details": item.get("technical_details", {}),
                "equipment": item.get("equipment", {})
            }
            existing_listing = await db.execute(
                select(ListingMobileDe).where(ListingMobileDe.url == combined_data.get("url"))
            )
            if existing_listing.scalar_one_or_none():  # Check if listing with the same URL already exists
                skipped += 1
                continue

            listing = ListingCreateRequestSchema(**combined_data)
            await listings_json_to_db(db=db, data=listing)
            created += 1
        except Exception as e:
            print(f"Error processing item {item}: {e}")

    return {
        "message": f"Successfully saved {created} listings to the database.",
        "skipped": skipped
    }


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


@router.get("/ml_best_price_search", response_model=dict)
async def ml_best_price_search(key: str, db: AsyncSession = Depends(get_db)):
    license_obj = await get_license_by_key(db, key)
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")

    listings = await get_filtered_for_ml(db=db, license_key=license_obj)
    flat_listings = await flatten_listing_ml(listings)  # [{'brand': ..., 'mileage': ..., ...}, {...}, ...]
    if not flat_listings:
        return {"detail": "No listings found"}
    valid_indexes = []
    input_for_model = []
    for i, features in enumerate(flat_listings):
        try:
            features = dict(features)
            features.pop('price', None)  # 🛑 do not submit target as input
            features = {
                k: (0 if v is None else v)
                for k, v in features.items()
            }
            input_for_model.append(features)
            valid_indexes.append(i)
            print(f"✅ Listing #{i} is valid for model input: {valid_indexes}")

        except Exception as e:
            print(f"⚠️ Skip listing #{i} due to error: {e}")
    # Make a forecast only on valid
    predicted_prices = predict_price(input_for_model)

    best_offer = None
    max_saving = float("-inf")

    for model_index, original_index in enumerate(valid_indexes):  #
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
                "brand": listing.brand,
                "model": listing.model,
                "url": listing.url,
            }
    print("✅ Model input columns:", list(input_for_model[0].keys()))  # Shows the columns used for prediction
    print("✅ Model predicted prices:", predicted_prices)  # Shows the predicted prices for each listing

    return {
        "best_offer": best_offer,
        "listings_count": len(flat_listings),
        "listings": flat_listings,
    }


@router.get("/average_price", response_model=list[AvgPriceByBrand])
async def get_average_price(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """
    Get average price, max price, min price, and count of car listings grouped by title.
    """
    return await get_avg_price_by_brand(limit, db)
