from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

def get_topics_from_keywords():
    """
    Genera una lista de temas a partir de las palabras clave de la lógica de calificación.
    """
    # Esta es una selección curada de las palabras clave más importantes
    # para usar en el menú desplegable.
    topics_dict = {
        'python': 'Python', 'javascript': 'JavaScript', 'java': 'Java', 'c#': 'C#',
        'html': 'HTML & CSS', 'sql': 'SQL', 'react': 'React', 'angular': 'Angular',
        'vue': 'Vue.js', 'node.js': 'Node.js', 'data science': 'Ciencia de Datos',
        'machine learning': 'Machine Learning', 'inteligencia artificial': 'Inteligencia Artificial',
        'excel': 'Excel', 'power bi': 'Power BI', 'marketing': 'Marketing Digital',
        'seo': 'SEO', 'hacking': 'Ethical Hacking', 'ciberseguridad': 'Ciberseguridad',
        'aws': 'AWS', 'azure': 'Azure', 'docker': 'Docker', 'diseño gráfico': 'Diseño Gráfico',
        'photoshop': 'Photoshop', 'figma': 'Figma', 'finanzas': 'Finanzas', 'trading': 'Trading'
    }
    # Creamos una lista de diccionarios para usarla fácilmente en la plantilla
    return [{'value': key, 'name': name} for key, name in topics_dict.items()]

def load_data():
    """
    Carga el archivo de datos final y pre-procesado.
    """
    try:
        path = os.path.join(basedir, "data", "cursos_calificados_final.csv")
        df = pd.read_csv(path, encoding='utf-8')
        df['title_lower'] = df['course_title'].str.lower()
        print(f"Archivo 'cursos_calificados_final.csv' cargado con {len(df)} cursos.")
        return df
    except Exception as e:
        print(f"ERROR CRÍTICO AL CARGAR 'cursos_calificados_final.csv': {e}")
        return pd.DataFrame()

master_df = load_data()
# Generamos la lista de temas una sola vez
TOPICS_LIST = get_topics_from_keywords()

def perform_search(query, level=None):
    """
    Realiza una búsqueda con el ranking por estrellas.
    """
    if master_df.empty or not query:
        return []
    
    mask = master_df['title_lower'].str.contains(query, na=False)
    results_df = master_df[mask].copy()
    
    if results_df.empty:
        return []
        
    level_score = pd.Series(0, index=results_df.index)
    if level == 'beginner':
        level_score += results_df['title_lower'].str.contains('principiantes|básico|cero|inicial', na=False, regex=True).astype(int)
    
    results_df['relevance_score'] = results_df['title_lower'].apply(lambda x: len(query) / len(x) if x and len(x) > 0 else 0)
    results_df['level_score'] = level_score
    
    scaler = MinMaxScaler()
    results_df['quality_score'] = scaler.fit_transform(results_df[['star_rating']]).flatten()
    
    results_df['final_score'] = (results_df['relevance_score'] * 0.4) + \
                                (results_df['quality_score'] * 0.5) - \
                                (results_df['level_score'] * 0.1) # Penalizamos un poco los cursos básicos en búsquedas generales
    
    ranked_results = results_df.sort_values(by='final_score', ascending=False)
    return ranked_results.head(9).rename(columns={'star_rating': 'num_subscribers'}).to_dict(orient='records')

def generate_learning_path(query):
    """
    Crea una ruta de aprendizaje estructurada por estrellas.
    """
    if master_df.empty or not query:
        return {}
    mask = master_df['title_lower'].str.contains(query, na=False)
    relevant_courses = master_df[mask]
    if relevant_courses.empty:
        return {}
    sorted_courses = relevant_courses.sort_values(by='star_rating', ascending=True)
    fundamentos = sorted_courses[sorted_courses['star_rating'] <= 2].head(2).to_dict(orient='records')
    desarrollo = sorted_courses[sorted_courses['star_rating'].between(3, 4)].head(3).to_dict(orient='records')
    especializacion = sorted_courses[sorted_courses['star_rating'] == 5].head(2).to_dict(orient='records')
    return {'fundamentos': fundamentos, 'desarrollo': desarrollo, 'especializacion': especializacion}

@app.route('/')
def home():
    # Ahora pasamos la lista de temas a la plantilla
    return render_template('index.html', topics=TOPICS_LIST)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('interes', '').strip().lower()
    cursos = perform_search(query)
    return jsonify(cursos=cursos)

@app.route('/recommend', methods=['POST'])
def recommend():
    query = request.form.get('interest_modal', '')
    level = request.form.get('level_modal', '')
    cursos = perform_search(query, level=level)
    return jsonify(cursos=cursos)

@app.route('/popular_courses')
def popular_courses():
    if master_df.empty:
        return jsonify(cursos=[])
    popular_selection = master_df[master_df['star_rating'] == 5].sample(n=9, replace=True)
    return jsonify(cursos=popular_selection.rename(columns={'star_rating': 'num_subscribers'}).to_dict(orient='records'))

@app.route('/learning_path', methods=['POST'])
def learning_path_route():
    query = request.form.get('query', '').strip().lower()
    if not query:
        return jsonify({'error': 'No se proporcionó una consulta'}), 400
    path = generate_learning_path(query)
    return jsonify(path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')