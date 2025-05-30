from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)
df = pd.read_csv("data/udemy_online_education_courses_dataset.csv")  # Ajusta ruta si está en otra carpeta

@app.route('/', methods=['GET', 'POST'])
def home():
    cursos = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('interes', '').strip().lower()
        if query:
            resultados = df[df['course_title'].str.lower().str.contains(query)]
            cursos = resultados.sort_values(by='num_subscribers', ascending=False).head(5).to_dict(orient='records')

    return render_template('index.html', cursos=cursos, query=query)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

