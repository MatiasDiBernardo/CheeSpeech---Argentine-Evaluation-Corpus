import re
import os
import unicodedata
import yaml

# Carga configuración
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

VERBOSE = config["verbose"]

# Load XML tags from YAML
with open(os.path.join("utils", "valid_xml_tags.yaml"), "r") as f:
    _tags_raw = yaml.safe_load(f)

# Convert lists to sets for efficient attribute validation
XML_TAGS = {}
for tag_name, tag_config in _tags_raw.items():
    XML_TAGS[tag_name] = {
        "req_attrs": set(tag_config.get("req_attrs", [])),  
        "opt_attrs": set(tag_config.get("opt_attrs", [])),
        "req_text": tag_config.get("req_text", False)
    }

# --- Validation -----------------------------------------------

def validate_xml_tags(text, valid_tags = XML_TAGS):
    errors = []    
    stack = []  # Stack to track open tags and detect mismatched/unclosed tags
    
    # Matches opening tags, closing tags, and self-closing tags with optional attributes
    tag_pattern = r'<(\/?)([a-zA-Z0-9_\-\.]+)([^>]*?)(\/?)>'
    
    previous_position = 0
    for match in re.finditer(tag_pattern, text):
        match_start = match.start()
        intermediate_text = text[previous_position:match_start]
        
        # Mark parent tag as having content (text between tags)
        if stack and intermediate_text.strip():
            stack[-1]['has_content'] = True

        previous_position = match.end()

        # tag_full = match.group(0)
        is_closing = match.group(1) == '/'
        tag_name = match.group(2)
        attrs_content = match.group(3)
        is_self_closing = match.group(4) == '/'
        
        current_line = text.count('\n', 0, match_start) + 1

        if tag_name not in valid_tags:
            errors.append(f"[Line {current_line}] Unknown tag: <{tag_name}>")
            continue
            
        tag_config = valid_tags[tag_name]
        
        required_attrs = tag_config.get('req_attrs', set())
        optional_attrs = tag_config.get('opt_attrs', set())
        allowed_total = required_attrs | optional_attrs

        if not is_closing:
            # Extract all attribute names from the tag (e.g., attr="value" → attr)
            present_attrs_list = re.findall(r'([a-zA-Z0-9_\-]+)\s*=', attrs_content)
            present_attrs_set = set(present_attrs_list)
            
            for attr in present_attrs_set:
                if attr not in allowed_total:
                    errors.append(f"[Línea {current_line}] Atributo no permitido '{attr}' en <{tag_name}>.")
            
            # Check for missing required attributes
            missing = required_attrs - present_attrs_set
            if missing:
                errors.append(
                    f"[Línea {current_line}] La etiqueta <{tag_name}> requiere los atributos: {list(missing)}"
                )

        if is_self_closing:
            continue
            
        elif is_closing:
            if not stack:
                errors.append(f"[Línea {current_line}] Cierre inesperado </{tag_name}>.")
                continue

            last_node = stack[-1]

            if last_node['name'] == tag_name:
                node_to_close = stack.pop()
                
                # Validate that required_text tags have content
                if config.get('req_text', False) and not node_to_close['has_content']:
                    errors.append(f"[Línea {current_line}] La etiqueta <{tag_name}> no puede estar vacía.")
                
                # Propagate content flag to parent tag
                if stack and node_to_close['has_content']:
                     stack[-1]['has_content'] = True
            else:
                # Find if tag exists deeper in stack (mismatched/interleaved tags)
                stack_names = [n['name'] for n in stack]
                if tag_name in stack_names:
                    errors.append(f"[Línea {current_line}] Cerrado </{tag_name}> pero faltaron cerrar internas.")
                    # Pop all tags until we find the matching opening tag
                    while stack and stack[-1]['name'] != tag_name:
                        stack.pop()
                    stack.pop() 
                else:
                    errors.append(f"[Línea {current_line}] Cierre huérfano </{tag_name}>.")
        else:
            stack.append({
                'name': tag_name, 
                'line': current_line, 
                'has_content': False
            })

    if stack:
        for node in stack:
            errors.append(f"[Final] La etiqueta <{node['name']}> (Línea {node['line']}) nunca se cerró.")

    return errors

def validate_folder(folder_path, valid_tags=XML_TAGS, extension=".txt"):
    """
    Search for files with the given extension in the folder and validate them.
    """
    if not os.path.exists(folder_path):
        print(f"Error: La carpeta '{folder_path}' no existe.")
        return

    files = [f for f in os.listdir(folder_path) if f.endswith(extension)]
    
    if not files:
        print(f"No se encontraron archivos {extension} en {folder_path}.")
        return

    if VERBOSE:
        print(f"📂 Analizando {len(files)} archivos en: {folder_path}\n")

    errors_found = False

    for file in files:
        full_path = os.path.join(folder_path, file)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            error_list = validate_xml_tags(content, valid_tags)
            
            if not error_list:
                if VERBOSE:
                    print(f"✅ {file}: CORRECTO")
                    print("-" * 60)
            else:
                errors_found = True
                print(f"❌ {file}: {len(error_list)} ERRORES")
                for err in error_list:
                    print(f"   • {err}")
                print("-" * 60)
            
        except Exception as e:
            print(f"⚠️  Error al leer {file}: {e}")
        

    return errors_found
    
# --- Normalization and Cleaning -------------------------------

def process_special_tags(text: str, special_attrs_config: dict):
    """
    Search for specific tags configured in special_attrs_config. key: 'tag', value: 'attribute'.
    For these tags, extracts the attribute value and REMOVES the internal text content.
    """
    processed_text = text
    
    for tag, attribute in special_attrs_config.items():        
        # Extract attribute value and replace tag+content with just the attribute
        pattern = rf'<{tag}\b[^>]*{attribute}=["\']([^"\'\']+)["\'][^>]*>(.*?)<\/{tag}>'
        processed_text = re.sub(pattern, r' \1 ', processed_text, flags=re.DOTALL | re.IGNORECASE)

        # Handle self-closing tag variant
        self_closing_pattern = rf'<{tag}\b[^>]*{attribute}=["\']([^"\'\']+)["\'][^>]*\/?>'                
        processed_text = re.sub(self_closing_pattern, r' \1 ', processed_text, flags=re.IGNORECASE)

    return processed_text

def replace_xml_block(text, tag_name, replacement):
    """
    Replaces an entire XML block (start tag + content + end tag) 
    with a specific string.
    """
    
    # Pattern 1: Standard block <tag>content</tag>
    block_pattern = rf'<{tag_name}\b.*?>.*?<\/{tag_name}>'    
    processed_text = re.sub(block_pattern, replacement, text, flags=re.DOTALL | re.IGNORECASE)
    
    # Pattern 2: Self-closing tags <tag />
    self_closing_pattern = rf'<{tag_name}\b.*?\/?>'    
    final_text = re.sub(self_closing_pattern, replacement, processed_text, flags=re.IGNORECASE)
    
    return final_text

def remove_tags(text):
    """
    Remove any XML/HTML tags (<tag>...</tag> or <tag />), leaving text content intact.
    Replaces tag with space to prevent words from sticking together.
    """
    
    clean_text = re.sub(r'<[^>]+>', ' ', text)
    return clean_text

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

def normalize(text: str, remove_all_punctuation: bool, normalize_uppercase: bool, allowed_chars: str, special_attrs_config: dict = None):
    """
    Removes XML tags, punctuation, and uppercase as specified, and cleans extra whitespace.
    """

    if special_attrs_config is None:
        special_attrs_config = {}

    # Por ahora saco los fillers pero habria que reemplazarlos con un simbolo, acá y en la transcripción del modelo.
    text = replace_xml_block(text, "filler", "")

    text = process_special_tags(text, special_attrs_config)
    
    text = remove_tags(text)
    
    text = remove_punctuation(text, remove_all_punctuation, allowed_chars)

    text = normalize_characters(text, normalize_uppercase)
    
    # Collapse multiple spaces to single space and trim edges
    final_result = re.sub(r'\s+', ' ', text).strip()
    
    return final_result


# if __name__ == "__main__":
#    transcripts_folder = os.path.join("data", "transcripts")
#    validate_folder(transcripts_folder, XML_TAGS)