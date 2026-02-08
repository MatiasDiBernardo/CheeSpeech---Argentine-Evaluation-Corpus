import os
import jiwer
import pandas as pd
import utils.xml as xml

def get_transcript_scores(audio_filename, model_name, text_ref, text_hyp, remove_all_punctuation, normalize_uppercase, allowed_special_chars, attribute_config=None, save_csv=True):
    """
    Calculates WER and CER between reference and hypothesis text after normalizing them.
    """
    text_ref_norm = xml.normalize(text_ref, remove_all_punctuation, normalize_uppercase, allowed_special_chars, attribute_config)
    text_hyp_norm = xml.normalize(text_hyp, remove_all_punctuation, normalize_uppercase, allowed_special_chars, attribute_config)
    
    output = jiwer.process_words(text_ref_norm, text_hyp_norm)
    cer_score = jiwer.cer(text_ref_norm, text_hyp_norm)
    
    word_count = len(text_ref_norm.split(' '))

    if save_csv:
        num = audio_filename.split('_')[-1].split('.')[0]
        df = pd.DataFrame({
            'audio_filename': [audio_filename],
            'wer': [output.wer],
            'cer': [cer_score],
            'wer_S': [output.substitutions],
            'wer_D': [output.deletions],
            'wer_I': [output.insertions],
            'N_words': [word_count],
            'GT_trans': [text_ref],
            'pred_trans': [text_hyp],
            'GT_trans_norm': [text_ref_norm],
            'pred_trans_norm': [text_hyp_norm]
        })
        df.to_csv(os.path.join("results", model_name, f"wer_{model_name}_{num}.csv"), index=False, encoding='utf-8-sig')

    return output.wer, cer_score, output.substitutions, output.deletions, output.insertions, word_count