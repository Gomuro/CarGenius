from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.cargurus import CarGurusService
from app.schemas.cargurus import CarGurusCreate, CarGurusUpdate

router = APIRouter()


@router.get("/load_labels")
async def load_labels(db: AsyncSession = Depends(get_db)):
    """load all labels from CarGurus API and save to DB"""
    try:
        await CarGurusService.load_cargurus_labels(db)
        return {"message": "Labels loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_by_label")
async def get_by_label(db: AsyncSession = Depends(get_db), name: str = Query(..., description="Name of the label")):
    """get label by name"""
    try:
        brand = await CarGurusService.get_by_label(db, name)
        return brand
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))