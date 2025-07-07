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
    """get label by name (legacy method)"""
    try:
        brand = await CarGurusService.get_by_label(db, name)
        return brand
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_by_criteria")
async def get_by_criteria(
    db: AsyncSession = Depends(get_db),
    brand: str = Query(None, description="Brand name"),
    model: str = Query(None, description="Model name"), 
    year: str = Query(None, description="Year")
):
    """get labels by specific criteria (brand, model, year) - more accurate search"""
    try:
        # Validate input parameters
        if not any([brand, model, year]):
            raise HTTPException(
                status_code=400, 
                detail="At least one search parameter (brand, model, or year) must be provided"
            )
        
        # Clean and validate parameters
        clean_brand = brand.strip() if brand else None
        clean_model = model.strip() if model else None
        clean_year = year.strip() if year else None
        
        # Validate year format if provided
        if clean_year:
            try:
                year_int = int(clean_year)
                if year_int < 1900 or year_int > 2030:
                    raise HTTPException(
                        status_code=400,
                        detail="Year must be between 1900 and 2030"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Year must be a valid number"
                )
        
        results = await CarGurusService.get_by_criteria(
            db, 
            brand=clean_brand, 
            model=clean_model, 
            year=clean_year
        )
        
        return results
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")