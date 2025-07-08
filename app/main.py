from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

def load_and_prepare_udemy(path):
    """Carga y procesa el dataset de Udemy."""
    try:
        df = pd.read_csv(path)
        print(f"Cargando {path}. Columnas encontradas: {list(df.columns)}")
        df = df.rename(columns={'course_title': 'title', 'num_subscribers': 'subscribers'})
        df['source'] = 'Udemy'
        df = df[['title', 'url', 'subscribers', 'price', 'source']]
        df['title'] = df['title'].astype(str)
        df['url'] = df['url'].astype(str)
        print(f"Procesado {path}: {len(df)} filas.")
        return df
    except FileNotFoundError:
        print(f"ADVERTENCIA: Archivo no encontrado en {path}. Se omitirá.")
    except Exception as e:
        print(f"ERROR al procesar {path}: {e}")
    return None

def load_and_prepare_courses2(path):
    """Carga y procesa el dataset de Coursera/edX."""
    try:
        df = pd.read_csv(path)
        print(f"Cargando {path}. Columnas encontradas: {list(df.columns)}")
        df.columns = df.columns.str.strip()
        df = df.rename(columns={'Course Name': 'title', 'Course URL': 'url', 'University': 'source'})
        df['subscribers'] = 0
        df['price'] = 0
        df = df[['title', 'url', 'subscribers', 'price', 'source']]
        df['title'] = df['title'].astype(str)
        df['url'] = df['url'].astype(str)
        print(f"Procesado {path}: {len(df)} filas.")
        return df
    except FileNotFoundError:
        print(f"ADVERTENCIA: Archivo no encontrado en {path}. Se omitirá.")
    except Exception as e:
        print(f"ERROR al procesar {path}: {e}")
    return None

def load_data():
    """Carga y combina todas las fuentes de datos."""
    all_dfs = []
    
    # Fuente 1: Udemy
    df_udemy = load_and_prepare_udemy(os.path.join("app", "data", "udemy_online_education_courses_dataset.csv"))
    if df_udemy is not None:
        all_dfs.append(df_udemy)

    # Fuente 2: Coursera/edX
    df_courses2 = load_and_prepare_courses2(os.path.join("app", "data", "courses_2.csv"))
    if df_courses2 is not None:
        all_dfs.append(df_courses2)

    # Fuente 3: YouTube
    youtube_tutorials = [
        {'title': 'Curso de Python desde Cero para Principiantes 2024', 'url': 'https://www.youtube.com/watch?v=nKPbfIU442g', 'subscribers': 1500000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Aprende HTML y CSS - Curso Completo Desde Cero 2024', 'url': 'https://www.youtube.com/watch?v=MJkdaVFHrto', 'subscribers': 950000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de JavaScript desde Cero para Principiantes', 'url': 'https://www.youtube.com/watch?v=z95mZodzlhI', 'subscribers': 1200000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de Inteligencia Artificial para Principiantes', 'url': 'https://www.youtube.com/watch?v=iX_on3hZ_q8', 'subscribers': 550000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso de Ciberseguridad y Hacking Ético desde Cero', 'url': 'https://www.youtube.com/watch?v=GmyyI_G4z4o', 'subscribers': 800000, 'price': 0, 'source': 'YouTube'},
        {'title': 'Curso Completo de Marketing Digital Desde Cero', 'url': 'https://www.youtube.com/watch?v=9m5t-bV3Y6c', 'subscribers': 650000, 'price': 0, 'source': 'YouTube'}
    ]
    df_youtube = pd.DataFrame(youtube_tutorials)
    all_dfs.append(df_youtube)
    print(f"Lista de tutoriales de YouTube cargada: {len(df_youtube)} filas.")

    if not all_dfs:
        print("Error crítico: No se pudo cargar ninguna fuente de datos.")
        return pd.DataFrame()

    master_df = pd.concat(all_dfs, ignore_index=True)
    
    # Limpieza Final
    master_df['title'] = master_df['title'].fillna('')
    master_df['title_lower'] = master_df['title'].str.lower()
    master_df['subscribers'] = pd.to_numeric(master_df['subscribers'], errors='coerce').fillna(0).astype(int)
    
    print(f"Carga de datos completa. Total de {len(master_df)} cursos cargados en el DataFrame maestro.")
    return master_df

master_df = load_data()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    if master_df.empty: return jsonify({"error": "Dataset no disponible"}), 500
    query = request.form.get('interes', '').strip().lower()
    if not query: return jsonify(cursos=[])
    resultados = master_df[master_df['title_lower'].str.contains(query, na=False)]
    cursos = resultados.sort_values(by='subscribers', ascending=False).head(10).to_dict(orient='records')
    return jsonify(cursos=cursos)

@app.route('/recommend', methods=['POST'])
def recommend():
    if master_df.empty: return jsonify({"error": "Dataset no disponible"}), 500
    interest_key = request.form.get('interest_modal', '')
    level = request.form.get('level_modal', '')
    interest_keywords = {
        'python': ['python'], 'web_development': ['html', 'css', 'javascript', 'web development'],
        'data_science': ['data science', 'analytics', 'machine learning'], 'marketing': ['marketing', 'seo'],
        'excel': ['excel'], 'design': ['graphic design', 'photoshop', 'illustrator'],
        'cybersecurity': ['cybersecurity', 'hacking'], 'ai': ['artificial intelligence', 'ia']
    }
    level_keywords = {'beginner': ['beginner', 'cero', 'básico'], 'intermediate': ['intermediate', 'complete', 'avanzado']}
    search_terms = interest_keywords.get(interest_key, [])
    if not search_terms: return jsonify(cursos=[])
    interest_regex = '|'.join(search_terms)
    results_df = master_df[master_df['title_lower'].str.contains(interest_regex, na=False)].copy()
    if level in level_keywords:
        level_regex = '|'.join(level_keywords[level])
        level_specific_df = results_df[results_df['title_lower'].str.contains(level_regex, na=False)]
        if not level_specific_df.empty: results_df = level_specific_df
    cursos = results_df.sort_values(by='subscribers', ascending=False).head(10).to_dict(orient='records')
    return jsonify(cursos=cursos)

@app.route('/free_courses', methods=['GET'])
def free_courses():
    if master_df.empty: return jsonify({"error": "Dataset no disponible"}), 500
    free_courses_df = master_df[master_df['price'] == 0]
    cursos = free_courses_df.sort_values(by='subscribers', ascending=False).head(10).to_dict(orient='records')
    return jsonify(cursos=cursos)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
