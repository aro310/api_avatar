# app/gemini_api.py
import requests
import json
import urllib.parse
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyC15PyLpKjHZPRPmqdxS2LYzbZKYQPQWIE"

# On repasse sur un appel standard (sans tools) donc Gemma-3 devrait fonctionner.
# Si Gemma-3 est instable, utilise "gemini-1.5-flash"
MODEL_NAME = "gemma-3-4b-it"

URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GOOGLE_API_KEY}"

def scrape_web_context(query: str) -> str:
    """
    Scrape les résultats DuckDuckGo (Version HTML).
    """
    try:
        encoded_query = urllib.parse.quote_plus(query + " football news")
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(search_url, headers=headers, timeout=3)
        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        snippets = soup.find_all('a', class_='result__snippet')
        
        for snippet in snippets[:3]: # 3 résultats suffisent pour le contexte
            text = snippet.get_text(strip=True)
            if text:
                results.append(f"- {text}")
        
        return "\n".join(results)

    except Exception as e:
        print(f"Erreur Scraping: {e}")
        return ""

def chat_with_gemini(prompt: str, history: list = None) -> dict:
    """
    Retourne un dictionnaire contenant la réponse et l'historique mis à jour.
    """
    if history is None:
        history = []

    # 1. Scraping (Grounding)
    web_context = ""
    keywords = ["score", "match", "résultat", "transfert", "joueur", "classement", "news", "actu", "qui"]
    
    if any(k in prompt.lower() for k in keywords):
        print("🔍 Recherche d'infos récentes...")
        web_data = scrape_web_context(prompt)
        if web_data:
            # On injecte le contexte web juste pour CE tour, sans polluer tout l'historique
            web_context = (
                f"INFORMATIONS TEMPS RÉEL (Web):\n{web_data}\n"
                "Utilise ces infos si pertinentes. "
            )

    # 2. Instruction Système (La personnalité est définie ICI, pas dans le message user)
    current_date = "Lundi 26 Janvier 2026" # Mettez une date dynamique en prod
    system_instruction_text = (
        f"Tu es Aro, un expert football passionné. Nous sommes le {current_date}. "
        "IMPORTANT : Ne dis JAMAIS 'Bonjour' ou 'Salut' au début de tes phrases, continue directement la conversation. "
        "Tu tutoies l'utilisateur. Tes réponses sont courtes, factuelles et dynamiques."
    )

    # 3. Préparation du message actuel
    # On combine le contexte web éventuel avec la question de l'utilisateur
    full_user_message = f"{web_context}\nQuestion utilisateur: {prompt}"

    # On crée une copie de l'historique pour l'envoi (pour ne pas modifier l'original tout de suite)
    payload_contents = list(history)
    payload_contents.append({
        "role": "user",
        "parts": [{"text": full_user_message}]
    })

    # 4. Construction du Payload JSON complet
    payload = {
        # 'system_instruction' est la clé magique pour définir le comportement global
        "system_instruction": {
            "parts": [{"text": system_instruction_text}]
        },
        "contents": payload_contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300,
        }
    }

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=20)
        
        if response.status_code != 200:
            return {"text": f"Erreur API ({response.status_code}): {response.text}", "history": history}

        result = response.json()
        
        try:
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
            
            # MISE À JOUR DE L'HISTORIQUE (IMPORTANT POUR LA SUITE)
            # On ajoute la question originale (sans le blabla technique du web context pour garder l'historique propre)
            history.append({"role": "user", "parts": [{"text": prompt}]})
            # On ajoute la réponse de l'IA
            history.append({"role": "model", "parts": [{"text": ai_response}]})

            return {
                "text": ai_response,
                "history": history
            }
            
        except (KeyError, IndexError, TypeError) as e:
            return {"text": "Désolé, je n'ai pas compris la réponse du serveur.", "history": history}

    except Exception as e:
        return {"text": f"Erreur interne : {str(e)}", "history": history}

# --- EXEMPLE D'UTILISATION (Simulation de boucle) ---
if __name__ == "__main__":
    conversation_history = []

    print("--- Aro Football Bot (Tape 'quit' pour sortir) ---")
    while True:
        user_input = input("\nToi: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        # On passe l'historique à la fonction et on récupère le résultat MIS A JOUR
        result = chat_with_gemini(user_input, conversation_history)
        
        print(f"Aro: {result['text']}")
        
        # On sauvegarde l'historique pour le prochain tour
        conversation_history = result['history']