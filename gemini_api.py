# app/gemini_api.py
# gemini_api.py
import requests
import os
import json

# Récupération de la clé API
GOOGLE_API_KEY = "AIzaSyC15PyLpKjHZPRPmqdxS2LYzbZKYQPQWIE"

# URL de l'API REST Gemini 1.5 Flash
# 2. Choix du modèle
# Tu peux remplacer par "gemini-1.5-flash", "gemini-1.5-pro", ou "gemma-2-27b-it"
# Note: Vérifie bien l'orthographe exacte du modèle sur Google AI Studio.
MODEL_NAME = "gemma-3-27b-it" 

# URL dynamique
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"

# Mémoire vive
conversation_history = []

def chat_with_gemini(prompt: str) -> str:
    global conversation_history
    
    # Sécurité prompt
    prompt_text = str(prompt) if prompt else ""

    # 1. Ajout user
    conversation_history.append({
        "role": "user", 
        "parts": [{"text": prompt_text}]
    })

    # On garde les 6 derniers messages
    recent_history = conversation_history[-6:]

    # 2. Payload
    # Note : Si le modèle Gemma ne supporte pas "systemInstruction", 
    # il faudra déplacer cette consigne dans le premier message "user".
    payload = {
        "systemInstruction": {
            "parts": [
                {"text": "Tu es Aro, assistant expert football. Réponds court (max 3 phrases). Direct, factuel, sympa."}
            ]
        },
        "contents": recent_history,
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 200,
            "topP": 0.9
        }
    }

    headers = {'Content-Type': 'application/json'}

    try:
        # 3. Appel HTTP
        response = requests.post(URL, headers=headers, data=json.dumps(payload))
        
        # Gestion erreur HTTP
        if response.status_code != 200:
            # Affiche l'erreur précise pour le débuggage
            return f"Erreur Modèle ({response.status_code}): {response.text}"

        result = response.json()

        # 4. Extraction
        try:
            reply_text = result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError, TypeError):
            return "Le modèle n'a rien renvoyé de lisible."

        # 5. Ajout réponse IA
        conversation_history.append({
            "role": "model", 
            "parts": [{"text": reply_text}]
        })

        return reply_text

    except Exception as e:
        return f"Erreur interne : {str(e)}"