import pandas as pd
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_star_rating(title):
    """
    Calcula una puntuación bruta basada en palabras clave y la convierte a una calificación de 1-5 estrellas.
    """
    if not isinstance(title, str):
        return 1

    title_lower = title.lower()
    
    keyword_scores = {
        'complete': 15000, 'masterclass': 20000, 'bootcamp': 18000, 'total': 12000,
        'cero a experto': 15000, 'de a a z': 12000, '2025': 5000, '2024': 3000,
        'python': 8000, 'javascript': 8000, 'java': 7000, 'c#': 6000, 'html': 5000,
        'css': 5000, 'sql': 7000, 'react': 9000, 'angular': 8500, 'vue': 8000,
        'node.js': 7500, 'django': 7000, 'flask': 6500, 'data science': 10000,
        'machine learning': 12000, 'inteligencia artificial': 12000, 'ia': 12000,
        'excel': 6000, 'power bi': 8000, 'tableau': 8000, 'marketing': 7000,
        'seo': 5000, 'hacking': 9000, 'ciberseguridad': 10000, 'cybersecurity': 10000,
        'aws': 9000, 'azure': 8500, 'docker': 7000, 'kubernetes': 7500, 'git': 4000,
        'diseño gráfico': 6000, 'photoshop': 5000, 'illustrator': 5000, 'figma': 6000,
        'introduction': -2000, 'introducción': -2000, 'básico': -3000,
        'principiantes': -4000, 'cero': -3000, 'intro': -2000, 'guía': -1000
    }
    
    raw_score = 1500
    for keyword, score in keyword_scores.items():
        if keyword in title_lower:
            raw_score += score
            
    if raw_score > 40000: return 5
    elif raw_score > 25000: return 4
    elif raw_score > 10000: return 3
    elif raw_score > 3000: return 2
    else: return 1

# ==============================================================================
# ▼▼▼ NUEVA FUNCIÓN INTELIGENTE PARA DETECTAR LA PLATAFORMA ▼▼▼
# ==============================================================================
def extract_site_from_url(url):
    """
    Extrae un nombre de sitio limpio de una URL.
    """
    if not isinstance(url, str) or not url.startswith('http'):
        return 'Desconocido'
    try:
        domain = urlparse(url).netloc
        if 'udemy.com' in domain: return 'Udemy'
        if 'coursera.org' in domain: return 'Coursera'
        if 'edx.org' in domain: return 'edX'
        if 'platzi.com' in domain: return 'Platzi'
        # Limpiamos el nombre para otros dominios
        clean_domain = domain.replace('www.', '').split('.')[0].capitalize()
        return clean_domain
    except:
        return 'Desconocido'
# ==============================================================================

def generate_ratings_file():
    logging.info("Iniciando la generación de calificaciones (con detección de plataforma)...")

    try:
        df1 = pd.read_csv("udemy_online_education_courses_dataset.csv", encoding='latin-1')
        df2 = pd.read_csv("courses_2.csv", encoding='latin-1')
        
        # En lugar de asignar 'Udemy' manualmente, dejaremos que la función lo haga
        master_df = pd.concat([df1, df2], ignore_index=True)
        master_df.dropna(subset=['course_title'], inplace=True) 
        logging.info(f"Se combinaron los archivos. Total de filas válidas: {len(master_df)}")

    except FileNotFoundError:
        logging.error("Error: Asegúrate de que los archivos originales están en la carpeta.")
        return

    # Aplicamos la lógica para la calificación y la detección de plataforma
    master_df['star_rating'] = master_df['course_title'].apply(calculate_star_rating)
    master_df['site'] = master_df['url'].apply(extract_site_from_url) # Usamos la nueva función aquí
    
    logging.info("Calificación y detección de plataforma aplicadas a todos los cursos.")
    
    final_columns = ['course_title', 'url', 'site', 'star_rating']
    final_df = master_df[final_columns].copy()
    final_df.fillna({'url': '#', 'site': 'Desconocido'}, inplace=True)

    output_filename = "cursos_calificados_final.csv"
    final_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    logging.info(f"¡PROCESO FINALIZADO!")
    logging.info(f"El archivo definitivo se ha guardado como: '{output_filename}'")

if __name__ == "__main__":
    generate_ratings_file()