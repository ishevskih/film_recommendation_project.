import os
import sys
import time
import requests
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'film_recommendation_project.settings')

import django
django.setup()

from films.models import Film

TMDB_API_KEY = 'cdeeea0530b40aeb7df474c215896986'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'

def clean_title(title):
    """Очищает название от мусора"""
    if not title:
        return ""
    
    # Убираем пробелы
    title = title.strip()
    
    # Убираем всё что в скобках (a.k.a., альтернативные названия)
    title = re.sub(r'\s*\(a\.k\.a\.[^)]*\)\s*', ' ', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\(aka[^)]*\)\s*', ' ', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\([^)]*a\.k\.a\.[^)]*\)\s*', ' ', title, flags=re.IGNORECASE)
    
    # Убираем ведущие кавычки и апострофы
    while title and title[0] in "'\"*":
        title = title[1:]
    
    # Убираем ведущие точки
    while title and title.startswith('...'):
        title = title[3:]
    title = title.lstrip('.')
    
    # Убираем год в скобках в конце
    year_match = re.search(r'\((\d{4})\)\s*$', title)
    if year_match:
        title = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
    
    # Убираем двоеточие после закрывающей кавычки
    match = re.match(r"^'([^']+)':\s*(.+)", title)
    if match:
        title = f"{match.group(1)}: {match.group(2)}"
    
    # "Film, The" -> "The Film"
    match = re.match(r"^(.+),\s*The$", title, re.IGNORECASE)
    if match:
        title = f"The {match.group(1)}"
    
    # Убираем лишние пробелы
    title = ' '.join(title.split())
    
    return title.strip()

def search_movie(title, year=None):
    """Ищет фильм в TMDB с несколькими попытками"""
    url = 'https://api.themoviedb.org/3/search/movie'
    
    # Создаём несколько вариантов запроса
    queries = [title]
    
    # Добавляем год к названию
    if year and year != 'None':
        queries.append(f"{title} {year}")
    
    for query in queries:
        params = {
            'api_key': TMDB_API_KEY,
            'query': query,
            'language': 'ru-RU'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                # Ищем фильм с подходящим годом
                for result in data['results']:
                    release_year = result.get('release_date', '')[:4]
                    if year and year != 'None':
                        if release_year == str(year):
                            return result
                    else:
                        return result
                
                return data['results'][0]
                
        except requests.RequestException as e:
            continue
    
    return None

def fetch_poster_url(poster_path):
    if poster_path:
        return f"{TMDB_IMAGE_BASE}{poster_path}"
    return None

def fetch_missing_posters():
    films = Film.objects.filter(poster_url__isnull=True)
    
    print(f"🎬 Загрузка постеров для {films.count()} фильмов без постеров...")
    print(f"   TMDB API Key: {TMDB_API_KEY[:10]}...")
    print()
    
    success = 0
    failed = 0
    not_found = 0
    
    for i, film in enumerate(films, 1):
        clean_title_name = clean_title(film.title)
        year = film.year if film.year else None
        
        print(f"[{i}/{films.count()}] 🔍 {clean_title_name} ({year or 'без года'})...", end=' ')
        
        movie_data = search_movie(clean_title_name, year)
        
        if movie_data:
            poster_url = fetch_poster_url(movie_data.get('poster_path'))
            
            if poster_url:
                film.poster_url = poster_url
                film.tmdb_id = movie_data.get('id')
                film.save()
                print("✅")
                success += 1
            else:
                print("❌ (нет постера)")
                failed += 1
        else:
            print("❌ (не найден)")
            not_found += 1
        
        time.sleep(0.3)
    
    print()
    print("=" * 50)
    print("🎉 Готово!")
    print(f"   ✅ Успешно: {success}")
    print(f"   ❌ Нет постера: {failed}")
    print(f"   ❌ Не найдено: {not_found}")
    print("=" * 50)

if __name__ == '__main__':
    fetch_missing_posters()