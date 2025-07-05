from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models.cargurus import CarGurus
from typing import Optional, List
import requests
from fastapi import HTTPException


class CarGurusService:
    
    @staticmethod
    async def upsert_cargurus_entry(
        db: AsyncSession, 
        entity_id: str, 
        label: Optional[str] = None
    ) -> CarGurus:
        """
        Inserts a new record or updates an existing one.
        Ensures that one entity_id has only one label.
        """
        result = await db.execute(
            select(CarGurus).filter(CarGurus.entity_id == entity_id)
        )
        existing_entry = result.scalar_one_or_none()
        
        if existing_entry:
            if label is not None:
                existing_entry.label = label
                await db.commit()
                await db.refresh(existing_entry)
            return existing_entry
        else:
            new_entry = CarGurus(
                entity_id=entity_id,
                label=label
            )
            db.add(new_entry)
            try:
                await db.commit()
                await db.refresh(new_entry)
                return new_entry
            except IntegrityError:
                await db.rollback()
                result = await db.execute(
                    select(CarGurus).filter(CarGurus.entity_id == entity_id)
                )
                existing_entry = result.scalar_one_or_none()
                return existing_entry
    
    @staticmethod
    async def get_by_entity_id(db: AsyncSession, entity_id: str) -> Optional[CarGurus]:
        """Get a record by entity_id"""
        result = await db.execute(
            select(CarGurus).filter(CarGurus.entity_id == entity_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_label(db: AsyncSession, name: str) -> List[CarGurus]:
        """Get records by label name"""
        result = await db.execute(
            select(CarGurus).filter(CarGurus.label.ilike(f"%{name}%"))
        )
        return result.scalars().all()

    @staticmethod
    async def update_label(db: AsyncSession, entity_id: str, new_label: str) -> Optional[CarGurus]:
        """Update the label for an existing entity_id"""
        result = await db.execute(
            select(CarGurus).filter(CarGurus.entity_id == entity_id)
        )
        entry = result.scalar_one_or_none()
        
        if entry:
            entry.label = new_label
            await db.commit()
            await db.refresh(entry)
            return entry
        return None

    @staticmethod
    async def load_cargurus_labels(db: AsyncSession) -> list[CarGurus]:
        """Load all labels from the CarGurus API and save them to the DB"""
        url = "https://www.cargurus.com/research/price-trends?entityIds=Index&startDate=1738620000000&endDate=1751662799999&_data=routes%2F%28%24intl%29.research.price-trends._index"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                saved_entries = []
                
                for price_trend in data.get("priceTrends", []):
                    if price_trend.get("type") == "MAKES":
                        entities = price_trend.get("entities", [])
                        
                        for entity in entities:
                            entity_id = entity.get("entityId")
                            label = entity.get("label")
                            if entity_id and label:
                                saved_entry = await CarGurusService.upsert_cargurus_entry(
                                    db=db,
                                    entity_id=entity_id,
                                    label=label
                                )
                                saved_entries.append(saved_entry)
                
                return saved_entries
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to load cargurus labels. Status: {response.status_code}"
                )
        except requests.RequestException as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Request failed: {str(e)}"
            )