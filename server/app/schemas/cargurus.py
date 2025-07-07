from pydantic import BaseModel
from typing import Optional


class CarGurusBase(BaseModel):
    entity_id: str
    label: Optional[str] = None


class CarGurusCreate(CarGurusBase):
    pass


class CarGurusUpdate(BaseModel):
    entity_id: Optional[str] = None
    label: Optional[str] = None


class CarGurusResponse(CarGurusBase):
    id: int

    class Config:
        from_attributes = True 