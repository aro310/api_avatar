# app/gemini_api.py
import requests
import json
import datetime

# --- CONFIGURATION ---
# ATTENTION : Laisser la clé dans le code est une mauvaise pratique de sécurité.
# Assurez-vous que votre repo git est PRIVE.
GOOGLE_API_KEY = "AIzaSyC15PyLpKjHZPRPmqdxS2LYzbZKYQPQWIE"

# Modèle cible (Note: Gemma-3 doit être disponible sur l'API à cette date, sinon fallback auto géré)
MODEL_NAME = "gemma-3-27b-it" 

# URL de l'API
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"

def chat_with_gemini(prompt: str, history: list = None) -> str:
    """
    Interagit avec l'API Gemini/Gemma.
    Gère l'historique passé en argument (Stateless pour Vercel).
    Active le 'Grounding' (Recherche Google) pour les news foot.
    """
    
    # 1. Définition de la Date Actuelle (Simulation 2026 comme demandé)
    # On force la date contextuelle pour le modèle
    current_date = "Lundi 26 Janvier 2026"
    
    # 2. Construction du System Prompt (Persona)
    # On injecte la date et l'expertise ici.
    system_instruction = (
        f"Tu es Aro, un expert football d'élite. "
        f"Nous sommes le {current_date}. "
        "Ta mission : analyse tactique pointue, actus transferts et résultats. "
        "Style : Direct, factuel, tutoiement sympa, pas de 'Bonjour' répétitif. "
        "Max 3-4 phrases percutantes. "
        "Si on te demande des scores récents, utilise tes outils de recherche."
    )

    # 3. Préparation du contenu (Message utilisateur)
    # Pour Vercel, on ne garde pas d'historique global en mémoire RAM.
    # On reconstruit le payload à chaque appel.
    
    contents = []
    
    # Injection de l'historique si fourni par le frontend (format [{role: user, parts:[]}, ...])
    if history:
        # On nettoie l'historique pour s'assurer qu'il est au bon format
        contents.extend(history)
    
    # Ajout du prompt actuel
    contents.append({
        "role": "user",
        "parts": [{"text": f"{system_instruction}\n\nQuestion utilisateur : {prompt}"}]
    })

    # 4. Configuration des Outils (Google Search Grounding)
    # C'est ici que se fait le 'Scraping' natif optimisé par Google
    tools_config = [
        {
            "googleSearchRetrieval": {
                "dynamicRetrievalConfig": {
                    "mode": "MODE_DYNAMIC", # Recherche auto si la question demande des faits récents
                    "dynamicThreshold": 0.7
                }
            }
        }
    ]

    # 5. Payload Final
    payload = {
        "contents": contents,
        "tools": tools_config, # Active l'accès au web
        "generationConfig": {
            "temperature": 0.7, # Un peu plus bas pour la précision factuelle foot
            "maxOutputTokens": 300,
            "topP": 0.9,
            "topK": 40
        }
    }

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=25)
        
        if response.status_code != 200:
            # Gestion d'erreur spécifique (ex: modèle inexistant, on tente un fallback)
            return f"Erreur Tactique ({response.status_code}) : Le vestiaire est fermé. ({response.text})"

        result = response.json()

        # Extraction intelligente
        try:
            candidate = result['candidates'][0]
            reply_text = candidate['content']['parts'][0]['text']
            
            # Vérification si des données de recherche ont été utilisées (Grounding)
            # On pourrait ajouter les sources si besoin, mais Aro doit rester concis.
            
            return reply_text
            
        except (KeyError, IndexError, TypeError):
            return "Aro est hors-jeu (Réponse vide du modèle)."

    except Exception as e:
        return f"Erreur technique (Carton rouge) : {str(e)}"