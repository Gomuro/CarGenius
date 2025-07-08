"""
CarGurus URL Extractor

Extracts listing IDs from CarGurus search results and generates URLs for detailed listing data.
"""
from typing import List, Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class CarGurusUrlExtractor:
    """
    Extracts listing URLs from CarGurus search page results
    """
    
    def __init__(self, base_url: str = "https://www.cargurus.com/Cars/detailListingJson.action"):
        self.base_url = base_url
        self.logger = logger
    
    def extract_listing_ids(self, search_data: Dict[str, Any]) -> List[int]:
        """
        Extract all listing IDs from search page data
        
        Args:
            search_data: JSON data from CarGurus search page
            
        Returns:
            List of listing IDs
        """
        listing_ids = []
        
        try:
            tiles = search_data.get('tiles', [])
            
            for tile in tiles:
                if 'data' in tile and 'id' in tile['data']:
                    listing_id = tile['data']['id']
                    listing_ids.append(listing_id)
                    
            self.logger.info(f"Extracted {len(listing_ids)} listing IDs")
            
        except Exception as e:
            self.logger.error(f"Error extracting listing IDs: {e}")
            
        return listing_ids
    
    def generate_detail_urls(self, listing_ids: List[int], search_params: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Generate detail listing URLs for given listing IDs
        
        Args:
            listing_ids: List of listing IDs
            search_params: Optional search parameters to include in URLs
            
        Returns:
            List of detail listing URLs
        """
        urls = []
        
        # Default parameters
        default_params = {
            'searchZip': '92562',
            'searchDistance': '100',
            'inclusionType': 'DEFAULT',
            'pid': 'null',
            'sourceContext': 'carGurusHomePageModel',
            'isDAVE': 'false'
        }
        
        # Update with provided parameters
        if search_params:
            default_params.update(search_params)
        
        for listing_id in listing_ids:
            # Build URL parameters
            params = [f"inventoryListing={listing_id}"]
            for key, value in default_params.items():
                params.append(f"{key}={value}")
            
            url = f"{self.base_url}?{'&'.join(params)}"
            urls.append(url)
        
        self.logger.info(f"Generated {len(urls)} detail URLs")
        return urls
    
    def extract_urls_from_search_file(self, search_file_path: str, search_params: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Extract detail URLs from search results file
        
        Args:
            search_file_path: Path to search results JSON file
            search_params: Optional search parameters
            
        Returns:
            List of detail URLs
        """
        try:
            with open(search_file_path, 'r', encoding='utf-8') as f:
                search_data = json.load(f)
            
            listing_ids = self.extract_listing_ids(search_data)
            urls = self.generate_detail_urls(listing_ids, search_params)
            
            return urls
            
        except Exception as e:
            self.logger.error(f"Error processing search file {search_file_path}: {e}")
            return []
    
    def extract_listings_summary(self, search_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract summary information about all listings
        
        Args:
            search_data: JSON data from CarGurus search page
            
        Returns:
            List of listing summaries
        """
        summaries = []
        
        try:
            tiles = search_data.get('tiles', [])
            
            for tile in tiles:
                if 'data' in tile:
                    data = tile['data']
                    summary = {
                        'id': data.get('id'),
                        'title': data.get('listingTitle', ''),
                        'make': data.get('makeName', ''),
                        'model': data.get('modelName', ''),
                        'year': data.get('carYear'),
                        'price': data.get('price'),
                        'mileage': data.get('mileage'),
                        'dealer': data.get('dealerName', ''),
                        'city': data.get('sellerCity', ''),
                        'vin': data.get('vin', ''),
                        'stock_number': data.get('stockNumber', '')
                    }
                    summaries.append(summary)
            
            self.logger.info(f"Extracted {len(summaries)} listing summaries")
            
        except Exception as e:
            self.logger.error(f"Error extracting listing summaries: {e}")
            
        return summaries


def extract_detail_urls_from_file(search_file_path: str, output_file: Optional[str] = None, search_params: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Convenience function to extract URLs from search file
    
    Args:
        search_file_path: Path to search results JSON file
        output_file: Optional path to save URLs
        search_params: Optional search parameters
        
    Returns:
        List of detail URLs
    """
    extractor = CarGurusUrlExtractor()
    urls = extractor.extract_urls_from_search_file(search_file_path, search_params)
    
    if output_file and urls:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for url in urls:
                    f.write(url + '\n')
            logger.info(f"Saved {len(urls)} URLs to {output_file}")
        except Exception as e:
            logger.error(f"Error saving URLs to file: {e}")
    
    return urls


def get_listing_parameters_from_search(search_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract search parameters that should be used in detail URLs
    
    Args:
        search_data: JSON data from CarGurus search page
        
    Returns:
        Dictionary of parameters to use in detail URLs
    """
    params = {}
    
    # Try to extract search parameters from the data
    # These might be in different places depending on the search structure
    if 'searchCriteria' in search_data:
        criteria = search_data['searchCriteria']
        if 'zip' in criteria:
            params['searchZip'] = str(criteria['zip'])
        if 'distance' in criteria:
            params['searchDistance'] = str(criteria['distance'])
    
    # Set defaults if not found
    if 'searchZip' not in params:
        params['searchZip'] = '92562'
    if 'searchDistance' not in params:
        params['searchDistance'] = '100'
    
    return params 