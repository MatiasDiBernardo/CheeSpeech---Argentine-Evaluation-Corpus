import whisper
import yaml

# Carga configuración
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

asr_config = config["ASR"]
MODEL_SIZE = asr_config["Whisper"]["model_size"]

def get_model():
    """Carga el modelo de Whisper especificado en la configuración.

    Returns:
        whisper.Whisper: Instancia del modelo de Whisper cargado.
    """
    return whisper.load_model(MODEL_SIZE)

# def asr_whisper(audio_path):
#     """Aplica Whisper para Speech-To-Text a un audio y devuelve un string con la transcripción.

#     Args:
#         audio_path (str): Path del audio a transcribir.
#     Returns:
#         str: Transcripción del audio
#     """

#     # Transcribe audio
#     result = model.transcribe(audio_path)

#     # Change only for test, original only returns resut
#     return result["text"]
