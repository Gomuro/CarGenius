import asyncio
import json
import os
import random
import time
import httpx
from pydantic import HttpUrl
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models.car import ListingMobileDe, TechnicalDetails, Equipment
from app.models.cargurus import CarGurus
from typing import Dict, Optional, List, Union
import requests
from fastapi import HTTPException
from app.services.extractors.cargurus_url_extractor import CarGurusUrlExtractor
from app.services.validators.cargurus_validator import validate_cargurus_url, CarGurusValidator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "searchPage.action.json")


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
            # response = requests.get(url)
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url)
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
                    model_with_year_data = await CarGurusService._fetch_data_model_with_year(db, model_label, model_id,
                                                                                             brand_label)
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
        await asyncio.sleep(0.5)
        url = f"https://www.cargurus.com/research/price-trends/{brand_label}-{brand_id}?entityIds={brand_id}&startDate=1738620000000&endDate=1751662799999&_data=routes%2F%28%24intl%29.research.price-trends.%24makeModelSlug"
        # response = requests.get(url)
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)
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
    async def _fetch_data_model_with_year(db: AsyncSession, model_label: str, model_id: str, brand_label: str) -> \
            Optional[Dict]:
        await asyncio.sleep(1)
        url = f"https://www.cargurus.com/research/price-trends/{brand_label}-{model_label}-{model_id}?entityIds={model_id}&startDate=1738620000000&endDate=1751662799999&_data=routes%2F%28%24intl%29.research.price-trends.%24makeModelSlug"
        # response = requests.get(url)
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)
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

    @staticmethod
    async def load_search_data_and_base_url(page_number: int) -> dict:
        search_url_template = (
            "https://www.cargurus.com/Cars/searchPage.action?"
            "searchId=cd991113-d908-44d1-b918-131871d60d58&zip=92562&distance=100"
            "&sourceContext=untrackedWithinSite_false_0&sortDir=ASC&sortType=BEST_MATCH"
            "&srpVariation=DEFAULT_SEARCH&isDeliveryEnabled=true&nonShippableBaseline=0"
            "&pageNumber={page_number}&filtersModified=true"
        )
        url = search_url_template.format(page_number=page_number)
        try:
            # response = requests.get(url)
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url)
            return response.json()
        except Exception as e:
            print(f"❌ Failed to fetch search page {page_number}: {e}")
            return {}

    @staticmethod
    async def fetch_validated_results_from_page(page_number: int) -> List:
        extractor = CarGurusUrlExtractor()
        validator = CarGurusValidator()

        print(f"🔍 Fetching page {page_number}")
        search_data = await CarGurusService.load_search_data_and_base_url(page_number)
        if not search_data:
            print(f"❌ No data on page {page_number}.")
            return []

        listing_ids = await extractor.extract_listing_ids(search_data)
        if not listing_ids:
            print(f"❌ No listing IDs found on page {page_number}.")
            return []

        detail_urls = await extractor.generate_detail_urls(listing_ids, search_data)

        results = []
        for detail_url in detail_urls:
            await asyncio.sleep(random.uniform(0.7, 1))
            result = await validator.validate_from_url(detail_url.strip())
            results.append(result)

        return results

    @staticmethod
    async def get_data_from_url_service(db: AsyncSession, max_pages: Optional[int] = None) -> List[dict]:
        all_data = []
        page_number = 1

        while True:
            if max_pages is not None and page_number > max_pages:
                break

            results = await CarGurusService.fetch_validated_results_from_page(page_number)
            if not results:
                break

            all_data.extend(results)
            page_number += 1

        return all_data

    @staticmethod
    async def save_to_db_from_url_service(db: AsyncSession, max_pages: Optional[int] = None) -> dict:
        created = 0
        skipped = 0
        page_number = 1

        while True:
            if max_pages is not None and page_number > max_pages:
                break

            results = await CarGurusService.fetch_validated_results_from_page(page_number)
            if not results:
                break

            for result in results:
                if not result.success:
                    continue

                listing_data = result.listing_data
                tech_data = result.technical_data
                equipment_data = result.equipment_data

                existing_listing = await db.execute(
                    select(ListingMobileDe).where(ListingMobileDe.url == listing_data["url"])
                )
                existing = existing_listing.scalar_one_or_none()

                if existing:
                    if not listing_data.get("is_active", True):
                        existing.is_active = False
                        await db.commit()
                    skipped += 1
                    continue

                try:
                    listing = ListingMobileDe(
                        brand=listing_data["brand"],
                        model=listing_data["model"],
                        registration_year=listing_data["registration_year"],
                        mileage=listing_data.get("mileage"),
                        city_or_postal_code=listing_data.get("city_or_postal_code"),
                        color=listing_data.get("color"),
                        price=listing_data["price"],
                        currency=listing_data.get("currency", "EUR"),
                        url=listing_data["url"],
                        is_active=listing_data.get("is_active", True)
                    )
                    db.add(listing)
                    await db.flush()

                    tech = TechnicalDetails(**tech_data, listing_id=listing.id)
                    db.add(tech)

                    equip = Equipment(**equipment_data, listing_id=listing.id)
                    db.add(equip)

                    await db.commit()
                    created += 1
                except (KeyError, ValueError, TypeError) as e:
                    print(f"Skipping listing due to error: {e}. Data: {listing_data}")
                    continue

            print(f"✅ Page {page_number} saved. Created: {created}, Skipped: {skipped}")
            page_number += 1

        return {"created": created, "skipped": skipped}

    @staticmethod
    async def check_car_status_service(url: str) -> Dict[str, Union[bool, int, str]]:
        """
        Check if a car listing is still active and whether it's new on the site.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            response = requests.get(str(url), headers=headers, timeout=15)
            response.raise_for_status()

            if "no longer available" in response.text.lower():
                return {
                    "is_active": False,
                    "is_new": False,
                    "days_on_market": 0,
                    "message": "Listing is no longer available"
                }

            data = response.json()
            days_on_market = data.get("listing", {}).get("listingHistory", {}).get("daysOnCarGurus", 999)
            is_new = days_on_market <= 3

            return {
                "is_active": True,
                "is_new": is_new,
                "days_on_market": days_on_market,
                "message": "Listing is active"
            }

        except requests.exceptions.RequestException as e:
            return {
                "is_active": False,
                "is_new": False,
                "days_on_market": 0,
                "message": f"Request failed: {e}"
            }
