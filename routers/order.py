from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import func
from Database import get_db, engine
from typing import List
from enum import Enum
import model
import schemas
import uuid

router = APIRouter(prefix="/order", tags=["Order"])

# 🟢 Buat Order baru
@router.post("/orders", response_model=schemas.OrderResponse)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):

    # Cari produk berdasarkan nama
    produk = db.query(model.Produk).filter(model.Produk.Name == order.name_pesanan).first()
    if not produk:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

    # Cek stok
    if produk.Stock < order.quantity:
        raise HTTPException(status_code=400, detail="Stok tidak mencukupi")

    # Hitung total harga
    total_harga = produk.Harga * order.quantity

    # Buat order baru
    new_order = model.Order(
        id=str(uuid.uuid4())[:8],
        produk_id=produk.ID,
        name_pesanan=produk.Name,
        quantity=order.quantity,
        total_harga=total_harga,
        status=model.OrderStatus.pending
    )
    db.add(new_order)

    # Kurangi stok produk
    produk.Stock -= order.quantity

    db.commit()
    db.refresh(new_order)

    # Invoice ke user
    return {
        "id": new_order.id,
        "name_pesanan": new_order.name_pesanan,
        "quantity": new_order.quantity,
        "harga_satuan": float(produk.Harga),
        "total_harga": float(new_order.total_harga),
        "status": new_order.status,
        "pesan": f"Pesanan '{new_order.name_pesanan}' sebanyak {new_order.quantity} berhasil dibuat."
    }

# 🟢 Ambil semua order
@router.get("/orders", response_model=List[schemas.OrderResponse])
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(model.Order).all()
    
    response = []
    for o in orders:
        response.append({
            "id": o.id,
            "name_pesanan": o.name_pesanan,
            "quantity": o.quantity,
            "harga_satuan": float(o.total_harga / o.quantity),
            "total_harga": float(o.total_harga),
            "status": o.status.value if isinstance(o.status, Enum) else o.status,
            "pesan": f"Pesanan '{o.name_pesanan}' sebanyak {o.quantity} berhasil dibuat."
        })
    return response

# 🟢 Ambil order berdasarkan ID
@router.get("/orders/{order_id}", response_model=schemas.OrderResponse)
def get_order_id(order_id: str, db: Session = Depends(get_db)):
    order = db.query(model.Order).filter(model.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order tidak ditemukan")

    # mapping ke dict sesuai response_model
    return {
        "id": order.id,
        "name_pesanan": order.name_pesanan,
        "quantity": order.quantity,
        "harga_satuan": float(order.total_harga / order.quantity),  # harga per item
        "total_harga": float(order.total_harga),
        "status": order.status.value if isinstance(order.status, Enum) else order.status,
        "pesan": f"Pesanan '{order.name_pesanan}' sebanyak {order.quantity} berhasil dibuat."
    }

# 🟢 Ambil order berdasarkan Name
@router.get("/order/{name_pesanan}", response_model=List[schemas.OrderResponse])
def get_order_name(name_pesanan: str, db: Session = Depends(get_db)):
    orders = db.query(model.Order).filter(model.Order.name_pesanan == name_pesanan).all()
    if not orders:
        raise HTTPException(status_code=404, detail=f"Order dengan nama '{name_pesanan}' tidak ditemukan")

    return [
        {
            "id": order.id,
            "name_pesanan": order.name_pesanan,
            "quantity": order.quantity,
            "harga_satuan": float(order.total_harga / order.quantity),
            "total_harga": float(order.total_harga),
            "status": order.status.value if hasattr(order.status, "value") else order.status,
            "pesan": f"Pesanan '{order.name_pesanan}' sebanyak {order.quantity} berhasil dibuat."
        }
        for order in orders
    ]

# 🟡 Update status order
@router.put("/orders/{order_id}", response_model=schemas.OrderResponse)
def update_order_status(order_id: str, status: schemas.OrderStatus, db: Session = Depends(get_db)):
    order = db.query(model.Order).filter(model.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order tidak ditemukan")

    # Update status
    order.status = status
    db.commit()
    db.refresh(order)

    # Mapping manual ke dict sesuai response_model
    return {
        "id": order.id,
        "name_pesanan": order.name_pesanan,
        "quantity": order.quantity,
        "harga_satuan": float(order.total_harga / order.quantity),
        "total_harga": float(order.total_harga),
        "status": order.status,
        "pesan": f"Pesanan '{order.name_pesanan}' sebanyak {order.quantity} berhasil diperbarui."
    }

# 🔴 Hapus order
@router.delete("/orders/{order_id}")
def delete_order(order_id: str, db: Session = Depends(get_db)):
    order = db.query(model.Order).filter(model.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order tidak ditemukan")

    db.delete(order)
    db.commit()
    return {"message": f"Order {order_id} berhasil dihapus"}
