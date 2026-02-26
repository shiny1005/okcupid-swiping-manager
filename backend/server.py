import os
from datetime import datetime
from typing import List, Optional, Dict

from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from okcupid_api import OkCupidClient
from okcupid_api import profile as ok_profile
from okcupid_api import swipe as ok_swipe
from okcupid_api.ai_auto_chat import AutoChatConfig, auto_chat_once


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://mongodb1234:iamanetstar@cluster0.svpkyqh.mongodb.net/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "okcupid_automation")

mongo_client = AsyncIOMotorClient(MONGODB_URI)
db = mongo_client[MONGODB_DB_NAME]
accounts_col = db["accounts"]
jobs_col = db["jobs"]
logs_col = db["logs"]
config_col = db["config"]


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
    actionsToday: int = 0
    successRate: float = 0.0
    failureRate: float = 0.0


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


app = FastAPI(title="OkCupid Automation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _account_from_doc(doc: dict) -> AccountOut:
    proxy_display: Optional[str] = None
    proxy_data = doc.get("proxy")
    if isinstance(proxy_data, dict):
        host = proxy_data.get("host")
        port = proxy_data.get("port")
        ptype = proxy_data.get("type") or "socks5"
        if host and port:
            proxy_display = f"{ptype}://{host}:{port}"

    return AccountOut(
        id=str(doc["_id"]),
        name=doc.get("name", ""),
        proxy=proxy_display,
        status=doc.get("status", "paused"),
        lastActive=doc.get("lastActive"),
        tokenExpiry=doc.get("tokenExpiry"),
        sessionState=doc.get("sessionState", "login_required"),
        loginRequired=doc.get("loginRequired", True),
        error=doc.get("error"),
        actionsToday=doc.get("actionsToday", 0),
        successRate=doc.get("successRate", 0.0),
        failureRate=doc.get("failureRate", 0.0),
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
    auth = doc.get("auth", {})
    # Token is stored directly; cookie_string may be stored either as a top-level
    # field in auth or nested under auth.cookies.cookie_string (for older docs).
    cookie_string = auth.get("cookie_string") or (
        (auth.get("cookies") or {}).get("cookie_string")
        if isinstance(auth.get("cookies"), dict)
        else None
    )
    token = auth.get("token")
    headers = {}
    if token:
        headers["Authorization"] = (
            token if token.startswith("Bearer ") else f"Bearer {token}"
        )
    base_url = os.getenv("OKCUPID_API_BASE")
    proxies: Optional[Dict[str, str]] = None
    proxy_cfg = doc.get("proxy") or {}
    if isinstance(proxy_cfg, dict):
        host = (proxy_cfg.get("host") or "").strip()
        port = proxy_cfg.get("port")
        if host and port:
            ptype = (proxy_cfg.get("type") or "socks5").strip().lower() or "socks5"
            user = (proxy_cfg.get("username") or "").strip()
            password = (proxy_cfg.get("password") or "").strip()
            auth_part = ""
            if user and password:
                auth_part = f"{user}:{password}@"
            url = f"{ptype}://{auth_part}{host}:{port}"
            proxies = {"http": url, "https": url}

    client = OkCupidClient(
        base_url=base_url,
        cookies=None,
        headers=headers or None,
        proxies=proxies,
    )
    if cookie_string:
        # Mirror browser cookie header so OkCupid recognizes the session.
        client.session.headers["Cookie"] = cookie_string
    return client


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
    proxy_data = doc.get("proxy")
    proxy_obj = None
    if isinstance(proxy_data, dict):
        proxy_obj = {
            "type": proxy_data.get("type"),
            "host": proxy_data.get("host"),
            "port": proxy_data.get("port"),
            "username": proxy_data.get("username"),
        }
    return {
        "id": out.id,
        "name": out.name,
        "proxy": proxy_obj,
        "hasAuth": bool(doc.get("auth", {}).get("token")),
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

    # For now, just run auto-chat once for the first account using stored auth.
    account_id = body.accountIds[0]
    doc = await accounts_col.find_one({"_id": ObjectId(account_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Account not found")

    client = _build_okcupid_client_from_account(doc)
    general = await _get_general_settings()
    ac = general.auto_chat
    funnel = (ac.funnel or "").strip() or os.getenv("AI_CHAT_FUNNEL", "")
    if not funnel:
        raise HTTPException(
            status_code=500,
            detail="Auto chat funnel is not set. Set it in General settings (Auto chat) or AI_CHAT_FUNNEL env.",
        )

    openai_key, _, openai_model = await _get_openai_config_doc()
    config = AutoChatConfig(
        funnel=funnel,
        openai_api_key=openai_key,
        cta_min_msgs=ac.cta_min_msgs,
        cta_max_msgs=ac.cta_max_msgs,
        delay_chat_part_min=ac.delay_chat_part_min,
        delay_chat_part_max=ac.delay_chat_part_max,
        model=openai_model or "gpt-4o-mini",
    )
    results = auto_chat_once(client, config=config)

    now = datetime.utcnow().isoformat()
    job_doc = {
        "accountId": account_id,
        "type": "Start AI Auto Chat",
        "status": "completed",
        "attempts": 1,
        "createdAt": now,
    }
    await jobs_col.insert_one(job_doc)

    await logs_col.insert_one(
        {
            "accountId": account_id,
            "timestamp": now,
            "level": "info",
            "source": "action",
            "message": f"AI auto chat sent messages: {results}",
        }
    )

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
    direction = "like"
    if sw.directions:
        direction = sw.directions[0] if sw.directions[0] in ("like", "pass") else "like"
    max_swipes = min(body.count, sw.max_swipes) if sw.max_swipes > 0 else body.count
    summary = ok_swipe.auto_swipe(
        client,
        direction=direction,
        max_swipes=max_swipes,
        delay_seconds=sw.delay_seconds,
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

    await logs_col.insert_one(
        {
            "accountId": account_id,
            "timestamp": now,
            "level": "info",
            "source": "action",
            "message": f"Auto swipe summary: {summary}",
        }
    )

    return {"status": "ok", "summary": summary}


@app.get("/api/profiles/{account_id}")
async def get_profile_info_api(account_id: str):
    doc = await accounts_col.find_one({"_id": ObjectId(account_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Account not found")

    client = _build_okcupid_client_from_account(doc)
    # For now, use the test profile id from sample or user id equal to account_id.
    # In real usage, you might store the OkCupid user id in the account document.
    target_user_id = os.getenv("OKCUPID_TEST_PROFILE_ID", account_id)
    data = ok_profile.get_profile(client, target_user_id)
    return {"accountId": account_id, "profile": data}

