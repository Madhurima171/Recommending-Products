import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from db import get_connection

def load_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    data = cursor.fetchall()
    conn.close()
    df = pd.DataFrame(data)
    df['tags'] = df['category'].fillna('') + ' ' + df['description'].fillna('')
    return df

def recommend(product_id):
    df = load_products()
    cv = CountVectorizer(stop_words='english')
    vectors = cv.fit_transform(df['tags']).toarray()
    similarity = cosine_similarity(vectors)
    
    try:
        idx = df[df['id'] == int(product_id)].index[0]
        distances = list(enumerate(similarity[idx]))
        distances = sorted(distances, key=lambda x: x[1], reverse=True)
        
        result = []
        for i in distances[1:5]:
            item = df.iloc[i[0]].to_dict()
            item['score'] = round(i[1] * 100, 2)
            result.append(item)
        return result
    except:
        return []