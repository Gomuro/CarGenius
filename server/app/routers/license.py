# app/routers/license.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.license import LicenseValidateRequest, LicenseValidateResponse, LicenseCreateRequest, \
    LicenseCreateResponse
from app.services.license import generate_license_key, validate_license_key, validate_license_key_device
from app.core.database import get_db

router = APIRouter()

@router.post("/generate", response_model=LicenseCreateResponse)
async def generate_license(request: LicenseCreateRequest, db: AsyncSession = Depends(get_db)):
    try:
        license = await generate_license_key(db, client_info=request.client_info)
        return {
            "key": license.key,
            "is_active": license.is_active,
            "created_at": license.created_at,
            "expires_at": license.expires_at,
            "client_info": license.client_info
        }
    except Exception as e:
        await db.rollback()
        print("ERROR:", e)
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
