# OkCupid Web API Client (Reverse-Engineered)

Python skeleton for interacting with OkCupid’s web API. Supports:

- **Profile** – view single profile, bulk fetch
- **Bio** – edit bio (single / bulk)
- **Swipe** – like/pass (single / bulk), **auto-swipe** (discovery feed)
- **AI Chat** – send messages (single / bulk)

Endpoints and payloads are placeholders; they must be filled in after reverse engineering okcupid.com.

**OkCupid uses GraphQL:** all API requests go to `https://e2p-okapi.api.okcupid.com/graphql/`. Set `api.api_host` in `sample.json` to that URL (no path) so the client sends requests there. Each action (profile, swipe, discovery, etc.) is a different GraphQL query or mutation; copy the `query`/`mutation` and variable names from DevTools into `okcupid_api/graphql_operations.py`.

### Data needed for auto-swipe

1. **Discovery feed endpoint** – URL (path) of the request that returns the list of profiles to swipe on (e.g. DoubleTake). → `config.py` → `discovery_feed`.
2. **Response shape** – which key holds the array of profiles? (e.g. `data`, `results`, `profiles`). → `swipe.py` → `get_candidates()`.
3. **User ID field** – field name for user id in each profile (e.g. `userid`, `user_id`, `id`). → `swipe.py` → `USER_ID_KEYS`.
4. **Swipe endpoint** – URL and body for a single like/pass. → `config.py` → `swipe`; `swipe.py` → `swipe()` body keys and `direction` values (`"like"` / `"pass"`).

---

## Reverse engineering the API

1. **Open OkCupid in Chrome**
   - Log in to your account.

2. **Open DevTools → Network**
   - F12 → Network tab.
   - Filter by **Fetch/XHR** (or “XHR”) to see API calls.

3. **Trigger each action and capture**
   - **Profile**: Open a user profile → note the request URL, method, and response.
   - **Edit bio**: Change your bio and save → capture the request (PATCH/PUT, body, path).
   - **Swipe**: Like or pass on a profile → capture the request (often POST to something like `/like` or `/vote`).
   - **AI chat**: Send an AI chat message → capture the request (path, body, headers).

4. **Record for each request**
   - **URL** (path and query).
   - **Method** (GET, POST, PATCH, etc.).
   - **Request headers** (especially `Authorization`, `X-CSRF-*`, `Content-Type`).
   - **Request body** (JSON keys and sample values).
   - **Response** (status and JSON shape).

5. **Update this codebase**
   - `okcupid_api/config.py` – set `API_BASE` / `API_HOST` and the `Endpoints` paths.
   - `okcupid_api/endpoints.py` – adjust if you use a different structure.
   - `okcupid_api/profile.py`, `bio.py`, `swipe.py`, `ai_chat.py` – use the real paths, body keys, and response parsing.

---

## Setup

```bash
cd E:\Project\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Credentials:** copy `sample.json.example` to `sample.json`, fill in your values (see below). `sample.json` is gitignored so it is never committed.

---

## sample.json – essential data

Put all sensitive and environment-specific data in `sample.json` (root of `backend/`). Required shape:

| Section | Field | Description |
|--------|--------|-------------|
| **auth** | **cookies** | `{"session": "...", "auth_token": "..."}` – copy cookie names/values from DevTools → Application → Cookies after logging in. |
| **auth** | **token** | Optional. Bearer or API key string if the API uses it (else `null`). |
| **auth** | **headers** | Optional. Extra headers, e.g. `{"X-CSRF-Token": "..."}` if required by the API. |
| **api** | **base_url** | Base URL, e.g. `"https://www.okcupid.com"`. |
| **api** | **api_host** | Optional. Separate API host if different from base (else `""`). |
| **api** | **user_agent** | Optional. Browser User-Agent string from DevTools. |
| **test_ids** | **profile_user_id** | Optional. A real profile ID for testing profile fetch. |
| **test_ids** | **target_user_id** | Optional. A profile ID for testing swipe. |
| **test_ids** | **thread_id** | Optional. An AI chat thread ID for testing AI chat. |
| **openai** | **api_key** | Optional. OpenAI API key for auto chat runner (alternative to `OPENAI_API_KEY` env var). |
| **openai** | **model** | Optional. OpenAI model name (default `gpt-4o-mini`). |
| **auto_chat** | **funnel** | Optional. Your Snap username (alternative to `AI_CHAT_FUNNEL` env var). |

Example (fill in real values after reverse engineering):

```json
{
  "auth": {
    "cookies": {
      "session": "YOUR_SESSION_COOKIE_VALUE",
      "auth_token": "YOUR_AUTH_TOKEN_IF_ANY"
    },
    "token": null,
    "headers": {
      "X-CSRF-Token": "IF_REQUIRED_FROM_DEVTOOLS"
    }
  },
  "api": {
    "base_url": "https://www.okcupid.com",
    "api_host": "",
    "user_agent": "Mozilla/5.0 (...)"
  },
  "test_ids": {
    "profile_user_id": "SAMPLE_PROFILE_UID",
    "target_user_id": "SAMPLE_TARGET_UID_FOR_SWIPE",
    "thread_id": "SAMPLE_AI_CHAT_THREAD_ID"
  }
}
```

Use `OkCupidClient.from_sample()` to build the client from this file.

---

## Usage (after filling endpoints)

```python
from okcupid_api import OkCupidClient
from okcupid_api import profile, bio, swipe, ai_chat

# From sample.json (recommended)
client = OkCupidClient.from_sample()

# Or manually
# client = OkCupidClient(base_url="...", cookies={"session": "..."})

# Single profile
p = profile.get_profile(client, "USER_ID")

# Bulk profiles
profiles = profile.get_profiles_bulk(client, ["id1", "id2"])

# Edit bio (single)
bio.edit_bio(client, "My new bio text.")

# Swipe (single)
swipe.swipe(client, "TARGET_USER_ID", direction="like")

# AI chat (single)
ai_chat.ai_chat(client, "Hello!", thread_id="THREAD_ID")
```

---

## Project layout

```
backend/
├── okcupid_api/
│   ├── __init__.py      # OkCupidClient export
│   ├── client.py        # HTTP session, request helpers
│   ├── config.py        # Base URL and endpoint paths (edit after RE)
│   ├── endpoints.py     # Method + path registry
│   ├── exceptions.py    # OkCupidAPIError, OkCupidAuthError, etc.
│   ├── profile.py       # get_profile, get_profiles_bulk
│   ├── bio.py           # edit_bio, edit_bio_bulk
│   ├── swipe.py         # swipe, swipe_bulk
│   └── ai_chat.py       # ai_chat, ai_chat_bulk
├── requirements.txt
├── .env.example
└── README.md
```

---

## Legal / ToS

Use of this client may be restricted by OkCupid’s Terms of Service. This is for educational and reverse-engineering reference only. Use responsibly and at your own risk.
