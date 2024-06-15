# onion_scraper.py
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse
from collections import deque
import spacy
from langdetect import detect, DetectorFactory
import time
from .text_classifier import TextClassifier
from .utils import get_nlp_model

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class OnionScraper:
    def __init__(self, base_url, proxy_host, proxy_port, db_manager, text_classifier=None, max_depth=3):
        self.base_url = base_url
        self.proxies = {'http': f'socks5h://{proxy_host}:{proxy_port}', 'https': f'socks5h://{proxy_host}:{proxy_port}'}
        self.db_manager = db_manager
        self.text_classifier = text_classifier
        self.to_visit = deque([(base_url, 0)])
        self.visited_urls = set()
        self.max_depth = max_depth
        logging.info(f"Inicializado el OnionScraper para la URL: {base_url}")

    def scrape(self):
        results = []
        while self.to_visit:
            url, depth = self.to_visit.popleft()
            logging.info(f"Visitando: {url} (Profundidad: {depth})")
            if url in self.visited_urls or depth > self.max_depth:
                continue
            self.visited_urls.add(url)

            start_time = time.time()  # Start time for connection
            try:
                response = requests.get(url, proxies=self.proxies, timeout=20)
                tiempo_conexion = time.time() - start_time  # Connection time calculation
                logging.info(f"Tiempo de conexión para {url}: {tiempo_conexion:.2f} segundos")

                if response.status_code == 200:
                    start_scraping_time = time.time()  # Start time for scraping
                    soup = BeautifulSoup(response.text, 'html.parser')
                    result = self.process_html(url, soup, depth)  # Process HTML
                    tiempo_scraping = time.time() - start_scraping_time  # Scraping time calculation
                    logging.info(f"Tiempo de scraping para {url}: {tiempo_scraping:.2f} segundos")

                    # Update result with times
                    result['tiempo_scraping'] = tiempo_scraping
                    result['tiempo_conexion'] = tiempo_conexion

                    # Save data with times
                    self.db_manager.save_data(url, result['titulo'], result['texto'], result['enlaces'], result['imagenes'], 
                                              result['scripts'], result['estilos'], result['metadatos'], result['entidades'], 
                                              result['clasificacion'], result['resumen'], result['es_ilicito'], 
                                              tiempo_scraping, tiempo_conexion, depth)
                    
                    results.append(result)
                    self.enqueue_links(url, soup, depth)
                else:
                    logging.error(f"Error al acceder a la página {url}: Código de estado {response.status_code}")
            except requests.RequestException as e:
                logging.error(f"Error al realizar la solicitud HTTP: {str(e)}")
        return results

    def process_html(self, url, soup, depth):
        title_tag = soup.find('title')
        titulo = title_tag.text.strip() if title_tag else "Sin título"
        texto_tags = soup.find_all(['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
        texto = ' '.join(tag.get_text(strip=True) for tag in texto_tags)
        enlaces = [urljoin(url, a['href']) for a in soup.find_all('a', href=True) if urlparse(urljoin(url, a['href'])).hostname == urlparse(self.base_url).hostname]
        imagenes = [img['src'] for img in soup.find_all('img', src=True)]
        scripts = [script['src'] for script in soup.find_all('script', src=True)]
        estilos = [link['href'] for link in soup.find_all('link', href=True) if 'stylesheet' in link.get('rel', [])]
        metadatos = {}
        for meta_tag in soup.find_all('meta'):
            nombre = meta_tag.get('name')
            contenido = meta_tag.get('content')
            if nombre and contenido:
                metadatos[nombre] = contenido

        nlp_model = get_nlp_model(texto)
        entidades = []
        if nlp_model:
            doc = nlp_model(texto)
            entidades = [(ent.text, ent.label_) for ent in doc.ents]

        resumen_clasificacion, es_ilicito = self.text_classifier.classify_text_with_chatgpt(texto)
        clasificacion_tematica = self.determine_theme(resumen_clasificacion)

        result = {
            'url': url,
            'titulo': titulo,
            'texto': texto,
            'enlaces': enlaces,
            'imagenes': imagenes,
            'scripts': scripts,
            'estilos': estilos,
            'metadatos': metadatos,
            'entidades': entidades,
            'clasificacion': clasificacion_tematica,
            'resumen': resumen_clasificacion,
            'es_ilicito': es_ilicito,
            'profundidad': depth
        }
        
        return result

    def determine_theme(self, classification_summary):
        topics = {
            "Drogas": ["droga", "cocaína", "marihuana", "heroína", "metanfetamina"],
            "Armas": ["arma", "fusil", "pistola", "munición", "explosivo"],
            "Finanzas": ["bitcoin", "criptomoneda", "dinero", "btc", "lavado de dinero", "banco"],
            "Hacking": ["hack", "ciberseguridad", "malware", "ransomware", "ddos", "phishing"],
            "Falsificacion Documental": ["pasaportes falsos", "identificación", "licencia", "documento falso", "visa", "falsificación de identidad"],
            "Servicios Ilegales": ["asesinato", "golpe", "fraude", "corrupción"],
            "Contenido Explicito": ["pornografía", "abuso", "explícito", "infantil"],
            "Mercado Negro": ["tráfico", "mercado negro", "venta ilegal", "comercio ilícito"],
            "Contrabando": ["contrabando", "mercancía ilegal", "traficante"],
            "Fraude": ["fraude", "estafa", "esquema ponzi", "phishing"],
            "Violencia": ["violencia", "terrorismo", "ataque", "secuestro"],
            "Extorsion": ["extorsión", "secuestro", "amenaza", "chantaje"],
            "Falsificacion": ["falsificación", "falso", "imitar", "fraude"]
        }
        classification_summary = classification_summary.lower()
        for theme, keywords in topics.items():
            if any(keyword in classification_summary for keyword in keywords):
                return theme
        return "Indeterminado"

    def enqueue_links(self, current_url, soup, depth):
        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(current_url, link['href'])
            if absolute_url not in self.visited_urls and self.is_internal_link(absolute_url):
                logging.info(f"Agregando a la cola: {absolute_url} (Profundidad: {depth + 1})")
                self.to_visit.append((absolute_url, depth + 1))

    def is_internal_link(self, url):
        return urlparse(url).netloc == urlparse(self.base_url).netloc
