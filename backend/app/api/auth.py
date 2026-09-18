from fastapi import APIRouter, HTTPException, status, Depends

from app.repositories import user_repository, profile_repository
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserOut
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    if user_repository.email_exists(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    password_hash = hash_password(payload.password)
    user = user_repository.create_user(payload.name, payload.email, password_hash, payload.role)

    # Every non-organization, non-admin user gets an (initially empty) profile.
    if payload.role in ("student", "professional"):
        profile_repository.create_profile(user["id"])

    token = create_access_token(subject=str(user["id"]), extra_claims={"role": user["role"]})
    return TokenResponse(access_token=token, user=UserOut(**user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = user_repository.get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been suspended.")

    token = create_access_token(subject=str(user["id"]), extra_claims={"role": user["role"]})
    return TokenResponse(access_token=token, user=UserOut(**user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(**current_user)
