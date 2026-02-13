from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserCreate, User
from app.schemas.token import Token, RefreshToken
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import auth_service
from app.core.dependencies import get_current_user

router = APIRouter()

@router.post("/register", response_model=User)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    return auth_service.register_user(db, user_data)

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = auth_service.authenticate_user(
        db, 
        login_data.username, 
        login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    tokens = auth_service.create_tokens(user.id)
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token
    )

@router.post("/login/oauth2")
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = auth_service.authenticate_user(
        db, 
        form_data.username, 
        form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    tokens = auth_service.create_tokens(user.id)
    return {
        "access_token": tokens.access_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshToken,
    db: Session = Depends(get_db)
):
    return auth_service.refresh_access_token(refresh_data.refresh_token)

@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user)
):

    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
async def get_me(
    current_user = Depends(get_current_user)
):
    return current_user