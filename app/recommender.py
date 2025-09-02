import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

def get_recommendations(course_id, data_df, top_n=5):
    features = ['star_rating'] # Only use star_rating as it's the only common numerical feature

    if not all(feature in data_df.columns for feature in features):
        raise ValueError(f"Faltan columnas necesarias en el dataset: {', '.join([f for f in features if f not in data_df.columns])}")

    if data_df[features].isnull().any().any():
        # Fill NaN values with 0 or a suitable default if necessary, or handle them
        # For now, we'll raise an error as per original logic
        raise ValueError("Existen valores nulos en las columnas numéricas del dataset")

    if course_id not in data_df['course_id'].values:
        raise ValueError(f"El course_id {course_id} no existe en la base de datos")

    df_features = data_df[features]
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_features)
    
    similarity = cosine_similarity(scaled_features)
    
    course_idx = data_df.index[data_df['course_id'] == course_id][0]
    scores = list(enumerate(similarity[course_idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    
    top_courses = [data_df.iloc[i[0]].to_dict() for i in scores[1:top_n+1]]
    return top_courses