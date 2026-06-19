from pydantic import BaseModel, EmailStr
from typing import Optional

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None

class UserRoleUpdate(BaseModel):
    role: str  # citizen, doctor, regional_admin, national_admin