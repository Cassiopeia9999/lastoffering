from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.core.password import hash_password, verify_password

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, password: str, contact: str):
    user = User(
        username=username,
        password_hash=hash_password(password),
        contact=contact
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def verify_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user
