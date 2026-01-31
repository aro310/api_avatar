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
    Scrape les résultats de recherche via DuckDuckGo (Version HTML légère).
    C'est plus rapide et moins bloqué que Google pour du scraping serveur.
    """
    try:
        # On nettoie la requête pour l'URL
        encoded_query = urllib.parse.quote_plus(query + " football news")
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        # Headers pour ressembler à un vrai navigateur (Indispensable pour ne pas être bloqué)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        

        # Timeout court (3s) pour ne pas faire laguer Vercel
        response = requests.get(search_url, headers=headers, timeout=3)
        
        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraction des snippets (les résumés de recherche)
        results = []
        # DuckDuckGo HTML utilise souvent la classe 'result__snippet'
        snippets = soup.find_all('a', class_='result__snippet')
        
        for snippet in snippets[:4]: # On prend seulement les 4 premiers pour limiter la taille
            text = snippet.get_text(strip=True)
            if text:
                results.append(f"- {text}")
        
        return "\n".join(results)

    except Exception as e:
        print(f"Erreur Scraping: {e}")
        return "" # En cas d'erreur, on renvoie vide pour ne pas bloquer le chat

def chat_with_gemini(prompt: str, history: list = None) -> str:
    # 1. Scraping des infos récentes (Grounding Manuel)
    # On ne le fait que si le prompt semble demander des infos factuelles
    web_context = ""
    keywords = ["score", "match", "résultat", "transfert", "joueur", "classement", "news", "actu", "qui"]
    
    if any(k in prompt.lower() for k in keywords):
        print("Scraping en cours...")
        web_data = scrape_web_context(prompt)
        if web_data:
            web_context = (
                f"\n[INFO DU WEB EN TEMPS RÉEL - UPDATE 2026]:\n{web_data}\n"
                "Utilise ces infos pour répondre si elles sont pertinentes."
            )

    # 2. Setup Persona
    current_date = "Lundi 26 Janvier 2026"
    system_instruction = (
        f"Tu es Aro, expert football. Nous sommes le {current_date}. "
        "Réponds de manière directe, factuelle et sympa (tutoiement). "
        "Pas de 'Bonjour' répétitif. Max 3 phrases."
    )

    # 3. Construction du Payload
    contents = []
    
    if history:
        contents.extend(history)
    
    # On combine : [Instruction] + [Contexte Web Scrappé] + [Question User]
    final_prompt = f"{system_instruction}\n{web_context}\n\nQuestion: {prompt}"

    contents.append({
        "role": "user",
        "parts": [{"text": final_prompt}]
    })

    # 4. Payload Standard (Sans 'tools' qui causaient l'erreur 400)
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300,
            "topP": 0.9
        }
    }

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=20)
        
        if response.status_code != 200:
            return f"Erreur API ({response.status_code}): {response.text}"

        result = response.json()

        try:
            return result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError, TypeError):
            return "Pas de réponse lisible du modèle."

    except Exception as e:
        return f"Erreur interne : {str(e)}"