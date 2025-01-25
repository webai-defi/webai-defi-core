from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.models.user import User
from src.schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.wallet_id == user.wallet_id).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User with this wallet_id already exists")
    new_user = User(wallet_id=user.wallet_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/users/{wallet_id}", response_model=UserResponse)
def login_user(wallet_id: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.wallet_id == wallet_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user