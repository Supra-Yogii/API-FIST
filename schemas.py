from pydantic import BaseModel
from typing import Optional
from enum import Enum
from decimal import Decimal

class Produk(BaseModel):   # ini untuk Create
    Name: str
    Harga: Decimal
    Stock: int
    Category: str

class ProdukUpdate(BaseModel):   # ini untuk Update
    Name: Optional [str] = None
    Harga: Optional [Decimal] = None
    Stock: Optional [int] = None
    Category: Optional [str] = None

class ProdukResponse(BaseModel):
    ID: int
    Name: str
    Harga: Decimal
    Stock: int
    Category: str

class ProdukSearch(BaseModel):
    name: str
    skip: Optional[int] = 0
    limit: Optional[int] = 10

# Enum untuk API
class OrderStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    completed = "completed"
    cancelled = "cancelled"

class OrderBase(BaseModel):
    produk_name: str
    quantity: int

class OrderCreate(BaseModel):
    name_pesanan: str
    quantity: int

class OrderResponse(BaseModel):
    id: str
    name_pesanan: str
    quantity: int
    harga_satuan: float
    total_harga: float
    status: str
    pesan: str

class UserUpdate(BaseModel):
    old_password: str
    new_username: Optional[str] = None
    new_password: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    
class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional [str] = None
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str