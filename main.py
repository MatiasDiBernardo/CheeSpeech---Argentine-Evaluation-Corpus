import os
import yaml
import tqdm
import pandas as pd

from chee_speech.ASR.whisper import get_model
from chee_speech.analytics.wer import get_transcript_scores

# Carga configuración
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

TEST = config["test"]
VERBOSE = config["verbose"]
VALIDATE_XML_TAGS = config["validate_xml_tags"]

asr_config = config["ASR"]
ASR_TYPE = asr_config["type"]
ASR_NAME = asr_config["model_name"]

norm_config = config["Normalization"]
REMOVE_ALL_PUNCTUATION = norm_config["remove_all_punctuation"]
NORMALIZE_UPPERCASE = norm_config["normalize_uppercase"]
FILLER_SYMBOL = norm_config["filler_symbol"]
special_attribute_config = norm_config["special_attribute_config"]

def transcribe_folder_and_score(audio_folder, transcript_folder, model_name, remove_all_punctuation, normalize_uppercase, 
                                filler_symbol=FILLER_SYMBOL, special_attrs_config=None, save_csv=True):
    """
    Transcribes all audio files in audio_folder using Whisper and calculates scores against 
    corresponding transcripts in transcript_folder.
    
    Args:
        audio_folder: Path to folder containing audio files (.wav, .mp3, etc.)
        transcript_folder: Path to folder containing reference transcripts (.txt)
        model: Whisper model to use (default: model_base)
        remove_all_punctuation: Whether to remove punctuation (default: True)
        normalize_uppercase: Whether to normalize uppercase (default: True)
        special_attrs_config: Configuration for special attributes (default: None)
    
    Returns:
        results: Tuple of (total_wer, total_cer, global_wer, total_errors, total_words)
    """
    if special_attrs_config is None:
        special_attrs_config = {}
    
    total_wer = 0.0
    total_cer = 0.0
    total_substitutions = 0
    total_deletions = 0
    total_insertions = 0
    total_words = 0
    
    # Get all audio files
    audio_files = sorted([f for f in os.listdir(audio_folder) if f.endswith(('.wav', '.mp3'))])

    os.makedirs(os.path.join("results", model_name), exist_ok=True)

    if ASR_TYPE == "Whisper":
            asr_model = get_model()
    else:
        raise ValueError(f"Unknown ASR type: {ASR_TYPE}")
    
    for audio_file in tqdm.tqdm(audio_files, desc="Transcribing audio files"):
        # Extract base name without extension
        num = os.path.splitext(audio_file)[0].split('_')[1]
        
        # Try to find corresponding transcript file
        transcript_path = os.path.join(transcript_folder, f"transcript_{num}.txt")
        
        if not os.path.exists(transcript_path):
            print(f"Warning: No transcript found for {audio_file}, skipping...")
            continue
        
        # Read reference transcript
        with open(transcript_path, 'r', encoding='utf-8') as f:
            text_ref = f.read()
        
        # Transcribe audio
        audio_path = os.path.join(audio_folder, audio_file)

        # If is not Whisper, could have errors. Best should be to implement a function in ASR module.
        text_hyp = asr_model.transcribe(audio_path, fp16=False)["text"]
        
        # Calculate scores
        wer_score, cer_score, wer_s, wer_d, wer_i, word_count = get_transcript_scores(audio_file, model_name, text_ref, text_hyp,
                                                                    remove_all_punctuation, normalize_uppercase, filler_symbol, special_attrs_config, save_csv=save_csv)
        
        total_wer += wer_score
        total_cer += cer_score
        total_substitutions += wer_s
        total_deletions += wer_d
        total_insertions += wer_i
        total_words += word_count
        
        if VERBOSE:
            print(f"  WER: {wer_score:.1%}, CER: {cer_score:.1%}, Subs: {wer_s}, Dels: {wer_d}, Ins: {wer_i}, Total Words: {word_count}")
    
    avg_wer = total_wer / len(audio_files) if len(audio_files) > 0 else 0
    avg_cer = total_cer / len(audio_files) if len(audio_files) > 0 else 0
    # Global WER: total errors divided by total words
    global_wer = (total_substitutions + total_deletions + total_insertions) / total_words if total_words > 0 else 0

    if VERBOSE:
        print(f"Average WER: {avg_wer:.2%}")
        print(f"Average CER: {avg_cer:.2%}")
        print(f"Global WER: {global_wer:.2%}")
        print(f"Total Subs: {total_substitutions}, Total Dels: {total_deletions}, Total Ins: {total_insertions}, Total Words: {total_words}")

    if save_csv:
        df = pd.DataFrame({
            'Average_WER': [avg_wer],
            'Average_CER': [avg_cer],
            'Global_WER': [global_wer],
            'Total_Substitutions': [total_substitutions],
            'Total_Deletions': [total_deletions],
            'Total_Insertions': [total_insertions],
            'Total_Words': [total_words]
        })
        df.to_csv(f"results/summary_wer_{model_name}.csv", index=False, encoding='utf-8-sig')

    return total_wer, total_cer, global_wer, total_substitutions + total_deletions + total_insertions, total_words

if __name__ == "__main__":
    if VALIDATE_XML_TAGS:
        import chee_speech.utils.xml as xml
        if VERBOSE:
            print("Validando etiquetas XML de las transcripciones...")
        errors_found = xml.validate_folder(os.path.join("data", "transcripts"))
        if errors_found:
            print("❌ Se encontraron errores en los archivos XML. Revisar los mensajes anteriores.")
            exit(1)
        else:
            if VERBOSE:
                print("✅ Validación XML completada sin errores.")

    if os.path.exists(os.path.join("results", f"summary_wer_{ASR_NAME}.csv")):
        print(f"Ya existe un resumen de WER para el modelo {ASR_NAME}. Continuá para sobreescribirlo.")
        input("Presiona Enter para continuar o Ctrl+C para cancelar...")

    transcribe_folder_and_score(os.path.join("data", "audios"), os.path.join("data", "transcripts"), ASR_NAME, REMOVE_ALL_PUNCTUATION, NORMALIZE_UPPERCASE,
                                 FILLER_SYMBOL, special_attribute_config)