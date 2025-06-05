# app/services/stats/analytics.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.car import ListingMobileDe
from app.schemas.stats.analytics import AvgPriceByBrand, ListingFilter


#
# async def get_filtered_listings(db: AsyncSession, filters: ListingFilter) -> list[ListingMobileDe]:
#     """
#     Get car listings filtered by the provided criteria.
#     """
#     conditions = [ListingMobileDe.is_active.is_(True)]
#
#     if filters.brand:
#         conditions.append(ListingMobileDe.brand.ilike(f"%{filters.brand}%"))
#     if filters.model:
#         conditions.append(ListingMobileDe.model.ilike(f"%{filters.model}%"))
#     if filters.registration_year:
#         conditions.append(ListingMobileDe.registration_year == filters.registration_year)
#     if filters.mileage:
#         conditions.append(ListingMobileDe.mileage <= filters.mileage)
#     if filters.city_or_postal_code:
#         conditions.append(ListingMobileDe.city_or_postal_code.ilike(f"%{filters.city_or_postal_code}%"))
#     if filters.color:
#         conditions.append(ListingMobileDe.color.ilike(f"%{filters.color}%"))
#     if filters.price_lte:
#         conditions.append(ListingMobileDe.price <= filters.price_lte)
#     if filters.price_gte:
#         conditions.append(ListingMobileDe.price >= filters.price_gte)
#
#
#     stmt = select(ListingMobileDe).where(and_(*conditions))
#     result = await db.execute(stmt)
#     return list(result.scalars().all())


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
