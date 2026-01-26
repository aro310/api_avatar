# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
# Import relatif propre
from gemini_api import chat_with_gemini

# Initialisation Flask
app = Flask(__name__)
# CORS : Autorise tout pour le dev, à restreindre en prod si besoin
CORS(app)

# Import optionnel Audio (Gestion d'erreur silencieuse si module absent)
try:
    from ele import generate_audio_base64
except ImportError:
    generate_audio_base64 = None

@app.route("/", methods=["GET"])
def home():
    """Health check rapide pour Vercel"""
    return jsonify({
        "status": "online",
        "service": "API Aro Football",
        "date_simulation": "26 Janvier 2026",
        "version": "Vercel-Optimized 2.0"
    })

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Endpoint Chat optimisé.
    Accepte { "prompt": "...", "history": [...] }
    """
    try:
        data = request.get_json()
        prompt = data.get("prompt")
        history = data.get("history", []) # Le frontend gère la mémoire

        if not prompt:
            return jsonify({"status": "error", "message": "Il manque le ballon (Prompt vide)"}), 400

        # Appel à la logique NLP
        response_text = chat_with_gemini(prompt, history)

        return jsonify({
            "status": "success",
            "response": response_text,
            # On pourrait renvoyer l'historique mis à jour ici si on voulait faire du stateful
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/run-script", methods=["POST"])
def run_script():
    """Endpoint Audio (TTS)"""
    try:
        if not generate_audio_base64:
             return jsonify({"status": "error", "message": "Module Audio (ele.py) non trouvé sur le serveur"}), 503

        data = request.get_json()
        texte = data.get("texte")

        if not texte:
            return jsonify({"status": "error", "message": "Texte manquant pour l'audio"}), 400

        # Génération
        audio_b64 = generate_audio_base64(texte)
        
        if not audio_b64:
            return jsonify({"status": "error", "message": "Échec génération ElevenLabs"}), 500

        return jsonify({
            "status": "success",
            "message": "Audio généré",
            "audio_base64": audio_b64
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# IMPORTANT POUR VERCEL :
# Vercel cherche 'app' automatiquement.
# Le bloc __main__ ne sert qu'au développement local.
if __name__ == "__main__":
    app.run(debug=True, port=5001)