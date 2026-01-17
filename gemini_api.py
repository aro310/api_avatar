# app/gemini_api.py
# gemini_api.py
import requests
import os
import json

# Récupération de la clé API
GOOGLE_API_KEY = "AIzaSyC15PyLpKjHZPRPmqdxS2LYzbZKYQPQWIE"

# URL de l'API REST Gemini 1.5 Flash
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"

# Mémoire vive (se reset au redémarrage serveur Vercel)
conversation_history = []

def chat_with_gemini(prompt: str) -> str:
    global conversation_history
    
    # Sécurité : on s'assure que le prompt est une chaîne de caractères
    prompt_text = str(prompt) if prompt else ""

    # 1. Ajout du message utilisateur à l'historique (Format strict Google)
    conversation_history.append({
        "role": "user", 
        "parts": [{"text": prompt_text}]
    })

    # On garde seulement les 6 derniers messages pour ne pas surcharger la requête
    recent_history = conversation_history[-6:]

    # 2. Construction du payload JSON
    # IMPORTANT : On utilise le champ "systemInstruction" dédié, au lieu de le mettre dans "contents"
    payload = {
        "systemInstruction": {
            "parts": [
                {"text": "Tu es Aro, un assistant expert football. Réponds de manière courte (max 3 phrases). Ne dis pas bonjour à chaque message. Sois direct, factuel et sympa."}
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
        
        # Gestion des erreurs HTTP (400, 500, etc.)
        if response.status_code != 200:
            error_msg = f"Erreur API Google ({response.status_code}): {response.text}"
            print(error_msg) # Pour voir l'erreur dans les logs Vercel
            return "Désolé, je rencontre un problème technique avec mon cerveau (API Google)."

        result = response.json()

        # 4. Extraction de la réponse
        try:
            reply_text = result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError, TypeError):
            # Si Google renvoie un JSON valide mais vide ou bloqué par la sécurité
            return "Je n'ai pas trouvé de réponse appropriée."

        # 5. Ajout de la réponse à l'historique (Rôle 'model' obligatoire pour Google)
        conversation_history.append({
            "role": "model", 
            "parts": [{"text": reply_text}]
        })

        return reply_text

    except Exception as e:
        print(f"Exception interne: {e}")
        return "Une erreur interne est survenue."