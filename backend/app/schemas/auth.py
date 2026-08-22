from pydantic import BaseModel
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: Optional[int] = None
    role: Optional[str] = None
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    permissions: Optional[List[str]] = []

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    organization_id: Optional[int] = None
    permissions: Optional[List[str]] = []
