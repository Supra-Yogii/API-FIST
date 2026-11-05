from fastapi import Depends, HTTPException, APIRouter, Form
from sqlalchemy.orm import Session
from Database import get_db
import model
from fastapi.responses import HTMLResponse
from utils import send_email
import auth_utils

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/forgot-username")
def forgot_username(email: str, db: Session = Depends(get_db)):
    user = db.query(model.User).filter(model.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    
    send_email(
        to=email,
        subject="Your Username",
        body=f"Your username is: {user.username}"
    )

    return {"message": "Username sent to your email"}

@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(model.User).filter(model.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    # Buat token reset password
    token_data = {"sub": user.username}
    reset_token = auth_utils.create_reset_token(token_data, minutes=15)

    # Kirim link ke email
    reset_link = f"http://localhost:8000/reset-password?token={reset_token}"
    send_email(to=email, subject="Reset Your Password", body=f"Click this link: {reset_link}")

    return {"message": "Password reset link sent to your email"}

@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_form(token: str):
    return f"""
    <html>
        <body>
            <form method="post" action="/reset-password">
                <input type="hidden" name="token" value="{token}">
                <input type="password" name="new_password" placeholder="Enter new password"/>
                <button type="submit">Reset Password</button>
            </form>
        </body>
    </html>
    """

# POST: proses reset password
@router.post("/reset-password", response_class=HTMLResponse)
def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Hapus token revoked yang sudah kadaluarsa
    auth_utils.cleanup_expired_tokens(db)

    # Verifikasi token
    payload = auth_utils.verify_access_token(token, db=db)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    username = payload.get("sub")
    jti = payload.get("jti")
    user = db.query(model.User).filter(model.User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update password baru
    user.hashed_password = auth_utils.get_password_hash(new_password)
    db.commit()

    # Blacklist token yang baru saja dipakai
    auth_utils.revoke_token(jti, db, lifetime_minutes=15)

    return HTMLResponse(
        content=f"<h3>Password {username} berhasil direset 🚀</h3>",
        status_code=200
    )
