from passlib.hash import argon2
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from jose import jwt
from jose.exceptions import JWTError,  ExpiredSignatureError
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import uuid4
from Database import get_db, engine
import model


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
# Hash password
def get_password_hash(password: str) -> str:
    return argon2.hash(password)

# Verifikasi password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return argon2.verify(plain_password, hashed_password)

# Buat token JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": str(uuid4())})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

# fungsi tambahan khusus reset password
def create_reset_token(data: dict, minutes: int = 15):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=minutes)
    to_encode.update({"exp": expire, "jti": str(uuid4())})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

# Verifikasi token JWT
def verify_access_token(token: str, db: Session = None):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")

        # kalau db dikasih, cek blacklist
        if db and jti and is_token_revoked(jti, db):
            return None  # token sudah di-blacklist

        return payload
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    jti = payload.get("jti")
    if db.query(model.RevokedToken).filter(model.RevokedToken.jti == jti).first():
        raise HTTPException(status_code=401, detail="Token revoked")

    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(model.User).filter(model.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="token Tidak Invalid")
    
    user = db.query(model.User).filter(model.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Tidak Ada User")
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Anda tidak berhak")
    
    return user

def revoke_token(jti: str, db: Session, lifetime_minutes: int = 15):
    """Masukkan token ke blacklist dan set expire otomatis"""
    revoked = model.RevokedToken(
        jti=jti,
        expires_at=datetime.utcnow() + timedelta(minutes=lifetime_minutes)
    )
    db.add(revoked)
    db.commit()
    return revoked

def cleanup_expired_tokens(db: Session):
    now = datetime.utcnow()
    db.query(model.RevokedToken).filter(model.RevokedToken.expires_at < now).delete()
    db.commit()

def is_token_revoked(jti: str, db: Session) -> bool:
    """Cek apakah token sudah di-blacklist"""
    return db.query(model.RevokedToken).filter(model.RevokedToken.jti == jti).first() is not None

def init_db():
    model.Base.metadata.create_all(bind=engine)
