from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from openai import OpenAI

from okcupid_api.client import OkCupidClient
from okcupid_api.conversations import (
    Me,
    get_conversation_thread,
    get_conversations_main,
    get_me,
    send_message,
)


@dataclass
class AutoChatConfig:
    funnel: str
    openai_api_key: Optional[str] = None
    cta_min_msgs: int = 2
    cta_max_msgs: int = 4
    delay_chat_part_min: float = 1.0
    delay_chat_part_max: float = 3.0
    model: str = "gpt-4o-mini"


SNAP_KW = [
    "snap",
    "snapchat",
    "sc",
    "whats ur snap",
    "what your snap",
    "whats your snap",
    "your snap",
    "ur snap",
    "got snap",
    "have snap",
    "on snap",
    "u on snap",
    "do u have snap",
]

CONTACT_KW = [
    "number",
    "phone",
    "ig",
    "instagram",
    "telegram",
    "whatsapp",
    "contact",
    "reach you",
    "text you",
    "socials",
    "discord",
    "facebook",
    "twitter",
    "tiktok",
    "off this app",
    "outside this app",
    "lets text",
    "wanna text",
]

ADDED_KW = [
    "i added",
    "added you",
    "added u",
    "just added",
    "sent u a request",
    "sent you a request",
    "added ur snap",
    "added your snap",
    "i add u",
    "added!",
    "texted u on snap",
    "texted you on snap",
    "messaged u on snap",
    "snapped u",
    "snapped you",
    "hit u up on snap",
    "texted u there",
    "messaged u there",
    "i texted u",
    "i texted you",
    "i messaged u",
]

NO_SNAP_KW = [
    "dont have snap",
    "don't have snap",
    "i dont use snap",
    "dont use snapchat",
    "no snap",
    "dont got snap",
    "i dont have sc",
    "deleted snap",
    "not on snap",
    "dont have snapchat",
    "never had snap",
]

REFUSED_KW = [
    "no thanks",
    "nah im good",
    "not interested",
    "ill pass",
    "nope",
    "no way",
    "pass",
    "rather not",
]

BOT_DOUBT_KW = [
    "are you real",
    "r u real",
    "are u a bot",
    "u a bot",
    "youre a bot",
    "fake",
    "scam",
    "catfish",
]

IG_REQUEST_KW = [
    "do u have ig",
    "whats ur ig",
    "whats your ig",
    "can we do ig",
    "give me ur ig",
    "u got ig",
    "u have insta",
    "how about ig",
    "ig instead",
    "insta instead",
]


CTA_STARTERS = [
    "oh btw add my snap {f}",
    "hmu on snap tho {f}",
    "add my snap {f}",
    "lets just talk on snap {f}",
    "txt me on snap {f}",
    "add me on snap {f}",
    "snap me at {f}",
    "but hmu on snap {f}",
    "my snap is {f} add me",
]

CTA_REASONS = [
    "i barely even check this app tbh",
    "im prob gonna delete this soon",
    "this app is kinda dead for me",
    "i never get notifs from this lol",
    "im lowkey never on here",
    "rather just talk on snap its easier",
    "i check snap way more than this",
    "snap is just easier for me",
]

WORD_VARIANTS_SNAP = ["snap", "ѕnаp", "ѕոար", "snapchat", "snpchat"]


BASE_PERSONA_PROMPT = """you're a bubbly girl in her early 20s on a dating app texting a guy u matched with.

THEIR NAME: {match_name}
CRITICAL NAME RULES:
- if name says "(not available)" or is empty -> NEVER use any name at all
- if a real name is provided -> you CAN use it occasionally (1 in 4 messages max)
- NEVER write [name] or [their name] or any brackets

how u text:
- all lowercase always
- short replies but enthusiastic
- use abbreviations: u, ur, r, rn, w, sm, fs, imo, ngl, tbh, lowkey, fr, lol, haha, lmfao, wyd, wbu, kinda, tho, rlly, ik, idk, nah, yea, bet, prtty, abt
- use "!!!!" for excitement
- use "omg" a lot
- use ".." for trailing off (NEVER "...")
- almost never use periods or commas
- NEVER use any emoji or emoticon
- never use asterisks
- can use "hehe" and "awww" and "ooo"

CRITICAL - how to reply:
- ALWAYS read what they ACTUALLY wrote and reply DIRECTLY to it
- if they asked a question -> ANSWER IT only; do NOT ask your own questions or answer questions they didn't ask
- NEVER dodge a question
- ONE reply = respond to what they said in one short message; do NOT write multiple questions and then answer them yourself
- if they ask what you study -> psychology, nursing, communications, marketing, interior design, business
- if they ask what you do -> barista, retail, nanny, freelance, server
- if they ask your age -> 19 or 20 or 21
- if they ask your name -> be playful "omg dont wanna say yet lol" or give a name
- if they ask where you live -> from around the area, keep vague
- if they compliment -> be flattered "awww thx!!!!"
- if they flirt -> match energy, be playful
- NEVER just reply with "haha" or "lol" alone
- mirror their energy

HANDLING FREAKS/SEXUAL:
- NEVER shut them down. play along indirectly. tease. be coy
- "hmm maybe..", "i mean depends..", "lol wouldnt u like to know"

NEVER: mention being a bot/AI, share social media, use emoji, use proper grammar, dodge questions, use [brackets]
"""


def _tone_for_count(our_count: int) -> str:
    if our_count <= 0:
        return "TONE: friendly but brief. 2-8 words max. slightly playful."
    if our_count == 1:
        return "TONE: warming up. interested. 4-12 words max. bubbly."
    return 'TONE: fully engaged. flirty, enthusiastic. 5-15 words max. "!!!!" and "omg".'


def _build_openai_client(api_key: Optional[str] = None) -> OpenAI:
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OpenAI API key is required (set OPENAI_API_KEY or sample.json openai.api_key)."
        )
    return OpenAI(api_key=api_key)


def _clean_reply(text: str) -> str:
    # Basic subset of the full cleanReply() described in ai_chat_prompt.txt
    t = text.strip().strip('"').strip("'")
    # collapse whitespace
    t = " ".join(t.split())
    # force lowercase
    t = t.lower()
    if not t:
        return "omg thats cool"
    return t


def _last_messages_sorted(messages: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(messages, key=lambda m: int(m.get("time", 0)))


def _count_ours_and_theirs(messages: List[Dict[str, Any]], me_id: str) -> Tuple[int, int]:
    our_count = sum(1 for m in messages if m.get("senderId") == me_id)
    their_count = sum(1 for m in messages if m.get("senderId") != me_id)
    return our_count, their_count


def _detect_keywords(text: str, keywords: Iterable[str]) -> bool:
    t = text.lower()
    return any(kw in t for kw in keywords)


def _multi_question(text: str) -> bool:
    return text.count("?") >= 2


def _build_chat_history(messages: List[Dict[str, Any]], me: Me, match_name: str) -> List[Dict[str, str]]:
    history: List[Dict[str, str]] = []
    for m in messages[-6:]:
        role = "assistant" if m.get("senderId") == me.id else "user"
        content = m.get("text") or ""
        history.append({"role": role, "content": content})
    system_msg = BASE_PERSONA_PROMPT.format(match_name=match_name or "(not available)")
    return [{"role": "system", "content": system_msg}] + history


def _call_openai_single_reply(
    client: OpenAI,
    history: List[Dict[str, str]],
    tone: str,
    max_tokens: int = 50,
    temperature: float = 0.85,
    model: str = "gpt-4o-mini",
) -> str:
    messages = history + [{"role": "system", "content": tone}]
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    text = resp.choices[0].message.content or ""
    return _clean_reply(text)


def _cta_break_in_parts(
    client: OpenAI,
    history: List[Dict[str, str]],
    funnel: str,
    their_last_message: str,
    model: str,
) -> List[str]:
    system_extra = (
        "you text in SHORT FRAGMENTS. write EXACTLY 3 separate texts:\n"
        "PART 1 - REACT: respond to what he just said (3-10 words). NO snap username here.\n"
        "PART 2 - SNAP: casually mention your snap (4-8 words). must contain username FUNNEL.\n"
        "PART 3 - REASON: give a reason why snap (4-10 words). MANDATORY.\n"
        "FORMAT as PART: lines. Always 3 parts. all lowercase, no emoji.\n"
        "Snap username: {funnel}\n"
        'His last message: "{last}"\n'
        "EXACTLY 3 PART lines."
    ).format(funnel=funnel, last=their_last_message)
    messages = history + [{"role": "system", "content": system_extra}]
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=120,
        temperature=0.85,
    )
    raw = resp.choices[0].message.content or ""
    parts: List[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line.lower().startswith("part"):
            continue
        _, _, rest = line.partition(":")
        if rest:
            parts.append(_clean_reply(rest))
    while len(parts) < 3:
        # simple fallback reasons
        if len(parts) == 1:
            parts.append(random.choice(CTA_STARTERS).format(f=funnel))
        else:
            parts.append(random.choice(CTA_REASONS))
    # ensure funnel present in second part
    if funnel not in parts[1]:
        parts[1] = parts[1] + f" snap me {funnel}"
    return parts[:3]


def decide_and_reply_for_thread(
    ok_client: OkCupidClient,
    *,
    me: Me,
    match_name: str,
    target_id: str,
    config: AutoChatConfig,
    openai_client: Optional[OpenAI] = None,
) -> Optional[List[str]]:
    """
    Process a single thread: decide whether to reply, and if so, send messages.
    Returns list of texts that were sent, or None if nothing sent.
    """
    thread = get_conversation_thread(ok_client, target_id=target_id, is_polled=False)
    messages = _last_messages_sorted(thread.get("messages") or [])
    if not messages:
        return None
    our_count, _their_count = _count_ours_and_theirs(messages, me.id)
    last = messages[-1]
    # double-send guard
    if last.get("senderId") == me.id:
        return None

    their_last_text = last.get("text") or ""
    lower_text = their_last_text.lower()

    if openai_client is None:
        openai_client = _build_openai_client()

    history = _build_chat_history(messages, me, match_name)
    tone = _tone_for_count(our_count)

    # Simplified subset of decision tree:
    # - If they ask for snap / any contact -> CTA break-in (3 parts)
    # - Otherwise normal single reply.
    sent_texts: List[str] = []
    if _detect_keywords(lower_text, SNAP_KW) or _detect_keywords(lower_text, CONTACT_KW):
        parts = _cta_break_in_parts(
            openai_client,
            history,
            config.funnel,
            their_last_text,
            model=config.model,
        )
        for idx, part in enumerate(parts):
            send_message(ok_client, target_id=target_id, text=part)
            sent_texts.append(part)
            if idx < len(parts) - 1:
                delay = random.uniform(
                    config.delay_chat_part_min, config.delay_chat_part_max
                )
                time.sleep(delay)
        return sent_texts

    # Normal single reply
    reply = _call_openai_single_reply(
        openai_client, history, tone, max_tokens=50, model=config.model
    )
    send_message(ok_client, target_id=target_id, text=reply)
    sent_texts.append(reply)
    return sent_texts


def auto_chat_once(
    client: OkCupidClient,
    *,
    config: AutoChatConfig,
) -> List[Tuple[str, List[str]]]:
    """
    Run one pass over all conversations and reply where it's your turn.
    Returns list of (target_id, [messages_sent]).
    """
    me = get_me(client)
    user_data = get_conversations_main(client, userid=me.id, filter_value="ALL")
    conv_root = user_data.get("conversationsAndMatches") or {}
    items: List[Dict[str, Any]] = (conv_root.get("data") or [])[:]

    results: List[Tuple[str, List[str]]] = []
    oa_client = _build_openai_client(config.openai_api_key)

    for item in items:
        correspondent = item.get("correspondent") or {}
        match = correspondent.get("user") or {}
        target_id = match.get("id")
        match_name = match.get("displayname") or "(not available)"
        snippet = item.get("snippet") or {}
        snippet_sender = (snippet.get("sender") or {}).get("id")
        # Skip if last snippet is ours
        if snippet_sender == me.id:
            continue
        if not target_id:
            continue
        sent = decide_and_reply_for_thread(
            client,
            me=me,
            match_name=match_name,
            target_id=target_id,
            config=config,
            openai_client=oa_client,
        )
        if sent:
            results.append((target_id, sent))
    return results


