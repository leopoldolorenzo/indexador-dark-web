# text_classifier.py
import requests
import json
import os
import logging

class TextClassifier:
    def __init__(self):
        logging.info("Inicializando el clasificador de texto.")
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logging.error("La clave de la API no está configurada en las variables de entorno.")
            raise ValueError("La clave de la API no está configurada en las variables de entorno.")
        self.url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        logging.info("Clasificador de texto inicializado.")

    def classify_text_response(self, texto_respuesta):
        texto_respuesta = texto_respuesta.lower()
        palabras_ilicitas = ["ilícito", "ilegal", "prohibido"]
        indicadores_licitos = ["no es ilícito", "no es ilegal", "no es prohibido", "es lícito", "es legal", "no contiene"]

        for indicador in indicadores_licitos:
            if indicador in texto_respuesta:
                logging.debug(f"Indicador lícito encontrado: {indicador}")
                return False

        for palabra in palabras_ilicitas:
            if palabra in texto_respuesta:
                logging.debug(f"Palabra ilícita encontrada: {palabra}")
                return True

        logging.debug("No se encontraron indicadores ilícitos. Clasificado como lícito por defecto.")
        return False

    def classify_text_with_chatgpt(self, texto):
        logging.info(f"Enviando texto a la API de OpenAI: {texto}")
        datos = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": f"Clasifica este texto como ilícito si incumple las normas o leyes españolas en vigor. Si no puedes clasificarlo como ilícito, entonces clasifícalo como lícito. , añade el porqué de la clasificacion y un resumen del texto: {texto}"}],
            "temperature": 0.7
        }
        try:
            respuesta = requests.post(self.url, headers=self.headers, data=json.dumps(datos))
            respuesta.raise_for_status()
            logging.info("Respuesta recibida exitosamente de la API de OpenAI.")
        except requests.RequestException as e:
            logging.error(f"Error al conectar con la API de OpenAI: {str(e)}")
            return None, None

        texto_respuesta = respuesta.json()['choices'][0]['message']['content'].strip()
        logging.debug(f"Respuesta de la API: {texto_respuesta}")
        es_ilicito = self.classify_text_response(texto_respuesta)
        logging.info(f"El texto ha sido clasificado como {'ilícito' if es_ilicito else 'lícito'}.")

        return texto_respuesta, es_ilicito

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    logging.info("Creando una instancia de TextClassifier y clasificando un texto de ejemplo.")
    classifier = TextClassifier()
    texto_para_clasificar = "Ejemplo de texto a clasificar."
    resumen_clasificacion, es_ilicito = classifier.classify_text_with_chatgpt(texto_para_clasificar)

    if resumen_clasificacion is None or es_ilicito is None:
        logging.info("No se pudo clasificar el texto.")
    else:
        logging.info(f"El texto es {'ilícito' if es_ilicito else 'lícito'}.")
        logging.info(f"Resumen de la clasificación: {resumen_clasificacion}")
