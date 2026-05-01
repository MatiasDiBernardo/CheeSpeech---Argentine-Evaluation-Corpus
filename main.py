import os
import yaml
import tqdm
import pandas as pd

from chee_speech.ASR.whisper import get_model, number_tokens
from chee_speech.analytics.wer import get_transcript_scores
from chee_speech.metrics import TranscriptionMetrics, save_metrics

# Carga configuración
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

TEST = config["test"]
VERBOSE = config["verbose"]
VALIDATE_XML_TAGS = config["validate_xml_tags"]

dataset_config = config["Dataset"]
DATASET_NAME = dataset_config["name"]
USES_REGION = dataset_config["uses_region"]

asr_config = config["ASR"]
ASR_TYPE = asr_config["type"]
ASR_NAME = asr_config["model_name"]

norm_config = config["Normalization"]
REMOVE_ALL_PUNCTUATION = norm_config["remove_all_punctuation"]
NORMALIZE_UPPERCASE = norm_config["normalize_uppercase"]
FILLER_SYMBOL = norm_config["filler_symbol"]
special_attribute_config = norm_config["special_attribute_config"]

def transcribe_folder_and_score(audio_folder, transcript_folder, metadata_folder, model_name, remove_all_punctuation, normalize_uppercase, 
                                filler_symbol=FILLER_SYMBOL, special_attrs_config=None, save_csv=True):
    """
    Transcribes all audio files in audio_folder using Whisper and calculates scores against 
    corresponding transcripts in transcript_folder.
    
    Args:
        audio_folder: Path to folder containing audio files (.wav, .mp3, etc.)
        transcript_folder: Path to folder containing reference transcripts (.txt)
        metadata_folder: Path to folder containing metadata files (.csv)
        model: Whisper model to use (default: model_base)
        remove_all_punctuation: Whether to remove punctuation (default: True)
        normalize_uppercase: Whether to normalize uppercase (default: True)
        special_attrs_config: Configuration for special attributes (default: None)
    
    Returns:
        results: Tuple of (total_wer, total_cer, global_wer, total_errors, total_words)
    """
    if special_attrs_config is None:
        special_attrs_config = {}
    
    # Track metrics per region and overall total
    metrics_by_region = {}
    total_metrics = TranscriptionMetrics(model=model_name, dataset=f"{DATASET_NAME}_Total")
    
    # Get all audio files
    audio_files = sorted([f for f in os.listdir(audio_folder) if f.endswith(('.wav', '.mp3'))])

    scores_key_name = f"{model_name}_{DATASET_NAME}".lower().replace(' ', '_')
    os.makedirs(os.path.join("results", scores_key_name), exist_ok=True)

    if ASR_TYPE == "Whisper":
            asr_model = get_model()
    else:
        raise ValueError(f"Unknown ASR type: {ASR_TYPE}")
    
    for audio_file in tqdm.tqdm(audio_files, desc="Transcribing audio files"):
        # Extract base name without extension
        num = os.path.splitext(audio_file)[0].split('_')[1]

        data_key = DATASET_NAME  # Default key
        if USES_REGION:
            # Try to find corresponding metadata file
            metadata_path = os.path.join(metadata_folder, f"metadata_{num}.csv")

            if not os.path.exists(metadata_path):
                print(f"Warning: No metadata found for {audio_file}, skipping...")
                continue

            metadata = pd.read_csv(metadata_path)
            if 'region' in metadata.columns:
                region = metadata['region'].iloc[0]
                data_key += f"_{region}"
        
            # Initialize metrics for this region if not exists
            if data_key not in metrics_by_region:
                metrics_by_region[data_key] = TranscriptionMetrics(model=model_name, dataset=data_key)
        
        # Try to find corresponding transcript file
        transcript_path = os.path.join(transcript_folder, f"transcript_{num}.txt")
        
        if not os.path.exists(transcript_path):
            print(f"Warning: No transcript found for {audio_file}, skipping...")
            continue
        
        # Read reference transcript
        with open(transcript_path, 'r', encoding='utf-8') as f:
            text_ref = f.read()
        
        audio_path = os.path.join(audio_folder, audio_file)

        # If is not Whisper, could have errors. Best should be to implement a function in ASR module.
        text_hyp = asr_model.transcribe(audio_path, fp16=False)["text"]
        # , suppress_tokens=number_tokens Encourage the model to transcribe numbers as text.
        
        # Calculate scores
        wer_score, cer_score, wer_s, wer_d, wer_i, word_count = get_transcript_scores(audio_file, scores_key_name, text_ref, text_hyp, remove_all_punctuation, normalize_uppercase, filler_symbol, special_attrs_config, save_csv=save_csv)
        
        if USES_REGION:
            metrics_by_region[data_key].add_scores(wer_score, cer_score, wer_s, wer_d, wer_i, word_count)

        total_metrics.add_scores(wer_score, cer_score, wer_s, wer_d, wer_i, word_count)
        
        if VERBOSE:
            print(f"  WER: {wer_score:.2%}, CER: {cer_score:.2%}, Subs: {wer_s}, Dels: {wer_d}, Ins: {wer_i}, Total Words: {word_count}")
    
    # Finalize metrics (both regional and total)
    for metric in metrics_by_region.values():
        metric.finalize()
    total_metrics.finalize()
    
    # Build metrics list with regions and total row
    metrics_list = list(metrics_by_region.values()) if USES_REGION else []
    metrics_list.append(total_metrics)
    
    if VERBOSE and metrics_list:
        for metric in metrics_list:
            print(f"\nDataset: {metric.dataset}")
            print(f"  Average WER: {metric.average_wer:.2f}%")
            print(f"  Average CER: {metric.average_cer:.2f}%")
            print(f"  Global WER: {metric.global_wer:.2f}%")
            print(f"  Total Subs: {metric.total_substitutions}, Total Dels: {metric.total_deletions}, Total Ins: {metric.total_insertions}, Total Words: {metric.total_words}")
    
    if save_csv and metrics_list:
        csv_filename = f"results/summary_wer_{model_name.lower().replace(' ', '_')}_{DATASET_NAME.lower()}.csv"
        save_metrics(metrics_list, csv_filename, overwrite=True)    
    

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

    transcribe_folder_and_score(os.path.join("data", "audios"), os.path.join("data", "transcripts"), os.path.join("data", "metadata"), ASR_NAME, REMOVE_ALL_PUNCTUATION, NORMALIZE_UPPERCASE,
                                 FILLER_SYMBOL, special_attribute_config)