from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from auth_utils import oauth2_scheme
from Database import get_db
import model
import auth_utils
import schemas

router = APIRouter(prefix="/user", tags=["User"])

# Hapus user (hanya admin)
@router.delete("/users/{user_id}", response_model=dict)
def delete_username_id(user_id: int,
                db: Session = Depends(get_db),
                current_admin: model.User = Depends(auth_utils.get_current_admin)):

    # Cari user berdasarkan ID
    user = db.query(model.User).filter(model.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cegah admin menghapus dirinya sendiri (opsional)
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Admin cannot delete themselves")

    # Simpan data user sebelum dihapus (untuk respon)
    deleted_user_info = {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }

    # Hapus user
    db.delete(user)
    db.commit()

    return {
        "message": "User Berhasil di hapus",
        "deleted_user": deleted_user_info
    }

@router.delete("/users/{username}")
def delete_username(
    username: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    # Verifikasi token
    payload = auth_utils.verify_access_token(token, db)
    if not payload:
        raise HTTPException(status_code=401, detail="Token tidak valid atau expired")

    # Cek role admin
    role = payload.get("role")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang bisa menghapus user")

    # Cari user target
    user = db.query(model.User).filter(model.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User dengan username '{username}' tidak ditemukan")

    # Hapus user
    db.delete(user)
    db.commit()

    return {"message": f"User '{username}' berhasil dihapus oleh admin"}

@router.put("/users/update_user")
def update_user(
    update_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: model.User = Depends(auth_utils.get_current_user),
    token: str = Depends(auth_utils.oauth2_scheme)
):
    # Verifikasi password lama
    if not auth_utils.verify_password(update_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect old password")

    # Tambahkan token lama ke blacklist
    payload = auth_utils.verify_access_token(token)
    jti = payload.get("jti")
    if jti:
        revoked = model.RevokedToken(jti=jti)
        db.add(revoked)
        db.commit()

    # Update username kalau ada
    if update_data.new_username:
        current_user.username = update_data.new_username

    # Update password kalau ada
    if update_data.new_password:
        current_user.hashed_password = auth_utils.get_password_hash(update_data.new_password)

    db.commit()
    db.refresh(current_user)

    return {"message": "User credentials updated. Please login again."}

@router.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user_admin(user_id: int,
                      update_data: schemas.UserUpdate,
                      db: Session = Depends(get_db),
                      current_admin: model.User = Depends(auth_utils.get_current_admin)):

    user = db.query(model.User).filter(model.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update_data.username:
        existing_user = db.query(model.User).filter(
            model.User.username == update_data.username,
            model.User.id != user.id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = update_data.username

    if update_data.password:
        hashed_password = auth_utils.get_password_hash(update_data.password)
        user.hashed_password = hashed_password

    db.commit()
    db.refresh(user)

    return user
