from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Film, Rating
from .recommender import SerendipityRecommender

def home(request):
    user = request.user if request.user.is_authenticated else None
    
    ser_level = request.GET.get('serendipity', '0.5')
    try:
        ser_level = float(ser_level)
    except (ValueError, TypeError):
        ser_level = 0.5
    ser_level = max(0.0, min(1.0, ser_level))
    
    if user and user.is_authenticated:
        recs = SerendipityRecommender(user.id).get_recommendations(ser_level, 12)
        watched_count = Rating.objects.filter(user=user, rating__gte=3.5).count()
    else:
        recs = [{'film': f, 'score': 0, 'accuracy': 0, 'serendipity': 0} 
                for f in Film.objects.all()[:12]]
        watched_count = 0
    
    # Вычисляем hue и проценты для каждого фильма
    for rec in recs:
        film_id = rec['film'].id or 42
        rec['hue'] = (film_id * 37) % 360
        rec['accuracy_percent'] = int(round(rec['accuracy'] * 100))
        rec['serendipity_percent'] = int(round(rec['serendipity'] * 100))
    
    return render(request, 'films/home.html', {
        'recommendations': recs,
        'serendipity_level': ser_level,
        'serendipity_pct': int(round(ser_level * 100)),
        'watched_count': watched_count,
    })

@login_required
def my_ratings(request):
    ratings = Rating.objects.filter(user=request.user).select_related('film').order_by('-timestamp')
    for rating in ratings:
        rating.hue = (rating.film.id * 37) % 360
    return render(request, 'films/my_ratings.html', {
        'ratings': ratings,
    })

@login_required
def film_detail(request, film_id):
    film = get_object_or_404(Film, id=film_id)
    user_rating = Rating.objects.filter(user=request.user, film=film).first()
    similar = [r for r in SerendipityRecommender(request.user.id).get_recommendations(0.3, 6) 
               if r['film'].id != film_id][:5]
    return render(request, 'films/film_detail.html', {
        'film': film, 'user_rating': user_rating, 'similar_films': similar
    })

@login_required
def rate_film(request, film_id):
    if request.method == 'POST':
        film = get_object_or_404(Film, id=film_id)
        rating = float(request.POST.get('rating', 0))
        if 0.5 <= rating <= 5.0:
            Rating.objects.update_or_create(user=request.user, film=film, defaults={'rating': rating})
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'error'}, status=405)

@login_required
def api_recommendations(request):
    ser_level = request.GET.get('serendipity', '0.5')
    try:
        ser_level = float(ser_level)
    except (ValueError, TypeError):
        ser_level = 0.5
    ser_level = max(0.0, min(1.0, ser_level))
    
    recs = SerendipityRecommender(request.user.id).get_recommendations(ser_level, 12)
    data = [{
        'id': r['film'].id, 'title': r['film'].title, 'year': r['film'].year, 'genres': r['film'].genres,
        'score': round(r['score'], 2), 'accuracy': round(r['accuracy'], 2), 'serendipity': round(r['serendipity'], 2)
    } for r in recs]
    return JsonResponse({'recommendations': data})

@login_required
def api_my_ratings(request):
    """API для получения оценок пользователя"""
    ratings = Rating.objects.filter(user=request.user).select_related('film').order_by('-timestamp')
    data = [{
        'film_id': r.film.id,
        'film_title': r.film.title,
        'film_genres': r.film.genres,
        'film_year': r.film.year,
        'film_poster_url': r.film.poster_url,  # ← ДОБАВЛЕНО!
        'rating': r.rating,
        'timestamp': r.timestamp.isoformat(),
    } for r in ratings]
    return JsonResponse({'ratings': data})

def login_view(request):
    return render(request, 'films/login.html')

def register_view(request):
    return render(request, 'films/register.html')