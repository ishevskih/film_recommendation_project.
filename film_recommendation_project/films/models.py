from django.db import models
from django.contrib.auth.models import User

class Film(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    genres = models.CharField(max_length=500, blank=True, verbose_name="Жанры")
    year = models.IntegerField(null=True, blank=True, verbose_name="Год")
    poster_url = models.URLField(blank=True, null=True, verbose_name="Постер")
    tmdb_id = models.IntegerField(blank=True, null=True, verbose_name="TMDB ID")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Фильм"
        verbose_name_plural = "Фильмы"
        ordering = ['-year', 'title']


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    film = models.ForeignKey(Film, on_delete=models.CASCADE, verbose_name="Фильм")
    rating = models.FloatField(verbose_name="Оценка")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата оценки")

    def __str__(self):
        return f'{self.user.username} - {self.film.title}: {self.rating}'

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        unique_together = ('user', 'film')
        ordering = ['-timestamp']