# # app/routers/ml.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.license import LicenseKey
from app.schemas.license import ListingFilter, ListingMlOut
from app.schemas.ml import PredictPriceRequest, PricePredictionResponse, ListingFilterML, ListingSchemaML, CarFeatures
from app.schemas.stats.analytics import ListingSchema, TechnicalDetailsSchema, EquipmentSchema, ListingOut
from app.services.license import get_license_by_key
from app.services.ml import evaluate_offer, rank_listings_by_price, get_best_offer_for_license
from app.services.stats.analytics import get_filtered
from app.utils import flatten_listing_ml
from ml.model_utils import load_model, get_ml_model
from ml.predict import predict_price

router = APIRouter()



@router.post("predict-best-price/")
async def predict_best_price(car_data: CarFeatures):
    try:
        input_data = [car_data.dict()]
        prediction = predict_price(input_data)
        print("🔮 PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPredicted price:", prediction)
        return {"predicted_price": prediction[0]}
    except Exception as e:
        print("❌ Error during prediction:", str(e))
        raise HTTPException(status_code=500, detail="Prediction failed " + str(e))



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


@router.post("/ml/suggest-price", response_model=PricePredictionResponse)
async def suggest_price(
    payload: PredictPriceRequest,
    db: AsyncSession = Depends(get_db)
):

    predicted_price = evaluate_offer(payload.dict())

    listing_filters = create_listing_filter_from_input(payload.dict())
    tech_filters = create_tech_filter_from_input(payload.dict())
    equipment_filters = create_equipment_filter_from_input(payload.dict())

    response = await get_filtered(
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


@router.get("/ml/{key}/best-offer", response_model=ListingSchemaML)
async def get_best_offer(key: str, db: AsyncSession = Depends(get_db)):
    license = await get_license_by_key(db, key)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")

    ml_model = get_ml_model()

    best_listing = await get_best_offer_for_license(db, license, ml_model)
    if not best_listing:
        raise HTTPException(status_code=404, detail="No suitable listings found")

    return ListingSchemaML(
        **flatten_listing_ml(best_listing),
        **(flatten_listing_ml(best_listing.technical_details) if best_listing.technical_details else {}),
        **(flatten_listing_ml(best_listing.equipment) if best_listing.equipment else {})
    )
