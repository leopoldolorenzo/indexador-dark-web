# Indexador Dark Web

Este proyecto es una herramienta de indexación para la Dark Web desarrollada como parte de mi Trabajo de Fin de Grado (TFG).

## Descripción

La herramienta permite realizar scraping de sitios web .onion en la Dark Web y almacena la información obtenida en una base de datos. Utiliza técnicas de procesamiento de lenguaje natural (NLP) para clasificar y resumir el contenido extraído.

## Características

- Scraping de sitios .onion utilizando la red TOR.
- Clasificación y resumen de texto utilizando OpenAI GPT.
- Almacenamiento de datos en una base de datos MySQL.
- Interfaz web desarrollada con Flask.

## Instalación

1. Clona este repositorio:

    ```bash
    git clone https://github.com/tu-usuario/tu-repositorio.git
    cd tu-repositorio
    ```

2. Crea un entorno virtual y actívalo:

    ```bash
    python -m venv nuevo_venv
    source nuevo_venv/bin/activate  # En Windows usa `nuevo_venv\Scripts\activate`
    ```

3. Instala las dependencias:

    ```bash
    pip install -r requirements.txt
    ```

4. Configura las variables de entorno:

    Crea un archivo `.env` en la raíz del proyecto con la siguiente información:

    ```env
    DB_HOST=tu_host
    DB_USER=tu_usuario
    DB_PASSWORD=tu_contraseña
    DB_NAME=tu_base_de_datos
    OPENAI_API_KEY=tu_clave_de_api
    ```

5. Ejecuta la aplicación:

    ```bash
    python src/main.py
    ```

## Uso

Accede a `http://localhost:5000` en tu navegador web y sigue las instrucciones para iniciar el scraping de un sitio .onion.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request para discutir cualquier cambio que desees realizar.

## Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT.
