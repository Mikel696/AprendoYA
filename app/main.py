from flask import Flask, render_template, request, jsonify, session, make_response
import pandas as pd
import os
import csv
from sklearn.preprocessing import MinMaxScaler
from werkzeug.security import generate_password_hash, check_password_hash
import json # Asegurarse de que json esté importado
import threading
import datetime

users_file_lock = threading.Lock()

app = Flask(__name__)
app.secret_key = os.urandom(24) # Clave secreta para la gestión de sesiones
basedir = os.path.abspath(os.path.dirname(__file__))
USERS_FILE_PATH = os.path.join(basedir, "data", "users.csv")

def get_topics_from_keywords():
    """
    Genera una lista de temas a partir de las palabras clave de la lógica de calificación
    para poblar el menú desplegable de recomendaciones.
    """
    topics_dict = {
        'python': 'Python', 'javascript': 'JavaScript', 'java': 'Java', 'c#': 'C#',
        'html': 'HTML & CSS', 'sql': 'SQL', 'react': 'React', 'angular': 'Angular',
        'vue': 'Vue.js', 'node.js': 'Node.js', 'data science': 'Ciencia de Datos',
        'machine learning': 'Machine Learning', 'inteligencia artificial': 'Inteligencia Artificial',
        'excel': 'Excel', 'power bi': 'Power BI', 'marketing': 'Marketing Digital',
        'seo': 'SEO', 'hacking': 'Ethical Hacking', 'ciberseguridad': 'Ciberseguridad',
        'aws': 'AWS', 'azure': 'Azure', 'docker': 'Docker', 'diseño gráfico': 'Diseño Gráfico',
        'photoshop': 'Photoshop', 'figma': 'Figma', 'finanzas': 'Finanzas', 'trading': 'Trading',
        'unity': 'Unity', 'blender': 'Blender', 'contabilidad': 'Contabilidad'
    }
    return [{'value': key, 'name': name} for key, name in topics_dict.items()]

def load_data():
    """
    Carga el archivo de datos final y pre-procesado con las calificaciones de estrellas.
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

def initialize_users_file():
    """
    Verifica si el archivo de usuarios existe y, si no, lo crea con una cabecera.
    """
    with users_file_lock: # Bloquear el archivo durante la inicialización
        if not os.path.exists(USERS_FILE_PATH):
            with open(USERS_FILE_PATH, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['email', 'password'])
            print(f"Archivo '{os.path.basename(USERS_FILE_PATH)}' no encontrado. Se ha creado uno nuevo.")

master_df = load_data()
TOPICS_LIST = get_topics_from_keywords()
initialize_users_file()

def perform_search(query, level=None):
    """
    Realiza una búsqueda con el ranking por estrellas, relevancia y nivel.
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
    
    results_df['final_score'] = (results_df['relevance_score'] * 0.4) + (results_df['quality_score'] * 0.5) - (results_df['level_score'] * 0.1)
    
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

# Definir la ruta al archivo de artículos del blog
BLOG_ARTICLES_FILE_PATH = os.path.join(basedir, "data", "blog_articles.json")

def load_blog_articles():
    try:
        with open(BLOG_ARTICLES_FILE_PATH, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        print(f"Archivo '{os.path.basename(BLOG_ARTICLES_FILE_PATH)}' cargado con {len(articles)} artículos.")
        return articles
    except FileNotFoundError:
        print(f"Archivo '{os.path.basename(BLOG_ARTICLES_FILE_PATH)}' no encontrado. Se devolverá una lista vacía.")
        return []
    except json.JSONDecodeError:
        print(f"Error al decodificar JSON en '{os.path.basename(BLOG_ARTICLES_FILE_PATH)}'. Se devolverá una lista vacía.")
        return []

BLOG_ARTICLES = load_blog_articles()

# --- Rutas de la Aplicación ---

@app.route('/')
def home():
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

# --- Rutas del Blog ---
@app.route('/api/blog/articles')
def get_blog_articles_summary():
    summary_articles = []
    for article in BLOG_ARTICLES:
        summary_articles.append({
            'id': article['id'],
            'title': article['title'],
            'summary': article['summary']
        })
    return jsonify(articles=summary_articles)

@app.route('/api/blog/article/<string:article_id>')
def get_blog_article(article_id):
    for article in BLOG_ARTICLES:
        if article['id'] == article_id:
            return jsonify(article)
    return jsonify({'message': 'Artículo no encontrado'}), 404

# --- Rutas de Autenticación ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Faltan datos'}), 400

    with users_file_lock: # Bloquear el archivo durante la lectura y escritura
        # Verificar si el usuario ya existe
        try:
            with open(USERS_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row and row[0] == email:
                        return jsonify({'message': 'El correo ya está registrado'}), 409
        except FileNotFoundError:
            # Esto no debería ocurrir gracias a initialize_users_file(), pero es una salvaguarda.
            pass

        # Guardar nuevo usuario
        hashed_password = generate_password_hash(password)
        with open(USERS_FILE_PATH, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([email, hashed_password])
    
    session['email'] = email
    return jsonify({'message': 'Registro exitoso', 'email': email}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    remember_me = data.get('remember_me', False) # Nuevo: obtener el estado de "recordarme"

    if not email or not password:
        return jsonify({'message': 'Faltan datos'}), 400

    with users_file_lock: # Bloquear el archivo durante la lectura
        try:
            with open(USERS_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                header = next(reader, None) # Leer cabecera de forma segura
                if not header:
                    return jsonify({'message': 'Usuario no encontrado'}), 404

                for row in reader:
                    if row and row[0] == email:
                        if check_password_hash(row[1], password):
                            session['email'] = email
                            response = make_response(jsonify({'message': 'Inicio de sesión exitoso', 'email': email}), 200)
                            if remember_me:
                                # Establecer una cookie de larga duración (ej. 30 días)
                                expires = datetime.datetime.now() + datetime.timedelta(days=30)
                                response.set_cookie('remember_me_email', email, expires=expires, httponly=True, secure=True, samesite='Lax')
                            return response
                        else:
                            return jsonify({'message': 'Contraseña incorrecta'}), 401
            
            return jsonify({'message': 'Usuario no encontrado'}), 404
        except FileNotFoundError:
            # Esto no debería ocurrir gracias a initialize_users_file()
            return jsonify({'message': 'Error interno del servidor'}), 500

@app.route('/api/logout')
def logout():
    session.pop('email', None)
    response = make_response(jsonify({'message': 'Sesión cerrada'}), 200)
    response.set_cookie('remember_me_email', '', expires=0, httponly=True, secure=True, samesite='Lax') # Eliminar la cookie
    return response

@app.route('/api/check_session')
def check_session():
    if 'email' in session:
        return jsonify({'logged_in': True, 'email': session['email']})
    
    # Nuevo: Verificar la cookie de "recordarme"
    remember_me_email = request.cookies.get('remember_me_email')
    if remember_me_email:
        # Aquí podrías añadir una verificación adicional si el email de la cookie es válido
        # Por simplicidad, asumimos que si la cookie existe, el usuario es válido.
        # En un sistema real, se verificaría contra la base de datos.
        session['email'] = remember_me_email
        return jsonify({'logged_in': True, 'email': remember_me_email})

    return jsonify({'logged_in': False})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')