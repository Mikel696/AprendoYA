import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

df = pd.read_csv("data/udemy_online_education_courses_dataset.csv", encoding='latin-1')

features = ['price', 'num_subscribers', 'num_reviews', 'num_lectures', 'content_duration']

if not all(feature in df.columns for feature in features):
    raise ValueError("Faltan columnas necesarias en el dataset")

if df[features].isnull().any().any():
    raise ValueError("Existen valores nulos en las columnas numéricas del dataset")

def get_recommendations(course_id, top_n=5):
    if course_id not in df['course_id'].values:
        raise ValueError(f"El course_id {course_id} no existe en la base de datos")

    df_features = df[features]
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_features)
    
    similarity = cosine_similarity(scaled_features)
    
    course_idx = df.index[df['course_id'] == course_id][0]
    scores = list(enumerate(similarity[course_idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    
    top_courses = [df.iloc[i[0]].to_dict() for i in scores[1:top_n+1]]
    return top_courses

