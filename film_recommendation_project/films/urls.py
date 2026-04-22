from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('my-ratings/', views.my_ratings, name='my_ratings'),
    path('film/<int:film_id>/', views.film_detail, name='film_detail'),
    path('rate/<int:film_id>/', views.rate_film, name='rate_film'),
    path('api/my-ratings/', views.api_my_ratings, name='api_my_ratings'),
    path('api/recommendations/', views.api_recommendations, name='api_recommendations'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
]