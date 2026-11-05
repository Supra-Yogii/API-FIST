from fastapi import Depends, HTTPException, Query, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import func
from Database import get_db
from typing import List, Optional
import model
import schemas
from utils import get_image_url

router = APIRouter(prefix="/produk", tags=["Produk"])


# untuk melihat List Produk dengan pagination
@router.get("/produk")
def get_all_produk(
    limit: int = 10,       # jumlah produk per halaman
    page: int = 1,         # halaman ke-
    db: Session = Depends(get_db)
):
    # hitung offset (mulai dari produk ke-berapa)
    offset = (page - 1) * limit

    # ambil produk sesuai halaman
    produk = db.query(model.Produk).offset(offset).limit(limit).all()

    # total semua produk untuk bantu frontend
    total = db.query(model.Produk).count()

    return {
        "page": page,
        "limit": limit,
        "total_produk": total,
        "total_halaman": (total + limit - 1) // limit,
        "data": produk
    }


# Membuat produk List Baru
@router.post("/produk")
def create_produk(produk: schemas.Produk, db: Session = Depends(get_db)):
    produk_baru = model.Produk(
        Name=produk.Name,
        Harga=produk.Harga,
        Stock=produk.Stock,
        Category=produk.Category
    )
    db.add(produk_baru)
    db.commit()
    db.refresh(produk_baru)

    return {
        "message": "Produk Baru berhasil ditambahkan",
        "data": produk_baru
    }

# untuk mencari semua list produk
@router.get("/produk/search", response_model=List[schemas.ProdukResponse])
def search_produk(
    name: Optional[str] = Query(None, description="Cari berdasarkan nama produk"),
    min_harga: Optional[float] = Query(None, description="Harga minimum"),
    max_harga: Optional[float] = Query(None, description="Harga maksimum"),
    sort_by: str = Query("name", description="Kolom untuk sorting: 'name' atau 'harga'"),
    order: str = Query("asc", description="Urutan: 'asc' atau 'desc'"),
    skip: int = Query(0, description="Lewati n produk (untuk pagination)"),
    limit: int = Query(10, description="Jumlah produk yang ditampilkan"),
    db: Session = Depends(get_db)
):
    query = db.query(model.Produk)

    # 🔍 Filter nama
    if name:
        query = query.filter(func.lower(model.Produk.Name).like(f"%{name.lower()}%"))

    # 💰 Filter harga
    if min_harga is not None:
        query = query.filter(model.Produk.Harga >= min_harga)
    if max_harga is not None:
        query = query.filter(model.Produk.Harga <= max_harga)

    # 📑 Sorting
    if sort_by == "name":
        sort_column = model.Produk.Name
    elif sort_by == "harga":
        sort_column = model.Produk.Harga
    else:
        raise HTTPException(status_code=400, detail="sort_by harus 'name' atau 'harga'")

    if order == "asc":
        query = query.order_by(sort_column.asc())
    elif order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        raise HTTPException(status_code=400, detail="order harus 'asc' atau 'desc'")

    # 🚦 Pagination
    hasil = query.offset(skip).limit(limit).all()

    if not hasil:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

    return hasil

# mencari produk berdasarkan ID
@router.get("/produk/{produk_ID}")
def Cari_Produk_Berdasarkan_Id(produk_ID: str, db: Session = Depends(get_db)):
    produk = db.query(model.Produk).filter(model.Produk.ID == produk_ID).first()
    if not produk:
        return {f"Produk Dengan ID {produk_ID} Tidak Di Temukan"}
    return produk

# untuk menghapus List Produk Dengan Id
@router.delete("/produk/{produk_ID}")
def delete_produk(produk_ID: str, db: Session = Depends(get_db)):
    produk = db.query(model.Produk).filter(model.Produk.ID == produk_ID).first()
    if not produk:
        return {"Produk tidak ditemukan"}

    db.delete(produk)
    db.commit()
    return {"messege": f"Produk dengan id {produk_ID} Berhasil di hapus"}

@router.post("/produk/search", response_model=list[schemas.ProdukResponse])
def search_produk_post(payload: schemas.ProdukSearch, db: Session = Depends(get_db)):
    query = db.query(model.Produk)

    # 🔍 filter nama
    query = query.filter(func.lower(model.Produk.Name).like(f"%{payload.name.lower()}%"))

    # 💰 urutkan harga tertinggi → terendah
    query = query.order_by(model.Produk.Harga.desc())

    # 🚦 pagination
    hasil = query.offset(payload.skip).limit(payload.limit).all()

    if not hasil:
        raise HTTPException(status_code=404, detail=f"Produk dengan nama '{payload.name}' tidak ditemukan")

    return hasil

# Untuk merubah List Produk Berdasarkan ID
@router.put("/produk/{produk_ID}")
def update_produk(produk_ID: str, produk_update: schemas.ProdukUpdate, db: Session = Depends(get_db)):
    produk = db.query(model.Produk).filter(model.Produk.ID == produk_ID).first()
    if not produk:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")


    old_data = {
        "id": produk.ID,
        "name": produk.Name,
        "harga": produk.Harga,
        "stock": produk.Stock,
        "category": produk.Category
    }
    # update hanya field yang dikirim

    if produk_update.Name is not None:
        produk.Name = produk_update.Name
    if produk_update.Harga is not None:
        produk.Harga = produk_update.Harga
    if produk_update.Stock is not None:
        produk.Stock = produk_update.Stock
    if produk_update.Category is not None:
        produk.Category = produk_update.Category

    db.commit()
    db.refresh(produk)

    return {
        "message": f"Produk dengan ID {produk_ID} berhasil diupdate",
        "old_data": old_data, 
        "new_data": {
            "ID": produk.ID,
            "Name": produk.Name,
            "Harga": produk.Harga,
            "Stock": produk.Stock,
            "Category": produk.Category
        }
    }

# ambil gambar daru unsplash
@router.put("/update_gambar_otomatis")
def gambar_produk(db: Session = Depends(get_db)):
    produk_list = db.query(model.Produk).all()
    if not produk_list:
        raise HTTPException(status_code=404, detail="Tidak ada produk ditemukan")
    
    updated_count = 0
    for produk in produk_list:
        if not produk.gambar_url:  # hanya update jika kolom Gambar kosong
            image_url = get_image_url(produk.Name)
            if image_url:
                produk.gambar_url = image_url
                updated_count += 1
    db.commit()
    return {"message": f"Gambar berhasil diperbarui untuk {updated_count} produk"}