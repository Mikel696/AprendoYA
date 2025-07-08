from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import random

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

def build_coursera_url(path):
    """Construye una URL completa y válida para Coursera."""
    if not isinstance(path, str) or path.startswith('http'):
        return path
    return f"https://www.coursera.org{path}" if path.startswith('/learn/') else f"https://www.coursera.org/learn/{path}"

def safe_load_and_process(path, column_map, default_source, url_builder=None):
    """
    Carga un archivo CSV de forma ultra robusta, mapeando columnas de forma flexible
    y aplicando un constructor de URL si es necesario.
    """
    try:
        df_original = pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
        col_map_lower = {col.strip().lower(): col for col in df_original.columns}
        print(f"Cargando {path}. Columnas originales: {list(df_original.columns)}")

        df_clean = pd.DataFrame()
        standard_columns = ['title', 'url', 'subscribers', 'price', 'source']

        for standard_col, possible_cols in column_map.items():
            for col_variant in possible_cols:
                if col_variant.lower() in col_map_lower:
                    original_col_name = col_map_lower[col_variant.lower()]
                    df_clean[standard_col] = df_original[original_col_name]
                    break
        
        if url_builder and 'url' in df_clean.columns:
            df_clean['url'] = df_clean['url'].apply(url_builder)

        for col in standard_columns:
            if col not in df_clean.columns:
                df_clean[col] = default_source if col == 'source' else 0 if col in ['subscribers', 'price'] else ''
        
        df_clean = df_clean[standard_columns].fillna({'title': '', 'url': '', 'source': default_source, 'subscribers': 0, 'price': 0})
        print(f"Procesado {path}: {len(df_clean)} filas.")
        return df_clean

    except FileNotFoundError:
        print(f"ERROR CRÍTICO: Archivo no encontrado en {path}.")
    except Exception as e:
        print(f"ERROR INESPERADO al procesar {path}: {e}")
    return pd.DataFrame()

def load_all_data():
    """Carga y combina todas las fuentes de datos."""
    all_dfs = []

    udemy_map = {'title': ['course_title'], 'url': ['url'], 'subscribers': ['num_subscribers'], 'price': ['price']}
    df_udemy = safe_load_and_process(os.path.join(basedir, "data", "udemy_online_education_courses_dataset.csv"), udemy_map, 'Udemy')
    if not df_udemy.empty:
        all_dfs.append(df_udemy)

    courses2_map = {'title': ['Course Name'], 'url': ['Course URL'], 'source': ['University']}
    df_courses2 = safe_load_and_process(os.path.join(basedir, "data", "courses_2.csv"), courses2_map, 'Coursera/edX', url_builder=build_coursera_url)
    if not df_courses2.empty:
        all_dfs.append(df_courses2)
    
    free_courses_data = [
        {'title': 'Desarrollo Web Responsive (freeCodeCamp)', 'url': 'https://www.freecodecamp.org/learn/responsive-web-design/', 'source': 'freeCodeCamp', 'price': 0, 'subscribers': 1000000},
        {'title': 'Algoritmos y Estructuras de Datos en JavaScript (freeCodeCamp)', 'url': 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/', 'source': 'freeCodeCamp', 'price': 0, 'subscribers': 800000},
        {'title': 'Fundamentos de Marketing Digital (Google Actívate)', 'url': 'https://learndigital.withgoogle.com/activate/course/digital-marketing', 'source': 'Google Actívate', 'price': 0, 'subscribers': 700000},
        {'title': 'Computación en la Nube (Google Actívate)', 'url': 'https://learndigital.withgoogle.com/activate/course/cloud-computing', 'source': 'Google Actívate', 'price': 0, 'subscribers': 500000},
    ]
    all_dfs.append(pd.DataFrame(free_courses_data))

    youtube_tutorials = [
        {'title': 'Curso de Python desde Cero para Principiantes 2025', 'url': 'https://www.youtube.com/watch?v=nKPbfIU442g', 'source': 'YouTube', 'price': 0, 'subscribers': 1500000},
        {'title': 'Curso HTML y CSS Desde Cero 2025', 'url': 'https://www.youtube.com/watch?v=MJkdaVFHrto', 'source': 'YouTube', 'price': 0, 'subscribers': 950000},
        {'title': 'Curso de JavaScript para Principiantes - Desde Cero', 'url': 'https://www.youtube.com/watch?v=z95mZodzlhI', 'source': 'YouTube', 'price': 0, 'subscribers': 1200000},
        {'title': 'Curso de INTELIGENCIA ARTIFICIAL desde CERO', 'url': 'https://www.youtube.com/watch?v=s_wz9j-2-sI', 'source': 'YouTube', 'price': 0, 'subscribers': 600000},
        {'title': 'Curso de Hacking Ético 2025 desde Cero', 'url': 'https://www.youtube.com/watch?v=GmyyI_G4z4o', 'source': 'YouTube', 'price': 0, 'subscribers': 800000},
    ]
    all_dfs.append(pd.DataFrame(youtube_tutorials))

    if not all_dfs:
        return pd.DataFrame()

    master_df = pd.concat(all_dfs, ignore_index=True)
    master_df['title_lower'] = master_df['title'].str.lower()
    master_df['source_lower'] = master_df['source'].str.lower()
    
    print("\nDIAGNÓSTICO FINAL DE CARGA:")
    print(master_df['source'].value_counts())
    print(f"Carga de datos completa. Total de {len(master_df)} cursos cargados.\n")
    return master_df

master_df = load_all_data()

def rank_by_relevance(df, query):
    """Ordena los resultados por relevancia, dando prioridad a coincidencias en el título."""
    df['score'] = df['title_lower'].str.contains(query, na=False).astype(int) * 2
    df['precision'] = len(query) / df['title_lower'].str.len().replace(0, 1)
    df['final_score'] = df['score'] + df['precision']
    return df.sort_values(by='final_score', ascending=False)

def perform_search(query):
    """Realiza una búsqueda inteligente en título y fuente, y ordena por relevancia."""
    if master_df.empty or not query:
        return []
        
    mask = (master_df['title_lower'].str.contains(query, na=False)) | \
           (master_df['source_lower'].str.contains(query, na=False))
    results_df = master_df[mask].copy()
    
    if results_df.empty:
        return []
        
    ranked_results = rank_by_relevance(results_df, query)
    return ranked_results.head(10).to_dict(orient='records')

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
    interest_keywords = {
        'python': ['python'], 'web_development': ['html', 'css', 'javascript'],
        'data_science': ['data science', 'analytics'], 'marketing': ['marketing'],
        'excel': ['excel'], 'design': ['graphic design'],
        'cybersecurity': ['cybersecurity', 'hacking'], 'ai': ['artificial intelligence', 'ia']
    }
    query = interest_keywords.get(interest_key, [""])[0]
    cursos = perform_search(query)
    return jsonify(cursos=cursos)

@app.route('/free_courses', methods=['GET'])
def free_courses():
    """Devuelve una lista de cursos 100% gratuitos."""
    if master_df.empty:
        return jsonify(cursos=[])
    
    free_sources = ['freeCodeCamp', 'Google Actívate', 'YouTube']
    free_courses_df = master_df[master_df['source'].isin(free_sources)].copy()
    
    udemy_free = master_df[(master_df['source'] == 'Udemy') & (master_df['price'] == 0)]
    
    all_free = pd.concat([free_courses_df, udemy_free], ignore_index=True)
    
    shuffled_free = all_free.sample(frac=1).head(10)
    return jsonify(cursos=shuffled_free.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
