from .utils import extract_fields_sequentially, is_valid_value

def extract_runt_data(text: str) -> dict:
    """
    Extracts vehicle information from the RUNT PDF text.
    
    Args:
        text (str): Full text from the RUNT PDF.
    
    Returns:
        dict: Dictionary with keys PLATE, BRAND, LINE, MODEL, COLOR, SERVICE.
    """
    upper_text = text.upper()
    fields_before_brand = ["PLACA DEL VEHÍCULO", "TIPO DE SERVICIO"]
    fields_after_brand = ["MARCA", "LÍNEA", "MODELO", "COLOR"]
    data = {}

    if "MARCA" in upper_text:
        before = upper_text.split("MARCA", 1)[0]
        after = "MARCA\n" + upper_text.split("MARCA", 1)[1]
        data.update(extract_fields_sequentially(before, fields_before_brand))
        data.update(extract_fields_sequentially(after, fields_after_brand))
    else:
        data.update(extract_fields_sequentially(upper_text, fields_before_brand + fields_after_brand))

    # Normalize field names
    friendly_keys = {
        "PLACA DEL VEHÍCULO": "PLATE",
        "TIPO DE SERVICIO": "SERVICE",
        "MARCA": "BRAND",
        "LÍNEA": "LINE",
        "MODELO": "MODEL",
        "COLOR": "COLOR"
    }

    return {friendly_keys.get(k, k): v for k, v in data.items()}
