# app.services.stats.license_stats.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from app.models.license import LicenseKey


async def get_license_count_by_day(db: AsyncSession, days: int):
    """
    Get the number of license keys created per day within the last N days.

    Args:
        db (AsyncSession): Database session.
        days (int): Number of days to look back from today.

    Returns:
        List of tuples with (date, count) representing number of created licenses per date.
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)

    # Select date and count of licenses grouped by creation date
    result = await db.execute(
        # Build a SELECT statement
        select(
            func.date(LicenseKey.created_at).label("date"),
            # Extract just the date (YYYY-MM-DD) part from created_at and label it as "date"
            func.count().label("count")  # Count the number of license records per date and label it as "count"
        )
        .where(LicenseKey.created_at >= start_date)  # Filter records to only include those created after the start_date
        .group_by(func.date(LicenseKey.created_at))  # Group results by date (so we can count licenses per day)
        .order_by(func.date(LicenseKey.created_at))  # Order the results chronologically by date
    )
    return result.all()  # Return all the grouped (date, count) rows as a list of tuples
