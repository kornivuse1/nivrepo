from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db
from app.auth import authenticate_user, create_access_token, get_current_user, get_user_by_username, hash_password
from app.models import User, UserRole, AppSettings

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _get_allow_registration(db: AsyncSession) -> bool:
    """Registration allowed from app settings (DB), or from config if no row."""
    result = await db.execute(select(AppSettings).limit(1))
    row = result.scalar_one_or_none()
    if not row:
        return get_settings().allow_registration
    return getattr(row, "allow_registration", get_settings().allow_registration)


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    username: str
    role: str


class RegisterIn(BaseModel):
    username: str
    password: str
    password_confirm: str


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    user.last_login_ip = _client_ip(request)
    token = create_access_token(user.username, user.role)
    return Token(access_token=token)


@router.get("/registration-allowed")
async def registration_allowed(db: AsyncSession = Depends(get_db)):
    """Public: whether new users can sign up (so the player can show/hide Sign up)."""
    return {"allow_registration": await _get_allow_registration(db)}


@router.post("/register", response_model=Token)
async def register(
    request: Request,
    body: RegisterIn,
    db: AsyncSession = Depends(get_db),
):
    if not await _get_allow_registration(db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration is disabled")
    if body.password != body.password_confirm:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
    if len(body.password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters")
    if await get_user_by_username(db, body.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    ip = _client_ip(request)
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        role=UserRole.viewer,
        created_ip=ip or None,
        last_login_ip=ip or None,
    )
    db.add(user)
    await db.flush()
    token = create_access_token(user.username, user.role)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut(username=user.username, role=user.role.value)
