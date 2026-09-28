import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import db
from app.routes_auth_users import router as auth_router
from app.routes_fleet import router as fleet_router
from app.routes_tracking import router as tracking_router

app = FastAPI(
    title="ScyllaDB Fleet Tracker API",
    description="Hệ thống quản lý dữ liệu theo dõi vị trí phương tiện vận tải và lịch sử hành trình của đội xe",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    db.connect()

@app.on_event("shutdown")
def shutdown_event():
    db.close()

# Routes
app.include_router(auth_router)
app.include_router(fleet_router)
app.include_router(tracking_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected" if db.session else "disconnected",
        "version": "1.0.0"
    }

# Mount static files nếu có frontend tĩnh
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
