import os
import time
from collections import defaultdict, deque
from pathlib import Path
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import anthropic

load_dotenv()

app = FastAPI()

DEFAULT_FRONTEND_ORIGIN = "https://seichi-map-rust.vercel.app"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_FRONTEND_ORIGIN).split(",")
    if origin.strip()
]
MAX_PREFETCH_SPOTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMITS = {
    "generate": 20,
    "prefetch": 2,
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# サーバーサイドキャッシュ（spot_id -> intro text）
_intro_cache: dict[str, str] = {}
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)

PREFECTURE_DATA_PATHS = [
    Path.cwd() / "frontend" / "public" / "seichi_data.json",
    Path.cwd() / "seichi_data.json",
    Path.cwd().parent / "seichi_data.json",
    Path(__file__).resolve().parent.parent / "frontend" / "public" / "seichi_data.json",
    Path(__file__).resolve().parent.parent / "seichi_data.json",
    Path(__file__).resolve().parent / "seichi_data.json",
]
FAMILIARITY_VALUES = {"", "Newcomer", "Casual fan", "Big fan"}
MOOD_VALUES = {"", "Emotional", "Exciting", "Heartwarming", "Romance"}
TRAVEL_STYLE_VALUES = {"", "Taking photos", "Relaxed walking", "Visiting many spots"}


def _load_spots() -> dict[str, dict]:
    for path in PREFECTURE_DATA_PATHS:
        if path.exists():
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            return {spot["id"]: spot for spot in data if spot.get("id")}
    return {}


SPOT_DATA = _load_spots()


class UserPrefs(BaseModel):
    nickname: str = Field(default="", max_length=40)
    familiarity: str = Field(default="", max_length=20)   # Newcomer / Casual fan / Big fan
    mood: str = Field(default="", max_length=20)          # Emotional / Exciting / Heartwarming / Romance
    travelStyle: str = Field(default="", max_length=30)   # Taking photos / Relaxed walking / Visiting many spots


class SpotRequest(BaseModel):
    id: str = Field(..., max_length=80)
    spot_name_en: str = Field(default="", max_length=120)
    anime_title_en: str = Field(default="", max_length=120)
    scene_description: str = Field(default="", max_length=1000)
    area: str = Field(default="", max_length=120)
    prefs: UserPrefs = UserPrefs()


def _client_key(request: Request, endpoint: str) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.client.host
    return f"{endpoint}:{ip}"


def _enforce_rate_limit(request: Request, endpoint: str) -> None:
    now = time.monotonic()
    bucket = _rate_buckets[_client_key(request, endpoint)]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= RATE_LIMITS[endpoint]:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    bucket.append(now)


def _validate_prefs(prefs: UserPrefs) -> None:
    if prefs.familiarity not in FAMILIARITY_VALUES:
        raise HTTPException(status_code=400, detail="Invalid familiarity")
    if prefs.mood not in MOOD_VALUES:
        raise HTTPException(status_code=400, detail="Invalid mood")
    if prefs.travelStyle not in TRAVEL_STYLE_VALUES:
        raise HTTPException(status_code=400, detail="Invalid travelStyle")


def _trusted_spot(requested: SpotRequest) -> SpotRequest:
    spot = SPOT_DATA.get(requested.id)
    if not spot:
        raise HTTPException(status_code=404, detail="Unknown spot id")
    _validate_prefs(requested.prefs)
    return SpotRequest(
        id=spot["id"],
        spot_name_en=spot.get("spot_name_en", ""),
        anime_title_en=spot.get("anime_title_en", ""),
        scene_description=spot.get("scene_description", ""),
        area=spot.get("area", ""),
        prefs=requested.prefs,
    )


def _build_prompt(spot: SpotRequest) -> str:
    p = spot.prefs
    prompt = (
        f"You are a friendly travel guide for anime fans visiting Japan. "
        f"Write exactly 2-3 short sentences in English introducing this anime pilgrimage spot to foreign tourists. "
        f"Be enthusiastic but concise. No headings, no bullet points, plain text only.\n\n"
        f"Spot: {spot.spot_name_en}\n"
        f"Anime: {spot.anime_title_en}\n"
        f"Scene: {spot.scene_description}\n"
        f"Area: {spot.area}"
    )
    instructions = []
    if p.nickname:
        instructions.append(f"You MUST start the text by addressing the reader as '{p.nickname}' (e.g. 'Hey {p.nickname},' or 'For you, {p.nickname},') — this is required every time.")
    if p.familiarity == "Newcomer":
        instructions.append("The reader is new to anime — explain simply without assuming prior knowledge.")
    elif p.familiarity == "Casual fan":
        instructions.append("The reader is a casual fan — be friendly and reference the show naturally.")
    elif p.familiarity == "Big fan":
        instructions.append("The reader is a big fan — go deeper, mention specific scenes or characters if relevant.")
    if p.mood == "Emotional":
        instructions.append("Emphasize the emotional and touching moments connected to this spot.")
    elif p.mood == "Exciting":
        instructions.append("Emphasize the exciting and dynamic aspects.")
    elif p.mood == "Heartwarming":
        instructions.append("Emphasize the warm, cozy, and uplifting atmosphere.")
    elif p.mood == "Romance":
        instructions.append("Emphasize the romantic or scenic beauty of the spot.")
    if p.travelStyle == "Taking photos":
        instructions.append("Suggest what makes this spot great for memorable photos.")
    elif p.travelStyle == "Relaxed walking":
        instructions.append("Suggest how to enjoy this spot at a leisurely pace.")
    elif p.travelStyle == "Visiting many spots":
        instructions.append("Keep it brief and highlight what is uniquely worth stopping for.")
    if instructions:
        prompt += "\n\nPersonalization:\n" + "\n".join(f"- {i}" for i in instructions)
        prompt += "\n\nIMPORTANT: Keep all proper nouns (anime titles, character names, place names) in their original form."
    return prompt


def _has_prefs(p: UserPrefs) -> bool:
    return bool(p.nickname or p.familiarity or p.mood or p.travelStyle)


def _generate(spot: SpotRequest) -> str:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": _build_prompt(spot)}],
    )
    return message.content[0].text


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-intro")
def generate_intro(spot: SpotRequest, request: Request):
    _enforce_rate_limit(request, "generate")
    spot = _trusted_spot(spot)
    personalized = _has_prefs(spot.prefs)
    if not personalized and spot.id in _intro_cache:
        return {"intro": _intro_cache[spot.id], "cached": True}
    try:
        text = _generate(spot)
        if not personalized:
            _intro_cache[spot.id] = text
        return {"intro": text, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prefetch-intros")
def prefetch_intros(spots: list[SpotRequest], request: Request):
    _enforce_rate_limit(request, "prefetch")
    if len(spots) > MAX_PREFETCH_SPOTS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_PREFETCH_SPOTS} spots per prefetch")
    results = {}
    for requested in spots:
        spot = _trusted_spot(requested)
        if spot.id not in _intro_cache:
            try:
                _intro_cache[spot.id] = _generate(spot)
            except Exception:
                pass
        results[spot.id] = _intro_cache.get(spot.id, "")
    return {"intros": results}
