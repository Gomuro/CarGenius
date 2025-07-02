# app/services/stats/analytics.py
import math
from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import joinedload

from app.models.car import ListingMobileDe, Equipment, TechnicalDetails
from app.models.license import LicenseKey
from app.schemas.stats.analytics import AvgPriceByBrand, ListingSchema, TechnicalDetailsSchema, EquipmentSchema, \
    ListingCreateRequestSchema, ListingOut, ListingFilteredResponse, ListingStats, ListingSchemaML
from app.services.stats.filter_mobilde import filtered_listings, filtered_tech_details, filtered_equipment


async def get_filtered_for_ml(
        db: AsyncSession,
        license_key: LicenseKey
) -> list[ListingSchemaML]:
    """
    Filtering listings with JOIN on TechnicalDetails and Equipment.
    This logic assumes filters for different car models are ORed,
    and specific criteria within one car model are ANDed.
    """
    filter_groups = []
    # A filter group represents one set of criteria for a car (e.g. brand, model, and its tech details)
    for raw_filter in license_key.filters:
        # Skip if not a dictionary
        if not isinstance(raw_filter, dict):
            continue

        # Initialize lists for conditions
        listing_conditions, tech_conditions, equip_conditions = [], [], []

        # Process each filter key-value pair
        for key, value in raw_filter.items():
            # Handle technical details
            if key == "technical_details" and isinstance(value, dict):
                for subkey, subvalue in value.items():
                    attr = getattr(TechnicalDetails, subkey, None)
                    if attr is not None:
                        if isinstance(subvalue, str):
                            tech_conditions.append(attr.ilike(f"%{subvalue}%"))
                        elif isinstance(subvalue, (int, float, bool)):
                            tech_conditions.append(attr == subvalue)
                        elif isinstance(subvalue, dict):
                            if "min" in subvalue:
                                tech_conditions.append(attr >= subvalue["min"])
                            if "max" in subvalue:
                                tech_conditions.append(attr <= subvalue["max"])

            # Handle equipment
            elif key == "equipment" and isinstance(value, dict):
                for subkey, subvalue in value.items():
                    attr = getattr(Equipment, subkey, None)
                    if attr is not None:
                        if isinstance(subvalue, (bool, int, float)):
                            equip_conditions.append(attr == subvalue)
                        elif isinstance(subvalue, str):
                            equip_conditions.append(attr.ilike(f"%{subvalue}%"))
                        elif isinstance(subvalue, dict):
                            if "min" in subvalue:
                                equip_conditions.append(attr >= subvalue["min"])
                            if "max" in subvalue:
                                equip_conditions.append(attr <= subvalue["max"])
            else:
                # Handle listing attributes
                if value is not None:
                    listing_attr = getattr(ListingMobileDe, key, None)
                    if listing_attr is not None:
                        if isinstance(value, str):
                            listing_conditions.append(listing_attr.ilike(f"%{value}%"))
                        elif isinstance(value, (int, float, bool)):
                            listing_conditions.append(listing_attr == value)
                        elif isinstance(value, dict):
                            if "min" in value:
                                listing_conditions.append(listing_attr >= value["min"])
                            if "max" in value:
                                listing_conditions.append(listing_attr <= value["max"])

        all_conditions = listing_conditions + tech_conditions + equip_conditions
        if all_conditions:
            filter_groups.append(and_(*all_conditions))

    # Base query to get all listings
    stmt = (
        select(ListingMobileDe)
        .outerjoin(ListingMobileDe.technical_details)
        .outerjoin(ListingMobileDe.equipment)
        .options(
            joinedload(ListingMobileDe.technical_details),
            joinedload(ListingMobileDe.equipment)
        )
    )
    
    # Apply filters if any
    if filter_groups:
        stmt = stmt.where(or_(*filter_groups))

    result = await db.execute(stmt)

    listings = list(result.scalars().all())
    return [ListingSchemaML.from_orm(item) for item in listings]


async def get_filtered(
        db: AsyncSession,
        listing_filters: ListingSchema,
        tech_filters: TechnicalDetailsSchema,
        equipment_filters: EquipmentSchema,
        page: int, size: int, total: int  # total is unused, calculated dynamically
) -> ListingFilteredResponse:
    """Filtering listings with JOIN on TechnicalDetails and Equipment, with proper pagination."""
    listing_conditions = filtered_listings(listing_filters)
    techdetails_conditions = filtered_tech_details(tech_filters)
    equipment_conditions = filtered_equipment(equipment_filters)
    
    all_conditions = and_(*listing_conditions, *techdetails_conditions, *equipment_conditions)

    # First, get the total count for pagination
    count_stmt = (
        select(func.count(ListingMobileDe.id))
        .outerjoin(ListingMobileDe.technical_details)
        .outerjoin(ListingMobileDe.equipment)
        .where(all_conditions)
    )
    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar_one_or_none() or 0
    
    # Then, fetch the paginated data
    offset = (page - 1) * size if page > 0 else 0
    stmt = (
        select(ListingMobileDe)
        .outerjoin(ListingMobileDe.technical_details)
        .outerjoin(ListingMobileDe.equipment)
        .options(
            joinedload(ListingMobileDe.technical_details),
            joinedload(ListingMobileDe.equipment)
        )
        .where(all_conditions)
        .limit(size)
        .offset(offset)
    )
    result = await db.execute(stmt)
    listings = list(result.scalars().all())
    listing_out = [ListingOut.from_orm(item) for item in listings]

    # Calculate stats based on all filtered results, not just the current page
    if total_count > 0:
        price_stmt = (
            select(
                func.avg(ListingMobileDe.price),
                func.min(ListingMobileDe.price),
                func.max(ListingMobileDe.price)
            )
            .outerjoin(ListingMobileDe.technical_details)
            .outerjoin(ListingMobileDe.equipment)
            .where(all_conditions)
        )
        stats_result = await db.execute(price_stmt)
        avg_price, min_price, max_price = stats_result.one_or_none()
    else:
        avg_price = min_price = max_price = 0
        
    total_pages = int(math.ceil(total_count / size)) if size > 0 else 0

    return ListingFilteredResponse(
        Listings=listing_out,  # Already paginated
        Stats=ListingStats(
            avg_price=round(avg_price, 2) if avg_price else 0,
            min_price=round(min_price, 2) if min_price else 0,
            max_price=round(max_price, 2) if max_price else 0,
            count=total_count
        ),
        page=page,
        size=size,
        total=total_pages
    )


async def listings_json_to_db(db: AsyncSession, data: ListingCreateRequestSchema) -> ListingMobileDe:
    """
    Save a listing to the database.
    """
    listing = ListingMobileDe(
        brand=data.brand,
        model=data.model,
        registration_year=data.registration_year,
        mileage=data.mileage,
        city_or_postal_code=data.city_or_postal_code,
        color=data.color,
        price=data.price,
        currency=data.currency,
        url=data.url,
    )

    technical_details = TechnicalDetails(
        **data.technical_details.dict() if data.technical_details else {})  # Show how to create TechnicalDetails from the schema
    equipment = Equipment(
        **data.equipment.dict() if data.equipment else {})  # Show how to create Equipment from the schema

    listing.technical_details = technical_details  # Add technical details to the listing
    listing.equipment = equipment  # Add equipment to the listing

    db.add(listing)  # Add the listing to the session
    await db.commit()  # Commit the session to save the listing
    await db.refresh(listing)  # Refresh the instance to get the updated state
    return listing


async def get_avg_price_by_brand(limit: int, db: AsyncSession) -> list[AvgPriceByBrand]:
    """
    Get average price, max price, min price, and count of car listings grouped by brand.
    """
    stmt = (
        select(
            ListingMobileDe.brand,
            func.avg(ListingMobileDe.price).label("avg_price"),
            func.min(ListingMobileDe.price).label("min_price"),
            func.max(ListingMobileDe.price).label("max_price"),
            func.count(ListingMobileDe.id).label("count")
        )
        .group_by(ListingMobileDe.brand)
        .order_by(func.avg(ListingMobileDe.price).desc())
        # .having(func.count(CarListingMobileDe.id) > 3)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        AvgPriceByBrand(
            brand=row.brand,
            avg_price=round(row.avg_price, 2),
            min_price=round(row.min_price, 2),
            max_price=round(row.max_price, 2),
            count=row.count
        )
        for row in rows
    ]


async def get_license_by_key(db: AsyncSession, key: str) -> Optional[LicenseKey]:
    """Fetch license key object from DB"""
    result = await db.execute(select(LicenseKey).where(LicenseKey.key == key))
    return result.scalar_one_or_none()
