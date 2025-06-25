# app/services/ml.py
from pydantic import ValidationError
from sqlalchemy import or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.car import ListingMobileDe
from app.services.stats.analytics import get_filtered, get_filtered2, get_filtered3
from ml.predict import predict_price


async def get_best_offer_for(input_data: dict, db: AsyncSession) -> dict:
    predicted_price = predict_price([input_data])[0]

    similar_cars_stmt = select(ListingMobileDe).where(
        ListingMobileDe.brand == input_data["brand"],
        ListingMobileDe.model == input_data["model"],
        ListingMobileDe.mileage <= input_data["mileage"] + 10000,
        ListingMobileDe.power >= input_data["power"] - 20,
        ListingMobileDe.registration_year >= input_data["registration_year"] - 1
    )

    listings = (await db.execute(similar_cars_stmt)).scalars().all()

    best_offer = None
    best_saving = float("-inf")

    for listing in listings:
        listing_dict = listing.to_dict_full()
        predicted = predict_price([listing_dict])[0]
        saving = predicted - listing.price  # How much cheaper than the norm?
        if saving > best_saving:
            best_saving = saving
            best_offer = {
                "url": listing.url,
                "actual_price": listing.price,
                "predicted_price": predicted,
                "saving": saving
            }

    return {
        "your_input_predicted_price": predicted_price,
        "best_offer": best_offer
    }

def evaluate_offer(listing_data: dict) -> dict:
    predicted_price = predict_price([listing_data])
    actual_price = listing_data.get("price", 0)

    return {
        "actual_price": actual_price,
        "predicted_price": predicted_price,
        "difference": actual_price - predicted_price,
        "is_profitable": actual_price < predicted_price * 0.85
    }


def rank_listings_by_price(listings: list[dict]) -> list[dict]:
    listing_with_diff = []

    for listing in listings:
        predicted = predict_price([listing])
        actual = listing.get("price", 0)
        diff = actual - predicted
        listing_with_diff.append((diff, listing))

    return [item[1] for item in sorted(listing_with_diff, key=lambda x: x[0])]


import json

async def get_best_offer_for_license(db, license_key, ml_model):
    raw_filters = license_key.filters or []

    try:
        filters = json.loads(raw_filters) if isinstance(raw_filters, str) else raw_filters
    except Exception as e:
        print(f"❌ Failed to parse filters JSON: {e}")
        return None

    best_listing = None
    best_score = float('-inf')

    for f in filters:
        print("🔍 Using filter:", f)
        results = await get_filtered2(db, filters=[f])

        for item in results:
            score = ml_model.predict(item)
            print("📊 Predicted score:", score)

            if score > best_score:
                best_score = score
                best_listing = item

    print("✅ Best listing:", best_listing)
    return best_listing
