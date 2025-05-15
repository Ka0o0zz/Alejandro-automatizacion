# import os
# import fitz  # PyMuPDF
# import re
# import unicodedata

# INPUT_DIR = "inputs"

# def normalize(text):
#     return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8").lower()

# def extract_text_from_pdf(file_path):
#     try:
#         if not file_path.lower().endswith(".pdf"):
#             return ""
#         doc = fitz.open(file_path)
#         text = ""
#         for page in doc:
#             text += page.get_text()
#         doc.close()
#         return text
#     except Exception as e:
#         print(f"⚠️ Error abriendo {file_path}: {e}")
#         return ""

# def extraer_datos_ejecucion(texto):
#     match = re.search(r"TOTAL\s*[:：]?\s*\$?\s*([\d\.,]+)", texto, re.IGNORECASE)
#     if match:
#         return match.group(1).strip()

#     lineas = texto.upper().splitlines()
#     for i, linea in enumerate(lineas):
#         if "DESCRIPCIÓN DEL INCUMPLIMIENTO" in linea:
#             for j in range(i - 1, max(i - 10, -1), -1):
#                 monto = re.search(r"\$?\s*([\d\.,]{4,})", lineas[j])
#                 if monto:
#                     return monto.group(1).strip()
#             break

#     return "NO ENCONTRADO"

# def main():
#     for folder in os.listdir(INPUT_DIR):
#         folder_path = os.path.join(INPUT_DIR, folder)
#         if os.path.isdir(folder_path):
#             ejecucion_encontrada = False
#             archivos = os.listdir(folder_path)

#             for filename in archivos:
#                 filename_norm = normalize(filename)
#                 if "ejecucion" in filename_norm and filename.lower().endswith(".pdf"):
#                     pdf_path = os.path.join(folder_path, filename)
#                     texto = extract_text_from_pdf(pdf_path)
#                     valor = extraer_datos_ejecucion(texto)
#                     print(f"📁 Caso {folder}: EJECUCIÓN = {valor}")
#                     ejecucion_encontrada = True
#                     break

#             if not ejecucion_encontrada:
#                 print(f"📁 Caso {folder}: ❌ No se encontró PDF de EJECUCIÓN")
#                 print(f"  ➤ Archivos en carpeta: {archivos}")

# if __name__ == "__main__":
#     main()

# /////////////////////////////////////////

# import fitz  # PyMuPDF
# import re

# def extract_text_from_pdf(file_path):
#     try:
#         if not file_path.lower().endswith(".pdf"):
#             return ""
#         doc = fitz.open(file_path)
#         text = ""
#         for page in doc:
#             text += page.get_text()
#         doc.close()
#         return text
#     except Exception as e:
#         print(f"⚠️ No se pudo abrir el archivo {file_path}: {e}")
#         return ""

# def extraer_datos_ejecucion(texto):
#     match = re.search(r"TOTAL\s*[:：]?\s*\$?\s*([\d\.,]+)", texto, re.IGNORECASE)
#     if match:
#         return {"EJECUCIÓN": match.group(1).strip()}

#     lineas = texto.upper().splitlines()
#     for i, linea in enumerate(lineas):
#         if "DESCRIPCIÓN DEL INCUMPLIMIENTO" in linea:
#             for j in range(i - 1, max(i - 10, -1), -1):
#                 monto = re.search(r"\$?\s*([\d\.,]{4,})", lineas[j])
#                 if monto:
#                     return {"EJECUCIÓN": monto.group(1).strip()}
#             break

#     return {"EJECUCIÓN": "NO ENCONTRADO"}

# if __name__ == "__main__":
#     ruta_pdf = "./inputs/222269/5 FORMULARIO DE EJECUCION 222269.pdf"
#     texto = extract_text_from_pdf(ruta_pdf)
#     ejecucion = extraer_datos_ejecucion(texto)
#     print("✅ Resultado extraído:")
#     print(ejecucion)

# ////////////////////////////////////////
import os
import re
import unicodedata
import fitz        # PyMuPDF
import pdfplumber
import warnings

INPUT_DIR = "inputs"


def normalize(text: str) -> str:
    """Normaliza texto a ASCII minúsculas sin acentos."""
    return unicodedata.normalize("NFKD", text) \
                      .encode("ASCII", "ignore") \
                      .decode("ASCII") \
                      .lower()


def extract_text_fitz(path: str) -> str:
    """Extrae todo el texto de un PDF usando PyMuPDF."""
    try:
        with fitz.open(path) as doc:
            return "\n".join(page.get_text() or "" for page in doc)
    except Exception:
        return ""


def extract_text_plumber(path: str) -> str:
    """Extrae todo el texto de un PDF usando pdfplumber."""
    try:
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        return ""


def extraer_datos_ejecucion(texto: str) -> str:
    """
    Busca en el texto:
      1) 'TOTAL' seguido de cifra
      2) cerca de 'DESCRIPCIÓN DEL INCUMPLIMIENTO'
      3) 'EJECUCIÓN' seguido de cifra
    """
    # 1) TOTAL ... cifra
    m = re.search(r"TOTAL\s*[:：]?\s*\$?\s*([\d\.,]+)", texto, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # 2) DESCRIPCIÓN DEL INCUMPLIMIENTO
    lines = texto.upper().splitlines()
    for i, line in enumerate(lines):
        if "DESCRIPCIÓN DEL INCUMPLIMIENTO" in line:
            for j in range(i-1, max(i-10, -1), -1):
                m2 = re.search(r"\$?\s*([\d\.,]{4,})", lines[j])
                if m2:
                    return m2.group(1).strip()
            break

    # 3) EJECUCIÓN ... cifra
    m3 = re.search(r"EJECUCIÓN\s*[:：]?\s*\$?\s*([\d\.,]+)", texto, re.IGNORECASE)
    if m3:
        return m3.group(1).strip()

    return "NO ENCONTRADO"


def extract_execution_amount_from_pdf(path: str) -> str:
    """Extrae importe de ejecución de un PDF usando PyMuPDF y pdfplumber como fallback."""
    text = extract_text_fitz(path)
    val = extraer_datos_ejecucion(text)
    if val != "NO ENCONTRADO":
        return val
    # Fallback con pdfplumber
    text = extract_text_plumber(path)
    return extraer_datos_ejecucion(text)


def extract_numero_acuses(filename: str) -> str:
    """Extrae el prefijo numérico de un archivo '* ACUSES ELECTRONICOS.pdf'."""
    base = os.path.splitext(filename)[0]
    norm = normalize(base)
    m = re.match(r"(\d+)\s*acuses electronicos", norm)
    return m.group(1) if m else "NO ENCONTRADO"


def main():
    warnings.filterwarnings("ignore", message="CropBox missing from /Page")

    for carpeta in sorted(os.listdir(INPUT_DIR)):
        ruta = os.path.join(INPUT_DIR, carpeta)
        if not os.path.isdir(ruta):
            continue

        valor = None
        # 1) Buscar todos los PDFs de ejecución (incluye 'ejecucion' y 'formulario de ejecucion')
        forms = [fn for fn in os.listdir(ruta)
                 if fn.lower().endswith(".pdf")
                 and "ejecucion" in normalize(fn)
                 and "acuses electronicos" not in normalize(fn)]

        if forms:
            # Elegir el PDF con mayor prefijo numérico
            best_fn = None
            best_num = -1
            for fn in forms:
                base = os.path.splitext(fn)[0]
                m = re.match(r"(\d+)", normalize(base))
                num = int(m.group(1)) if m else 0
                if num > best_num:
                    best_num = num
                    best_fn = fn
            # Extraer importe de ejecución
            path_pdf = os.path.join(ruta, best_fn)
            valor = extract_execution_amount_from_pdf(path_pdf)
        else:
            # 2) Fallback: extraer el prefijo numérico de 'acuses electronicos'
            acuses = next((fn for fn in os.listdir(ruta)
                           if fn.lower().endswith(".pdf")
                           and "acuses electronicos" in normalize(fn)), None)
            if acuses:
                valor = extract_numero_acuses(acuses)

        # 3) Mostrar resultado
        if valor and valor != "NO ENCONTRADO":
            print(f"📁 Caso {carpeta}: EJECUCIÓN = {valor}")
        else:
            print(f"📁 Caso {carpeta}: ❌ No se encontró valor de EJECUCIÓN")

if __name__ == "__main__":
    main()
