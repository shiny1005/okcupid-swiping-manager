import base64
import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Tuple

from bson import ObjectId
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from okcupid_api import OkCupidClient
from okcupid_api import profile as ok_profile
from okcupid_api import swipe as ok_swipe
from okcupid_api.load_sample import (
    get_api,
    get_auth,
    get_graphql_settings,
    get_swipe_settings,
)
from examples.auto_swipe_example import _build_client_from_db_account
from examples.auto_chat_runner import (
    get_merged_auto_chat_config,
    run_auto_chat_once_for_client,
)
from examples.show_profile_settings import get_profile_summary
from examples.update_bio_example import update_bio_for_client
from examples.update_realname_example import update_realname_for_client




MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://mongodb1234:iamanetstar@cluster0.svpkyqh.mongodb.net/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "okcupid_automation")

mongo_client = AsyncIOMotorClient(MONGODB_URI)
db = mongo_client[MONGODB_DB_NAME]
accounts_col = db["accounts"]
jobs_col = db["jobs"]
logs_col = db["logs"]
config_col = db["config"]


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, payload: dict):
        msg = json.dumps(payload)
        dead: list[WebSocket] = []
        for ws in self.active_connections:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


ws_manager = ConnectionManager()


async def _broadcast_log(log_doc: dict):
    payload = {
        "type": "log",
        "payload": {
            "id": str(log_doc.get("_id", "")),
            "accountId": str(log_doc.get("accountId", "")),
            "timestamp": log_doc.get("timestamp", ""),
            "level": log_doc.get("level", "info"),
            "source": log_doc.get("source", "action"),
            "message": log_doc.get("message", ""),
        },
    }
    await ws_manager.broadcast_json(payload)


async def _broadcast_profile_update(account_id: str):
    await ws_manager.broadcast_json(
        {"type": "profile_update", "payload": {"accountId": account_id}}
    )


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        try:
            return ObjectId(str(v))
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Not a valid ObjectId") from exc


class AccountOut(BaseModel):
    id: str = Field(alias="id")
    name: str
    proxy: Optional[str] = None
    status: str = "paused"
    lastActive: Optional[str] = None
    tokenExpiry: Optional[str] = None
    sessionState: str = "login_required"
    loginRequired: bool = True
    error: Optional[str] = None
    # Legacy stats (kept for compatibility, but not actively updated)
    actionsToday: int = 0
    successRate: float = 0.0
    failureRate: float = 0.0
    # Swipe statistics (cumulative per account)
    swipeLikes: int = 0
    swipePasses: int = 0
    swipeErrors: int = 0
    swipeLikeRate: float = 0.0
    swipePassRate: float = 0.0
    swipeErrorRate: float = 0.0


class ProxyConfig(BaseModel):
    type: Optional[str] = "socks5"
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None


class AccountCreate(BaseModel):
    name: str
    authentication_token: str
    cookie: str
    proxy: ProxyConfig


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    authentication_token: Optional[str] = None
    cookie: Optional[str] = None
    proxy: Optional[ProxyConfig] = None


class JobOut(BaseModel):
    id: str
    accountId: Optional[str] = None
    type: str
    status: str
    attempts: int
    createdAt: str


class LogOut(BaseModel):
    id: str
    accountId: str
    timestamp: str
    level: str
    source: str
    message: str


class RateConfig(BaseModel):
    maxActionsPerHour: int = 60
    delayMinMs: int = 2000
    delayMaxMs: int = 7000
    randomizationEnabled: bool = True
    retryLimit: int = 3


class OpenAIConfigIn(BaseModel):
    apiKey: Optional[str] = None
    model: Optional[str] = None


class OpenAIConfigOut(BaseModel):
    hasKey: bool
    maskedKey: Optional[str] = None
    model: Optional[str] = None


class SwipeSettings(BaseModel):
    directions: List[str] = ["pass", "like"]
    like_percentage: int = 30
    max_swipes: int = 10
    delay_seconds: float = 1.5


class AutoChatSettings(BaseModel):
    funnel: str = ""
    poll_seconds: int = 4
    cta_min_msgs: int = 2
    cta_max_msgs: int = 4
    delay_chat_part_min: float = 2.0
    delay_chat_part_max: float = 3.0


class GeneralSettings(BaseModel):
    swipe: SwipeSettings = SwipeSettings()
    auto_chat: AutoChatSettings = AutoChatSettings()


class AiChatRequest(BaseModel):
    accountIds: List[str]


class AutoSwipeRequest(BaseModel):
    accountIds: List[str]
    count: int = 50


class UpdateBioRequest(BaseModel):
    accountId: str
    bio: str


class UpdateRealnameRequest(BaseModel):
    accountId: str
    realname: str


app = FastAPI(title="OkCupid Automation API")

# CORS: allow any origin for flexible access (any frontend can call this API).
_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Return 500 with CORS headers so the frontend gets a proper response on server errors."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=_CORS_HEADERS,
        )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Internal server error"},
        headers=_CORS_HEADERS,
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)


def _parse_jwt_session(token: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse JWT to derive tokenExpiry (ISO string) and sessionState (ok/expiring/expired/login_required).
    Returns (tokenExpiry, sessionState). No signature verification.
    """
    if not token or not isinstance(token, str):
        return None, "login_required"
    t = token.strip()
    if t.lower().startswith("bearer "):
        t = t[7:].strip()
    parts = t.split(".")
    if len(parts) != 3:
        return None, "login_required"
    try:
        payload_b64 = parts[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        return None, "login_required"
    exp = payload.get("exp")
    if exp is None:
        return None, "login_required"
    try:
        exp_ts = int(exp)
    except (TypeError, ValueError):
        return None, "login_required"
    now_ts = int(datetime.now(timezone.utc).timestamp())
    expiry_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    token_expiry_str = expiry_dt.strftime("%Y-%m-%d %H:%M UTC")
    if exp_ts < now_ts:
        return token_expiry_str, "expired"
    if exp_ts < now_ts + 3600:
        return token_expiry_str, "expiring"
    return token_expiry_str, "ok"


def _account_from_doc(doc: dict) -> AccountOut:
    proxy_display: Optional[str] = None
    proxy_data = doc.get("proxy")
    if isinstance(proxy_data, dict):
        host = proxy_data.get("host")
        port = proxy_data.get("port")
        ptype = proxy_data.get("type") or "socks5"
        if host and port:
            proxy_display = f"{ptype}://{host}:{port}"

    likes = int(doc.get("swipeLikes") or 0)
    passes = int(doc.get("swipePasses") or 0)
    errors = int(doc.get("swipeErrors") or 0)
    total_swipes = likes + passes + errors
    if total_swipes > 0:
        like_rate = likes / total_swipes
        pass_rate = passes / total_swipes
        error_rate = errors / total_swipes
    else:
        like_rate = pass_rate = error_rate = 0.0

    auth = doc.get("auth") or {}
    token = auth.get("token")
    token_expiry, session_state = _parse_jwt_session(token)
    last_active = doc.get("lastActive")
    if token_expiry is None and doc.get("tokenExpiry"):
        token_expiry = doc.get("tokenExpiry")
    if session_state == "login_required" and not token:
        login_required = True
    else:
        login_required = session_state in ("expired", "login_required")

    return AccountOut(
        id=str(doc["_id"]),
        name=doc.get("name", ""),
        proxy=proxy_display,
        status=doc.get("status", "paused"),
        lastActive=last_active,
        tokenExpiry=token_expiry or "—",
        sessionState=session_state,
        loginRequired=login_required,
        error=doc.get("error"),
        actionsToday=doc.get("actionsToday", 0),
        successRate=doc.get("successRate", 0.0),
        failureRate=doc.get("failureRate", 0.0),
        swipeLikes=likes,
        swipePasses=passes,
        swipeErrors=errors,
        swipeLikeRate=like_rate,
        swipePassRate=pass_rate,
        swipeErrorRate=error_rate,
    )


async def _get_rate_config() -> RateConfig:
    doc = await config_col.find_one({"_id": "rate_config"})
    if not doc:
        cfg = RateConfig()
        await config_col.insert_one({"_id": "rate_config", **cfg.model_dump()})
        return cfg
    return RateConfig(**{k: v for k, v in doc.items() if k != "_id"})


def _mask_api_key(key: str) -> str:
    if len(key) <= 11:
        return "***"
    return key[:7] + "..." + key[-4:]


async def _get_openai_api_key() -> Optional[str]:
    doc = await config_col.find_one({"_id": "openai_config"})
    if not doc:
        return None
    api_key = doc.get("apiKey")
    if not isinstance(api_key, str) or not api_key.strip():
        return None
    return api_key.strip()


async def _get_openai_config_doc() -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Returns (api_key, masked_key, model)."""
    doc = await config_col.find_one({"_id": "openai_config"})
    if not doc:
        return None, None, None
    api_key = doc.get("apiKey")
    if not isinstance(api_key, str) or not api_key.strip():
        return None, None, doc.get("model") or None
    key = api_key.strip()
    return key, _mask_api_key(key), (doc.get("model") or "gpt-4o-mini")


async def _get_general_settings() -> GeneralSettings:
    doc = await config_col.find_one({"_id": "general_settings"})
    if not doc:
        return GeneralSettings()
    swipe = doc.get("swipe")
    auto_chat = doc.get("auto_chat")
    return GeneralSettings(
        swipe=SwipeSettings(**(swipe if isinstance(swipe, dict) else {})),
        auto_chat=AutoChatSettings(**(auto_chat if isinstance(auto_chat, dict) else {})),
    )


def _build_okcupid_client_from_account(doc: dict) -> OkCupidClient:
    # Reuse the shared client builder from the examples so behavior is
    # consistent between CLI scripts and the API server. That helper already
    # prefers the internal API host (e.g. https://e2p-okapi.api.okcupid.com)
    # and merges sample.json defaults with account-specific auth & proxy.
    return _build_client_from_db_account(doc)


@app.get("/api/accounts", response_model=List[AccountOut])
async def list_accounts() -> List[AccountOut]:
    docs = accounts_col.find()
    results: List[AccountOut] = []
    async for doc in docs:
        results.append(_account_from_doc(doc))
    return results


@app.post("/api/accounts", response_model=AccountOut)
async def create_account_api(body: AccountCreate) -> AccountOut:
    now = datetime.utcnow().isoformat()
    proxy_doc = body.proxy.model_dump(exclude_none=True)
    doc = {
        "name": body.name,
        "proxy": proxy_doc,
        "status": "paused",
        "lastActive": None,
        "tokenExpiry": None,
        "sessionState": "login_required",
        "loginRequired": True,
        "error": None,
        "actionsToday": 0,
        "successRate": 0.0,
        "failureRate": 0.0,
        "swipeLikes": 0,
        "swipePasses": 0,
        "swipeErrors": 0,
        "createdAt": now,
        "auth": {
            "token": body.authentication_token,
            "cookie_string": body.cookie,
        },
    }
    res = await accounts_col.insert_one(doc)
    doc["_id"] = res.inserted_id
    return _account_from_doc(doc)


@app.get("/api/accounts/{account_id}")
async def get_account_api(account_id: str):
    doc = await accounts_col.find_one({"_id": ObjectId(account_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Account not found")
    out = _account_from_doc(doc)
    auth = doc.get("auth") or {}
    # Token is stored directly; cookie_string may be stored either as a top-level
    # field in auth or nested under auth.cookies.cookie_string (for older docs).
    cookie_string = auth.get("cookie_string") or (
        (auth.get("cookies") or {}).get("cookie_string")
        if isinstance(auth.get("cookies"), dict)
        else None
    )
    proxy_data = doc.get("proxy")
    proxy_obj = None
    if isinstance(proxy_data, dict):
        proxy_obj = {
            "type": proxy_data.get("type"),
            "host": proxy_data.get("host"),
            "port": proxy_data.get("port"),
            "username": proxy_data.get("username"),
            "password": proxy_data.get("password"),
        }
    return {
        "id": out.id,
        "name": out.name,
        "proxy": proxy_obj,
        "hasAuth": bool(auth.get("token")),
        "authenticationToken": auth.get("token") or "",
        "cookie": cookie_string or "",
    }
    

@app.put("/api/accounts/{account_id}", response_model=AccountOut)
async def update_account_api(account_id: str, body: AccountUpdate) -> AccountOut:
    doc = await accounts_col.find_one({"_id": ObjectId(account_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Account not found")
    updates: Dict[str, object] = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.authentication_token is not None or body.cookie is not None:
        auth = dict(doc.get("auth") or {})
        if body.authentication_token is not None and body.authentication_token.strip():
            auth["token"] = body.authentication_token.strip()
        if body.cookie is not None and body.cookie.strip():
            auth["cookie_string"] = body.cookie.strip()
        updates["auth"] = auth
    if body.proxy is not None:
        updates["proxy"] = body.proxy.model_dump(exclude_none=True) if body.proxy else None
    if not updates:
        return _account_from_doc(doc)
    await accounts_col.update_one(
        {"_id": ObjectId(account_id)},
        {"$set": updates},
    )
    doc = await accounts_col.find_one({"_id": ObjectId(account_id)})
    return _account_from_doc(doc)


@app.delete("/api/accounts/{account_id}", status_code=204)
async def delete_account_api(account_id: str) -> None:
    result = await accounts_col.delete_one({"_id": ObjectId(account_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")


@app.get("/api/jobs", response_model=List[JobOut])
async def list_jobs() -> List[JobOut]:
    docs = jobs_col.find().sort("createdAt", -1)
    results: List[JobOut] = []
    async for doc in docs:
        results.append(
            JobOut(
                id=str(doc["_id"]),
                accountId=doc.get("accountId"),
                type=doc.get("type", ""),
                status=doc.get("status", "pending"),
                attempts=doc.get("attempts", 0),
                createdAt=doc.get("createdAt", ""),
            )
        )
    return results


@app.get("/api/logs", response_model=List[LogOut])
async def list_logs() -> List[LogOut]:
    docs = logs_col.find().sort("timestamp", -1).limit(200)
    results: List[LogOut] = []
    async for doc in docs:
        results.append(
            LogOut(
                id=str(doc["_id"]),
                accountId=str(doc.get("accountId", "")),
                timestamp=doc.get("timestamp", ""),
                level=doc.get("level", "info"),
                source=doc.get("source", "action"),
                message=doc.get("message", ""),
            )
        )
    return results


@app.get("/api/rate-config", response_model=RateConfig)
async def get_rate_config() -> RateConfig:
    return await _get_rate_config()


@app.post("/api/rate-config", response_model=RateConfig)
async def update_rate_config_api(body: RateConfig) -> RateConfig:
    await config_col.update_one(
        {"_id": "rate_config"},
        {"$set": body.model_dump()},
        upsert=True,
    )
    return body


@app.get("/api/openai-config", response_model=OpenAIConfigOut)
async def get_openai_config() -> OpenAIConfigOut:
    _, masked, model = await _get_openai_config_doc()
    return OpenAIConfigOut(
        hasKey=masked is not None,
        maskedKey=masked,
        model=model,
    )


@app.post("/api/openai-config", response_model=OpenAIConfigOut)
async def update_openai_config_api(body: OpenAIConfigIn) -> OpenAIConfigOut:
    key = (body.apiKey or "").strip()
    model = (body.model or "").strip() or None
    if key:
        # Setting or rotating key: save key and set model (default if not provided)
        update: Dict[str, object] = {"apiKey": key}
        update["model"] = model or "gpt-4o-mini"
        await config_col.update_one(
            {"_id": "openai_config"},
            {"$set": update},
            upsert=True,
        )
    elif model is not None:
        # Update model only
        doc = await config_col.find_one({"_id": "openai_config"})
        if not doc or not doc.get("apiKey"):
            raise HTTPException(
                status_code=400,
                detail="Set an API key first before updating the model.",
            )
        await config_col.update_one(
            {"_id": "openai_config"},
            {"$set": {"model": model}},
            upsert=True,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide apiKey and/or model to update.",
        )
    _, masked, out_model = await _get_openai_config_doc()
    return OpenAIConfigOut(
        hasKey=masked is not None,
        maskedKey=masked,
        model=out_model,
    )


@app.get("/api/general-settings", response_model=GeneralSettings)
async def get_general_settings() -> GeneralSettings:
    return await _get_general_settings()


@app.get("/api/effective-config")
async def get_effective_config():
    """Return config used by backend and example scripts. No secrets (no tokens, keys, cookies)."""
    out: Dict = {
        "sample_json_loaded": False,
        "api": {},
        "graphql": {},
        "auth_header_keys": [],
        "general_settings": {},
        "openai": {"hasKey": False, "model": None},
        "accounts_count": 0,
    }
    try:
        api_cfg = get_api()
        out["api"] = {k: v for k, v in (api_cfg or {}).items() if isinstance(v, str)}
        gql_cfg = get_graphql_settings()
        out["graphql"] = {k: v for k, v in (gql_cfg or {}).items() if isinstance(v, str)}
        auth_cfg = get_auth()
        headers = auth_cfg.get("headers") or {}
        if isinstance(headers, dict):
            out["auth_header_keys"] = list(headers.keys())
        out["sample_json_loaded"] = True
    except Exception:
        pass
    general = await _get_general_settings()
    out["general_settings"] = {
        "swipe": general.swipe.model_dump(),
        "auto_chat": general.auto_chat.model_dump(),
    }
    _, _, openai_model = await _get_openai_config_doc()
    openai_has = await _get_openai_api_key()
    out["openai"] = {"hasKey": bool(openai_has), "model": openai_model}
    out["accounts_count"] = await accounts_col.count_documents({})
    return out


@app.post("/api/general-settings", response_model=GeneralSettings)
async def update_general_settings_api(body: GeneralSettings) -> GeneralSettings:
    await config_col.update_one(
        {"_id": "general_settings"},
        {
            "$set": {
                "swipe": body.swipe.model_dump(),
                "auto_chat": body.auto_chat.model_dump(),
            }
        },
        upsert=True,
    )
    return body


@app.post("/api/automation/ai-auto-chat")
async def start_ai_auto_chat(body: AiChatRequest):
    if not body.accountIds:
        return {"status": "no_accounts"}

    account_id = body.accountIds[0]
    doc = await accounts_col.find_one({"_id": ObjectId(account_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Account not found")

    client = _build_okcupid_client_from_account(doc)
    general_doc = await config_col.find_one({"_id": "general_settings"})
    openai_doc = await config_col.find_one({"_id": "openai_config"})

    auto_cfg, openai_cfg = get_merged_auto_chat_config(general_doc, openai_doc)
    try:
        results = run_auto_chat_once_for_client(client, auto_cfg, openai_cfg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    now = datetime.utcnow().isoformat()
    job_doc = {
        "accountId": account_id,
        "type": "Start AI Auto Chat",
        "status": "completed",
        "attempts": 1,
        "createdAt": now,
    }
    await jobs_col.insert_one(job_doc)
    await accounts_col.update_one(
        {"_id": ObjectId(account_id)},
        {"$set": {"lastActive": now}},
    )
    log_doc = {
        "accountId": account_id,
        "timestamp": now,
        "level": "info",
        "source": "action",
        "message": f"AI auto chat sent messages: {results}",
    }
    result = await logs_col.insert_one(log_doc)
    log_doc["_id"] = result.inserted_id
    await _broadcast_log(log_doc)

    return {"status": "ok", "results": results}


@app.post("/api/automation/auto-swipe")
async def auto_swipe(body: AutoSwipeRequest):
    if not body.accountIds or body.count <= 0:
        return {"status": "no_accounts"}

    account_id = body.accountIds[0]
    doc = await accounts_col.find_one({"_id": ObjectId(account_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Account not found")

    client = _build_okcupid_client_from_account(doc)
    general = await _get_general_settings()
    sw = general.swipe

    # Directions and like/pass split: mirror examples/auto_swipe_example.py
    swipe_cfg = get_swipe_settings()
    gql_cfg = get_graphql_settings()

    directions_env = os.getenv("SWIPE_DIRECTIONS")
    if directions_env:
        directions = [d.strip() for d in directions_env.split(",") if d.strip()]
    else:
        cfg_dirs = sw.directions or swipe_cfg.get("directions")
        if isinstance(cfg_dirs, list) and cfg_dirs:
            directions = [str(d).strip() for d in cfg_dirs if str(d).strip()]
        else:
            directions = [
                os.getenv("SWIPE_DIRECTION")
                or swipe_cfg.get("direction", "like")
            ]

    like_pct = sw.like_percentage or swipe_cfg.get("like_percentage")
    max_total = min(body.count, sw.max_swipes) if sw.max_swipes > 0 else body.count
    delay = sw.delay_seconds or float(
        os.getenv("SWIPE_DELAY") or swipe_cfg.get("delay_seconds", 1.5)
    )
    discovery_path = gql_cfg.get("discovery_path") or None
    initial_stacks_path = gql_cfg.get("initial_stacks_path") or None
    swipe_path = gql_cfg.get("swipe_path") or None

    totals: Dict[str, dict] = {}
    error_logs: list[dict] = []
    for direction in directions:
        dir_max = max_total
        if (
            isinstance(like_pct, (int, float))
            and "like" in directions
            and "pass" in directions
            and len(directions) == 2
        ):
            like_count = int(round(max_total * (float(like_pct) / 100.0)))
            like_count = max(0, min(max_total, like_count))
            pass_count = max_total - like_count
            if direction == "like":
                dir_max = like_count
            elif direction == "pass":
                dir_max = pass_count

        summary = ok_swipe.auto_swipe(
            client,
            direction=direction,
            max_swipes=dir_max,
            delay_seconds=delay,
            discovery_graphql_path=discovery_path,
            initial_stacks_path=initial_stacks_path,
            swipe_graphql_path=swipe_path,
        )
        totals[direction] = summary

        # Collect error details for dedicated log entries so they are visible in the UI.
        results = summary.get("results") or []
        if isinstance(results, list):
            for item in results:
                if not isinstance(item, dict):
                    continue
                err = item.get("error")
                if not err:
                    continue
                error_logs.append(
                    {
                        "direction": direction,
                        "user_id": item.get("user_id"),
                        "error": str(err),
                    }
                )

    # Aggregate swipe stats for this run
    like_swiped = int(totals.get("like", {}).get("swiped", 0))
    pass_swiped = int(totals.get("pass", {}).get("swiped", 0))
    error_total = sum(int(s.get("errors", 0)) for s in totals.values())

    if like_swiped or pass_swiped or error_total:
        await accounts_col.update_one(
            {"_id": ObjectId(account_id)},
            {
                "$inc": {
                    "swipeLikes": like_swiped,
                    "swipePasses": pass_swiped,
                    "swipeErrors": error_total,
                }
            },
        )

    now = datetime.utcnow().isoformat()
    job_doc = {
        "accountId": account_id,
        "type": f"Auto swipe {body.count}",
        "status": "completed",
        "attempts": 1,
        "createdAt": now,
    }
    await jobs_col.insert_one(job_doc)
    await accounts_col.update_one(
        {"_id": ObjectId(account_id)},
        {"$set": {"lastActive": now}},
    )
    log_doc = {
        "accountId": account_id,
        "timestamp": now,
        "level": "info",
        "source": "action",
        "message": f"Auto swipe summary: {totals}",
    }
    result = await logs_col.insert_one(log_doc)
    log_doc["_id"] = result.inserted_id
    await _broadcast_log(log_doc)

    # Detailed error logs for each failed swipe, if any.
    if error_logs:
        error_docs = []
        for entry in error_logs:
            error_docs.append(
                {
                    "accountId": account_id,
                    "timestamp": now,
                    "level": "error",
                    "source": "auto-swipe",
                    "message": (
                        f"Auto swipe error ({entry.get('direction')} "
                        f"user {entry.get('user_id')}): {entry.get('error')}"
                    ),
                }
            )
        result = await logs_col.insert_many(error_docs)
        for i, d in enumerate(error_docs):
            d["_id"] = result.inserted_ids[i]
            await _broadcast_log(d)

    return {"status": "ok", "summary": totals}


@app.get("/api/profiles/{account_id}")
async def get_profile_info_api(account_id: str):
    doc = await accounts_col.find_one({"_id": ObjectId(account_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        client = _build_okcupid_client_from_account(doc)
        summary = get_profile_summary(client)
        return {
            "accountId": account_id,
            **summary,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Failed to load profile from OkCupid.",
                "error": str(e),
            },
            headers=_CORS_HEADERS,
        )


@app.post("/api/profile/update-bio")
async def update_profile_bio(body: UpdateBioRequest):
    doc = await accounts_col.find_one({"_id": ObjectId(body.accountId)})
    if not doc:
        raise HTTPException(status_code=404, detail="Account not found")
    client = _build_okcupid_client_from_account(doc)
    updated = update_bio_for_client(client, body.bio.strip())
    now = datetime.utcnow().isoformat()
    log_doc = {
        "accountId": body.accountId,
        "timestamp": now,
        "level": "info",
        "source": "action",
        "message": "Updated bio via API.",
    }
    result = await logs_col.insert_one(log_doc)
    log_doc["_id"] = result.inserted_id
    await _broadcast_log(log_doc)
    await _broadcast_profile_update(body.accountId)
    return {
        "status": "ok",
        "bio": updated.get("rawContent") or updated.get("processedContent"),
    }


@app.post("/api/profile/update-realname")
async def update_profile_realname(body: UpdateRealnameRequest):
    doc = await accounts_col.find_one({"_id": ObjectId(body.accountId)})
    if not doc:
        raise HTTPException(status_code=404, detail="Account not found")
    client = _build_okcupid_client_from_account(doc)
    result = update_realname_for_client(client, body.realname.strip())
    now = datetime.utcnow().isoformat()
    log_doc = {
        "accountId": body.accountId,
        "timestamp": now,
        "level": "info",
        "source": "action",
        "message": f"Updated realname via API: {body.realname.strip()}",
    }
    insert_result = await logs_col.insert_one(log_doc)
    log_doc["_id"] = insert_result.inserted_id
    await _broadcast_log(log_doc)
    await _broadcast_profile_update(body.accountId)
    return {"status": "ok", "result": result}

