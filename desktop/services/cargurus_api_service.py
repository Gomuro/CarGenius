import asyncio
import aiohttp
from desktop.GLOBAL import GLOBAL
from typing import Optional, Dict, Any, List, Tuple
import requests
from datetime import datetime, timedelta

class CargurusAPIService:
    def __init__(self):
        self.base_url = GLOBAL.CARGURUS_API_BASE_URL
        self.api_prefix = GLOBAL.CARGURUS_API_PREFIX
        self.api_raw_data_endpoint = GLOBAL.CARGURUS_API_RAW_DATA_ENDPOINT
        self.is_loading = False

    async def _request(self, entity_ids: list[str], start_date: int, end_date: int) -> Optional[Any]:
        """Base method for making HTTP requests"""
        self.is_loading = True
        entity_ids_str = ",".join(entity_ids) if entity_ids else "Index"
        url = f"{self.base_url}{self.api_prefix}{entity_ids_str}&startDate={start_date}&endDate={end_date}{self.api_raw_data_endpoint}"
        response = requests.get(url)
        return response.json()
    
    async def get_cargurus_data(self, entity_ids: list[str], start_date: Optional[int] = None, end_date: Optional[int] = None) -> Optional[Any]:
        try:
            # Use default 1-year range if not provided
            if start_date is None:
                start_date = int((datetime.now() - timedelta(days=365)).timestamp() * 1000)
            if end_date is None:
                end_date = int(datetime.now().timestamp() * 1000)
                
            data = await self._request(entity_ids, start_date, end_date)
            return data
        except Exception as e:
            # print(f"Error getting cargurus data: {e}")
            return None
        
    def get_cargurus_data_sync(self, entity_ids: list[str], start_date: Optional[int] = None, end_date: Optional[int] = None) -> Optional[Any]:
        """Synchronous version using asyncio.run"""
        try:
            return asyncio.run(self.get_cargurus_data(entity_ids, start_date=start_date, end_date=end_date))
        except Exception as e:
            # print(f"Error in sync cargurus data: {e}")
            return None

    def format_price_trends_for_graph(self, cargurus_data: Dict) -> List[Tuple[int, float, int]]:
        """
        Format CarGurus price trends data for TimeSeriesLineGraphWidget
        Returns list of (time_index, price, timestamp) tuples
        """
        try:
            formatted_data = []
            
            # Check if we have pricePointsEntities (detailed time series with real dates)
            if "pricePointsEntities" in cargurus_data and cargurus_data["pricePointsEntities"]:
                entity = cargurus_data["pricePointsEntities"][0]  # Take first entity
                price_points = entity.get("pricePoints", [])
                
                for i, point in enumerate(price_points):
                    price = point.get("price", 0)
                    timestamp = point.get("date", 0)  # Unix timestamp in milliseconds
                    formatted_data.append((i, price, timestamp))
                    
            # Fallback to priceTrends if no detailed data (with estimated dates)
            elif "priceTrends" in cargurus_data:
                current_time = datetime.now()
                
                for price_trend_section in cargurus_data["priceTrends"]:
                    if price_trend_section.get("type") == "MAKES":
                        entities = price_trend_section.get("entities", [])
                        if entities:
                            # Take first entity's price trends
                            entity = entities[0]
                            trends = entity.get("priceTrends", [])
                            
                            for i, trend in enumerate(trends):
                                price = trend.get("averagePrice", 0)
                                # Use 'tw' (time window) to calculate approximate date
                                days_ago = trend.get("tw", i * 30)  # Default to 30-day intervals
                                estimated_date = current_time - timedelta(days=days_ago)
                                timestamp = int(estimated_date.timestamp() * 1000)  # Convert to milliseconds
                                formatted_data.append((i, price, timestamp))
                            break
            
            # Reduce data points for better visualization (keep max 30 points)
            if len(formatted_data) > 30:
                step = len(formatted_data) // 30
                formatted_data = [formatted_data[i] for i in range(0, len(formatted_data), step)]
                # Re-index the data points but keep original timestamps
                formatted_data = [(i, price, timestamp) for i, (_, price, timestamp) in enumerate(formatted_data)]
            
            return formatted_data if formatted_data else [(0, 25000, 0)]  # Fallback
            
        except Exception as e:
            # print(f"Error formatting price trends: {e}")
            return [(0, 25000, 0)]  # Fallback data

    def get_entity_id_by_label(self, label: str, cargurus_data: Dict) -> Optional[str]:
        """
        Find entity ID for a given label from CarGurus data
        """
        try:
            for price_trend_section in cargurus_data.get("priceTrends", []):
                if price_trend_section.get("type") in ["MAKES", "MODELS"]:
                    entities = price_trend_section.get("entities", [])
                    for entity in entities:
                        if entity.get("label", "").lower() == label.lower():
                            return entity.get("entityId")
            return None
        except Exception as e:
            # print(f"Error finding entity ID for label {label}: {e}")
            return None

    def get_label_from_server(self, label_name: str) -> Optional[Dict]:
        """
        Get label data from your server's CarGurus database
        """
        try:
            server_url = f"{GLOBAL.API_BASE_URL}/cargurus/get_by_label"
            params = {"name": label_name}
            
            response = requests.get(server_url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                # print(f"Server returned status {response.status_code}")
                return None
        except Exception as e:
            # print(f"Error getting label from server: {e}")
            return None

