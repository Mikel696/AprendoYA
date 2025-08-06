from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)

# Obtenemos la ruta base de la aplicación
basedir = os.path.abspath(os.path.dirname(__file__))

def load_data():
    """
    Carga el archivo de datos final y pre-procesado con las calificaciones de estrellas.
    """
    try:
        # La ruta al archivo de datos final en la carpeta 'data'
        path = os.path.join(basedir, "data", "cursos_calificados_final.csv")
        df = pd.read_csv(path, encoding='utf-8')
        # Creamos una columna en minúsculas para facilitar las búsquedas
        df['title_lower'] = df['course_title'].str.lower()
        print(f"Archivo 'cursos_calificados_final.csv' cargado exitosamente con {len(df)} cursos.")
        return df
    except Exception as e:
        print(f"ERROR CRÍTICO AL CARGAR 'cursos_calificados_final.csv': {e}")
        # Si hay un error, devolvemos un DataFrame vacío para que la app no se caiga
        return pd.DataFrame()

# Cargamos el dataframe maestro una sola vez al iniciar la aplicación
master_df = load_data()

def perform_search(query, level=None):
    """
    Realiza una búsqueda con un ranking que combina relevancia del título, nivel y la calificación de estrellas.
    """
    if master_df.empty or not query:
        return []
    
    print(f"\n--- BÚSQUEDA AVANZADA PARA: '{query}' (Nivel: {level}) ---")
    
    # Buscamos cursos cuyo título contenga la consulta del usuario
    mask = master_df['title_lower'].str.contains(query, na=False)
    results_df = master_df[mask].copy()
    
    print(f"Resultados encontrados antes de ranking: {len(results_df)}")
    if results_df.empty:
        return []
        
    # --- CÁLCULO DE RANKING HÍBRIDO ---
    
    # 1. Puntuación de Relevancia del Título
    results_df['relevance_score'] = results_df['title_lower'].apply(lambda x: len(query) / len(x) if x and len(x) > 0 else 0)
    
    # 2. Puntuación de Nivel (Principiante, Intermedio)
    level_score = pd.Series(0, index=results_df.index)
    if level == 'beginner':
        beginner_keywords = ['principiantes', 'cero', 'introduction', 'básico', 'inicial']
        for keyword in beginner_keywords:
            level_score += results_df['title_lower'].str.contains(keyword, na=False).astype(int)
    elif level == 'intermediate':
        intermediate_keywords = ['intermedio', 'avanzado', 'completo', 'masterclass', 'total']
        for keyword in intermediate_keywords:
            level_score += results_df['title_lower'].str.contains(keyword, na=False).astype(int)
    results_df['level_score'] = level_score
    
    # 3. Puntuación de Calidad/Popularidad (BASADA EN ESTRELLAS)
    # Normalizamos la calificación de 1-5 estrellas a un valor entre 0 y 1 para que sea comparable.
    if len(results_df) > 1:
        scaler = MinMaxScaler()
        results_df['quality_score'] = scaler.fit_transform(results_df[['star_rating']]).flatten()
    else:
        results_df['quality_score'] = 0.5
        
    # 4. Puntuación Final (Combinamos todo, dando más peso a la relevancia y calidad)
    results_df['final_score'] = (results_df['relevance_score'] * 0.4) + \
                                (results_df['level_score'] * 0.2) + \
                                (results_df['quality_score'] * 0.4)
    
    # Ordenamos los resultados por la puntuación final
    ranked_results = results_df.sort_values(by='final_score', ascending=False)
    
    print(f"Top 5 resultados por puntuación final:")
    print(ranked_results[['course_title', 'site', 'star_rating', 'final_score']].head())
    
    # Renombramos 'star_rating' a 'num_subscribers' para no tener que cambiar el HTML del frontend.
    # El frontend mostrará la calificación de estrellas (ej: ⭐ 5) en lugar de un número de suscriptores.
    return ranked_results.head(7).rename(columns={'star_rating': 'num_subscribers'}).to_dict(orient='records')

# --- Rutas de la Aplicación Web (Endpoints) ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('interes', '').strip().lower()
    cursos = perform_search(query)
    return jsonify(cursos=cursos)

@app.route('/recommend', methods=['POST'])
def recommend():
    interest_key = request.form.get('interest_modal', '')
    level = request.form.get('level_modal', '')
    interest_keywords = {
        'python': ['python'], 'web_development': ['html', 'css', 'javascript'],
        'data_science': ['data science', 'analytics'], 'marketing': ['marketing'],
        'excel': ['excel'], 'design': ['diseño gráfico'],
        'cybersecurity': ['cybersecurity', 'hacking'], 'ai': ['inteligencia artificial', 'ia']
    }
    query = interest_keywords.get(interest_key, [""])[0]
    cursos = perform_search(query, level=level)
    return jsonify(cursos=cursos)

@app.route('/free_courses', methods=['GET'])
def free_courses():
    if master_df.empty:
        return jsonify(cursos=[])
    
    # Mostramos los cursos de 5 estrellas como una selección de cursos populares.
    free_selection = master_df[master_df['star_rating'] == 5].sample(n=10, replace=True)
    return jsonify(cursos=free_selection.rename(columns={'star_rating': 'num_subscribers'}).to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')