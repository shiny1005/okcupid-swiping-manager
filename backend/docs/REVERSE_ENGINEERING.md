# Reverse engineering checklist – OkCupid Web API

Use this while capturing requests in Chrome DevTools (Network → XHR/fetch).

## 1. Profile

| Action | What to capture |
|--------|------------------|
| Open a user profile (click on a card or search result) | URL, method (GET?), query params, response JSON shape |
| (If exists) “Load more” or batch profile fetch | URL, method, body (e.g. `user_ids`), response |

**Update in code:** `config.py` → `profile_view`, `profile_bulk`; `profile.py` → path format and response parsing.

---

## 2. Edit bio

| Action | What to capture |
|--------|------------------|
| Change “About me” / bio and click Save | URL, method (PATCH/PUT?), request body keys (`bio`, `about_me`, etc.), response |

**Update in code:** `config.py` → `bio_edit`, `bio_bulk`; `bio.py` → body keys and response handling.

---

## 3. Swipe (like / pass)

| Action | What to capture |
|--------|------------------|
| Click Like (or Yes) on a profile | URL, method (usually POST), body (e.g. `userid`, `vote`, `direction`), response |
| Click Pass (or No) | Same; note how “pass” is encoded (e.g. `direction: "pass"` or `vote: 0`) |
| (If exists) Batch like/pass | URL and body format for multiple targets |

**Update in code:** `config.py` → `swipe`, `swipe_bulk`; `swipe.py` → body keys and `direction` values.

### Discovery feed (for auto-swipe)

Auto-swipe needs a **source of profiles** to swipe on (e.g. DoubleTake / discovery feed).

| Action | What to capture |
|--------|------------------|
| Open the swipe/stack screen (DoubleTake or main discovery) | Request that returns the **list of profiles** (cards). |
| Note | Full URL (path + query), method (GET/POST), and **response JSON shape**. |

You need: (1) **Endpoint URL** (path) → `config.py` → `discovery_feed`. (2) **Response shape** – where is the list? (e.g. `data.data`, `data.results`, `data.profiles`) → update `get_candidates()` in `swipe.py`. (3) **User ID field** in each item (e.g. `userid`, `user_id`, `id`) → set `USER_ID_KEYS` in `swipe.py` if different.

---

## 4. AI chat

| Action | What to capture |
|--------|------------------|
| Open AI chat / send first message | URL, method, body (e.g. `message`, `thread_id`, `conversation_id`), response |
| Send another message in same thread | Same; note how thread/conversation is identified |
| (If exists) Batch or multi-thread | URL and body for multiple messages/threads |

**Update in code:** `config.py` → `ai_chat`, `ai_chat_bulk`; `ai_chat.py` → body keys and response parsing.

---

## 5. Auth and headers

For each captured request, note:

- **Cookies** – which cookie names are sent (e.g. `session`, `auth`, `okcupid_*`). Set these in `.env` as `OKCUPID_COOKIE_<name>=<value>`.
- **Headers** – `Authorization`, `X-CSRF-Token`, `X-Requested-With`, or any custom header. Add to `OkCupidClient(headers={...})` or in `client.py` defaults.
- **Origin / Referer** – already set in client; change if API uses a different origin.

---

## 6. Base URL

- If all calls go to `https://www.okcupid.com/...`, set `OKCUPID_API_BASE=https://www.okcupid.com`.
- If there is a separate API host (e.g. `https://api.okcupid.com`), set `OKCUPID_API_HOST` and use that in `config.py` for `base_url`.

After each discovery, update `okcupid_api/config.py` and the corresponding module (profile, bio, swipe, ai_chat), then run `examples/usage.py` or your own script to verify.
