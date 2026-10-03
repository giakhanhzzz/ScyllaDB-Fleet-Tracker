from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from app.database import db
from app.routes_auth_users import router as auth_router
from app.routes_fleet import router as fleet_router
from app.routes_tracking import router as tracking_router

@asynccontextmanager
async def lifespan(app):
    try:
        db.connect()
        yield
    finally:
        db.close()

app = FastAPI(title="ScyllaDB Fleet Tracker API", version="0.2.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(fleet_router)
app.include_router(tracking_router)

@app.get("/api/health")
def health_check():
    row = db.execute("SELECT release_version FROM system.local").one()
    if not row:
        raise HTTPException(503, "ScyllaDB chưa sẵn sàng")
    return {"status": "healthy", "database": "connected", "release_version": row.release_version}

# Source checkout: project/frontend. Docker image: /app/frontend.
frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
if not frontend_dir.is_dir():
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
