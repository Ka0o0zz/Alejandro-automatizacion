# main.py

import os
import logging
import pandas as pd

from extractor.reader import extract_text_from_pdf
from extractor.execution import extract_execution_data
from extractor.runt import extract_runt_data
from extractor.personal import extract_personal_block, extract_personal_data

INPUT_DIR = "inputs"
OUTPUT_FILE = "outputs/datos_extraidos.xlsx"

# Crear carpetas necesarias
os.makedirs("logs", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/run.log"),
        logging.StreamHandler()
    ],
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Columnas en español
columnas = [
    "NÚMERO", "EJECUCIÓN", "PLACA", "MARCA", "LÍNEA", "MODELO", "COLOR",
    "SERVICIO", "CORREO", "DIRECCIÓN", "NOMBRE", "CÉDULA", "DOMICILIO"
]

def main():
    datos_totales = []

    for folder in os.listdir(INPUT_DIR):
        ruta_carpeta = os.path.join(INPUT_DIR, folder)
        if not os.path.isdir(ruta_carpeta):
            continue

        logging.info(f"📁 Procesando carpeta: {folder}")
        datos = {"NÚMERO": folder}

        for archivo in os.listdir(ruta_carpeta):
            ruta_pdf = os.path.join(ruta_carpeta, archivo)
            texto = extract_text_from_pdf(ruta_pdf)

            if "MONTO MÁXIMO DE LA OBLIGACIÓN GARANTIZADA" in texto.upper():
                logging.info(f"  ✅ Ejecución detectada: {archivo}")
                datos.update(extract_execution_data(texto))

            elif "PLACA DEL VEHÍCULO" in texto.upper():
                logging.info(f"  ✅ RUNT detectado: {archivo}")
                datos.update(extract_runt_data(texto))

            elif "5" in archivo or "EJECUCIÓN" in archivo.upper() or "EJECUCION" in archivo.upper():
                logging.info(f"  ✅ Datos personales detectados: {archivo}")
                bloque = extract_personal_block(texto)
                if bloque:
                    personales = extract_personal_data(bloque)
                    # Mapear claves internas → en español
                    datos.update({
                        "CORREO": personales.get("EMAIL", "NO ENCONTRADO"),
                        "DIRECCIÓN": personales.get("ADDRESS", "NO ENCONTRADO"),
                        "NOMBRE": personales.get("FULL_NAME", "NO ENCONTRADO"),
                        "CÉDULA": personales.get("ID_NUMBER", "NO ENCONTRADO"),
                        "DOMICILIO": personales.get("CITY", "NO ENCONTRADO"),
                    })

        datos_totales.append(datos)

    df = pd.DataFrame(datos_totales, columns=columnas)
    df.to_excel(OUTPUT_FILE, index=False)
    logging.info(f"\n✅ Archivo exportado correctamente a: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
