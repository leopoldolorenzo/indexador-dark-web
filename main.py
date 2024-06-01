# main.py
from flask import Flask, render_template, request, redirect, url_for
from urllib.parse import urlparse
import io
import base64
import matplotlib.pyplot as plt
from config import Config
from scraping.onion_scraper import OnionScraper
from scraping.database_manager import DatabaseManager
from scraping.text_classifier import TextClassifier

app = Flask(__name__)
app.config.from_object(Config)

def get_database_config():
    return {
        'host': app.config['DB_HOST'],
        'user': app.config['DB_USER'],
        'password': app.config['DB_PASSWORD'],
        'database': app.config['DB_NAME']
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        db_manager = DatabaseManager(**get_database_config())
        text_classifier = TextClassifier()
        scraper = OnionScraper(url, Config.PROXY_HOST, Config.PROXY_PORT, db_manager, text_classifier)
        try:
            results = scraper.scrape()
            domain = urlparse(url).netloc
            return render_template('results.html', results=results, domain=domain)
        except Exception as e:
            message = f"Error durante el scraping: {e}"
            return render_template('results.html', message=message)
        finally:
            db_manager.close()
    return render_template('index.html')

@app.route('/results')
def results():
    message = "Resultados del último scraping."
    return render_template('results.html', message=message)

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url']
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    db_manager = DatabaseManager(**get_database_config())
    text_classifier = TextClassifier()
    scraper = OnionScraper(url, Config.PROXY_HOST, Config.PROXY_PORT, db_manager, text_classifier)
    try:
        results = scraper.scrape()
        domain = urlparse(url).netloc
        return render_template('results.html', results=results, domain=domain)
    except Exception as e:
        return render_template('results.html', message=str(e))
    finally:
        db_manager.close()

@app.route('/history')
def history():
    db_manager = DatabaseManager(**get_database_config())
    try:
        history_data = db_manager.get_history()
        return render_template('history.html', history=history_data)
    finally:
        db_manager.close()

@app.route('/stats')
def stats():
    domain = request.args.get('domain')
    if not domain:
        return "Domain parameter is missing", 400

    db_manager = DatabaseManager(**get_database_config())
    try:
        stats_data = db_manager.get_stats_for_domain(domain)
        summary_data = db_manager.get_summary_for_domain(domain)
        return render_template('stats.html', stats=stats_data, summary=summary_data)
    finally:
        db_manager.close()

@app.route('/stats_tematica')
def stats_tematica():
    db_manager = DatabaseManager(**get_database_config())
    try:
        stats_tematica_data = db_manager.get_stats_by_tematica()
        labels = [stat['clasificacion_tematica'] for stat in stats_tematica_data]
        data = [stat['count'] for stat in stats_tematica_data]
        
        # Crear gráfico de pastel con fondo oscuro y letras blancas
        plt.style.use('dark_background')
        fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie(data, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
        ax.axis('equal')  # Para que el gráfico sea circular

        # Personalizar texto
        for text in texts:
            text.set_color('white')
        for autotext in autotexts:
            autotext.set_color('white')

        # Guardar gráfico en un buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        buf.seek(0)
        img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()

        return render_template('stats_tematica.html', img_data=img_data)
    finally:
        db_manager.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
