import pandas as pd
import os

# This script counts statistics from each CSV in a folder.
# Number of men and women, laughs, fillers, etc.

# --- Configuration ---

# Define the folder where your original CSVs are located
folder = os.path.join("data", "metadata")

# ---------------------

def process_csvs():
    """
    Iterates through the folder, counts statistics from each CSV and saves them to an excel file.
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

# --- Run the script ---
if __name__ == "__main__":
    process_csvs()