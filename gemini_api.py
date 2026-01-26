# app/gemini_api.py
import requests
import json
import datetime

# --- CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyC15PyLpKjHZPRPmqdxS2LYzbZKYQPQWIE"

# ATTENTION : Si Gemma-3 refuse encore les "tools" après cette correction, 
# c'est que le modèle spécifique ne supporte pas encore la recherche web via API.
# Dans ce cas, changez pour "gemini-1.5-flash" ou "gemini-2.0-flash-exp".
MODEL_NAME = "gemma-3-27b-it" 

# URL de l'API (v1beta est requis pour les outils)
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"

def chat_with_gemini(prompt: str, history: list = None) -> str:
    """
    Interagit avec l'API.
    Correction : Utilise la syntaxe simplifiée 'googleSearch' demandée par l'erreur 400.
    """
    
    # 1. Contexte Temporel (Simulation 2026)
    current_date = "Lundi 26 Janvier 2026"
    
    # 2. System Prompt (Expert Foot)
    system_instruction = (
        f"Tu es Aro, expert football d'élite. Nous sommes le {current_date}. "
        "Ton style : Direct, factuel, tutoiement, pas de bonjour répétitif. "
        "Analyse tactique et mercato. Max 3-4 phrases. "
        "Si tu cherches des infos, utilise Google Search."
    )

    # 3. Construction du Payload
    contents = []
    
    # Injection historique (si fourni par le front)
    if history:
        contents.extend(history)
    
    # Ajout du prompt actuel
    contents.append({
        "role": "user",
        "parts": [{"text": f"{system_instruction}\n\nRequête : {prompt}"}]
    })

    # 4. CONFIGURATION DES OUTILS (CORRECTION ERREUR 400)
    # L'erreur demandait d'utiliser l'outil simple 'googleSearch' au lieu de 'retrieval'.
    tools_config = [
        {
            "googleSearch": {} 
        }
    ]

    # 5. Payload Final
    payload = {
        "contents": contents,
        "tools": tools_config, # Activation recherche Web
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300,
            "topP": 0.9
        }
    }

    headers = {'Content-Type': 'application/json'}

    try:
        # Timeout un peu plus long car la recherche Google prend 1-2 sec de plus
        response = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=30)
        
        if response.status_code != 200:
            return f"Erreur Tactique ({response.status_code}) : {response.text}"

        result = response.json()

        # 6. Extraction Robuste
        try:
            candidate = result['candidates'][0]
            
            # Vérification du contenu
            if 'content' in candidate and 'parts' in candidate['content']:
                reply_text = candidate['content']['parts'][0]['text']
                return reply_text
            else:
                # Parfois le modèle renvoie uniquement des métadonnées de recherche sans texte si la question est obscure
                return "L'arbitre consulte la VAR (Pas de réponse textuelle, rephrase ta question)."

        except (KeyError, IndexError, TypeError) as e:
            # Log pour le débogage serveur si besoin
            print(f"DEBUG JSON: {result}") 
            return "Problème de finition devant le but (Erreur lecture réponse)."

    except Exception as e:
        return f"Erreur technique : {str(e)}"