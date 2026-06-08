from films.models import Film, Rating

class SerendipityRecommender:
    def __init__(self, user_id):
        self.user_id = user_id
        # Получаем понравившиеся фильмы (рейтинг >= 3.5)
        self.watched = list(Rating.objects.filter(user_id=user_id, rating__gte=3.5).select_related('film'))
        self.all_films = list(Film.objects.exclude(id__in=[w.film.id for w in self.watched]))
        
        # Собираем жанры пользователя
        self.user_genres = {}
        for r in self.watched:
            for genre in r.film.genres.split('|'):
                genre = genre.strip()
                if genre:
                    self.user_genres[genre] = self.user_genres.get(genre, 0) + 1
        
        print(f"👤 Пользователь {user_id}: {len(self.watched)} оценок, жанры: {self.user_genres}")
    
    def get_recommendations(self, ser_level=0.5, top_n=10):
        """
        ser_level: 0.0 = только похожие жанры, 1.0 = только новые жанры
        """
        # Холодный старт — нет оценок
        if not self.watched:
            print("⚠️ Холодный старт — популярные фильмы")
            popular = Film.objects.all().order_by('-id')[:top_n]
            return [{'film': f, 'score': 0.5, 'accuracy': 0.5, 'serendipity': 0.5} for f in popular]
        
        recs = []
        
        for film in self.all_films:
            # Жанры фильма
            film_genres = set(g.strip() for g in film.genres.split('|') if g.strip())
            user_genre_set = set(self.user_genres.keys())
            
            # 1. ACCURACY: сколько жанров фильма совпадает с любимыми
            if film_genres and user_genre_set:
                matching_genres = film_genres & user_genre_set
                acc = len(matching_genres) / len(film_genres)
            else:
                acc = 0.0
            
            # 2. SERENDIPITY: сколько жанров фильма НОВЫЕ для пользователя
            if film_genres:
                new_genres = film_genres - user_genre_set
                ser = len(new_genres) / len(film_genres)
            else:
                ser = 0.0
            
            # 3. POPULARITY: бонус за популярность
            pop_count = Rating.objects.filter(film=film).count()
            pop = min(pop_count / 100, 1.0)
            
            # === ФОРМУЛА (без переопределения acc/ser!) ===
            if ser_level <= 0.3:
                # КОНСЕРВАТИВНО: упор на совпадающие жанры
                final_score = acc * 0.8 + pop * 0.2
            elif ser_level >= 0.7:
                # СМЕЛО: упор на новые жанры
                final_score = ser * 0.8 + pop * 0.2
            else:
                # БАЛАНС: плавный переход
                final_score = acc * (1 - ser_level) + ser * ser_level
            
            recs.append({
                'film': film,
                'score': final_score,
                'accuracy': round(acc, 3),
                'serendipity': round(ser, 3),
                'matching_genres': len(film_genres & user_genre_set),
                'new_genres': len(film_genres - user_genre_set),
            })
        
        # Сортируем по score
        recs.sort(key=lambda x: x['score'], reverse=True)
        
        # Отладка в консоль
        print(f"🎲 ser_level={ser_level}: Топ-3:")
        for i, r in enumerate(recs[:3], 1):
            print(f"   {i}. {r['film'].title[:35]:35} | acc={r['accuracy']:.3f}, ser={r['serendipity']:.3f}, match={r['matching_genres']}, new={r['new_genres']}")
        
        return recs[:top_n] 