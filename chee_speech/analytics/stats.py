import pandas as pd
import numpy as np
import os

# ---------------------

def get_metadata_stats(folder):
    """
    Iterates through the folder, counts statistics from each metadata CSV and saves them to an excel file. Number of men and women, laughs, fillers, etc.
    """
    
    print(f"Buscando archivos CSV en: {folder}")
    
    csv_files = [f for f in os.listdir(folder) if f.endswith(".csv")]
    
    if not csv_files:
        print("Aviso: No se encontraron archivos .csv en la carpeta de entrada.")
        return

    print(f"Se encontraron {len(csv_files)} archivos CSV. Procesando...")

    # Counters
    total_files = 0
    total_filler = 0
    total_laughter = 0
    total_ss = 0  # Single speaker
    total_ms = 0  # Multi speaker
    total_men_ss = 0
    total_women_ss = 0
    total_speakers_ms = 0
    total_men_ms = 0
    total_women_ms = 0
    regions = {}

    for file_name in csv_files:
        try:
            df = pd.read_csv(os.path.join(folder, file_name))
            total_files += 1
            
            total_filler += df.loc[0, "has_filler"]
            total_laughter += df.loc[0, "has_laughter"]

            # Classify as multi or single speaker and count by gender
            if df.loc[0, "num_speakers"] > 1:
                total_ms += 1
                total_speakers_ms += df.loc[0, "num_speakers"]
                total_men_ms += df.loc[0, "gen_speakers"].count('M')
                total_women_ms += df.loc[0, "gen_speakers"].count('F')
            else:
                total_ss += 1
                total_men_ss += df.loc[0, "gen_speakers"].count('M')
                total_women_ss += df.loc[0, "gen_speakers"].count('F')
            
            # Count by region
            region = df.loc[0, "region"]
            if region in regions:
                regions[region] += 1
            else:
                regions[region] = 1

            # print(f"  -> Procesado: {file_name}")

        except pd.errors.EmptyDataError:
            print(f"  -> Error: El archivo {file_name} está vacío y fue omitido.")
        except Exception as e:
            print(f"  -> Error: No se pudo procesar {file_name}. Detalle: {e}")

    # Calculate gender distribution as proportion of total speakers in multi-speaker files
    male_dist_ms = total_men_ms / total_speakers_ms if total_speakers_ms > 0 else 0
    female_dist_ms = total_women_ms / total_speakers_ms if total_speakers_ms > 0 else 0

    stats_df = pd.DataFrame({
        "Total Archivos": [total_files],
        "Total Fillers": [total_filler],
        "Total Risas": [total_laughter],
        "Total Single Speaker": [total_ss],
        "Hombres SS": [total_men_ss],
        "Mujeres SS": [total_women_ss],
        "Total Multi Speaker": [total_ms],
        "Hombres MS": [male_dist_ms],
        "Mujeres MS": [female_dist_ms],
    })

    # Add region counts as separate columns
    for region, count in regions.items():
        stats_df[f"Region {region}"] = [count]

    stats_df.to_excel(f"analytics/stats_{total_files}.xlsx", index=False)

    print("\n¡Proceso completado!")

def get_wer_scores(folder):
    '''Iterates through the folder with results, reads the WER scores from each CSV and returns them as lists for plotting. Also returns the model name for labeling.'''
    csv_files = [f for f in os.listdir(folder) if f.endswith(".csv")]
    
    if not csv_files:
        print("Aviso: No se encontraron archivos .csv en la carpeta de entrada.")
        return

    wer_scores = []
    audio_nums = []

    for file_name in csv_files:
        df = pd.read_csv(os.path.join(folder, file_name))
        if 'wer' in df.columns:
            wer_scores.append(df['wer'].values[0])
            audio_nums.append(int(file_name.split(".")[0].split("_")[-1]))
        else:
            print(f"  -> Advertencia: El archivo {file_name} no contiene la columna 'wer' y fue omitido.")

    model_name = folder.split("/")[-1]

    return audio_nums, wer_scores, model_name

def plot_wer_scores(wer_scores_arrays, audio_nums_arrays, model_names = [], colors = []):

    import numpy as np
    import matplotlib.pyplot as plt    

    plt.figure(figsize=(10, 6))
    for i, wer_scores in enumerate(wer_scores_arrays):
        plt.scatter(audio_nums_arrays[i], wer_scores, label=model_names[i] if model_names else f'Model {i+1}', color=colors[i] if colors else None, alpha=0.7)
        plt.axhline(np.mean(wer_scores) + np.std(wer_scores), color=colors[i] if colors else None, linestyle='--', label=f'{model_names[i]} Mean + Std Dev WER' if model_names else f'Model {i+1} Mean + Std Dev WER')
    plt.xlabel('Número de Audio')
    plt.ylabel('WER')
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.show()

def calculate_datasets_global_wer(folders):
    csv_files = []
    for folder in folders:
        csvs = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".csv")]
        csv_files.extend(csvs)

    if not csv_files:
        print("Aviso: No se encontraron archivos .csv en la carpeta de entrada.")
        return
    
    dict_aux = {} # key: model_name, value: [Total WER, Total Errors, Total Words, Total Files]
    for file_path in csv_files:
        df = pd.read_csv(file_path)
        if 'Global_WER' in df.columns and 'Total_Substitutions' in df.columns and 'Total_Deletions' in df.columns and 'Total_Insertions' in df.columns and 'Total_Words' in df.columns:
            model_name = df['Model'].values[0]
            key = model_name
            if key not in dict_aux:
                dict_aux[key] = [0, 0, 0, 0] # Total WER, Total Errors, Total Words, Total Files
            dict_aux[key][0] += df['Global_WER'].values[0]
            dict_aux[key][1] += df['Total_Substitutions'].values[0] + df['Total_Deletions'].values[0] + df['Total_Insertions'].values[0]
            dict_aux[key][2] += df['Total_Words'].values[0]
            dict_aux[key][3] += 1
        else:
            print(f"  -> Advertencia: El archivo {file_path} no contiene las columnas necesarias y fue omitido.")

    dict_results = {}
    for model_name, values in dict_aux.items():
        avg_wer = values[0] / values[3] if values[3] > 0 else 0
        global_wer = values[1] / values[2] if values[2] > 0 else 0
        dict_results[model_name] = {
            'Avg WER': f"{np.round(avg_wer, 4) * 100}%",
            'Global WER': f"{np.round(global_wer, 4) * 100}%",
            'Total Errors':int(values[1]),
            'Total Words': int(values[2])
        }

    return dict_results


if __name__ == "__main__":
    # Define the folder where your original CSVs are located
    # folder = os.path.join("data", "metadata")
    folders = [os.path.join("results", "Buenos Aires"), os.path.join("results", "Centro")]

    # get_metadata_stats(folder)

    # models = ["whisper_tiny", "whisper_base"] #, "whisper_small", "whisper_medium"]
    colors = ["tab:blue", "tab:orange"] #, "tab:green", "tab:red"]
    wers = []
    audio_nums_arr = []
    # for model in models:
    audio_nums, wer_scores, model_name = get_wer_scores(os.path.join("results", "whisper_tiny_cheespeech"))    
    wers.append(np.array(wer_scores))
    audio_nums_arr.append(audio_nums)
    audio_nums, wer_scores, model_name = get_wer_scores(os.path.join("results", "whisper_base_cheespeech"))
    wers.append(np.array(wer_scores) * 100)
    audio_nums_arr.append(audio_nums)        
    plot_wer_scores(wers, audio_nums_arr, ["tiny", "base"], ["tab:blue", "tab:orange"])

    # results = calculate_datasets_global_wer(folders)
    # print("Resultados para el leaderboard:") 
    # for model_name, metrics in results.items():
    #     print(f"Modelo: {model_name}")
    #     for metric_name, value in metrics.items():
    #         print(f"  {metric_name}: {value}")