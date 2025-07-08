from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import random

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

def load_and_prepare_udemy(path):
    """Carga y procesa el dataset de Udemy."""
    try:
        df = pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        df = df.rename(columns={'course_title': 'title', 'num_subscribers': 'subscribers'})
        df['source'] = 'Udemy'
        df = df[['title', 'url', 'subscribers', 'price', 'source']]
        df['title_lower'] = df['title'].str.lower()
        print(f"Dataset de Udemy cargado: {len(df)} filas.")
        return df
    except Exception as e:
        print(f"ERROR al procesar Udemy: {e}")
    return pd.DataFrame()

def load_and_prepare_courses2(path):
    """Carga y procesa el dataset de Coursera/edX."""
    try:
        df = pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        df = df.rename(columns={'Course Name': 'title', 'Course URL': 'url', 'University': 'source'})
        df['subscribers'] = 0  # No hay datos de suscriptores
        df['price'] = 0
        df = df[['title', 'url', 'subscribers', 'price', 'source']]
        df['title_lower'] = df['title'].str.lower()
        print(f"Dataset de Coursera/edX cargado: {len(df)} filas.")
        return df
    except Exception as e:
        print(f"ERROR al procesar Coursera/edX: {e}")
    return pd.DataFrame()

def load_youtube_data():
    """Carga la lista de tutoriales de YouTube."""
    youtube_tutorials = [
        {'title': 'Curso de Python desde Cero para Principiantes 2025', 'url': 'https://www.youtube.com/watch?v=nKPbfIU442g', 'subscribers': 1500000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso HTML y CSS Desde Cero 2025', 'url': 'https://www.youtube.com/watch?v=MJkdaVFHrto', 'subscribers': 950000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de JavaScript para Principiantes - Desde Cero', 'url': 'https://www.youtube.com/watch?v=z95mZodzlhI', 'subscribers': 1200000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de INTELIGENCIA ARTIFICIAL desde CERO', 'url': 'https://www.youtube.com/watch?v=s_wz9j-2-sI', 'subscribers': 600000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de Hacking Ético 2025 desde Cero', 'url': 'https://www.youtube.com/watch?v=GmyyI_G4z4o', 'subscribers': 800000, 'price': 0, 'source': 'YouTube'},
        {'title': 'CURSO DE MARKETING DIGITAL Gratis y Completo 2025', 'url': 'https://www.youtube.com/watch?v=9m5t-bV3Y6c', 'subscribers': 650000, 'price': 0, 'source': 'YouTube'}
    ]
    df = pd.DataFrame(youtube_tutorials)
    df['title_lower'] = df['title'].str.lower()
    print(f"Dataset de YouTube cargado: {len(df)} filas.")
    return df

# Cargar todas las fuentes de datos al iniciar
df_udemy = load_and_prepare_udemy(os.path.join(basedir, "data", "udemy_online_education_courses_dataset.csv"))
df_courses2 = load_and_prepare_courses2(os.path.join(basedir, "data", "courses_2.csv"))
df_youtube = load_youtube_data()

@app.route('/')
def home():
    return render_template('index.html')

def search_and_combine(query, limit_per_source=4):
    """Busca en cada fuente de datos y combina los resultados."""
    all_results = []

    # Buscar en Udemy
    if not df_udemy.empty:
        udemy_results = df_udemy[df_udemy['title_lower'].str.contains(query, na=False)]
        udemy_results = udemy_results.sort_values(by='subscribers', ascending=False).head(limit_per_source)
        all_results.extend(udemy_results.to_dict(orient='records'))

    # Buscar en Coursera/edX
    if not df_courses2.empty:
        courses2_results = df_courses2[df_courses2['title_lower'].str.contains(query, na=False)]
        # Como no hay suscriptores, tomamos una muestra aleatoria de los resultados
        if len(courses2_results) > limit_per_source:
            courses2_results = courses2_results.sample(n=limit_per_source)
        all_results.extend(courses2_results.to_dict(orient='records'))

    # Buscar en YouTube
    if not df_youtube.empty:
        youtube_results = df_youtube[df_youtube['title_lower'].str.contains(query, na=False)]
        youtube_results = youtube_results.sort_values(by='subscribers', ascending=False).head(limit_per_source)
        all_results.extend(youtube_results.to_dict(orient='records'))
    
    # Mezclar los resultados para que no aparezcan agrupados por fuente
    random.shuffle(all_results)
    
    return all_results

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('interes', '').strip().lower()
    if not query: return jsonify(cursos=[])
    
    cursos = search_and_combine(query)
    return jsonify(cursos=cursos)

@app.route('/recommend', methods=['POST'])
def recommend():
    interest_key = request.form.get('interest_modal', '')
    level = request.form.get('level_modal', '')
    
    interest_keywords = {
        'python': ['python'], 'web_development': ['html', 'css', 'javascript', 'web development'],
        'data_science': ['data science', 'analytics', 'machine learning'], 'marketing': ['marketing', 'seo'],
        'excel': ['excel'], 'design': ['graphic design', 'photoshop', 'illustrator'],
        'cybersecurity': ['cybersecurity', 'hacking'], 'ai': ['artificial intelligence', 'ia']
    }
    
    search_terms = interest_keywords.get(interest_key, [])
    if not search_terms: return jsonify(cursos=[])
    
    # Usamos el primer término de búsqueda como la consulta principal
    query = search_terms[0]
    
    cursos = search_and_combine(query)
    return jsonify(cursos=cursos)

@app.route('/free_courses', methods=['GET'])
def free_courses():
    all_free_results = []

    if not df_udemy.empty:
        udemy_free = df_udemy[df_udemy['price'] == 0].sort_values(by='subscribers', ascending=False).head(4)
        all_free_results.extend(udemy_free.to_dict(orient='records'))

    # Todos los cursos de courses2 y youtube se asumen gratuitos
    if not df_courses2.empty:
        all_free_results.extend(df_courses2.sample(n=min(len(df_courses2), 4)).to_dict(orient='records'))
        
    if not df_youtube.empty:
        all_free_results.extend(df_youtube.head(4).to_dict(orient='records'))
        
    random.shuffle(all_free_results)
    return jsonify(cursos=all_free_results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
