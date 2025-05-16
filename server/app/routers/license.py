from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.license import LicenseCreateResponse, LicenseValidateRequest, LicenseValidateResponse, LicenseInfo, \
    LicenseCreateRequest
from app.services.license import generate_license_key, validate_license_key
from app.core.database import get_db

router = APIRouter()


@router.post("/generate", response_model=LicenseCreateResponse)
async def generate_license_route(data: LicenseCreateRequest, db: AsyncSession = Depends(get_db)):
    license = await generate_license_key(db, client_info=data.client_info)
    return LicenseCreateResponse(
        key=license.key,
        is_active=license.is_active,
        created_at=license.created_at,
        expires_at=license.expires_at,
        client_info=license.client_info
    )


@router.post("/validate", response_model=LicenseValidateResponse)
async def validate_license_route(data: LicenseValidateRequest, db: AsyncSession = Depends(get_db)):
    """
    Validate a license key.
    """
    is_valid = await validate_license_key(data.key, data.client_info, db)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid license key")
    return LicenseValidateResponse(is_valid=is_valid)
