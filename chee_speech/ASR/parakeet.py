import os
import torch
import librosa
import soundfile as sf
import nemo.collections.asr as nemo_asr

def get_model(model_name="nvidia/parakeet-tdt-0.6b-v3"):
    """
    Descarga y carga el modelo acústico en memoria.
    Retorna la instancia del modelo lista para inferencia.
    """
    print(f"Cargando modelo '{model_name}'...")
    modelo = nemo_asr.models.ASRModel.from_pretrained(model_name=model_name)
    
    if torch.cuda.is_available():
        modelo = modelo.cuda()
        print("Modelo cargado exitosamente en GPU.")
    else:
        print("Advertencia: Procesando en CPU.")
        
    modelo.eval()
    
    return modelo


CARPETA_PROXY = "./data/audios_proxy_asr"
os.makedirs(CARPETA_PROXY, exist_ok=True)

def transcribe(modelo, ruta_audio_original):
    if not os.path.exists(ruta_audio_original):
        return None

    nombre_archivo = os.path.basename(ruta_audio_original)
    ruta_proxy = os.path.join(CARPETA_PROXY, nombre_archivo.replace(".wav", "_16k.wav"))
    
    # Hay que convertir el audio a 16 kHz para usar Parakeet.
    audio_array, sr = librosa.load(ruta_audio_original, sr=16000, mono=True)             
    sf.write(ruta_proxy, audio_array, 16000)
    
    transcripcion = modelo.transcribe([ruta_proxy], batch_size=1)
    
    texto_crudo = transcripcion[0][0] if isinstance(transcripcion, tuple) else transcripcion[0]

    if os.path.exists(ruta_proxy):
        try:
            os.remove(ruta_proxy)
        except OSError as e:
            print(f"Advertencia: No se pudo borrar el proxy temporal {ruta_proxy}: {e}")

    return texto_crudo.text if hasattr(texto_crudo, 'text') else texto_crudo
        
        