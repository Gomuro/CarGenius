# app/utils.py
from app.schemas.stats.analytics import ListingSchemaML


async def flatten_listing_ml(listings: list[ListingSchemaML]) -> list[dict]:
    flat_listings = []

    for listing in listings:
        listing_dict = listing.dict()
        flat_listing = ({k: v for k, v in listing_dict.items() if k not in ["technical_details", "equipment"]})

        technical_details = listing_dict.get("technical_details", {}) or {}
        equipment = listing_dict.get("equipment", {}) or {}

        flat_listing.update(technical_details)
        flat_listing.update(equipment)

        for k, v in flat_listing.items():
            if isinstance(v, bool):
                flat_listing[k] = int(v)
        flat_listings.append(flat_listing)
    return flat_listings
