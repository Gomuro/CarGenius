from pydantic import BaseModel
from datetime import date


class LicenseCountByDay(BaseModel):
    """
    Schema for license counts by day.
    Represents the number of licenses created on a specific date.
    """
    date: date  # The date for which the count is recorded
    count: int  # The number of licenses created on that date
