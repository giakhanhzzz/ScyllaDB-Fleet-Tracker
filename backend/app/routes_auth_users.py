from fastapi import APIRouter, Depends, HTTPException
from cassandra.query import BatchStatement
from app.database import db
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserUpdate
from app.security import create_access_token, current_user, hash_password, require_role, verify_password
from app.services import row_to_dict
from datetime import datetime, timezone

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

@router.post("/users", status_code=201)
def create_user(req: UserCreate, user=Depends(require_role(["ADMIN"]))):
    if db.execute(db.prepared_statements["login"], (req.username,)).one():
        raise HTTPException(409, "Tên đăng nhập đã tồn tại")
    now = datetime.now(timezone.utc)
    company = user["company_id"]
    batch = BatchStatement()
    batch.add("INSERT INTO users_by_username (username,password_hash,full_name,role,company_id,active,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
              (req.username,hash_password(req.password),req.full_name,req.role,company,True,now))
    batch.add("INSERT INTO users_by_company (company_id,username,full_name,role,active,created_at) VALUES (%s,%s,%s,%s,%s,%s)",
              (company,req.username,req.full_name,req.role,True,now))
    db.execute(batch)
    return {"username": req.username, "role": req.role, "active": True}

@router.patch("/users/{username}")
def update_user(username: str, req: UserUpdate, user=Depends(require_role(["ADMIN"]))):
    row = db.execute(db.prepared_statements["login"], (username,)).one()
    if not row or row.company_id != user["company_id"]:
        raise HTTPException(404, "Không tìm thấy người dùng trong công ty")
    if all(value is None for value in (req.password, req.full_name, req.role, req.active)):
        raise HTTPException(422, "Cần ít nhất một trường cần sửa")
    if username == user["username"] and (req.active is False or (req.role is not None and req.role != "ADMIN")):
        raise HTTPException(409, "Admin không được tự khóa hoặc bỏ quyền của mình")
    full_name = req.full_name if req.full_name is not None else row.full_name
    role = req.role if req.role is not None else row.role
    active = req.active if req.active is not None else row.active
    password_hash = hash_password(req.password) if req.password is not None else row.password_hash
    batch = BatchStatement()
    batch.add("UPDATE users_by_username SET password_hash=%s,full_name=%s,role=%s,active=%s WHERE username=%s",
              (password_hash,full_name,role,active,username))
    batch.add("UPDATE users_by_company SET full_name=%s,role=%s,active=%s WHERE company_id=%s AND username=%s",
              (full_name,role,active,user["company_id"],username))
    db.execute(batch)
    return {"username": username, "role": role, "active": active}
