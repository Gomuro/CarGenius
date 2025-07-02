# app/routers/stats/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import distinct, func
from app.core.database import get_db
from app.models.car import ListingMobileDe
from app.schemas.stats.analytics import AvgPriceByBrand, ListingSchema, TechnicalDetailsSchema, \
    EquipmentSchema, ListingCreateRequestSchema, ListingFilteredResponse
from app.services.license import get_license_by_key
from app.services.stats.analytics import get_avg_price_by_brand, get_filtered, listings_json_to_db, get_filtered_for_ml
import json
from app.utils import flatten_listing_ml
from ml.predict import predict_price
from typing import List

router = APIRouter()


@router.get("/filter-options")
async def get_filter_options(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Get all available filter options (brands, models, colors, years) without loading full dataset.
    This provides the options for filter dropdowns efficiently.
    """
    try:
        # Get distinct brands
        brands_result = await db.execute(
            select(distinct(ListingMobileDe.brand))
            .where(ListingMobileDe.is_active == True)
            .order_by(ListingMobileDe.brand)
        )
        brands = [brand for brand in brands_result.scalars().all() if brand is not None]

        # Get distinct models
        models_result = await db.execute(
            select(distinct(ListingMobileDe.model))
            .where(ListingMobileDe.is_active == True)
            .order_by(ListingMobileDe.model)
        )
        models = [model for model in models_result.scalars().all() if model is not None]

        # Get distinct colors
        colors_result = await db.execute(
            select(distinct(ListingMobileDe.color))
            .where(ListingMobileDe.is_active == True)
            .order_by(ListingMobileDe.color)
        )
        colors = [color for color in colors_result.scalars().all() if color is not None]

        # Get distinct years
        years_result = await db.execute(
            select(distinct(ListingMobileDe.registration_year))
            .where(ListingMobileDe.is_active == True)
            .order_by(ListingMobileDe.registration_year.desc())
        )
        years = [year for year in years_result.scalars().all() if year is not None]

        # Get price ranges (min/max for reference)
        price_result = await db.execute(
            select(
                func.min(ListingMobileDe.price),
                func.max(ListingMobileDe.price)
            ).where(ListingMobileDe.is_active == True)
        )
        min_price, max_price = price_result.one()

        return {
            "brands": brands,
            "models": models,
            "colors": colors,
            "years": years,
            "price_range": {
                "min": min_price or 0,
                "max": max_price or 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving filter options: {str(e)}")


@router.get("/filter-options/models")
async def get_models_for_brand(brand: str = None, db: AsyncSession = Depends(get_db)) -> List[str]:
    """
    Get distinct models, optionally filtered by brand.
    This is useful for cascading dropdowns.
    """
    try:
        query = select(distinct(ListingMobileDe.model)).where(ListingMobileDe.is_active == True)

        if brand and brand != "Any Brand":
            query = query.where(ListingMobileDe.brand == brand)

        query = query.order_by(ListingMobileDe.model)

        result = await db.execute(query)
        models = [model for model in result.scalars().all() if model is not None]
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving models: {str(e)}")


@router.get("/filter-options/colors")
async def get_colors_for_filters(
        brand: str = None,
        model: str = None,
        registration_year: int = None,
        db: AsyncSession = Depends(get_db)
) -> List[str]:
    """
    Get distinct colors, optionally filtered by brand, model, and year.
    This is useful for cascading dropdowns.
    """
    try:
        query = select(distinct(ListingMobileDe.color)).where(ListingMobileDe.is_active == True)

        if brand and brand != "Any Brand":
            query = query.where(ListingMobileDe.brand == brand)
        if model and model != "Any Model":
            query = query.where(ListingMobileDe.model == model)
        if registration_year:
            query = query.where(ListingMobileDe.registration_year == registration_year)

        query = query.order_by(ListingMobileDe.color)

        result = await db.execute(query)
        colors = [color for color in result.scalars().all() if color is not None]
        return colors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving colors: {str(e)}")


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
        equipment_filters: EquipmentSchema = Depends(),
        page: int = Query(ge=0, default=1),
        size: int = Query(ge=1, le=100, default=20),
        total: int = Query(ge=0, default=0)
) -> {ListingFilteredResponse}:
    """
    Search for car listings based on various filters.
    """
    return await get_filtered(
        db=db,
        listing_filters=listing_filters,
        tech_filters=tech_filters,
        equipment_filters=equipment_filters,
        page=page,
        size=size,
        total=total
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
            features.pop('price', None)  # do not submit target as input
            features = {
                k: (0 if v is None else v)
                for k, v in features.items()
            }
            input_for_model.append(features)
            valid_indexes.append(i)
            print(f"✅ Listing #{i} is valid for model input: {valid_indexes}")

        except Exception as e:
            print(f"Skip listing #{i} due to error: {e}")
    # Make a forecast only on valid
    predicted_prices = predict_price(input_for_model)

    offers = []

    for model_index, original_index in enumerate(valid_indexes):
        listing = listings[original_index]
        predicted = predicted_prices[model_index]
        actual = listing.price
        saving = predicted - actual

        offer = {
            "actual_price": actual,
            "predicted_price": predicted,
            "saving": saving,
            "brand": listing.brand,
            "model": listing.model,
            "registration_year": listing.registration_year,
            "meleage": listing.mileage,
            "color": listing.color,
            "url": listing.url,
        }
        offers.append(offer)

    # Sort by benefit and take the top 10
    top_offers = sorted(offers, key=lambda x: x["saving"], reverse=True)[:10]

    return {
        "top_offers": top_offers,
        "listings_count": len(flat_listings),
    }


@router.get("/average_price", response_model=list[AvgPriceByBrand])
async def get_average_price(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """
    Get average price, max price, min price, and count of car listings grouped by title.
    """
    return await get_avg_price_by_brand(limit, db)
