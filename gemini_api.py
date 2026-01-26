# app/gemini_api.py
import requests
import json
from typing import List, Dict, Optional

# Clé API (gardée en dur comme demandé)
GOOGLE_API_KEY = "AIzaSyC15PyLpKjHZPRPmqdxS2LYzbZKYQPQWIE"

# Modèle demandé
MODEL_NAME = "gemma-3-27b-it"

# URL de l'API
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"

# Instructions système simulées (hack car Gemma refuse systemInstruction)
INSTRUCTION_SETUP = [
    {
        "role": "user",
        "parts": [{
            "text": (
                "Tu es Aro, un assistant expert en football. "
                "Tu réponds toujours en français, de façon très courte (maximum 3 phrases), "
                "directe, factuelle, sympathique et enthousiaste. "
                "Ne commence jamais par bonjour ou salutations répétées. "
                "La date actuelle est le 26 janvier 2026. "
                "Tes connaissances en football sont à jour jusqu’à cette date inclusivement "
                "(résultats, classements, transferts, actualités récentes)."
            )
        }]
    },
    {
        "role": "model",
        "parts": [{"text": "Compris ! Je suis Aro, expert football, prêt à répondre avec les dernières infos au 26 janvier 2026."}]
    }
]

def chat_with_gemini(
    user_prompt: str,
    previous_messages: Optional[List[Dict]] = None
) -> str:
    """
    Fonction optimisée pour Vercel (stateless).
    - user_prompt : le nouveau message de l'utilisateur
    - previous_messages : liste des messages précédents (format Gemini API)
      Le client doit conserver et renvoyer cet historique pour maintenir la conversation.
    """
    if previous_messages is None:
        previous_messages = []

    if not user_prompt or not user_prompt.strip():
        return "Erreur : prompt vide."

    # Construction de l'historique complet
    current_user_message = {
        "role": "user",
        "parts": [{"text": user_prompt.strip()}]
    }
    all_messages = previous_messages + [current_user_message]

    # Limitation du contexte pour éviter les dépassements de tokens (sécurité + coût)
    # On garde les instructions + les 12 derniers échanges max
    recent_messages = all_messages[-12:]

    # Contexte final = instructions forcées + messages récents
    full_contents = INSTRUCTION_SETUP + recent_messages

    # Payload
    payload = {
        "contents": full_contents,
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 200,
            "topP": 0.9
        },
        # Safety settings légers (football = contenu sûr)
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    }

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(
            URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=20  # Timeout raisonnable pour Vercel
        )

        if response.status_code != 200:
            return f"Erreur API ({response.status_code}) : {response.text[:200]}"

        result = response.json()

        # Extraction sécurisée de la réponse
        try:
            reply_text = result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            # Gestion des cas où le modèle bloque ou ne renvoie rien
            if "candidates" in result and result["candidates"]:
                if "finishReason" in result["candidates"][0]:
                    reason = result["candidates"][0]["finishReason"]
                    if reason == "SAFETY":
                        return "Désolé, la réponse a été bloquée par les filtres de sécurité."
            return "Le modèle n’a rien renvoyé de lisible."

        return reply_text.strip()

    except requests.Timeout:
        return "Erreur : timeout de la requête Gemini."
    except requests.ConnectionError:
        return "Erreur : problème de connexion à l’API Gemini."
    except Exception as e:
        return f"Erreur interne : {str(e)}"