from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from Database import get_db
import model
import auth_utils
import schemas
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Auth"])

# Register user
@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Cek username & email
    if db.query(model.User).filter(model.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username Sudah Ada")

    if db.query(model.User).filter(model.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email Sudah Terdaftar")

    # Hash password
    hashed_password = auth_utils.get_password_hash(user.password)

    # Buat user baru
    new_user = model.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role="user"
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return new_user

# Login user
@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(model.User).filter(model.User.username == form_data.username).first()
    if not user or not auth_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Username atau password salah")
    
    # Buat token dengan role
    access_token = auth_utils.create_access_token({
        "sub": user.username,
        "role": user.role  
    })
    
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route (user)
@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: model.User = Depends(auth_utils.get_current_user)):
    return current_user

# Admin route
@router.get("/admin", response_model=schemas.UserResponse)
def read_admin(current_admin: model.User = Depends(auth_utils.get_current_admin)):
    return current_admin
