# app/gemini_api.py


import requests
import json
import os
import urllib.parse
import feedparser
from bs4 import BeautifulSoup

# =====================================================
# CONFIG
# =====================================================
GOOGLE_API_KEY = "AIzaSyC15PyLpKjHZPRPmqdxS2LYzbZKYQPQWIE"# clé gérée par la plateforme
MODEL_NAME = "gemma-3-27b-it"

URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FootballBot/1.0)"
}

# =====================================================
# SOURCES FOOTBALL (RSS = STABLE & FIABLE)
# =====================================================
RSS_SOURCES = {
    "ESPN": "https://www.espn.com/espn/rss/soccer/news",
    "L_EQUIPE": "https://www.lequipe.fr/rss/actu_rss_Football.xml",
    "BBC": "https://feeds.bbci.co.uk/sport/football/rss.xml",
}

# =====================================================
# SCRAPING RSS (PRIORITAIRE)
# =====================================================
def scrape_rss_football(query: str) -> str:
    results = []

    for source, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)

            for entry in feed.entries[:6]:
                title = entry.get("title", "")
                summary = BeautifulSoup(
                    entry.get("summary", ""), "html.parser"
                ).get_text()

                text = f"{title} {summary}"

                if query.lower() in text.lower():
                    results.append(
                        f"SOURCE: {source}\nINFO: {title}"
                    )

        except Exception as e:
            print(f"RSS error {source}: {e}")

    return "\n".join(results[:6])


# =====================================================
# FALLBACK DUCKDUCKGO (SI RSS VIDE)
# =====================================================
def scrape_duckduckgo(query: str) -> str:
    try:
        encoded = urllib.parse.quote_plus(query + " football")
        url = f"https://html.duckduckgo.com/html/?q={encoded}"

        response = requests.get(url, headers=HEADERS, timeout=3)
        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.text, "html.parser")
        snippets = soup.find_all("a", class_="result__snippet")

        data = []
        for s in snippets[:4]:
            txt = s.get_text(strip=True)
            if txt:
                data.append(f"INFO: {txt}")

        return "\n".join(data)

    except Exception:
        return ""


# =====================================================
# CHAT GEMMA-3 (OPTIMISÉ ACTU)
# =====================================================
def chat_with_gemini(prompt: str, history: list = None) -> str:
    # --- Web Context ---
    web_context = ""
    rss_data = scrape_rss_football(prompt)

    if rss_data:
        web_context = (
            "\n[INFORMATIONS FOOTBALL RÉCENTES – SOURCES FIABLES]\n"
            + rss_data
        )
    else:
        ddg_data = scrape_duckduckgo(prompt)
        if ddg_data:
            web_context = (
                "\n[INFORMATIONS WEB – À VÉRIFIER]\n"
                + ddg_data
            )
        else:
            web_context = "\n[AUCUNE INFORMATION RÉCENTE CONFIRMÉE]\n"

    # --- Instruction FORTE (spécifique Gemma-3) ---
    system_instruction = (
        "Tu es Aro, expert football.\n"
        "LES INFORMATIONS WEB CI-DESSOUS SONT RÉCENTES ET PRIORITAIRES "
        "SUR TA CONNAISSANCE INTERNE.\n"
        "N’INVENTE RIEN.\n"
        "Si l’info n’est pas confirmée par les sources, dis clairement "
        "'information non confirmée'.\n"
        "Réponse courte, factuelle, tutoiement."
    )

    final_prompt = f"""
{system_instruction}

DATE: 26 Janvier 2026
{web_context}

QUESTION: {prompt}
"""

    contents = history or []
    contents.append({
        "role": "user",
        "parts": [{"text": final_prompt}]
    })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 400,
            "topP": 0.9
        }
    }

    try:
        response = requests.post(
            URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=20
        )

        if response.status_code != 200:
            return f"Erreur API {response.status_code}: {response.text}"

        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"Erreur interne: {str(e)}"
