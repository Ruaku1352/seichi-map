import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
import anthropic

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# サーバーサイドキャッシュ（spot_id -> intro text）
_intro_cache: dict[str, str] = {}


class SpotRequest(BaseModel):
    id: str
    spot_name_en: str
    anime_title_en: str
    scene_description: str
    area: str


def _build_prompt(spot: SpotRequest) -> str:
    return (
        f"You are a friendly travel guide for anime fans visiting Japan. "
        f"Write exactly 2-3 short sentences in English introducing this anime pilgrimage spot to foreign tourists. "
        f"Be enthusiastic but concise. No headings, no bullet points, plain text only.\n\n"
        f"Spot: {spot.spot_name_en}\n"
        f"Anime: {spot.anime_title_en}\n"
        f"Scene: {spot.scene_description}\n"
        f"Area: {spot.area}"
    )


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
def generate_intro(spot: SpotRequest):
    if spot.id in _intro_cache:
        return {"intro": _intro_cache[spot.id], "cached": True}
    try:
        text = _generate(spot)
        _intro_cache[spot.id] = text
        return {"intro": text, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prefetch-intros")
def prefetch_intros(spots: list[SpotRequest]):
    results = {}
    for spot in spots:
        if spot.id not in _intro_cache:
            try:
                _intro_cache[spot.id] = _generate(spot)
            except Exception:
                pass
        results[spot.id] = _intro_cache.get(spot.id, "")
    return {"intros": results}
