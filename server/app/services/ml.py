from app.models.car import ListingMobileDe
from app.schemas.license import ListingFilter
from ml.predict import predict_price

def evaluate_offer(listing_data: dict) -> dict:
    predicted_price = predict_price(listing_data)
    actual_price = listing_data.get("price", 0)

    return {
        "actual_price": actual_price,
        "predicted_price": predicted_price,
        "difference": actual_price - predicted_price,
        "is_profitable": actual_price < predicted_price * 0.85
    }




from typing import List

def rank_listings_by_price(listings: List[ListingFilter]) -> List[ListingFilter]:
    """
    ML or heuristic function to rank listings by best price.
    Here we simply sort ascending by price as a placeholder.
    """
    return sorted(listings, key=lambda x: x.price)
