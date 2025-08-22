from __future__ import annotations
import hmac, json, os
from hashlib import sha256
from typing import Optional, Any, Dict
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field, constr

# 專案既有：Supabase 客戶端
from app.db import supabase  # type: ignore

router = APIRouter(prefix="/internal/whitelist", tags=["internal-whitelist"]) 
BOT_SECRET = os.getenv("BOT_SECRET", "")

# ---------- Pydantic Models ----------
class UpsertBody(BaseModel):
    provider: constr(strip_whitespace=True, to_lower=True) = Field(..., regex=r"^[a-z0-9_\-]+$")
    user_id: constr(strip_whitespace=True, min_length=5, max_length=128)
    plan_code: constr(strip_whitespace=True, to_lower=True, min_length=2, max_length=64)  # e.g. pro_month, pro_year, elite_month, elite_year
    order_no: Optional[str] = None
    period_no: Optional[str] = None
    access_until: datetime  # 由你方後端依 Webhook 決議後傳入
    ts: int

class RemoveBody(BaseModel):
    provider: constr(strip_whitespace=True, to_lower=True)
    user_id: constr(strip_whitespace=True, min_length=5, max_length=128)
    reason: constr(strip_whitespace=True, to_lower=True)
    ts: int

# ---------- Helpers ----------

def _hmac_ok(raw_body: bytes, signature_hex: str) -> bool:
    if not BOT_SECRET:
        return False
    mac = hmac.new(BOT_SECRET.encode("utf-8"), raw_body, sha256).hexdigest()
    return hmac.compare_digest(mac, signature_hex)

async def _require_sig_and_key(request: Request, signature: Optional[str], idem_key: Optional[str]) -> tuple[str, bytes]:
    raw = await request.body()
    if not signature or not _hmac_ok(raw, signature):
        raise HTTPException(status_code=401, detail="invalid signature")
    if not idem_key:
        raise HTTPException(status_code=400, detail="missing X-Idempotency-Key")
    return idem_key, raw

# 簡單的型錄快取（記憶體級，進程重啟後重載）
_PLAN_CACHE: dict[str, dict] = {}

def _load_plan(plan_code: str) -> dict:
    global _PLAN_CACHE
    if plan_code in _PLAN_CACHE:
        return _PLAN_CACHE[plan_code]
    resp = supabase.table("subscription_plans").select("*").eq("plan_code", plan_code).eq("is_active", True).limit(1).execute()
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=400, detail=f"unknown or inactive plan_code: {plan_code}")
    _PLAN_CACHE[plan_code] = rows[0]
    return rows[0]

def _record_event(idem_key: str, kind: str, payload: Dict[str, Any]) -> bool:
    try:
        supabase.table("whitelist_events").insert({
            "idempotency_key": idem_key,
            "event_type": kind,
            "payload": payload,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }).execute()
        return True
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False
        raise

# ---------- Endpoints ----------
@router.post("/upsert", status_code=200)
async def upsert(
    request: Request,
    x_signature: Optional[str] = Header(default=None, alias="X-Signature"),
    x_idem: Optional[str] = Header(default=None, alias="X-Idempotency-Key"),
    body: UpsertBody = None,
):
    idem_key, raw = await _require_sig_and_key(request, x_signature, x_idem)
    first_time = _record_event(idem_key, "upsert", json.loads(raw.decode("utf-8")))
    if not first_time:
        return {"ok": True, "idempotent": True}

    if body.provider != "line":
        raise HTTPException(status_code=400, detail="unsupported provider")

    plan = _load_plan(body.plan_code)
    # 將型錄資訊快照到白名單，避免日後型錄變更影響已購用戶
    rec = {
        "user_id": body.user_id,
        "provider": body.provider,
        "plan_code": body.plan_code,
        "tier": plan.get("tier"),                 # 'pro' | 'elite' | ...
        "period": plan.get("period"),             # 'month' | 'year'
        "period_months": plan.get("period_months"),
        "scope": plan.get("scope"),               # JSONB 權限清單
        "order_no": body.order_no,
        "period_no": body.period_no,
        "access_until": body.access_until.isoformat().replace("+00:00", "Z"),
        "status": "active",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    supabase.table("bot_whitelist").upsert(rec, on_conflict="user_id").execute()
    return {"ok": True}

@router.post("/remove", status_code=200)
async def remove(
    request: Request,
    x_signature: Optional[str] = Header(default=None, alias="X-Signature"),
    x_idem: Optional[str] = Header(default=None, alias="X-Idempotency-Key"),
    body: RemoveBody = None,
):
    idem_key, raw = await _require_sig_and_key(request, x_signature, x_idem)
    first_time = _record_event(idem_key, "remove", json.loads(raw.decode("utf-8")))
    if not first_time:
        return {"ok": True, "idempotent": True}

    supabase.table("bot_whitelist").upsert({
        "user_id": body.user_id,
        "provider": body.provider,
        "status": "removed",
        "removed_reason": body.reason,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }, on_conflict="user_id").execute()
    return {"ok": True}

@router.post("/echo")
async def echo(request: Request, x_signature: Optional[str] = Header(default=None, alias="X-Signature")):
    raw = await request.body()
    if not x_signature or not _hmac_ok(raw, x_signature):
        raise HTTPException(status_code=401, detail="invalid signature")
    return json.loads(raw.decode("utf-8"))