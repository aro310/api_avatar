import os
import base64
from elevenlabs.client import ElevenLabs
from elevenlabs import save

# Initialisation du client (Utilisez des variables d'environnement sur Vercel !)
# Remplacez os.environ.get par votre clé si test local, mais cachez-la sur Vercel
api_key = "sk_6ac41ace41d5569923b6cd1e2f48461cdc146299e585b922"
client = ElevenLabs(api_key=api_key)

def generate_audio_base64(texte):
    """
    Génère l'audio et retourne une chaîne Base64 jouable par le frontend.
    """
    try:
        # 1. Génération audio (retourne un générateur)
        audio = client.text_to_speech.convert(
            text=texte,
            voice_id="SOYHLrjzK2X1ezoPC6cr",
            model_id="eleven_multilingual_v2",
            optimize_streaming_latency=3
        )

        # 2. Sauvegarde temporaire dans /tmp (seul dossier accessible en écriture sur Vercel)
        output_path = "/tmp/aro.mp3"
        save(audio, output_path)

        # 3. Conversion en Base64 pour renvoyer au frontend
        with open(output_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            base64_audio = base64.b64encode(audio_bytes).decode('utf-8')

        # 4. Nettoyage (facultatif mais propre)
        os.remove(output_path)

        return base64_audio

    except Exception as e:
        print(f"Erreur ElevenLabs: {str(e)}")
        raise e