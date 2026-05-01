"""
Transcription metrics handler for WER and CER evaluation.

This module provides a dataclass for transcription metrics
with support for reading/writing to CSV files via standalone functions.
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List
from numpy import round


@dataclass
class TranscriptionMetrics:
    """
    Represents transcription metrics that can be aggregated and finalized.
    
    Attributes:
        model: Name of the ASR model
        dataset: Name of the dataset/region evaluated
        average_wer: Average Word Error Rate
        average_cer: Average Character Error Rate
        global_wer: Global WER calculated from total errors/total words
        total_substitutions: Total number of word substitutions
        total_deletions: Total number of word deletions
        total_insertions: Total number of word insertions
        total_words: Total number of words in reference transcripts
    """
    
    model: str
    dataset: str
    average_wer: float = 0.0
    average_cer: float = 0.0
    global_wer: float = 0.0
    total_substitutions: int = 0
    total_deletions: int = 0
    total_insertions: int = 0
    total_words: int = 0
    _file_count: int = 0  # Internal counter for averaging
    
    def add_scores(self, wer: float, cer: float, subs: int, dels: int, ins: int, word_count: int) -> None:
        """Accumulate scores from a single file."""
        self.average_wer += wer
        self.average_cer += cer
        self.total_substitutions += subs
        self.total_deletions += dels
        self.total_insertions += ins
        self.total_words += word_count
        self._file_count += 1
    
    def finalize(self) -> None:
        """Calculate final averages and global metrics."""
        if self._file_count > 0:
            self.average_wer = round((self.average_wer / self._file_count) * 100, 4) 
            self.average_cer = round((self.average_cer / self._file_count) * 100, 4)
        
        if self.total_words > 0:
            self.global_wer = round(((self.total_substitutions + self.total_deletions + self.total_insertions) / self.total_words) * 100, 4)


def save_metrics(metrics_list: List[TranscriptionMetrics], filepath: str | Path, overwrite: bool = True) -> None:
    """
    Save metrics to CSV file.
    
    Args:
        metrics_list: List of TranscriptionMetrics instances to save
        filepath: Path to the CSV file
        overwrite: If True, overwrite existing file. If False, append to it.
    """
    if not metrics_list:
        print("Warning: No metrics to save")
        return
    
    filepath = Path(filepath)
    mode = 'w' if overwrite else 'a'
    file_exists = filepath.exists()
    
    fieldnames = [
        'Model',
        'Dataset',
        'Average_WER',
        'Average_CER',
        'Global_WER',
        'Total_Substitutions',
        'Total_Deletions',
        'Total_Insertions',
        'Total_Words'
    ]
    
    with open(filepath, mode, newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        # Write header only if file is new or overwriting
        if overwrite or not file_exists:
            writer.writeheader()
        
        for metric in metrics_list:
            row = {
                'Model': metric.model,
                'Dataset': metric.dataset,
                'Average_WER': metric.average_wer,
                'Average_CER': metric.average_cer,
                'Global_WER': metric.global_wer,
                'Total_Substitutions': metric.total_substitutions,
                'Total_Deletions': metric.total_deletions,
                'Total_Insertions': metric.total_insertions,
                'Total_Words': metric.total_words
            }
            writer.writerow(row)
    
    print(f"Metrics saved to {filepath}")


def load_metrics(filepath: str | Path) -> List[TranscriptionMetrics]:
    """
    Load metrics from existing CSV file.
    
    Args:
        filepath: Path to the CSV file to load
        
    Returns:
        List of TranscriptionMetrics instances
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    
    metrics_list = []
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row_dict in reader:
            metric = TranscriptionMetrics(
                model=row_dict['Model'],
                dataset=row_dict['Dataset'],
                average_wer=float(row_dict['Average_WER']),
                average_cer=float(row_dict['Average_CER']),
                global_wer=float(row_dict['Global_WER']),
                total_substitutions=int(row_dict['Total_Substitutions']),
                total_deletions=int(row_dict['Total_Deletions']),
                total_insertions=int(row_dict['Total_Insertions']),
                total_words=int(row_dict['Total_Words'])
            )
            metrics_list.append(metric)
    
    return metrics_list
