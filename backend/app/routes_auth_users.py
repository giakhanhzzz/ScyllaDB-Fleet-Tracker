from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import LoginRequest, TokenResponse, UserCreate
from app.security import verify_password, create_access_token, require_role, hash_password
from app.database import db
from app.config import settings
from datetime import datetime, timezone

router = APIRouter(prefix="/api", tags=["Auth & Users"])

@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    # Q1: Login theo username
    if not db.session:
        # Chế độ demo dự phòng khi ScyllaDB chưa sẵn sàng
        mock_users = {
            "khanh_admin": ("ADMIN", "Phạm Gia Khánh"),
            "vu_dispatcher": ("DISPATCHER", "Trà Ngọc Nguyên Vũ"),
            "luan_viewer": ("VIEWER", "Lê Hữu Luân"),
        }
        if req.username in mock_users:
            role, full_name = mock_users[req.username]
            token = create_access_token({"sub": req.username, "role": role, "company_id": settings.COMPANY_ID})
            return TokenResponse(
                access_token=token,
                username=req.username,
                full_name=full_name,
                role=role,
                company_id=settings.COMPANY_ID
            )
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")

    row = db.session.execute(db.prepared_statements["login"], (req.username,)).one()
    if not row or not row.active or not verify_password(req.password, row.password_hash):
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")

    token = create_access_token({"sub": row.username, "role": row.role, "company_id": row.company_id})
    return TokenResponse(
        access_token=token,
        username=row.username,
        full_name=row.full_name,
        role=row.role,
        company_id=row.company_id
    )

@router.get("/users")
def list_users(user=Depends(require_role(["ADMIN"]))):
    # Q2: Danh sách user theo công ty (Chỉ Admin)
    if not db.session:
        return [
            {"username": "khanh_admin", "full_name": "Phạm Gia Khánh", "role": "ADMIN", "active": True},
            {"username": "vu_dispatcher", "full_name": "Trà Ngọc Nguyên Vũ", "role": "DISPATCHER", "active": True},
            {"username": "luan_viewer", "full_name": "Lê Hữu Luân", "role": "VIEWER", "active": True},
        ]
    rows = db.session.execute("SELECT username, full_name, role, active, created_at FROM users_by_company WHERE company_id = %s", (settings.COMPANY_ID,))
    return [dict(r._asdict()) for r in rows]
