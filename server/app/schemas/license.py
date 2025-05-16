from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LicenseCreateRequest(BaseModel):
    client_info: Optional[str] = None


class LicenseCreateResponse(BaseModel):
    key: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    client_info: Optional[str]


class LicenseValidateRequest(BaseModel):
    key: str
    client_info: str


class LicenseValidateResponse(BaseModel):
    is_valid: bool


class LicenseInfo(BaseModel):
    key: str
    is_active: bool
    created_at: datetime
    client_info: Optional[str]
