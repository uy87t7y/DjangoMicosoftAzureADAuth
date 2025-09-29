from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class AzureUserSchema(BaseModel):
    user_id: str = Field(..., alias='user_id')
    name: Optional[str]
    first_name: Optional[str]
    email: Optional[EmailStr]
    office_location: Optional[str]
    position: Optional[str]
    roles: List[str] = []
    graph_token: Optional[str]

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
