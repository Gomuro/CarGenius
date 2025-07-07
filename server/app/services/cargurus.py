import time
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models.cargurus import CarGurus
from typing import Dict, Optional, List
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
        """Get records by label name (legacy method)"""
        result = await db.execute(
            select(CarGurus).filter(CarGurus.label.ilike(f"%{name}%"))
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_by_criteria(
        db: AsyncSession, 
        brand: Optional[str] = None, 
        model: Optional[str] = None, 
        year: Optional[str] = None
    ) -> List[CarGurus]:
        """
        Get records by specific criteria (brand, model, year)
        More accurate than free-text search
        """
        from sqlalchemy import and_, or_
        
        # Input validation
        if not any([brand, model, year]):
            return []
        
        # Sanitize inputs to prevent SQL injection (even though we're using parameterized queries)
        if brand:
            brand = brand.strip()[:100]  # Limit length
        if model:
            model = model.strip()[:100]  # Limit length  
        if year:
            year = year.strip()[:4]  # Years should be 4 digits max
        
        # Build search patterns based on the data structure
        search_conditions = []
        
        # Case 1: Brand only - exact match
        if brand and not model and not year:
            search_conditions.append(CarGurus.label.ilike(f"{brand}"))
        
        # Case 2: Model only - try various patterns
        elif model and not year and not brand:
            search_conditions.extend([
                CarGurus.label.ilike(f"{model}"),
                CarGurus.label.ilike(f"{model}%")  # Model with potential year suffix
            ])
        
        # Case 3: Model + Year - most specific search
        elif model and year:
            search_conditions.extend([
                CarGurus.label.ilike(f"{year} {model}"),
                CarGurus.label.ilike(f"{model} {year}"),
                CarGurus.label.ilike(f"{year}%{model}%"),
                CarGurus.label.ilike(f"{model}%{year}%")
            ])
        
        # Case 4: Brand + Model (no year)
        elif brand and model and not year:
            search_conditions.extend([
                CarGurus.label.ilike(f"{model}"),
                CarGurus.label.ilike(f"{brand} {model}"),
                CarGurus.label.ilike(f"{model}%")
            ])
        
        # Case 5: Brand + Year (no model) - less common
        elif brand and year and not model:
            search_conditions.extend([
                CarGurus.label.ilike(f"%{brand}%{year}%"),
                CarGurus.label.ilike(f"{year}%{brand}%")
            ])
        
        # Case 6: All three provided
        elif brand and model and year:
            search_conditions.extend([
                CarGurus.label.ilike(f"{year} {model}"),
                CarGurus.label.ilike(f"{model} {year}"),
                CarGurus.label.ilike(f"{brand} {model} {year}"),
                CarGurus.label.ilike(f"{year} {brand} {model}"),
                CarGurus.label.ilike(f"{model}%{year}%")
            ])
        
        if not search_conditions:
            return []
        
        # Execute query with OR conditions
        result = await db.execute(
            select(CarGurus).filter(or_(*search_conditions))
        )
        
        results = result.scalars().all()
        
        # Post-process results to rank by accuracy
        return CarGurusService._rank_search_results(results, brand, model, year)
    
    @staticmethod
    def _rank_search_results(
        results: List[CarGurus], 
        brand: Optional[str] = None, 
        model: Optional[str] = None, 
        year: Optional[str] = None
    ) -> List[CarGurus]:
        """
        Rank search results by accuracy/relevance
        Most specific matches first
        """
        if not results:
            return results
        
        def calculate_score(item: CarGurus) -> int:
            label = item.label.lower() if item.label else ""
            score = 0
            
            # Exact matches get highest scores
            if brand and model and year:
                target = f"{model} {year}".lower()
                if label == target:
                    score += 100
                elif label.startswith(target):
                    score += 90
                elif target in label:
                    score += 80
            
            elif model and year:
                target = f"{model} {year}".lower()
                if label == target:
                    score += 100
                elif label.startswith(target):
                    score += 90
            
            elif model:
                target = model.lower()
                if label == target:
                    score += 100
                elif label.startswith(target):
                    score += 90
                elif target in label:
                    score += 70
            
            elif brand:
                target = brand.lower()
                if label == target:
                    score += 100
                elif label.startswith(target):
                    score += 90
            
            # Penalty for extra words (less specific matches)
            word_count = len(label.split())
            expected_words = sum([1 for x in [brand, model, year] if x])
            if word_count > expected_words:
                score -= (word_count - expected_words) * 5
            
            return score
        
        # Sort by score (highest first)
        ranked_results = sorted(results, key=calculate_score, reverse=True)
        return ranked_results

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
                saved_brand_entity = []
                
                for price_trend in data.get("priceTrends", []):
                    if price_trend.get("type") == "MAKES":
                        entities = price_trend.get("entities", [])
                        
                        for entity in entities:
                            entity_id = entity.get("entityId")
                            label = entity.get("label")
                            if entity_id and label:
                                await CarGurusService.upsert_cargurus_entry(
                                    db=db,
                                    entity_id=entity_id,
                                    label=label
                                )
                                saved_brand_entity.append((entity_id, label))
                
                
                saved_model_entity = []
                for brand_entity in saved_brand_entity:
                    brand_id = brand_entity[0]
                    brand_label = brand_entity[1]
                    print(f"Brand: {brand_label} ({brand_id})")
                    models_data = await CarGurusService._fetch_data_model(db, brand_label, brand_id)
                    # Add brand_label to each model entity
                    models_with_brand = [(model[0], model[1], brand_label) for model in models_data]
                    saved_model_entity.extend(models_with_brand)
                    
                
                saved_model_entity_with_year = []
                for model_entity in saved_model_entity:
                    model_id = model_entity[0]
                    model_label = model_entity[1]
                    brand_label = model_entity[2]
                    print(f"Model: {model_label} ({model_id})")
                    model_with_year_data = await CarGurusService._fetch_data_model_with_year(db, model_label, model_id, brand_label)
                    saved_model_entity_with_year.extend(model_with_year_data)
                    
                
                return saved_model_entity
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
            
    @staticmethod
    async def _fetch_data_model(db: AsyncSession, brand_label: str, brand_id: str) -> Optional[Dict]:
        time.sleep(0.5)
        url = f"https://www.cargurus.com/research/price-trends/{brand_label}-{brand_id}?entityIds={brand_id}&startDate=1738620000000&endDate=1751662799999&_data=routes%2F%28%24intl%29.research.price-trends.%24makeModelSlug"
        response = requests.get(url)
        data = response.json()
        price_trends = data.get("priceTrends", [])
        models = []
        saved_model_entity = []
        for price_trend in price_trends:
            if price_trend.get("type") == "MODELS":
                models = price_trend.get("entities", [])
                for model in models:
                    model_id = model.get("entityId")
                    model_label = model.get("label")
                    if model_id and model_label:
                        await CarGurusService.upsert_cargurus_entry(
                            db=db,
                            entity_id=model_id,
                            label=model_label
                        )
                        saved_model_entity.append((model_id, model_label))
        return saved_model_entity
    
    @staticmethod
    async def _fetch_data_model_with_year(db: AsyncSession, model_label: str, model_id: str, brand_label: str) -> Optional[Dict]:
        time.sleep(1)
        url = f"https://www.cargurus.com/research/price-trends/{brand_label}-{model_label}-{model_id}?entityIds={model_id}&startDate=1738620000000&endDate=1751662799999&_data=routes%2F%28%24intl%29.research.price-trends.%24makeModelSlug"
        response = requests.get(url)
        data = response.json()
        price_trends = data.get("priceTrends", [])
        saved_year_entity = []
        
        for price_trend in price_trends:
            if price_trend.get("type") == "CARS":
                cars = price_trend.get("entities", [])
                for car in cars:
                    car_id = car.get("entityId")
                    car_label = car.get("label")
                    if car_id and car_label:
                        await CarGurusService.upsert_cargurus_entry(
                            db=db,
                            entity_id=car_id,
                            label=car_label
                        )
                        saved_year_entity.append((car_id, car_label))
        
        return saved_year_entity