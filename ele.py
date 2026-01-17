# ele.py
import os
import requests
import base64

# On récupère la clé API (Variable d'environnement Vercel ou fallback local)
ELEVENLABS_API_KEY = "sk_6ac41ace41d5569923b6cd1e2f48461cdc146299e585b922"
def generate_audio_base64(texte):
    """
    Génère l'audio via l'API REST d'ElevenLabs (sans SDK)
    et retourne une chaîne Base64 jouable.
    """
    voice_id = "SOYHLrjzK2X1ezoPC6cr" # ID de la voix (Aro ?)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }

    data = {
        "text": texte,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    try:
        # Appel direct à l'API (beaucoup plus léger que le SDK)
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
            print(f"Erreur ElevenLabs ({response.status_code}): {response.text}")
            return None

        # Conversion directe du contenu binaire en Base64
        audio_base64 = base64.b64encode(response.content).decode('utf-8')
        return audio_base64

    except Exception as e:
        print(f"Exception lors de la génération audio: {str(e)}")
        return None