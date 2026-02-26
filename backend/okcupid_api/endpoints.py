"""
Central registry of API endpoint paths and HTTP methods.
Update this file as you discover real endpoints from okcupid.com Network tab.
"""

from okcupid_api.config import ENDPOINTS

# Format: (method, path_template_or_path)
# Paths are relative to ENDPOINTS.base_url unless they start with http.

PROFILE = [
    ("GET", ENDPOINTS.profile_view),           # single
    ("POST", ENDPOINTS.profile_bulk),          # bulk (or GET with query params)
]

BIO = [
    ("PATCH", ENDPOINTS.bio_edit),             # single (or PUT)
    ("POST", ENDPOINTS.bio_bulk),              # bulk
]

SWIPE = [
    ("POST", ENDPOINTS.swipe),                 # single like/pass
    ("POST", ENDPOINTS.swipe_bulk),            # bulk
]

AI_CHAT = [
    ("POST", ENDPOINTS.ai_chat),               # single message/thread
    ("POST", ENDPOINTS.ai_chat_bulk),          # bulk
]
