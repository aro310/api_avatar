from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
from gemini_api import chat_with_gemini

# Importation directe de la fonction depuis ele.py
try:
    from ele import generate_audio_base64
except ImportError:
    generate_audio_base64 = None

app = Flask(__name__)
CORS(app)

# Swagger Config
app.config['SWAGGER'] = {
    'title': 'Aro API',
    'uiversion': 3
}
swagger = Swagger(app)

@app.route("/api/run-script", methods=["POST"])
def run_script():
    """
    Génère un audio avec ElevenLabs.
    ---
    tags:
      - Audio
    parameters:
      - in: body
        name: body
        required: true
        schema:
          properties:
            texte:
              type: string
              example: "Bonjour, je suis Aro."
    responses:
      200:
        description: Audio retourné en base64
    """
    try:
        data = request.get_json()
        texte = data.get("texte")

        if not texte:
            return jsonify({"status": "error", "message": "Le texte est manquant"}), 400

        if generate_audio_base64:
            # On récupère l'audio encodé en base64
            audio_b64 = generate_audio_base64(texte)
            
            return jsonify({
                "status": "success", 
                "message": "Audio généré",
                "audio_base64": audio_b64, # Le frontend devra jouer ça
                "texte_original": texte
            })
        else:
             return jsonify({"status": "error", "message": "Module ElevenLabs non chargé"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Chat avec Gemini.
    ---
    tags:
      - Gemini
    parameters:
      - in: body
        name: body
        required: true
        schema:
          properties:
            prompt:
              type: string
    """
    try:
        data = request.get_json()
        prompt = data.get("prompt")

        if not prompt:
            return jsonify({"status": "error", "message": "Prompt manquant"}), 400

        response_text = chat_with_gemini(prompt)

        return jsonify({
            "status": "success",
            "response": response_text
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Nécessaire pour le dev local, ignoré par Vercel
if __name__ == "__main__":
    app.run(debug=True, port=5001)