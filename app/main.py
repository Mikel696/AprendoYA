from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

def load_data():
    """
    Carga todos los datos de cursos desde CSVs y una lista estática,
    y los combina en un único DataFrame.
    """
    # --- Fuente 1: Udemy Dataset (Primario) ---
    try:
        udemy_path = os.path.join("app", "data", "udemy_online_education_courses_dataset.csv")
        df_udemy = pd.read_csv(udemy_path)
        df_udemy = df_udemy.rename(columns={'course_title': 'title', 'num_subscribers': 'subscribers'})
        df_udemy['source'] = 'Udemy'
        df_udemy = df_udemy[['title', 'url', 'subscribers', 'price', 'source']]
    except FileNotFoundError:
        print("Advertencia: No se encontró el dataset de Udemy. Se omitirá.")
        df_udemy = pd.DataFrame()

    # --- Fuente 2: Dataset Adicional (courses_2.csv de Kaggle) ---
    try:
        courses2_path = os.path.join("app", "data", "courses_2.csv")
        df_courses2 = pd.read_csv(courses2_path)
        df_courses2 = df_courses2.rename(columns={'course_name': 'title', 'course_url': 'url', 'students_enrolled': 'subscribers'})
        df_courses2['source'] = 'Varias Plataformas'
        df_courses2['price'] = 0 # Asumimos que son gratis si no hay precio
        df_courses2 = df_courses2[['title', 'url', 'subscribers', 'price', 'source']]
    except FileNotFoundError:
        print("Advertencia: No se encontró el dataset 'courses_2.csv'. Se omitirá.")
        df_courses2 = pd.DataFrame()

    # --- Fuente 3: Lista Estática de Tutoriales de YouTube ---
    youtube_tutorials = [
        {'title': 'Curso de Python desde Cero para Principiantes', 'url': 'https://www.youtube.com/watch?v=nKPbfIU442g', 'subscribers': 1000000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Aprende HTML y CSS - Curso Desde Cero', 'url': 'https://www.youtube.com/watch?v=videoseries?list=PL_XTM0wZ2_q_T-J4L_AlK_psf2E4Sj_2A', 'subscribers': 800000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de JavaScript desde Cero', 'url': 'https://www.youtube.com/watch?v=z95mZodzlhI', 'subscribers': 1200000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de Inteligencia Artificial para Principiantes', 'url': 'https://www.youtube.com/watch?v=iX_on3hZ_q8', 'subscribers': 500000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de Ciberseguridad: Hacking Ético', 'url': 'https://www.youtube.com/watch?v=GmyyI_G4z4o', 'subscribers': 750000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso Completo de Marketing Digital', 'url': 'https://www.youtube.com/watch?v=9m5t-bV3Y6c', 'subscribers': 600000, 'price': 0, 'source': 'YouTube'}
    ]
    df_youtube = pd.DataFrame(youtube_tutorials)

    # --- Combinar todos los DataFrames ---
    master_df = pd.concat([df_udemy, df_courses2, df_youtube], ignore_index=True)
    
    # --- Limpieza de Datos ---
    master_df['title_lower'] = master_df['title'].str.lower().fillna('')
    master_df['subscribers'] = pd.to_numeric(master_df['subscribers'], errors='coerce').fillna(0).astype(int)
    
    return master_df

# Cargar los datos una sola vez al iniciar la aplicación
master_df = load_data()

@app.route('/')
def home():
    """Renderiza la página principal."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Maneja la búsqueda del formulario principal."""
    if master_df.empty:
        return jsonify({"error": "Dataset no disponible"}), 500
    
    query = request.form.get('interes', '').strip().lower()
    if not query:
        return jsonify(cursos=[])

    resultados = master_df[master_df['title_lower'].str.contains(query, na=False)]
    cursos = resultados.sort_values(by='subscribers', ascending=False).head(10).to_dict(orient='records')
    return jsonify(cursos=cursos)

@app.route('/recommend', methods=['POST'])
def recommend():
    """Procesa el test vocacional y devuelve recomendaciones."""
    if master_df.empty:
        return jsonify({"error": "Dataset no disponible"}), 500

    interest_key = request.form.get('interest_modal', '')
    level = request.form.get('level_modal', '')

    # Mapa de intereses a palabras clave de búsqueda
    interest_keywords = {
        'python': ['python'],
        'web_development': ['html', 'css', 'javascript', 'web development', 'full stack', 'react', 'angular', 'vue'],
        'data_science': ['data science', 'analytics', 'machine learning', 'big data', 'ciencia de datos'],
        'marketing': ['marketing', 'seo', 'social media'],
        'excel': ['excel', 'spreadsheets'],
        'design': ['graphic design', 'photoshop', 'illustrator', 'figma', 'diseño grafico'],
        'cybersecurity': ['cybersecurity', 'hacking', 'ciberseguridad'],
        'ai': ['artificial intelligence', 'inteligencia artificial', 'ia']
    }

    # Mapa de niveles a palabras clave
    level_keywords = {
        'beginner': ['beginner', 'cero', 'introduction', 'básico', 'scratch'],
        'intermediate': ['intermediate', 'complete', 'masterclass', 'intermedio', 'avanzado']
    }

    # Filtrar por interés
    search_terms = interest_keywords.get(interest_key, [])
    if not search_terms:
        return jsonify(cursos=[])
    
    interest_regex = '|'.join(search_terms)
    results_df = master_df[master_df['title_lower'].str.contains(interest_regex, na=False)].copy()

    # Filtrar por nivel
    if level in level_keywords:
        level_regex = '|'.join(level_keywords[level])
        level_specific_df = results_df[results_df['title_lower'].str.contains(level_regex, na=False)]
        if not level_specific_df.empty:
            results_df = level_specific_df

    recommended_courses = results_df.sort_values(by='subscribers', ascending=False).head(10).to_dict(orient='records')
    return jsonify(cursos=recommended_courses)

@app.route('/free_courses', methods=['GET'])
def free_courses():
    """Devuelve una lista de cursos gratuitos populares."""
    if master_df.empty:
        return jsonify({"error": "Dataset no disponible"}), 500

    free_courses_df = master_df[master_df['price'] == 0]
    popular_free_courses = free_courses_df.sort_values(by='subscribers', ascending=False).head(10).to_dict(orient='records')
    return jsonify(cursos=popular_free_courses)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

