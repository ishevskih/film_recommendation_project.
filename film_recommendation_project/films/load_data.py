import os
import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь поиска Python
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'film_recommendation_project.settings')

import django
django.setup()

from films.models import Film, Rating
from django.contrib.auth.models import User
import pandas as pd

# Путь к датасету
DATASET_PATH = BASE_DIR / 'data' / 'ml-latest-small'

def load_movies():
    print("Загрузка фильмов...")
    df_movies = pd.read_csv(DATASET_PATH / 'movies.csv')
    
    count = 0
    for _, row in df_movies.iterrows():
        genres_str = '|'.join(row['genres'].split('|')) if row['genres'] != '(no genres listed)' else ''
        
        film, created = Film.objects.get_or_create(
            id=row['movieId'],
            defaults={
                'title': row['title'],
                'genres': genres_str,
            }
        )
        if created:
            count += 1
    
    print(f"✅ Добавлено фильмов: {count}")

def load_ratings():
    print("Загрузка оценок...")
    df_ratings = pd.read_csv(DATASET_PATH / 'ratings.csv')
    
    unique_user_ids = df_ratings['userId'].unique()
    
    user_map = {}
    for ml_user_id in unique_user_ids:
        django_user, created = User.objects.get_or_create(
            username=f'ml_user_{ml_user_id}',
        )
        user_map[ml_user_id] = django_user
    
    print(f"✅ Создано пользователей: {len(user_map)}")
    
    batch_size = 1000
    total_loaded = 0
    
    for start in range(0, len(df_ratings), batch_size):
        batch = df_ratings.iloc[start:start + batch_size]
        ratings_to_create = []
        
        for _, row in batch.iterrows():
            try:
                user = user_map[row['userId']]
                film = Film.objects.get(id=row['movieId'])
                
                rating_obj = Rating(
                    user=user,
                    film=film,
                    rating=row['rating']
                )
                ratings_to_create.append(rating_obj)
            except Film.DoesNotExist:
                continue
        
        Rating.objects.bulk_create(ratings_to_create, ignore_conflicts=True)
        total_loaded += len(ratings_to_create)
        print(f"📊 Загружено оценок: {total_loaded}/{len(df_ratings)}")
    
    print(f"✅ Всего загружено оценок: {total_loaded}")

if __name__ == '__main__':
    print("🎬 Начинаем загрузку данных из MovieLens...")
    print(f"📁 Путь к датасету: {DATASET_PATH}")
    print()
    
    load_movies()
    print()
    load_ratings()
    print()
    print("🎉 Загрузка данных завершена!")