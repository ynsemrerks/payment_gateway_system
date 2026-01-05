"""Authentication API endpoints."""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

router = APIRouter()


class LoginRequest(BaseModel):
    username: str  # Email
    password: str  # API Key


class LoginResponse(BaseModel):
    user_id: int
    email: str
    api_key: str
    message: str


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User Login",
    description="Login with Email and API Key"
)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate using Email and API Key.
    """
    # Treat username as email and password as api_key
    user = db.query(User).filter(
        User.email == credentials.username,
        User.api_key == credentials.password
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or API key"
        )
    
    return LoginResponse(
        user_id=user.id,
        email=user.email,
        api_key=user.api_key,
        message="Login successful"
    )
