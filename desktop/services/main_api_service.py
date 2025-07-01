import asyncio
import aiohttp
from desktop.GLOBAL import GLOBAL
from typing import Optional, Dict, Any


class APIService:
    def __init__(self):
        self.base_url = GLOBAL.API_BASE_URL
        self.api_prefix = GLOBAL.API_PREFIX
        self.is_loading = False

    async def _request(self, method: str, endpoint: str, data: Optional[Any] = None) -> Optional[Any]:
        """Base method for making HTTP requests"""
        self.is_loading = True
        url = f"{self.base_url}{self.api_prefix}{endpoint}"

        print(f"Making {method} request to {url} with data: {data}")

        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    params = {k: v for k, v in data.items() if v is not None} if data else None
                    async with session.get(url, params=params) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method.upper() == "POST":
                    async with session.post(url, json=data) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method.upper() == "PUT":
                    async with session.put(url, json=data) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method.upper() == "DELETE":
                    async with session.delete(url) as response:
                        response.raise_for_status()
                        return await response.json()
        except aiohttp.ClientError as e:
            print(f"API error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        finally:
            self.is_loading = False

    # License endpoints
    async def validate_license(self, key: str, client_info: str, device_id: Optional[str] = None) -> Optional[Dict]:
        """Validate license key"""
        endpoint = "/license/validate_key_device" if device_id else "/license/validate"
        data = {"key": key, "client_info": client_info}
        if device_id:
            data["device_id"] = device_id
        return await self._request("POST", endpoint, data)

    async def generate_license(self, client_info: Optional[str] = None) -> Optional[Dict]:
        """Generate new license key"""
        return await self._request("POST", "/license/generate", {"client_info": client_info})

    # Analytics endpoints
    async def get_average_prices(self, limit: int = 20) -> Optional[Dict]:
        """Get average prices by brand"""
        return await self._request("GET", "/analytics/average_price", {"limit": limit})

    async def get_filter_options(self) -> Optional[Dict]:
        """Get all available filter options (brands, models, colors, years) efficiently"""
        return await self._request("GET", "/analytics/filter-options")

    async def get_models_for_brand(self, brand: str = None) -> Optional[list]:
        """Get distinct models for a specific brand"""
        params = {}
        if brand:
            params["brand"] = brand
        return await self._request("GET", "/analytics/filter-options/models", params)

    async def get_colors_for_filters(self, brand: str = None, model: str = None, registration_year: int = None) -> Optional[list]:
        """Get distinct colors filtered by brand, model, and year"""
        params = {}
        if brand:
            params["brand"] = brand
        if model:
            params["model"] = model
        if registration_year:
            params["registration_year"] = registration_year
        return await self._request("GET", "/analytics/filter-options/colors", params)

    async def search_listings(self, filters: Dict) -> Optional[Dict]:
        """Search car listings with filters and get statistics"""
        return await self._request("GET", "/analytics/filter-search", filters)

    async def save_json_to_db(self) -> Optional[Dict]:
        """Save JSON data to database"""
        return await self._request("POST", "/analytics/json-to-db")

    # Stats endpoints
    async def get_license_stats(self, days: int = 30) -> Optional[Dict]:
        """Get license creation statistics"""
        return await self._request("GET", "/stats/licenses-per-day", {"days": days})

    async def get_best_offer(self, license_key: str) -> Optional[Dict]:
        """Get the best offer based on user's tracked filters."""
        return await self._request("GET", "/analytics/ml_best_price_search", {"key": license_key})

    # Filter management endpoints
    async def get_tracked_filters(self, license_key: str) -> Optional[list]:
        """Get tracked filters for a license"""
        return await self._request("GET", f"/license/{license_key}/filters")

    async def update_tracked_filters(self, license_key: str, filters: list) -> Optional[list]:
        """Update tracked filters for a license"""
        return await self._request("PUT", f"/license/{license_key}/filters", filters)

    async def clear_tracked_filters(self, license_key: str) -> Optional[list]:
        """Clear all tracked filters for a license"""
        return await self._request("DELETE", f"/license/{license_key}/filters")

    # GPT endpoints
    async def ask_gpt(self, user_id: str, prompt: str, context: Optional[Dict] = None, chat_history: Optional[list] = None) -> Optional[Dict]:
        """Ask a question to the GPT model."""
        endpoint = "/gpt/ask"
        data = {
            "user_id": user_id, 
            "gpt_prompt": prompt, 
            "context": context,
            "chat_history": chat_history or []
        }
        return await self._request("POST", endpoint, data)

    # Sync wrapper methods
    def validate_license_sync(self, key: str, client_info: str, device_id: Optional[str] = None) -> Optional[Dict]:
        return asyncio.run(self.validate_license(key, client_info, device_id))

    def generate_license_sync(self, client_info: Optional[str] = None) -> Optional[Dict]:
        return asyncio.run(self.generate_license(client_info))

    def get_average_prices_sync(self, limit: int = 20) -> Optional[Dict]:
        return asyncio.run(self.get_average_prices(limit))

    def get_filter_options_sync(self) -> Optional[Dict]:
        """Synchronous wrapper for get_filter_options"""
        return asyncio.run(self.get_filter_options())

    def get_models_for_brand_sync(self, brand: str = None) -> Optional[list]:
        """Synchronous wrapper for get_models_for_brand"""
        return asyncio.run(self.get_models_for_brand(brand))

    def get_colors_for_filters_sync(self, brand: str = None, model: str = None, registration_year: int = None) -> Optional[list]:
        """Synchronous wrapper for get_colors_for_filters"""
        return asyncio.run(self.get_colors_for_filters(brand, model, registration_year))

    def search_listings_sync(self, filters: Dict) -> Optional[Dict]:
        return asyncio.run(self.search_listings(filters))

    def get_license_stats_sync(self, days: int = 30) -> Optional[Dict]:
        return asyncio.run(self.get_license_stats(days))

    def get_best_offer_sync(self, license_key: str) -> Optional[Dict]:
        """Synchronous wrapper for get_best_offer"""
        return asyncio.run(self.get_best_offer(license_key))

    def get_tracked_filters_sync(self, license_key: str) -> Optional[list]:
        return asyncio.run(self.get_tracked_filters(license_key))

    def update_tracked_filters_sync(self, license_key: str, filters: list) -> Optional[list]:
        return asyncio.run(self.update_tracked_filters(license_key, filters))

    def clear_tracked_filters_sync(self, license_key: str) -> Optional[list]:
        return asyncio.run(self.clear_tracked_filters(license_key))

    def ask_gpt_sync(self, user_id: str, prompt: str, context: Optional[Dict] = None, chat_history: Optional[list] = None) -> Optional[Dict]:
        """Synchronous wrapper for ask_gpt"""
        return asyncio.run(self.ask_gpt(user_id, prompt, context, chat_history))

    def get_is_loading(self) -> bool:
        return self.is_loading