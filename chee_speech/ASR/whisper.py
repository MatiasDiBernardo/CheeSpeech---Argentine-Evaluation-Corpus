import whisper
import yaml

# Carga configuración
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

asr_config = config["ASR"]
VERBOSE = config["verbose"]
MODEL_SIZE = asr_config["Whisper"]["model_size"]

def get_model():
    """Carga el modelo de Whisper especificado en la configuración.

    Returns:
        whisper.Whisper: Instancia del modelo de Whisper cargado.
    """
    if VERBOSE:
        print(f"Cargando modelo Whisper '{MODEL_SIZE}'...")
    return whisper.load_model(MODEL_SIZE)


#encourage model to transcribe words literally
tokenizer = whisper.tokenizer.get_tokenizer(multilingual=True)  # use multilingual=True if using multilingual model
number_tokens = [
    i
    for i in range(tokenizer.eot)
    if all(c in "0123456789" for c in tokenizer.decode([i]).removeprefix(" "))
]

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
