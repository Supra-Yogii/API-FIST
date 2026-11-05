from fastapi import FastAPI
from sqlalchemy.orm import Session
from threading import Timer
import auth_utils
from Database import SessionLocal

app = FastAPI()

def cleanup_tokens_periodically(db: Session):
    """Fungsi untuk membersihkan token kadaluarsa"""
    auth_utils.cleanup_expired_tokens(db)

@app.on_event("startup")
def start_background_tasks():
    """Jalankan cleanup token setiap 60 detik di background"""
    def run_periodically():
        db = SessionLocal()
        try:
            cleanup_tokens_periodically(db)
        finally:
            db.close()
        Timer(60, run_periodically).start()  # loop setiap 60 detik

    run_periodically()
