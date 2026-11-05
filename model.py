from Database import Base
from sqlalchemy import Column, Integer, VARCHAR, String, ForeignKey, Enum, DECIMAL, DateTime
import enum
from datetime import datetime
from enum import Enum as PyEnum


class Produk(Base):
    __tablename__ = "produk"

    ID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(VARCHAR(255), index=True)
    Harga = Column (DECIMAL(15,2))
    Stock = Column(Integer)
    Category = Column(VARCHAR(100))
    gambar_url = Column(String(255))  # URL gambar produk

# Enum untuk database
class OrderStatus(enum.Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    completed = "completed"
    cancelled = "cancelled"

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    produk_id = Column(Integer, ForeignKey("produk.ID"))
    name_pesanan = Column(String(255))
    quantity = Column(Integer)
    total_harga = Column(DECIMAL(15,2))
    status = Column(Enum(OrderStatus))

class UserRole(str, PyEnum):
    admin = "admin"
    user = "user"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True)
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user)

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)