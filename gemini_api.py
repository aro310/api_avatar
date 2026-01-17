# app/gemini_api.py
import google.generativeai as genai
import os

# Récupération de la clé depuis les variables d'environnement
GOOGLE_API_KEY = "AIzaSyC15PyLpKjHZPRPmqdxS2LYzbZKYQPQWIE"

# Configuration de l'API
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("⚠️ Clé API Google manquante")

# Initialisation du modèle
MODEL_NAME = "gemini-1.5-flash" # J'ai mis un modèle standard, remets "gemma-3-27b-it" si tu y as accès
model = None

try:
    model = genai.GenerativeModel(MODEL_NAME)
    print(f"✅ Modèle Gemini initialisé ({MODEL_NAME})")
except Exception as e:
    print(f"⚠️ Erreur d’initialisation du modèle Gemini : {e}")

# 🧠 Mémoire courte (Attention: s'efface lors des redémarrages Vercel)
conversation_history = []

def chat_with_gemini(prompt: str) -> str:
    global model
    if not model:
        return "Erreur : modèle non initialisé (vérifie ta clé API)."

    try:
        # Ajoute le message user
        conversation_history.append({"role": "user", "content": prompt})

        # Construit le contexte (limité aux 5 derniers échanges)
        context = "\n".join(
            [f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history[-5:]]
        )

        system_instructions = (
            "Tu es Aro, un assistant spécialisé dans le football. "
            "Réponds de manière naturelle, fluide, sans saluer ni te présenter à chaque message. "
            "Réponds en 1 à 4 phrases maximum. "
        )

        full_prompt = f"{system_instructions}\n\nHistorique récent :\n{context}\n\nAro:"

        generation_config = genai.types.GenerationConfig(
            max_output_tokens=180,
            temperature=0.8,
            top_p=0.9,
            top_k=40,
        )

        response = model.generate_content(full_prompt, generation_config=generation_config)

        if not response or not getattr(response, "text", None):
            return "⚠️ Aucune réponse générée par Gemini."

        reply = response.text.strip()

        # Ajoute la réponse assistant
        conversation_history.append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        print("💥 Erreur Gemini :", str(e))
        return f"Erreur interne : {str(e)}"