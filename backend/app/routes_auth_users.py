from fastapi import APIRouter, Depends, HTTPException
from app.database import db
from app.schemas import LoginRequest, TokenResponse
from app.security import create_access_token, current_user, require_role, verify_password
from app.services import row_to_dict

router = APIRouter(prefix="/api", tags=["Auth & Users"], dependencies=[Depends(db.require_ready)])

@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    row = db.execute(db.prepared_statements["login"], (req.username,)).one()
    if not row or not row.active or not verify_password(req.password, row.password_hash):
        raise HTTPException(401, "Sai tên đăng nhập hoặc mật khẩu")
    return TokenResponse(access_token=create_access_token({"sub": row.username}),
                         username=row.username, full_name=row.full_name,
                         role=row.role, company_id=row.company_id)

@router.get("/auth/me")
def me(user=Depends(current_user)):
    return user

@router.get("/users")
def list_users(user=Depends(require_role(["ADMIN"]))):
    rows = db.execute("SELECT username,full_name,role,active,created_at FROM users_by_company WHERE company_id = %s", (user["company_id"],))
    return [row_to_dict(row) for row in rows]
