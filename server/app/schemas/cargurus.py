from pydantic import BaseModel
from typing import Optional


class CarGurusBase(BaseModel):
    entity_id: str
    cargurus_brand: Optional[str] = None


class CarGurusCreate(CarGurusBase):
    pass


class CarGurusUpdate(BaseModel):
    entity_id: Optional[str] = None
    cargurus_brand: Optional[str] = None


class CarGurusResponse(CarGurusBase):
    id: int

    class Config:
        from_attributes = True 