# app/routers/stats/analytics.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.stats.analytics import AvgPriceByBrand, ListingOut, ListingFilter
from app.services.stats.analytics import get_avg_price_by_brand
from app.services.stats.filter_mobilde import filtered_listings

router = APIRouter()


@router.get("/search", response_model=list[ListingOut])
async def search_listings(db: AsyncSession = Depends(get_db), filters: ListingFilter = Depends()) -> list[ListingOut]:
    """
    Search for car listings based on various filters.
    """
    return await filtered_listings(db=db, filters=filters)


@router.get("/average_price", response_model=list[AvgPriceByBrand])
async def get_average_price(limit: int=20, db: AsyncSession = Depends(get_db)):
    """
    Get average price, max price, min price, and count of car listings grouped by title.
    """
    return await get_avg_price_by_brand(limit, db)
