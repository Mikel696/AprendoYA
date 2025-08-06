from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import random
from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

def load_all_data():
    """
    Carga y combina los dos archivos CSV con la nueva estructura de columnas,
    manejando explícitamente la codificación de texto.
    """
    all_dfs = []
    print("--- INICIANDO CARGA DE DATOS CON NUEVA ESTRUCTURA ---")

    files_to_load = [
        "udemy_online_education_courses_dataset.csv",
        "courses_2.csv"
    ]

    for file_name in files_to_load:
        try:
            path = os.path.join(basedir, "data", file_name)
            # --- CORRECCIÓN DEFINITIVA: Se especifica la codificación 'latin1' ---
            df = pd.read_csv(path, encoding='latin1', on_bad_lines='skip')
            df.columns = df.columns.str.strip().str.lower()
            print(f"[{file_name}] Columnas encontradas: {list(df.columns)}")
            
            required_cols = ['course_title', 'url', 'num_subscribers', 'site']
            if all(col in df.columns for col in required_cols):
                all_dfs.append(df[required_cols])
                print(f"[{file_name}] Carga exitosa: {len(df)} filas.")
            else:
                print(f"[{file_name}] ERROR: Faltan columnas requeridas. Se omitirá.")

        except Exception as e:
            print(f"[{file_name}] ERROR AL CARGAR: {e}")

    if not all_dfs:
        print("--- ERROR CRÍTICO: NINGUNA FUENTE DE DATOS CARGADA ---")
        return pd.DataFrame()

    master_df = pd.concat(all_dfs, ignore_index=True)
    
    master_df.fillna({'course_title': '', 'url': '', 'site': 'Desconocida'}, inplace=True)
    master_df['num_subscribers'] = pd.to_numeric(master_df['num_subscribers'], errors='coerce').fillna(0).astype(int)
    master_df['title_lower'] = master_df['course_title'].str.lower()
    
    print("\n--- DIAGNÓSTICO FINAL DE CARGA ---")
    print(master_df['site'].value_counts())
    print(f"TOTAL DE CURSOS CARGADOS: {len(master_df)}")
    print("-------------------------------------\n")
    return master_df

master_df = load_all_data()

def perform_search(query, level=None):
    """
    Realiza una búsqueda con un sistema de ranking híbrido avanzado que considera
    relevancia, popularidad y nivel del curso.
    """
    if master_df.empty or not query:
        return []
    
    print(f"\n--- INICIANDO BÚSQUEDA AVANZADA PARA: '{query}' (Nivel: {level}) ---")
    
    mask = master_df['title_lower'].str.contains(query, na=False)
    results_df = master_df[mask].copy()
    
    print(f"Resultados encontrados antes de ranking: {len(results_df)}")
    if results_df.empty:
        return []
        
    # --- CÁLCULO DE RANKING HÍBRIDO AVANZADO ---
    
    # 1. Puntuación de Relevancia del Título
    results_df['relevance_score'] = results_df['title_lower'].apply(lambda x: len(query) / len(x) if x else 0)
    
    # 2. Puntuación de Nivel (si se especifica)
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
    
    # 3. Puntuación de Popularidad (suscriptores normalizados)
    if len(results_df) > 1:
        scaler = MinMaxScaler()
        results_df['popularity_score'] = scaler.fit_transform(results_df[['num_subscribers']]).flatten()
    else:
        results_df['popularity_score'] = 0.5 # Valor neutral si solo hay un resultado

    # 4. Puntuación Final (combinando todo, dando más peso a la relevancia y al nivel)
    results_df['final_score'] = (results_df['relevance_score'] * 0.5) + \
                                (results_df['level_score'] * 0.3) + \
                                (results_df['popularity_score'] * 0.2)
    
    ranked_results = results_df.sort_values(by='final_score', ascending=False)
    
    print(f"Top 5 resultados por puntuación final:")
    print(ranked_results[['course_title', 'site', 'final_score']].head())
    
    return ranked_results.head(7).to_dict(orient='records')

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
    level = request.form.get('level_modal', '') # Capturamos el nivel
    interest_keywords = {
        'python': ['python'], 'web_development': ['html', 'css', 'javascript'],
        'data_science': ['data science', 'analytics'], 'marketing': ['marketing'],
        'excel': ['excel'], 'design': ['graphic design'],
        'cybersecurity': ['cybersecurity', 'hacking'], 'ai': ['artificial intelligence', 'ia']
    }
    query = interest_keywords.get(interest_key, [""])[0]
    # Pasamos el nivel a la función de búsqueda
    cursos = perform_search(query, level=level)
    return jsonify(cursos=cursos)

@app.route('/free_courses', methods=['GET'])
def free_courses():
    if master_df.empty:
        return jsonify(cursos=[])
    
    shuffled_courses = master_df.sample(frac=1).head(10)
    return jsonify(cursos=shuffled_courses.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

# --- INICIO DEL NUEVO CÓDIGO PARA LA RUTA DE APRENDIZAJE ---

def generate_learning_path(query):
    """
    Analiza la base de datos para generar una ruta de aprendizaje estructurada
    basada en una consulta de búsqueda.
    """
    if master_df.empty or not query:
        return {}

    print(f"\n--- GENERANDO RUTA DE APRENDIZAJE PARA: '{query}' ---")

    # --- 1. Definir palabras clave para cada nivel ---
    beginner_keywords = ['principiantes', 'cero', 'introduction', 'básico', 'inicial', 'beginner']
    intermediate_keywords = ['completo', 'total', 'masterclass', 'bootcamp']
    
    # Palabras clave de especialización (esto puede crecer mucho)
    # Ejemplo para 'python'
    specialization_keywords = {
        'python': ['django', 'flask', 'data science', 'machine learning', 'api', 'pandas', 'numpy'],
        'web_development': ['react', 'vue', 'angular', 'backend', 'frontend', 'fullstack', 'node.js'],
        'data_science': ['machine learning', 'deep learning', 'tableau', 'power bi', 'big data']
    }

    # --- 2. Función auxiliar para buscar y clasificar cursos ---
    def find_courses(keywords, is_beginner=False, is_specialization=False, main_query=""):
        # La máscara base siempre requiere la consulta principal en el título
        base_mask = master_df['title_lower'].str.contains(main_query, na=False)
        
        # Combinar palabras clave en un patrón de búsqueda regex
        keyword_pattern = '|'.join(keywords)
        keyword_mask = master_df['title_lower'].str.contains(keyword_pattern, na=False)

        if is_beginner:
            # Para principiantes, buscamos el tema Y una palabra clave de principiante
            final_mask = base_mask & keyword_mask
        elif is_specialization:
            # Para especialización, buscamos el tema Y una palabra clave de especialización
             final_mask = base_mask & keyword_mask
        else:
            # Para intermedio/desarrollo, buscamos el tema y palabras clave intermedias,
            # pero EXCLUIMOS los cursos que ya son de principiantes.
            beginner_pattern = '|'.join(beginner_keywords)
            not_beginner_mask = ~master_df['title_lower'].str.contains(beginner_pattern, na=False)
            final_mask = base_mask & keyword_mask & not_beginner_mask

        # Si no se encuentran cursos con las palabras clave específicas, 
        # nos quedamos con los que solo contienen el tema principal (para intermedio).
        if not is_beginner and not is_specialization and master_df[final_mask].empty:
             final_mask = base_mask & not_beginner_mask

        results = master_df[final_mask]
        # Ordenamos por popularidad (número de suscriptores) para obtener los mejores
        return results.sort_values(by='num_subscribers', ascending=False).head(3).to_dict(orient='records')

    # --- 3. Construir la ruta ---
    learning_path = {
        "fundamentos": find_courses(beginner_keywords, is_beginner=True, main_query=query),
        "desarrollo": find_courses(intermediate_keywords, main_query=query)
    }

    # Búsqueda de especializaciones
    spec_keywords = specialization_keywords.get(query, [])
    if spec_keywords:
        learning_path["especializacion"] = find_courses(spec_keywords, is_specialization=True, main_query=query)
    else:
        # Si no hay palabras clave de especialización definidas, dejamos la sección vacía
        learning_path["especializacion"] = []


    print(f"Ruta generada: {len(learning_path['fundamentos'])} fundamentos, {len(learning_path['desarrollo'])} desarrollo, {len(learning_path['especializacion'])} especialización.")
    return learning_path


@app.route('/learning_path', methods=['POST'])
def learning_path():
    """
    Endpoint para generar la ruta de aprendizaje.
    """
    query = request.form.get('query', '').strip().lower()
    path_data = generate_learning_path(query)
    return jsonify(path_data)

# --- FIN DEL NUEVO CÓDIGO ---
