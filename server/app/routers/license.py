# app/routers/license.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.license import ListingFilter, LicenseCreateResponse, LicenseCreateRequest, LicenseValidateResponse, \
    LicenseValidateRequest

from app.services.license import generate_license_key, validate_license_key, validate_license_key_device, \
    get_license_by_key, update_license_filters
from app.core.database import get_db
from app.core.logger import logger
from app.core.rate_limiter import limiter

router = APIRouter()


@router.post("/generate", response_model=LicenseCreateResponse)
@limiter.limit("3/minute")
async def generate_license(request: Request, payload: LicenseCreateRequest, db: AsyncSession = Depends(get_db)):
    try:
        logger.info("Generating license key for client: %s", payload.client_info)
        license_key = await generate_license_key(db, client_info=payload.client_info)
        return license_key
    except Exception as e:
        await db.rollback()
        logger.error("Failed to generate license key: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to create license")


@router.post("/validate", response_model=LicenseValidateResponse)
async def validate_license_route(data: LicenseValidateRequest, db: AsyncSession = Depends(get_db)):
    is_valid = await validate_license_key(data.key, data.client_info, db)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid license key")
    return LicenseValidateResponse(is_valid=is_valid)


@router.post("/validate_key_device", response_model=LicenseValidateResponse)
async def validate_license_route_device(data: LicenseValidateRequest, db: AsyncSession = Depends(get_db)):
    is_valid, message = await validate_license_key_device(data.key, data.device_id, data.client_info, db)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    return LicenseValidateResponse(is_valid=is_valid, message=message)


@router.get("/{key}/filters", response_model=List[ListingFilter])

async def get_filters(key: str, db: AsyncSession = Depends(get_db)):
    license_key = await get_license_by_key(db, key)
    if not license_key:
        raise HTTPException(status_code=404, detail="License key not found")

    return [f for f in license_key.filters if isinstance(f, dict)]


@router.put("/{key}/filters", response_model=List[ListingFilter])
async def update_filters(
        key: str,
        payload: List[ListingFilter],
        db: AsyncSession = Depends(get_db)
):
    license_key = await get_license_by_key(db, key)
    if not license_key:
        raise HTTPException(status_code=404, detail="License key not found")
    updated_license = await update_license_filters(db, license_key, payload)
    return updated_license.filters


@router.delete("/{key}/filters", response_model=List[ListingFilter])

async def clear_filters(key: str, db: AsyncSession = Depends(get_db)):
    license_key = await get_license_by_key(db, key)
    if not license_key:
        raise HTTPException(status_code=404, detail="License key not found")

    await update_license_filters(db, license_key, [])
    return [f for f in license_key.filters if isinstance(f, dict)]

