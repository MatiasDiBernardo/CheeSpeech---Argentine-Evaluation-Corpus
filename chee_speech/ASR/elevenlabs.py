from elevenlabs.client import ElevenLabs
import yaml

# Carga configuración
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

asr_config = config["ASR"]
VERBOSE = config["verbose"]
API_KEY = asr_config["ElevenLabs"]["api_key"]

elevenlabs = ElevenLabs(api_key=API_KEY)
# transcription = elevenlabs.speech_to_text.convert(file="data/audios/audio_0006.wav", model_id="scribe_v2", tag_audio_events=True, language_code=None, diarize=True, include_timestamps=True, include_confidence=True)