from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

# Leemos el dataset una sola vez al iniciar la app para mejorar el rendimiento
try:
    # Asegúrate que la ruta al CSV sea correcta según tu estructura en Render
    df = pd.read_csv("app/data/udemy_online_education_courses_dataset.csv")
    # Limpiamos los títulos para facilitar la búsqueda
    df['course_title_lower'] = df['course_title'].str.lower()
except FileNotFoundError:
    print("Error: El archivo del dataset no se encontró. Asegúrate de que la ruta es correcta.")
    df = pd.DataFrame() # Creamos un DataFrame vacío para evitar que la app falle

@app.route('/', methods=['GET', 'POST'])
def home():
    cursos = []
    query = ""
    # Esta lógica es para el buscador principal, no para el modal.
    # La dejamos como está.
    if request.method == 'POST' and 'interes' in request.form:
        if not df.empty:
            query = request.form.get('interes', '').strip().lower()
            if query:
                resultados = df[df['course_title_lower'].str.contains(query)]
                cursos = resultados.sort_values(by='num_subscribers', ascending=False).head(5).to_dict(orient='records')

    return render_template('index.html', cursos=cursos, query=query)

@app.route('/recommend', methods=['POST'])
def recommend():
    """
    Procesa las respuestas del test modal y devuelve las recomendaciones como JSON.
    """
    if df.empty:
        return jsonify({"error": "Dataset no disponible"}), 500

    # 1. Obtener las respuestas del usuario del formulario del modal
    interest = request.form.get('interest_modal', '')
    level = request.form.get('level_modal', '')

    # 2. Lógica de recomendación simple basada en palabras clave
    results_df = df[df['course_title_lower'].str.contains(interest)].copy()

    # 3. Mapeo de niveles a palabras clave
    level_keywords = {
        'beginner': ['beginner', 'beginners', 'from scratch', 'introduction', 'básico', 'cero'],
        'intermediate': ['intermediate', 'masterclass', 'complete', 'intermedio', 'avanzado', 'total']
    }
    
    # 4. Filtrar por nivel si se especificó uno
    if level in level_keywords:
        keyword_list = level_keywords[level]
        level_regex = '|'.join(keyword_list)
        
        level_specific_df = results_df[results_df['course_title_lower'].str.contains(level_regex, na=False)]
        
        if not level_specific_df.empty:
            results_df = level_specific_df

    # 5. Ordenar por popularidad y obtener el top 5
    recommended_courses = results_df.sort_values(by='num_subscribers', ascending=False).head(5)
    
    # 6. Devolver los resultados en formato JSON
    return jsonify(cursos=recommended_courses.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

