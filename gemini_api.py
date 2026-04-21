import requests
import json
import urllib.parse
from bs4 import BeautifulSoup
import os

# --- CONFIGURATION ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"
URL = "https://api.groq.com/openai/v1/chat/completions"

def scrape_web_context(query: str) -> str:
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

        for snippet in snippets[:4]:
            text = snippet.get_text(strip=True)
            if text:
                results.append(f"- {text}")

        return "\n".join(results)

    except Exception as e:
        print(f"Erreur Scraping: {e}")
        return ""

from mcp_service import mcp_service

def chat_with_gemini(prompt: str, history: list = None):
    # 1. Scraping des infos récentes
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
    from datetime import datetime
    import locale

    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except:
        locale.setlocale(locale.LC_TIME, '')

    current_date = datetime.now().strftime("%A %d %B %Y")

    system_instruction = (
        f"Tu es Aro, assistant personnel intelligent et expert football. Tu as accès à des outils externes MCP (n8n, Google Agenda). "
        f"Nous sommes le {current_date}.\n\n"
        "RÈGLES STRICTES POUR L'AGENDA :\n"
        "- Si l'utilisateur demande son agenda, programme, ou événements, TU DOIS ABSOLUMENT utiliser ton outil Google Calendar.\n"
        "- NE TENTE JAMAIS D'INVENTER ou de deviner des événements, utilise OBLIGATOIREMENT l'outil pour obtenir les vraies données.\n"
        "- Attends le retour de l'outil avant d'affirmer quoi que ce soit sur le planning de l'utilisateur.\n\n"
        "Réponds de manière directe, factuelle et sympa (tutoiement). "
        "Pas de 'Bonjour' répétitif. Max 3 phrases par réponse."
    )

    # 3. Construction des messages (format OpenAI)
    messages = [{"role": "system", "content": system_instruction}]

    if history:
        messages.extend(history)

    final_prompt = f"{web_context}\n\nQuestion: {prompt}" if web_context else prompt
    messages.append({"role": "user", "content": final_prompt})

    # 4. Intégration MCP Tools (format OpenAI)
    tools = []
    try:
        mcp_tools = mcp_service.get_tools()
        if mcp_tools:
            for t in mcp_tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema
                    }
                })
    except Exception as e:
        print(f"Erreur lors du chargement des outils MCP: {e}")

    # 5. Payload Groq
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 300,
        "top_p": 0.9
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=20)

        if response.status_code != 200:
            return f"Erreur API ({response.status_code}): {response.text}"

        result = response.json()
        message = result['choices'][0]['message']

        # Gestion du Tool Calling (MCP)
        if message.get('tool_calls'):
            tool_call = message['tool_calls'][0]
            call_name = tool_call['function']['name']
            
            # --- LOG START: ACTION DETECTION FOR FRONTEND ---
            action_type = None
            call_name_lower = call_name.lower()
            if 'calendar' in call_name_lower or 'agenda' in call_name_lower:
                action_type = "open_calendar"
            elif 'mail' in call_name_lower or 'gmail' in call_name_lower or 'email' in call_name_lower:
                action_type = "open_email"
            # --- LOG END ---
            
            call_args = json.loads(tool_call['function']['arguments'])
            print(f"Utilisation de l'outil: {call_name}")

            # Exécution via MCP
            mcp_res = mcp_service.execute_tool(call_name, call_args)

            text_results = []
            if mcp_res and getattr(mcp_res, 'content', None):
                for content_item in mcp_res.content:
                    if content_item.type == "text":
                        text_results.append(content_item.text)

            mcp_result_string = "\n".join(text_results) if text_results else "Tool executed."

            # Deuxième appel avec le résultat de l'outil
            messages.append(message)  # réponse du modèle avec tool_call
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call['id'],
                "content": mcp_result_string
            })

            payload["messages"] = messages

            response_2 = requests.post(URL, headers=headers, data=json.dumps(payload), timeout=30)
            if response_2.status_code != 200:
                return f"Erreur API 2ème passe ({response_2.status_code}): {response_2.text}"

            result_2 = response_2.json()
            return {"response": result_2['choices'][0]['message']['content'], "action": action_type}

        else:
            return {"response": message['content'], "action": None}

    except (KeyError, IndexError, TypeError) as e:
        print("Erreur parsing réponse:", result, e)
        return "Pas de réponse lisible du modèle."
    except Exception as e:
        return f"Erreur interne : {str(e)}"