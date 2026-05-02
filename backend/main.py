from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import psycopg2
import psycopg2.extras
import os
import secrets

app = FastAPI(title="名刺アプリ API")

# CORS（フロントエンドのGitHub PagesのURLを設定）
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 管理者認証（Basic Auth）
security = HTTPBasic()
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "changeme")

def get_db():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        yield conn
    finally:
        conn.close()

def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, ADMIN_USER)
    correct_pass = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証失敗",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# ── スキーマ ──────────────────────────────────────
class ProfileCreate(BaseModel):
    name: str
    furigana: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    team: Optional[str] = None
    phone: Optional[str] = None
    condition: Optional[str] = None
    notes: Optional[str] = None

class ProfileUpdate(ProfileCreate):
    pass

# ── DB初期化 ──────────────────────────────────────
@app.on_event("startup")
def startup():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                furigana TEXT,
                gender TEXT,
                age INTEGER,
                team TEXT,
                phone TEXT,
                condition TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
    conn.commit()
    # 既存テーブルへのカラム追加（既にある場合はスキップ）
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS furigana TEXT")
    conn.commit()
    conn.close()

# ── 公開エンドポイント ────────────────────────────

@app.get("/api/login")
def login(name: str, conn=Depends(get_db)):
    """名前でログイン→プロフィール返却"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM profiles WHERE name = %s", (name,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="名前が見つかりません")
    return dict(row)

# ── 管理者エンドポイント ──────────────────────────

@app.get("/api/admin/profiles")
def list_profiles(conn=Depends(get_db), admin=Depends(require_admin)):
    """全プロフィール一覧"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM profiles ORDER BY id")
        rows = cur.fetchall()
    return [dict(r) for r in rows]

@app.post("/api/admin/profiles", status_code=201)
def create_profile(data: ProfileCreate, conn=Depends(get_db), admin=Depends(require_admin)):
    """プロフィール新規作成"""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO profiles (name, furigana, gender, age, team, phone, condition, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (data.name, data.furigana, data.gender, data.age, data.team, data.phone, data.condition, data.notes))
            row = cur.fetchone()
        conn.commit()
        return dict(row)
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=409, detail="同じ名前が既に登録されています")

@app.put("/api/admin/profiles/{profile_id}")
def update_profile(profile_id: int, data: ProfileUpdate, conn=Depends(get_db), admin=Depends(require_admin)):
    """プロフィール更新"""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            UPDATE profiles
            SET name=%s, furigana=%s, gender=%s, age=%s, team=%s, phone=%s, condition=%s, notes=%s, updated_at=NOW()
            WHERE id=%s RETURNING *
        """, (data.name, data.furigana, data.gender, data.age, data.team, data.phone, data.condition, data.notes, profile_id))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="プロフィールが見つかりません")
    conn.commit()
    return dict(row)

@app.delete("/api/admin/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: int, conn=Depends(get_db), admin=Depends(require_admin)):
    """プロフィール削除"""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM profiles WHERE id=%s", (profile_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="プロフィールが見つかりません")
    conn.commit()
