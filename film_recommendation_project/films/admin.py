from django.contrib import admin
from .models import Film, Rating

@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = ['title', 'year', 'genres']
    search_fields = ['title', 'genres']
    list_filter = ['year']

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'film', 'rating', 'timestamp']
    list_filter = ['rating', 'timestamp']
    search_fields = ['user__username', 'film__title']   