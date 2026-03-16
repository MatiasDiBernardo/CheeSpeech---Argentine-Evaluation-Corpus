# Argentine Benchmark

This repository contains utils to create an argentine speech corpus with extensive metadata, such as ASR transcription, data augmentation, WER and CER evaluation.

## ASR Leaderboard 

<table>
    <thead>
        <tr> <th rowspan=2>Model</th> <th rowspan=2>Avg WER</th> <th rowspan=2>Global WER</th> <th colspan=2>Bs. As.</th> <th colspan=2>Centro</th> </tr>
        <tr>
                                                                                    <th>Avg WER</th><th>Global WER</th>  <th >Avg WER</th><th>Global WER</th>
        </tr>
    </thead>
    <tbody>
        <tr> <td>Whisper Turbo </td>  <td> - %</td> <td> - %</td>  <td>11,1 %</td> <td>11,6 %</td>  <td> - %</td> <td> - %</td>  </tr>
        <tr> <td>Whisper Large </td>  <td> - %</td> <td> - %</td>  <td>11,6 %</td> <td>12,3 %</td>  <td> - %</td> <td> - %</td>  </tr>
        <tr> <td>Whisper Medium </td>  <td> - %</td> <td> - %</td>  <td>14 %</td> <td>14,5 %</td>  <td> - %</td> <td> - %</td>  </tr>
        <tr> <td>Whisper Small </td>  <td> - %</td> <td> - %</td>  <td>17,3 %</td> <td>17,2 %</td>  <td> - %</td> <td> - %</td>  </tr>
        <tr> <td>Whisper Base </td>  <td> - %</td> <td> - %</td>  <td>23,6 %</td> <td>24,3 %</td>  <td> - %</td> <td> - %</td>  </tr>
        <tr> <td>Whisper Tiny </td>  <td> - %</td> <td> - %</td>  <td>35,1 %</td> <td>34,2 %</td>  <td> - %</td> <td> - %</td>  </tr>
    </tbody>
</table>


## Main Configuration (`config.yaml`)

The `config.yaml` file allows you to adjust key parameters for each stage of the processing chain. Options include:

- **Global**
    - `test`: Enable or disable test mode.
    - `verbose`: Enable or disable verbose output.
    - `validate_xml_tags`: Validate or not the use of the xml tags in the transcripts according to `utils/valid_xml_tags.yaml`.

- **ASR (Automatic Speech Recognition)**
    - `type`: Only Whisper model at the moment.
    - `model_name`: Personalized name given to a set of results, used for naming the folder and csv files.
    - **Whisper**
       - `model_size`: Whisper model size ("small", "large", "turbo", etc.).

- **Normalization (for WER and CER evalutaion)**
    - `remove_all_punctuation`: If true, removes all punctuation. If false, keeps grammatically relevant punctuation (.,;?!).
    - `normalize_uppercase`: If true normalizes all to lower case.
    - `filler_symbol`: Character used to replace the content of `<filler>` tags, if there is any in the transcripts.
    - `special_attribute_config`: Following the yaml syntax, a dictionary with tag names and attributes, when the content of th tag should be replaced by the attribute value, when normalized.

You can modify these parameters in `config.yaml` to change how you use the project.

## Installation

From the project root copy-paste the appropriate commands:

### Poetry Installation
Use this if you only need the preprocessing pipeline (VAD, segmentation, denoising hooks, transcription hooks). This keeps the environment small and fast to install.
```bash
poetry install
```

### Pip Installation
Plain venv + pip (if you don’t use Poetry). 

Create a virtual environment: 
```bash
python -m venv .venv
```
Activate it (on macOS/Linux):
```bash
source .venv/bin/activate
```

or on Windows:
```bash
".venv/Scripts/activate.bat"
```

And install with pip:
```bash
pip install .
```