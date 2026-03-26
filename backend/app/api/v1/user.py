from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from backend.app.core.deps import get_db, get_current_user
from backend.app.core.security import create_access_token
from backend.app.crud import user as crud_user
from backend.app.models.user import User
from backend.app.schemas.user import UserRegister, UserLogin, UserUpdate, UserOut, Token
from backend.app.utils.file_utils import save_upload_image

router = APIRouter(prefix="/users", tags=["用户"])


@router.post("/register", response_model=UserOut, status_code=201, summary="用户注册")
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if crud_user.get_user_by_username(db, payload.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    new_user = crud_user.create_user(
        db=db,
        username=payload.username,
        password=payload.password,
        contact=payload.contact,
    )
    return new_user


@router.post("/login", response_model=Token, summary="用户登录")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    db_user = crud_user.verify_user(db, payload.username, payload.password)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut, summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut, summary="修改个人资料")
def update_me(payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated = crud_user.update_user_profile(db, current_user, payload.model_dump(exclude_unset=True))
    return updated


@router.post("/me/avatar", response_model=UserOut, summary="上传/更换头像")
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image_path = save_upload_image(file)
    updated = crud_user.update_user_avatar(db, current_user, image_path)
    return updated
