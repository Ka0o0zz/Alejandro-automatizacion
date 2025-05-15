import fitz  # PyMuPDF
import logging

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text from a PDF file using PyMuPDF.
    
    Args:
        file_path (str): Path to the PDF file.
    
    Returns:
        str: Extracted text, or empty string if file couldn't be processed.
    """
    if not file_path.lower().endswith(".pdf"):
        logging.warning(f"Skipped non-PDF file: {file_path}")
        return ""

    try:
        with fitz.open(file_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    except Exception as e:
        logging.error(f"Failed to read PDF {file_path}: {e}")
        return ""
