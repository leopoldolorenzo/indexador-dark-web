# database_manager.py
import mysql.connector
import logging
import uuid
import time

class DatabaseManager:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.connect()

    def connect(self):
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    use_pure=True
                )
                logging.info("Conexión a la base de datos establecida con éxito.")
                self.create_tables()
                break
            except mysql.connector.Error as error:
                logging.error(f"Error al conectar a la base de datos: {error}")
                retry_count += 1
                time.sleep(2)
                if retry_count == max_retries:
                    raise ConnectionError("Error al conectar a la base de datos después de varios intentos.")

    def create_tables(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS datos_completos (
                    id CHAR(36) PRIMARY KEY,
                    url VARCHAR(255) NOT NULL,
                    titulo VARCHAR(255),
                    texto TEXT,
                    fecha_captura DATETIME DEFAULT CURRENT_TIMESTAMP,
                    clasificacion_tematica VARCHAR(255),
                    resumen TEXT,
                    es_ilicito TINYINT(1),
                    tiempo_scraping FLOAT,
                    tiempo_conexion FLOAT,
                    profundidad INT,
                    INDEX (url),
                    INDEX (clasificacion_tematica)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS imagenes (
                    id CHAR(36) PRIMARY KEY,
                    datos_completos_id CHAR(36),
                    url VARCHAR(255),
                    imagen VARCHAR(255),
                    FOREIGN KEY (datos_completos_id) REFERENCES datos_completos(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enlaces (
                    id CHAR(36) PRIMARY KEY,
                    datos_completos_id CHAR(36),
                    url VARCHAR(255),
                    enlace VARCHAR(1000),
                    FOREIGN KEY (datos_completos_id) REFERENCES datos_completos(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadatos (
                    id CHAR(36) PRIMARY KEY,
                    datos_completos_id CHAR(36),
                    url VARCHAR(255),
                    nombre VARCHAR(255),
                    contenido TEXT,
                    FOREIGN KEY (datos_completos_id) REFERENCES datos_completos(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entidades (
                    id CHAR(36) PRIMARY KEY,
                    datos_completos_id CHAR(36),
                    url VARCHAR(255),
                    entidad VARCHAR(255),
                    tipo VARCHAR(255),
                    FOREIGN KEY (datos_completos_id) REFERENCES datos_completos(id)
                )
            """)
            self.connection.commit()

    def save_data(self, url, titulo, texto, enlaces, imagenes, scripts, estilos, metadatos, entidades,
                  clasificacion_tematica, resumen, es_ilicito, tiempo_scraping, tiempo_conexion, profundidad):
        try:
            self.connection.start_transaction()
            with self.connection.cursor() as cursor:
                data_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO datos_completos (id, url, titulo, texto, clasificacion_tematica, resumen, es_ilicito, tiempo_scraping, tiempo_conexion, profundidad)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (data_id, url, titulo, texto, clasificacion_tematica, resumen, es_ilicito, tiempo_scraping, tiempo_conexion, profundidad))
                
                for enlace in enlaces:
                    enlace_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO enlaces (id, datos_completos_id, url, enlace)
                        VALUES (%s, %s, %s, %s)
                    """, (enlace_id, data_id, url, enlace))
                
                for imagen in imagenes:
                    imagen_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO imagenes (id, datos_completos_id, url, imagen)
                        VALUES (%s, %s, %s, %s)
                    """, (imagen_id, data_id, url, imagen))
                
                for nombre, contenido in metadatos.items():
                    meta_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO metadatos (id, datos_completos_id, url, nombre, contenido)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (meta_id, data_id, url, nombre, contenido))
                
                for entidad, tipo in entidades:
                    entidad_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO entidades (id, datos_completos_id, url, entidad, tipo)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (entidad_id, data_id, url, entidad, tipo))

            self.connection.commit()
            logging.info(f"Datos guardados exitosamente para URL={url}")
        except mysql.connector.Error as err:
            self.connection.rollback()
            logging.error(f"Error al guardar datos: {err}")

    def get_history(self):
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM datos_completos ORDER BY fecha_captura DESC")
            return cursor.fetchall()

    def get_stats_for_domain(self, domain):
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT url, tiempo_scraping, tiempo_conexion, profundidad, clasificacion_tematica, es_ilicito
                FROM datos_completos
                WHERE url LIKE %s
            """, ('%' + domain + '%',))
            return cursor.fetchall()

    def get_summary_for_domain(self, domain):
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_urls,
                    MAX(profundidad) as max_profundidad,
                    SUM(tiempo_scraping) as total_tiempo_scraping,
                    SUM(tiempo_conexion) as total_tiempo_conexion
                FROM datos_completos
                WHERE url LIKE %s
            """, ('%' + domain + '%',))
            summary_data = cursor.fetchone()
            cursor.execute("""
                SELECT clasificacion_tematica, COUNT(*) as count
                FROM datos_completos
                WHERE url LIKE %s
                GROUP BY clasificacion_tematica
            """, ('%' + domain + '%',))
            summary_data['clasificaciones'] = cursor.fetchall()
            return summary_data

    def get_stats_by_tematica(self):
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT clasificacion_tematica, COUNT(*) as count
                FROM datos_completos
                GROUP BY clasificacion_tematica
            """)
            return cursor.fetchall()

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("Conexión a la base de datos cerrada.")

# Configurar el logging al inicio del módulo
logging.basicConfig(level=logging.INFO)
