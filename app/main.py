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

        # Crea un nuevo DataFrame limpio con columnas estándar
        df_clean = pd.DataFrame()
        standard_columns = ['title', 'url', 'subscribers', 'price', 'source']

        # Mapea columnas una por una de forma segura
        for standard_col, possible_original_cols in column_map.items():
            for original_col in possible_original_cols:
                if original_col in df_original.columns:
                    df_clean[standard_col] = df_original[original_col]
                    break  # Pasa a la siguiente columna estándar

        # Asegura que todas las columnas estándar existan, rellenando si es necesario
        for col in standard_columns:
            if col not in df_clean.columns:
                if col == 'source':
                    df_clean[col] = default_source
                elif col in ['subscribers', 'price']:
                    df_clean[col] = 0
                else:
                    df_clean[col] = ''
        
        # Asegura el orden y los tipos de datos correctos
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
    """Carga y combina todas las fuentes de datos usando la nueva función robusta."""
    all_dfs = []

    # Mapa de columnas para el archivo de Udemy
    udemy_map = {
        'title': ['course_title', 'title'],
        'url': ['url'],
        'subscribers': ['num_subscribers', 'subscribers'],
        'price': ['price']
    }
    df_udemy = safe_load_and_process(os.path.join(basedir, "data", "udemy_online_education_courses_dataset.csv"), udemy_map, 'Udemy')
    if not df_udemy.empty:
        all_dfs.append(df_udemy)

    # Mapa de columnas para el archivo de Coursera/edX
    courses2_map = {
        'title': ['Course Name', 'title'],
        'url': ['Course URL', 'url'],
        'source': ['University', 'source']
    }
    df_courses2 = safe_load_and_process(os.path.join(basedir, "data", "courses_2.csv"), courses2_map, 'Coursera/edX')
    if not df_courses2.empty:
        all_dfs.append(df_courses2)

    # Carga de datos de YouTube
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
    print(f"Lista de tutoriales de YouTube cargada: {len(df_youtube)} filas.")

    if not all_dfs:
        print("Error crítico: No se pudo cargar ninguna fuente de datos.")
        return pd.DataFrame()

    master_df = pd.concat(all_dfs, ignore_index=True)
    master_df['title_lower'] = master_df['title'].str.lower()
    
    print("\nDIAGNÓSTICO FINAL DE CARGA:")
    print(master_df['source'].value_counts())
    excel_courses_count = master_df[master_df['title_lower'].str.contains('excel')].shape[0]
    print(f"Se encontraron {excel_courses_count} cursos que contienen 'excel'.")
    print(f"Carga de datos completa. Total de {len(master_df)} cursos cargados.\n")
    return master_df

# Cargar los datos y definir las rutas de la aplicación
master_df = load_data()

@app.route('/')
def home():
    return render_template('index.html')

def search_and_combine(query, limit_per_source=4):
    """Busca en cada fuente de datos y combina los resultados de forma justa."""
    all_results = []
    
    # Dividir el DataFrame maestro por fuente para la búsqueda
    sources = master_df['source'].unique()
    for source_name in sources:
        df_source = master_df[master_df['source'] == source_name]
        results = df_source[df_source['title_lower'].str.contains(query, na=False)]
        
        # Ordenar por suscriptores si hay, si no, tomar muestra aleatoria
        if 'subscribers' in results.columns and results['subscribers'].sum() > 0:
            results = results.sort_values(by='subscribers', ascending=False)
        else:
            results = results.sample(frac=1) # Mezclar aleatoriamente
            
        all_results.extend(results.head(limit_per_source).to_dict(orient='records'))

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
    interest_keywords = {
        'python': ['python'], 'web_development': ['html', 'css', 'javascript', 'web development'],
        'data_science': ['data science', 'analytics', 'machine learning'], 'marketing': ['marketing', 'seo'],
        'excel': ['excel'], 'design': ['graphic design', 'photoshop', 'illustrator'],
        'cybersecurity': ['cybersecurity', 'hacking'], 'ai': ['artificial intelligence', 'ia']
    }
    search_terms = interest_keywords.get(interest_key, [])
    if not search_terms: return jsonify(cursos=[])
    query = search_terms[0]
    cursos = search_and_combine(query)
    return jsonify(cursos=cursos)

@app.route('/free_courses', methods=['GET'])
def free_courses():
    free_courses_df = master_df[master_df['price'] == 0]
    # Para ser justos, tomamos una muestra de cursos gratuitos de cada fuente
    sources = free_courses_df['source'].unique()
    all_free_results = []
    for source_name in sources:
        df_source = free_courses_df[free_courses_df['source'] == source_name]
        results = df_source.sort_values(by='subscribers', ascending=False).head(4)
        all_free_results.extend(results.to_dict(orient='records'))
        
    random.shuffle(all_free_results)
    return jsonify(cursos=all_free_results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

