from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import random

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

def safe_load_and_process(path, column_map, default_source):
    """
    Carga un archivo CSV de forma ultra robusta, mapeando columnas de forma flexible
    y creando una tabla estandarizada sin fallar.
    """
    try:
        df_original = pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
        df_original.columns = df_original.columns.str.strip()
        print(f"Cargando {path}. Columnas originales encontradas: {list(df_original.columns)}")

        df_clean = pd.DataFrame()
        standard_columns = ['title', 'url', 'subscribers', 'price', 'source']

        for standard_col, possible_original_cols in column_map.items():
            for original_col in possible_original_cols:
                if original_col in df_original.columns:
                    df_clean[standard_col] = df_original[original_col]
                    break

        for col in standard_columns:
            if col not in df_clean.columns:
                df_clean[col] = default_source if col == 'source' else 0 if col in ['subscribers', 'price'] else ''
        
        df_clean = df_clean[standard_columns]
        df_clean['title'] = df_clean['title'].fillna('').astype(str)
        df_clean['url'] = df_clean['url'].fillna('').astype(str)
        df_clean['subscribers'] = pd.to_numeric(df_clean['subscribers'], errors='coerce').fillna(0).astype(int)
        df_clean['price'] = pd.to_numeric(df_clean['price'], errors='coerce').fillna(0).astype(int)
        df_clean['source'] = df_clean['source'].fillna(default_source).astype(str)

        print(f"Procesado {path}: {len(df_clean)} filas.")
        return df_clean

    except FileNotFoundError:
        print(f"ERROR CRÍTICO: Archivo no encontrado en {path}.")
    except Exception as e:
        print(f"ERROR INESPERADO al procesar {path}: {e}")
    return pd.DataFrame()

def load_data():
    """Carga y combina todas las fuentes de datos."""
    all_dfs = []

    udemy_map = {'title': ['course_title', 'title'], 'url': ['url'], 'subscribers': ['num_subscribers', 'subscribers'], 'price': ['price']}
    df_udemy = safe_load_and_process(os.path.join(basedir, "data", "udemy_online_education_courses_dataset.csv"), udemy_map, 'Udemy')
    if not df_udemy.empty:
        all_dfs.append(df_udemy)

    courses2_map = {'title': ['Course Name', 'title'], 'url': ['Course URL', 'url'], 'source': ['University', 'source']}
    df_courses2 = safe_load_and_process(os.path.join(basedir, "data", "courses_2.csv"), courses2_map, 'Coursera/edX')
    if not df_courses2.empty:
        all_dfs.append(df_courses2)

    youtube_tutorials = [
        {'title': 'Curso de Python desde Cero para Principiantes 2025', 'url': 'https://www.youtube.com/watch?v=nKPbfIU442g', 'subscribers': 1500000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso HTML y CSS Desde Cero 2025', 'url': 'https://www.youtube.com/watch?v=MJkdaVFHrto', 'subscribers': 950000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de JavaScript para Principiantes - Desde Cero', 'url': 'https://www.youtube.com/watch?v=z95mZodzlhI', 'subscribers': 1200000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de INTELIGENCIA ARTIFICIAL desde CERO', 'url': 'https://www.youtube.com/watch?v=s_wz9j-2-sI', 'subscribers': 600000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de Hacking Ético 2025 desde Cero', 'url': 'https://www.youtube.com/watch?v=GmyyI_G4z4o', 'subscribers': 800000, 'price': 0, 'source': 'YouTube'},
        {'title': 'CURSO DE MARKETING DIGITAL Gratis y Completo 2025', 'url': 'https://www.youtube.com/watch?v=9m5t-bV3Y6c', 'subscribers': 650000, 'price': 0, 'source': 'YouTube'}
    ]
    df_youtube = pd.DataFrame(youtube_tutorials)
    all_dfs.append(df_youtube)

    if not all_dfs:
        print("Error crítico: No se pudo cargar ninguna fuente de datos.")
        return pd.DataFrame()

    master_df = pd.concat(all_dfs, ignore_index=True)
    # CORRECCIÓN: Crear columnas en minúsculas para título Y fuente
    master_df['title_lower'] = master_df['title'].str.lower()
    master_df['source_lower'] = master_df['source'].str.lower()
    
    print("\nDIAGNÓSTICO FINAL DE CARGA:")
    print(master_df['source'].value_counts().head())
    excel_courses_count = master_df[master_df['title_lower'].str.contains('excel')].shape[0]
    print(f"Se encontraron {excel_courses_count} cursos que contienen 'excel'.")
    print(f"Carga de datos completa. Total de {len(master_df)} cursos cargados.\n")
    return master_df

master_df = load_data()

@app.route('/')
def home():
    return render_template('index.html')

def rank_by_relevance(df, query):
    """
    Calcula un puntaje de relevancia y ordena el DataFrame.
    Un puntaje más alto es mejor (la consulta es una parte más grande del título).
    """
    # Evitar división por cero si hay títulos vacíos
    df['relevance_score'] = len(query) / df['title_lower'].str.len().replace(0, 1)
    
    # Prioridad extra si la consulta aparece al principio del título.
    df['starts_with_bonus'] = df['title_lower'].str.startswith(query).astype(int) * 0.5
    
    df['final_score'] = df['relevance_score'] + df['starts_with_bonus']
    
    # Ordena por el nuevo puntaje final, eliminando el orden por suscriptores
    return df.sort_values(by='final_score', ascending=False)

def perform_search(query):
    """
    Realiza una búsqueda inteligente en el DataFrame maestro y la ordena por relevancia.
    """
    if master_df.empty or not query:
        return []
        
    # CORRECCIÓN: Buscar tanto en el título como en la fuente del curso
    results_df = master_df[
        master_df['title_lower'].str.contains(query, na=False) | 
        master_df['source_lower'].str.contains(query, na=False)
    ].copy()
    
    if results_df.empty:
        return []
        
    ranked_results = rank_by_relevance(results_df, query)
    
    return ranked_results.head(10).to_dict(orient='records')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('interes', '').strip().lower()
    cursos = perform_search(query)
    return jsonify(cursos=cursos)

@app.route('/recommend', methods=['POST'])
def recommend():
    interest_key = request.form.get('interest_modal', '')
    interest_keywords = {
        'python': ['python'], 'web_development': ['html', 'css', 'javascript', 'web development'],
        'data_science': ['data science', 'analytics', 'machine learning'], 'marketing': ['marketing', 'seo'],
        'excel': ['excel'], 'design': ['graphic design', 'photoshop', 'illustrator'],
        'cybersecurity': ['cybersecurity', 'hacking'], 'ai': ['artificial intelligence', 'ia']
    }
    search_terms = interest_keywords.get(interest_key, [])
    if not search_terms:
        return jsonify(cursos=[])
        
    query = search_terms[0]
    cursos = perform_search(query)
    return jsonify(cursos=cursos)

@app.route('/free_courses', methods=['GET'])
def free_courses():
    if master_df.empty:
        return jsonify(cursos=[])
        
    free_courses_df = master_df[master_df['price'] == 0].copy()
    
    if not free_courses_df.empty:
        shuffled_free_courses = free_courses_df.sample(frac=1).head(10)
        return jsonify(cursos=shuffled_free_courses.to_dict(orient='records'))
        
    return jsonify(cursos=[])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
