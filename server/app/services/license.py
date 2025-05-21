# app/servoces/license.py
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.license import LicenseKey


async def generate_license_key(db: AsyncSession, client_info: str = None, expires_in_days: int = 30) -> LicenseKey:
    license = LicenseKey(
        client_info=client_info,
        expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days)
    )
    db.add(license)
    await db.commit()
    await db.refresh(license)
    return license


async def validate_license_key(key: str, client_info: str, db: AsyncSession) -> bool:
    """
    Validate the license key by checking if it exists and is active.
    """
    result = await db.execute(select(LicenseKey).where(LicenseKey.key == key))
    license = result.scalar_one_or_none()
    if license and license.is_active and license.client_info == client_info:
        return True
    return False
