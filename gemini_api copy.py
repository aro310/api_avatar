# app/gemini_api.py
# gemini_api.py
import requests
import os
import json

# Récupération de la clé API
GOOGLE_API_KEY = "AIzaSyC15PyLpKjHZPRPmqdxS2LYzbZKYQPQWIE"

# 2. Choix du modèle
# Le modèle Gemma refuse "systemInstruction", donc on adapte la stratégie
MODEL_NAME = "gemma-3-27b-it" 
# Note : Si "gemma-3" ne fonctionne pas ou n'est pas stable, utilise "gemma-2-27b-it" ou "gemini-1.5-flash"

# URL de l'API
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"

# Mémoire vive
conversation_history = []

def chat_with_gemini(prompt: str) -> str:
    global conversation_history
    
    # Sécurité prompt
    prompt_text = str(prompt) if prompt else ""

    # 1. Ajout du message utilisateur réel à l'historique
    conversation_history.append({
        "role": "user", 
        "parts": [{"text": prompt_text}]
    })

    # On récupère les derniers échanges
    recent_history = conversation_history[-6:]

    # 2. Construction du contexte avec le "Hack" pour Gemma
    # Au lieu d'utiliser systemInstruction, on simule un premier échange
    # où l'utilisateur donne la consigne et le modèle accepte.
    
    instruction_setup = [
        {
            "role": "user",
            "parts": [{"text": "Instructions système : Tu es Aro, un assistant expert football. Réponds court (max 3 phrases). Direct, factuel et sympa. Ne dis pas bonjour à chaque fois."}]
        },
        {
            "role": "model",
            "parts": [{"text": "Compris. Je suis Aro, expert football. Je serai bref et direct."}]
        }
    ]

    # On combine : [Instructions forcées] + [Historique réel]
    full_context = instruction_setup + recent_history

    # 3. Payload (Sans le champ systemInstruction qui bloquait)
    payload = {
        "contents": full_context,
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 200,
            "topP": 0.9
        }
    }

    headers = {'Content-Type': 'application/json'}

    try:
        # 4. Appel HTTP
        response = requests.post(URL, headers=headers, data=json.dumps(payload))
        
        if response.status_code != 200:
            return f"Erreur Modèle ({response.status_code}): {response.text}"

        result = response.json()

        # 5. Extraction
        try:
            reply_text = result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError, TypeError):
            return "Le modèle n'a rien renvoyé de lisible."

        # 6. Ajout de la réponse à l'historique
        conversation_history.append({
            "role": "model", 
            "parts": [{"text": reply_text}]
        })

        return reply_text

    except Exception as e:
        return f"Erreur interne : {str(e)}"