# app.routers.stats.license_stats.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEFAULT_LICENSE_DURATION_DAYS
from app.core.database import get_db
from app.schemas.stats.license_stats import LicenseCountByDay
from app.services.stats.license_stats import get_license_count_by_day

router = APIRouter()


@router.get("/licenses-per-day", response_model=list[LicenseCountByDay])
async def license_per_day(days: int = DEFAULT_LICENSE_DURATION_DAYS, db: AsyncSession = Depends(get_db)):
    """
    API endpoint to get number of license keys created per day.

    Args:
        days (int): Number of past days to include in the results (default: 30).
        db (AsyncSession): Injected async database session.

    Returns:
        List[LicenseCountByDay]: List of dates with corresponding license creation counts.
    """
    # Query license creation stats from the service
    data = await get_license_count_by_day(db, days=days)
    # Transform raw SQL result into response schema list
    return [{"date": row.date, "count": row.count} for row in data]
