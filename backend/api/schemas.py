from datetime import datetime
from pydantic import BaseModel, Field

class SessionCreate(BaseModel):
    customer_id: int

class SessionResponse(BaseModel):
    id: int
    customer_id: int
    status: str
    created_at: datetime

class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)

class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime