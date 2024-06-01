import spacy
from langdetect import detect, DetectorFactory
import logging

nlp = spacy.load('en_core_web_sm')
DetectorFactory.seed = 0

def get_nlp_model(text):
    try:
        if len(text) > 20:
            lang = detect(text)
            return nlp if lang == 'en' else None
        else:
            logging.warning("Texto demasiado corto para detección de idioma fiable. Se asume que el idioma es inglés.")
            return nlp
    except Exception as e:
        logging.error(f"Error detectando el idioma: {str(e)}")
        return None
