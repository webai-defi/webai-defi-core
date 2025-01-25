from pydantic import BaseModel

class UserCreate(BaseModel):
    wallet_id: str

class UserResponse(BaseModel):
    id: int
    wallet_id: str

    class Config:
        orm_mode = True