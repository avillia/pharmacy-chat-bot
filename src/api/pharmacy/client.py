from __future__ import annotations
from asyncio import run as run_async
from httpx import AsyncClient, HTTPError
from src.core.models import Pharmacy, Prescription


class PharmacyAPIError(Exception):
    """Custom exception for pharmacy API errors."""
    pass


class PharmacyClient:    
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    async def fetch_all_pharmacies(self) -> list[Pharmacy]:
        try:
            async with AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url)
                response.raise_for_status()
                
                pharmacy_data = response.json()
                return [self._parse_pharmacy_data(data) for data in pharmacy_data]
                
        except HTTPError as e:
            raise PharmacyAPIError(f"Failed to fetch pharmacy data: {str(e)}") from e
        except Exception as e:
            raise PharmacyAPIError(f"Unexpected error fetching pharmacy data: {str(e)}") from e
    
    def fetch_all_pharmacies_sync(self) -> list[Pharmacy]:
        return run_async(self.fetch_all_pharmacies())
    
    def _parse_pharmacy_data(self, data: dict) -> Pharmacy:

        prescriptions = []
        if 'prescriptions' in data and data['prescriptions']:
            prescriptions = [
                Prescription(drug=rx['drug'], count=rx['count'])
                for rx in data['prescriptions']
            ]
        
        return Pharmacy(
            id=data['id'],
            name=data['name'],
            phone=data['phone'],
            email=data.get('email'),
            city=data['city'],
            state=data['state'],
            prescriptions=prescriptions
        )

