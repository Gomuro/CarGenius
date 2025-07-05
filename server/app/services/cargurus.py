from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models.cargurus import CarGurus
from typing import Optional
import requests
from fastapi import HTTPException


class CarGurusService:
    
    @staticmethod
    async def upsert_cargurus_entry(
        db: AsyncSession, 
        entity_id: str, 
        cargurus_brand: Optional[str] = None
    ) -> CarGurus:
        """
        Вставляє новий запис або оновлює існуючий.
        Забезпечує, що один entity_id має тільки одну марку.
        """
        # Спочатку шукаємо існуючий запис
        result = await db.execute(
            select(CarGurus).filter(CarGurus.entity_id == entity_id)
        )
        existing_entry = result.scalar_one_or_none()
        
        if existing_entry:
            # Якщо запис існує, оновлюємо марку
            if cargurus_brand is not None:
                existing_entry.cargurus_brand = cargurus_brand
                await db.commit()
                await db.refresh(existing_entry)
            return existing_entry
        else:
            # Якщо запису немає, створюємо новий
            new_entry = CarGurus(
                entity_id=entity_id,
                cargurus_brand=cargurus_brand
            )
            db.add(new_entry)
            try:
                await db.commit()
                await db.refresh(new_entry)
                return new_entry
            except IntegrityError:
                # Якщо сталася помилка унікальності, откатуємо та повертаємо існуючий
                await db.rollback()
                result = await db.execute(
                    select(CarGurus).filter(CarGurus.entity_id == entity_id)
                )
                existing_entry = result.scalar_one_or_none()
                return existing_entry
    
    @staticmethod
    async def get_by_entity_id(db: AsyncSession, entity_id: str) -> Optional[CarGurus]:
        """Отримати запис за entity_id"""
        result = await db.execute(
            select(CarGurus).filter(CarGurus.entity_id == entity_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_brand_by_name(db: AsyncSession, name: str) -> Optional[CarGurus]:
        """Отримати запис за назвою марки"""
        result = await db.execute(
            select(CarGurus).filter(CarGurus.cargurus_brand.ilike(f"%{name}%"))
        )
        return result.scalars().all()
    @staticmethod
    async def update_brand(db: AsyncSession, entity_id: str, new_brand: str) -> Optional[CarGurus]:
        """Оновити марку для існуючого entity_id"""
        result = await db.execute(
            select(CarGurus).filter(CarGurus.entity_id == entity_id)
        )
        entry = result.scalar_one_or_none()
        
        if entry:
            entry.cargurus_brand = new_brand
            await db.commit()
            await db.refresh(entry)
            return entry
        return None

    @staticmethod
    async def load_cargurus_brands(db: AsyncSession) -> list[CarGurus]:
        """Завантажити всі марки з CarGurus API та зберегти в БД"""
        url = "https://www.cargurus.com/research/price-trends?entityIds=Index&startDate=1738620000000&endDate=1751662799999&_data=routes%2F%28%24intl%29.research.price-trends._index"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                saved_entries = []
                
                # Знаходимо секцію MAKES
                for price_trend in data.get("priceTrends", []):
                    if price_trend.get("type") == "MAKES":
                        entities = price_trend.get("entities", [])
                        
                        for entity in entities:
                            entity_id = entity.get("entityId")
                            cargurus_brand = entity.get("label")
                            if entity_id and cargurus_brand:
                                # Використовуємо upsert для збереження
                                saved_entry = await CarGurusService.upsert_cargurus_entry(
                                    db=db,
                                    entity_id=entity_id,
                                    cargurus_brand=cargurus_brand
                                )
                                saved_entries.append(saved_entry)
                
                return saved_entries
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to load cargurus brands. Status: {response.status_code}"
                )
        except requests.RequestException as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Request failed: {str(e)}"
            )