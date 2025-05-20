# app/routers/license.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.license import LicenseKey
from app.schemas.license import LicenseValidateRequest, LicenseValidateResponse, LicenseCreateRequest
from app.services.license import generate_license_key, validate_license_key
from app.core.database import get_db
from uuid import uuid4
from datetime import datetime, timedelta


router = APIRouter()

@router.post("/generate")
async def generate_license(request: LicenseCreateRequest, db: AsyncSession = Depends(get_db)):
    try:
        key = str(uuid4())
        now = datetime.utcnow()
        expires = now + timedelta(days=30)

        license_key = LicenseKey(
            key=key,
            is_active=True,
            created_at=now,
            expires_at=expires,
            client_info=request.client_info
        )

        db.add(license_key)
        await db.commit()
        await db.refresh(license_key)

        return {"key": license_key.key, "expires_at": license_key.expires_at}
    except Exception as e:
        await db.rollback()
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail="Failed to create license")



@router.post("/validate")
async def validate_license_route(data: LicenseValidateRequest, db: AsyncSession = Depends(get_db)):
    """
    Validate a license key.
    """
    is_valid = await validate_license_key(data.key, data.client_info, db)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid license key")
    return LicenseValidateResponse(is_valid=is_valid)
