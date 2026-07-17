from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import get_db
from src.models.user import User
from src.auth.hashing import hash_password, verify_password
from src.auth.jwt import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code = status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    hashed = hash_password(request.password)

    new_user = User(email = request.email , hashed_password=hashed)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Account created successfully", "email": new_user.email}



@router.post("/login")
def login(request:LoginRequest , db: Session = Depends(get_db)):
    
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password")
    

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


    token = create_access_token(data = {"sub": user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "email": user.email
    }