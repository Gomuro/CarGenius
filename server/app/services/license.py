# app/services/license.py
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from typing import Tuple, Optional, List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.license import LicenseKey
from app.schemas.license import ListingFilter


async def generate_license_key(db: AsyncSession, client_info: str = None, expires_in_days: int = 30) -> LicenseKey:
    """Generate a new license key."""
    now = datetime.now(timezone.utc)
    licens_obj = LicenseKey(
        key=str(uuid.uuid4()),
        client_info=client_info,
        is_active=True,
        created_at=now,
        expires_at=now + timedelta(days=expires_in_days)
    )
    db.add(licens_obj)
    await db.commit()
    await db.refresh(licens_obj)
    return licens_obj


async def validate_license_key(key: str, client_info: str, db: AsyncSession) -> bool:
    """
    Validate the license key by checking if it exists and is active.
    """
    result = await db.execute(select(LicenseKey).where(LicenseKey.key == key))
    licens_obj = result.scalar_one_or_none()
    if licens_obj and licens_obj.is_active and licens_obj.client_info == client_info:
        return True
    return False


async def validate_license_key_device(key: str, device_id: str, client_info: str, db: AsyncSession) -> Tuple[bool, str]:
    result = await db.execute(select(LicenseKey).where(LicenseKey.key == key))  # Fetch the license key by its key
    licens_obj = result.scalar_one_or_none()  # expect a maximum of one entry. Object or None or MultipleResultsFound.
    if not licens_obj:
        return False, "License key not found"
    if not licens_obj.is_active:
        return False, "License key is not active"
    if licens_obj.expires_at and licens_obj.expires_at < datetime.now(timezone.utc):
        return False, "License key has expired"
    if licens_obj.device_id is None:
        # First time activation — bind device
        licens_obj.device_id = device_id
        licens_obj.client_info = client_info
        await db.commit()  # Save the device binding
        return True, "License activated and device bound"
    if licens_obj.device_id != device_id:
        return False, "Device mismatch. This license is bound to another device"
    return True, "License key is valid"


async def get_license_by_key(db: AsyncSession, key: str) -> Optional[LicenseKey]:
    """Retrieve a license by its key."""
    result = await db.execute(select(LicenseKey).where(LicenseKey.key == key))
    return result.scalar_one_or_none()   # Expecting a single LicenseKey object or None if not found


async def update_license_filters(db: AsyncSession, license_key: LicenseKey, filters: List[ListingFilter]) -> LicenseKey:
    """Update filters for a given license key with validation."""

    allowed_keys = set(ListingFilter.__fields__.keys())

    for i, f in enumerate(filters):
        print(f"[DEBUG] Type of filter[{i}]:", type(f), f)
        filter_dict = f.dict(exclude_unset=True)
        invalid_keys = set(filter_dict.keys()) - allowed_keys
        if invalid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter keys: {', '.join(invalid_keys)}. Allowed keys: {', '.join(allowed_keys)}"
            )

    license_key.filters = [f.dict(exclude_unset=True) for f in filters]

    await db.commit()
    await db.refresh(license_key)
    return license_key
