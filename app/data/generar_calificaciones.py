import pandas as pd
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_star_rating(title):
    """
    Calcula una puntuación bruta basada en un diccionario expandido de palabras clave y la convierte a una calificación de 1-5 estrellas.
    """
    if not isinstance(title, str):
        return 1

    title_lower = title.lower()
    
    # ==============================================================================
    # ▼▼▼▼▼▼▼▼▼▼▼▼▼▼ DICCIONARIO DE PUNTUACIÓN EXPANDIDO ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
    # ==============================================================================
    keyword_scores = {
        # --- Modificadores de Valor (Tipo de Curso) ---
        'masterclass': 20000, 'bootcamp': 18000, 'complete': 15000, 'completo': 15000, 
        'cero a experto': 15000, 'total': 12000, 'de a a z': 12000, 'intensivo': 10000,
        'profesional': 8000,
        
        # --- Bonificación por Relevancia (Año) ---
        '2025': 5000, '2024': 3000, '2023': 1000,
        
        # --- Tópicos de Programación y Desarrollo Web ---
        'python': 8000, 'javascript': 8000, 'java': 7000, 'c#': 6500, 'php': 6000,
        'go (golang)': 7500, 'ruby': 6000, 'swift': 7000, 'kotlin': 7000,
        'html': 5000, 'css': 5000, 'sql': 7500, 'nosql': 6500, 'mongodb': 6800,
        'react': 9000, 'angular': 8500, 'vue': 8000, 'node.js': 7500, 'next.js': 8500,
        'django': 7000, 'flask': 6500, 'api': 5000, 'rest': 5000, 'graphql': 6000,
        'wordpress': 5000, 'elementor': 4000,
        
        # --- Tópicos de Datos e IA ---
        'data science': 10000, 'ciencia de datos': 10000, 'machine learning': 12000,
        'inteligencia artificial': 12000, 'ia': 12000, 'deep learning': 13000,
        'power bi': 8000, 'tableau': 8000, 'analítica': 7000, 'analytics': 7000,
        'big data': 9000,
        
        # --- Tópicos de Cloud, DevOps y Ciberseguridad ---
        'aws': 9000, 'azure': 8500, 'google cloud': 8500, 'docker': 7000, 
        'kubernetes': 7500, 'devops': 9000, 'git': 4000, 'github': 4000,
        'hacking': 9000, 'ciberseguridad': 10000, 'cybersecurity': 10000,
        
        # --- Tópicos de Negocios y Finanzas ---
        'marketing': 7000, 'seo': 5000, 'sem': 5000, 'google ads': 6000, 'facebook ads': 6000,
        'excel': 6000, 'finanzas': 6500, 'contabilidad': 6000, 'inversiones': 7000,
        'bolsa de valores': 7000, 'trading': 7500, 'emprendimiento': 7000, 'negocios': 6000,
        
        # --- Tópicos de Diseño y Creatividad ---
        'diseño gráfico': 6000, 'diseño ux': 8000, 'diseño ui': 8000,
        'photoshop': 5000, 'illustrator': 5000, 'figma': 7000, 'blender': 7500,
        'unity': 8500, 'unreal engine': 9000, 'fotografía': 5000, 'edición de video': 6000,
        'after effects': 6500, 'premiere pro': 6000,
        
        # --- Tópicos de Hobbies y Desarrollo Personal ---
        'guitarra': 4000, 'piano': 4000, 'canto': 3500, 'dibujo': 4000,
        'productividad': 5000, 'notion': 4500,
        
        # --- Modificadores de Nivel (ajustan la puntuación) ---
        'introduction': -2000, 'introducción': -2000, 'básico': -3000,
        'principiantes': -4000, 'cero': -3000, 'intro': -2000, 'guía': -1000
    }
    # ==============================================================================
    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
    # ==============================================================================

    raw_score = 1500
    for keyword, score in keyword_scores.items():
        if keyword in title_lower:
            raw_score += score
            
    if raw_score > 45000: return 5
    elif raw_score > 30000: return 4
    elif raw_score > 12000: return 3
    elif raw_score > 4000: return 2
    else: return 1

def extract_site_from_url(url):
    if not isinstance(url, str) or not url.startswith('http'):
        return 'Desconocido'
    try:
        domain = urlparse(url).netloc
        if 'udemy.com' in domain: return 'Udemy'
        if 'coursera.org' in domain: return 'Coursera'
        if 'edx.org' in domain: return 'edX'
        if 'platzi.com' in domain: return 'Platzi'
        clean_domain = domain.replace('www.', '').split('.')[0].capitalize()
        return clean_domain
    except:
        return 'Desconocido'

def generate_final_file():
    logging.info("Iniciando la generación de calificaciones con LÓGICA EXPANDIDA...")

    try:
        df1 = pd.read_csv("udemy_online_education_courses_dataset.csv", encoding='latin-1')
        df2 = pd.read_csv("courses_2.csv", encoding='latin-1')
        
        master_df = pd.concat([df1, df2], ignore_index=True)
        master_df.dropna(subset=['course_title'], inplace=True) 
        logging.info(f"Se combinaron los archivos originales. Total de filas válidas: {len(master_df)}")

    except FileNotFoundError:
        logging.error("Error: Asegúrate de que los archivos originales están en la carpeta.")
        return

    master_df['star_rating'] = master_df['course_title'].apply(calculate_star_rating)
    master_df['site'] = master_df['url'].apply(extract_site_from_url)
    
    logging.info("Calificación y detección de plataforma aplicadas a todos los cursos.")
    
    final_columns = ['course_title', 'url', 'site', 'star_rating']
    final_df = master_df[final_columns].copy()
    final_df.fillna({'url': '#', 'site': 'Desconocido'}, inplace=True)

    output_filename = "cursos_calificados_final.csv"
    final_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    logging.info(f"¡PROCESO FINALIZADO!")
    logging.info(f"El archivo definitivo se ha guardado como: '{output_filename}'")

if __name__ == "__main__":
    generate_final_file()