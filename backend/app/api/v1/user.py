from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.schemas.user import UserRegister, UserLogin, Token
from backend.app.core.deps import get_db
from backend.app.core.security import create_access_token
from backend.app.crud import user as crud_user

from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.user import UserOut
from fastapi import Depends

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", status_code=201)
def register(user: UserRegister, db: Session = Depends(get_db)):
    # 1. 检查用户名是否存在
    existing_user = crud_user.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # 2. 创建用户
    new_user = crud_user.create_user(
        db=db,
        username=user.username,
        password=user.password,
        contact=user.contact
    )

    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }


@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    # 1. 校验用户
    db_user = crud_user.verify_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 2. 生成 JWT
    access_token = create_access_token(
        data={"sub": db_user.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
@router.get("/me", response_model=UserOut)
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return current_user