# gemini_api.py (2026)
import requests
import json
import re
from functools import lru_cache
from datetime import datetime
from bs4 import BeautifulSoup

# =============================
# CONFIG API (clé en dur)
# =============================

GOOGLE_API_KEY = "AIzaSyC15PyLpKjHZPRPmqdxS2LYzbZKYQPQWIE"
MODEL_NAME = "gemma-3-27b-it"

API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"
)

HEADERS = {"Content-Type": "application/json"}

# Session HTTP persistante (plus rapide sur Vercel)
session = requests.Session()
session.headers.update(HEADERS)

# =============================
# MÉMOIRE CONVERSATION
# =============================

MAX_HISTORY = 4
conversation_history = []

# =============================
# NLP FOOTBALL (léger)
# =============================

FOOTBALL_TERMS = (
    "joueur", "club", "but", "buts", "match", "transfert",
    "palmarès", "ligue", "can", "coupe", "championnat",
    "ballon d'or", "fifa", "caf", "uefa"
)

def is_football_query(text: str) -> bool:
    t = text.lower()
    return any(word in t for word in FOOTBALL_TERMS)

# =============================
# SCRAPING WIKIPEDIA (2026)
# =============================

@lru_cache(maxsize=128)
def fetch_wikipedia_context(query: str) -> str:
    query = query.replace(" ", "_")
    urls = [
        f"https://fr.wikipedia.org/wiki/{query}",
        f"https://en.wikipedia.org/wiki/{query}"
    ]

    for url in urls:
        try:
            r = session.get(url, timeout=4)
            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            paragraph = soup.select_one("p")

            if paragraph:
                text = re.sub(r"\[\d+\]", "", paragraph.text).strip()
                return text[:600]
        except Exception:
            pass

    return ""

# =============================
# CONTEXTE SYSTÈME (Gemma Hack)
# =============================

SYSTEM_CONTEXT = [
    {
        "role": "user",
        "parts": [{
            "text": (
                "Instructions système : Tu es ARO, analyste football professionnel en 2026. "
                "Réponses courtes (2–3 phrases max), factuelles et à jour. "
                "Si utile, base-toi sur Wikipédia. "
                "Pas de salutations inutiles."
            )
        }]
    },
    {
        "role": "model",
        "parts": [{"text": "Compris."}]
    }
]

# =============================
# FONCTION PRINCIPALE
# =============================

def chat_with_gemini(prompt: str) -> str:
    global conversation_history

    prompt = str(prompt).strip()
    if not prompt:
        return "Question vide."

    # Enrichissement Wikipédia si football
    wiki_context = ""
    if is_football_query(prompt):
        wiki_context = fetch_wikipedia_context(prompt)

    # Mémoire utilisateur
    conversation_history.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })
    conversation_history = conversation_history[-MAX_HISTORY:]

    enriched_prompt = prompt
    if wiki_context:
        enriched_prompt += (
            "\n\nContexte Wikipédia :\n"
            f"{wiki_context}\n"
            f"(vérifié {datetime.utcnow().year})"
        )

    contents = (
        SYSTEM_CONTEXT +
        conversation_history[:-1] +
        [{"role": "user", "parts": [{"text": enriched_prompt}]}]
    )

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.5,
            "topP": 0.9,
            "maxOutputTokens": 160
        }
    }

    try:
        response = session.post(
            API_URL,
            data=json.dumps(payload),
            timeout=8
        )

        if response.status_code != 200:
            return "Erreur modèle."

        data = response.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]

        conversation_history.append({
            "role": "model",
            "parts": [{"text": reply}]
        })

        return reply.strip()

    except Exception:
        return "Erreur interne."
