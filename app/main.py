from flask import Flask, render_template, request, jsonify, session, make_response
import pandas as pd
import os

from sklearn.preprocessing import MinMaxScaler
from werkzeug.security import generate_password_hash, check_password_hash
import json
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required
from recommender import get_recommendations

app = Flask(__name__)
app.secret_key = os.urandom(24)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data', 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Optional: set the login view

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<User {self.email}>'

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Favorite user_id={self.user_id} course_id={self.course_id}>'




with app.app_context():
    db.create_all()

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
        df = pd.read_csv(path, encoding='utf-8-sig')
        if 'course_id' in df.columns:
            df['course_id'] = pd.to_numeric(df['course_id'], errors='coerce').fillna(0).astype(int)
        df['title_lower'] = df['course_title'].str.lower()
        print(f"Archivo 'cursos_calificados_final.csv' cargado con {len(df)} cursos.")
        return df
    except Exception as e:
        print(f"ERROR CRÍTICO AL CARGAR 'cursos_calificados_final.csv': {e}")
        return pd.DataFrame()



master_df = load_data()


def perform_search(query, level=None, platform=None):
    """
    Realiza una búsqueda con el ranking por estrellas, relevancia y nivel, y filtros adicionales.
    """
    if master_df.empty:
        return []

    results_df = master_df.copy()

    if query:
        mask = results_df['title_lower'].str.contains(query, na=False)
        results_df = results_df[mask]

    if platform:
        results_df = results_df[results_df['site'].str.lower() == platform.lower()]

    if results_df.empty:
        return []

    level_score = pd.Series(0, index=results_df.index)
    if level == 'beginner':
        level_score += results_df['title_lower'].str.contains('principiantes|básico|cero|inicial', na=False, regex=True).astype(int)

    if query:
        results_df['relevance_score'] = results_df['title_lower'].apply(lambda x: len(query) / len(x) if x and len(x) > 0 else 0)
    else:
        results_df['relevance_score'] = 0
        
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

TOPICS_LIST = get_topics_from_keywords()

# --- Rutas de la Aplicación ---

@app.route('/')
def home():
    return render_template('index.html', topics=TOPICS_LIST)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('interes', '').strip().lower()
    platform = request.form.get('platform', None)

    cursos = perform_search(query, platform=platform)
    return jsonify(cursos=cursos)

@app.route('/recommend', methods=['POST'])
def recommend():
    query = request.form.get('interest_modal', '')
    level = request.form.get('level_modal', '')
    platform = request.form.get('platform', None)
    
    cursos = perform_search(query, level=level, platform=platform)
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

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'El correo ya está registrado'}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    login_user(new_user) # Log in the newly registered user
    return jsonify({'message': 'Registro exitoso', 'email': email}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    remember_me = data.get('remember_me', False)

    if not email or not password:
        return jsonify({'message': 'Faltan datos'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Credenciales inválidas'}), 401

    login_user(user, remember=remember_me)
    response = make_response(jsonify({'message': 'Inicio de sesión exitoso', 'email': user.email}), 200)
    return response

@app.route('/api/logout')
def logout():
    logout_user()
    response = make_response(jsonify({'message': 'Sesión cerrada'}), 200)
    return response

@app.route('/api/check_session')
def check_session():
    if current_user.is_authenticated:
        return jsonify({'logged_in': True, 'email': current_user.email})
    return jsonify({'logged_in': False})

# --- Rutas de Favoritos ---

@app.route('/api/favorites', methods=['GET'])
@login_required
def get_favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    favorite_course_ids = [f.course_id for f in favorites]
    
    if not favorite_course_ids:
        return jsonify(cursos=[])

    master_df_copy = master_df.copy()
    master_df_copy['course_id'] = pd.to_numeric(master_df_copy['course_id'], errors='coerce').fillna(0).astype(int)
    
    favorite_courses = master_df_copy[master_df_copy['course_id'].isin(favorite_course_ids)]
    return jsonify(cursos=favorite_courses.to_dict(orient='records'))

@app.route('/api/favorites/add', methods=['POST'])
@login_required
def add_favorite():
    data = request.get_json()
    course_id = data.get('course_id')

    if not course_id:
        return jsonify({'message': 'Falta el ID del curso'}), 400

    existing_favorite = Favorite.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if existing_favorite:
        return jsonify({'message': 'El curso ya está en favoritos'}), 409

    new_favorite = Favorite(user_id=current_user.id, course_id=course_id)
    db.session.add(new_favorite)
    db.session.commit()
    
    return jsonify({'message': 'Curso añadido a favoritos'}), 201

@app.route('/api/favorites/remove', methods=['POST'])
@login_required
def remove_favorite():
    data = request.get_json()
    course_id = data.get('course_id')

    if not course_id:
        return jsonify({'message': 'Falta el ID del curso'}), 400

    favorite_to_remove = Favorite.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not favorite_to_remove:
        return jsonify({'message': 'El curso no está en favoritos'}), 404

    db.session.delete(favorite_to_remove)
    db.session.commit()
    
    return jsonify({'message': 'Curso eliminado de favoritos'}), 200

# --- Rutas de Dashboard ---

@app.route('/api/dashboard')
@login_required
def dashboard():
    favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.id.desc()).all()
    
    recommendations = []
    recent_favorites = []

    if favorites:
        # Get the most recent favorite course_id
        most_recent_favorite_course_id = favorites[0].course_id
        
        # Get the course_title for the most recent favorite
        most_recent_favorite_course = master_df[master_df['course_id'] == most_recent_favorite_course_id]
        if not most_recent_favorite_course.empty:
            most_recent_favorite_course_title = most_recent_favorite_course['course_title'].iloc[0]
            
            # Get recommendations based on the most recent favorite's title
            try:
                recommendations = get_recommendations(most_recent_favorite_course_title, master_df, top_n=3)
            except Exception as e:
                print(f"Error al obtener recomendaciones para el dashboard: {e}")

        # Get the user's most recent favorites
        favorite_course_ids = [f.course_id for f in favorites]
        recent_favorites_df = master_df[master_df['course_id'].isin(favorite_course_ids)]
        recent_favorites = recent_favorites_df.head(3).to_dict(orient='records')

    return jsonify({
        'recommendations': recommendations,
        'recent_favorites': recent_favorites
    })



@app.route('/api/platforms', methods=['GET'])
def get_platforms():
    if master_df.empty:
        return jsonify(platforms=[])
    
    unique_platforms = master_df['site'].dropna().unique().tolist()
    return jsonify(platforms=unique_platforms)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')