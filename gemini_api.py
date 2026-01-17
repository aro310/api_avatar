# app/gemini_api.py
# gemini_api.py
import requests
import os
import json

# Récupération de la clé API
GOOGLE_API_KEY = "AIzaSyC15PyLpKjHZPRPmqdxS2LYzbZKYQPQWIE"

# URL de l'API REST Gemini 1.5 Flash
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"

# Mémoire vive (se reset au redémarrage serveur)
conversation_history = []

def chat_with_gemini(prompt: str) -> str:
    global conversation_history
    
    # 1. Ajout du message utilisateur à l'historique
    conversation_history.append({"role": "user", "parts": [{"text": prompt}]})

    # 2. Préparation du payload pour l'API REST
    # On limite l'historique aux 10 derniers échanges pour ne pas saturer
    recent_history = conversation_history[-10:]

    # Instructions système (Aro)
    system_instruction = {
        "role": "user",
        "parts": [{"text": "Tu es Aro, un assistant expert football. Réponds court (max 3 phrases). Ne dis pas bonjour à chaque fois. Sois direct et sympa."}]
    }
    
    # On insère l'instruction système au tout début (astuce pour l'API REST simple)
    contents = [system_instruction] + recent_history

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 200,
            "topP": 0.9
        }
    }

    headers = {'Content-Type': 'application/json'}

    try:
        # 3. Appel HTTP (Ultra léger comparé au SDK)
        response = requests.post(URL, headers=headers, data=json.dumps(payload))
        
        if response.status_code != 200:
            return f"Erreur API Google ({response.status_code}): {response.text}"

        result = response.json()

        # 4. Parsing de la réponse JSON complexe de Google
        try:
            reply_text = result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return "Erreur: Gemini n'a pas renvoyé de texte valide."

        # 5. Ajout de la réponse à l'historique (Note: API attend 'model', pas 'assistant')
        conversation_history.append({"role": "model", "parts": [{"text": reply_text}]})

        return reply_text

    except Exception as e:
        return f"Erreur interne : {str(e)}"