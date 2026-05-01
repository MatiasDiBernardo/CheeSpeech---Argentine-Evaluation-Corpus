import re
import unicodedata
from num2words import num2words
import chee_speech.utils.xml as xml

def remove_punctuation(text:str, remove_all_punctuation:bool, excluded_chars:str = ''):
    """
    Remove unwanted symbols.
    
    Args:
        text (str): Text to clean.
        remove_punctuation (bool): 
            - True: Remove all (dots, commas, slashes, etc). Keep only letters/numbers.
            - False: Remove slashes and rare symbols, but KEEP grammatical punctuation (.,;?!).
    """
    if not remove_all_punctuation:
        excluded_chars += r'\.,;?!¡¿'  # Allowed punctuation marks: .,;?!¡¿

    return re.sub(r'[^\w\s' + excluded_chars + r'\-]', '', text)        

def normalize_characters(text, normalize_uppercase=True, remove_accents=True):
    if normalize_uppercase:
        text = text.lower()
    
    if remove_accents:
        # Decompose characters (e.g., 'á' becomes 'a' + '´')
        normalized_text = unicodedata.normalize('NFD', text)
        
        # Filter out accent marks (category 'Mn' = Mark, nonspacing)
        text = ''.join(
            c for c in normalized_text 
            if unicodedata.category(c) != 'Mn'
        )
        
    return text

def normalize_numbers_to_words(text: str, lang: str = 'es') -> str:
    """
    Convert all numbers in text to their word representation.
    
    Args:
        text (str): Text containing numbers to normalize.
        lang (str): Language code for num2words (default: 'es' for Spanish).
    
    Returns:
        str: Text with numbers converted to words.
    
    Example:
        >>> normalize_numbers_to_words("Tengo 25 años y 3 hermanos")
        "Tengo veinticinco años y tres hermanos"
    """
    return re.sub(r'\b\d+\b', lambda m: num2words(int(m.group(0)), lang=lang), text)

def normalize(text: str, remove_all_punctuation: bool, normalize_uppercase: bool, allowed_chars: str, special_attrs_config: dict = None):
    """
    Removes XML tags, punctuation, and uppercase as specified, and cleans extra whitespace.
    """

    if special_attrs_config is None:
        special_attrs_config = {}

    # Por ahora saco los fillers pero habria que reemplazarlos con un simbolo, acá y en la transcripción del modelo.
    text = xml.replace_xml_block(text, "filler", "")

    text = xml.process_special_tags(text, special_attrs_config)
    
    text = xml.remove_tags(text)
    
    text = remove_punctuation(text, remove_all_punctuation, allowed_chars)

    text = normalize_characters(text, normalize_uppercase)
    
    text = normalize_numbers_to_words(text)
    
    # Collapse multiple spaces to single space and trim edges
    final_result = re.sub(r'\s+', ' ', text).strip()
    
    return final_result