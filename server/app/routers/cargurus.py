from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.cargurus import CarGurusService
from app.schemas.cargurus import CarGurusCreate, CarGurusUpdate

router = APIRouter()


@router.get("/load_brands")
async def load_brands(db: AsyncSession = Depends(get_db)):
    """load all brands from CarGurus API and save to DB"""
    try:
        await CarGurusService.load_cargurus_brands(db)
        return {"message": "Brands loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_brand_by_name")
async def get_brand_by_name(db: AsyncSession = Depends(get_db), name: str = Query(..., description="Name of the brand")):
    """get brand by name"""
    try:
        brand = await CarGurusService.get_brand_by_name(db, name)
        return brand
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))