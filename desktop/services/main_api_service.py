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

    # Sync wrapper methods
    def validate_license_sync(self, key: str, client_info: str, device_id: Optional[str] = None) -> Optional[Dict]:
        return asyncio.run(self.validate_license(key, client_info, device_id))

    def generate_license_sync(self, client_info: Optional[str] = None) -> Optional[Dict]:
        return asyncio.run(self.generate_license(client_info))

    def get_average_prices_sync(self, limit: int = 20) -> Optional[Dict]:
        return asyncio.run(self.get_average_prices(limit))

    def search_listings_sync(self, filters: Dict) -> Optional[Dict]:
        return asyncio.run(self.search_listings(filters))

    def get_license_stats_sync(self, days: int = 30) -> Optional[Dict]:
        return asyncio.run(self.get_license_stats(days))

    def get_tracked_filters_sync(self, license_key: str) -> Optional[list]:
        return asyncio.run(self.get_tracked_filters(license_key))

    def update_tracked_filters_sync(self, license_key: str, filters: list) -> Optional[list]:
        return asyncio.run(self.update_tracked_filters(license_key, filters))

    def clear_tracked_filters_sync(self, license_key: str) -> Optional[list]:
        return asyncio.run(self.clear_tracked_filters(license_key))

    def get_is_loading(self) -> bool:
        return self.is_loading