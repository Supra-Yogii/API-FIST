from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers import produk, order, auth, user, admin


app = FastAPI()
app.include_router(produk.router)
app.include_router(order.router) 
app.include_router(auth.router)  
app.include_router(user.router)
app.include_router(admin.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # asal frontend kamu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)