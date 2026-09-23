from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class Genre(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    def __str__(self):
        return self.name


class Language(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(
        max_length=150,
        unique=True,
    )

    def __str__(self):
        return self.name


class Movie(models.Model):

    title = models.CharField(
        max_length=250,
        db_index=True,
    )

    genres = models.ManyToManyField(
        Genre,
        related_name="movies",
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="movies",
    )

    release_date = models.DateField(
        db_index=True,
    )

    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0,
        db_index=True,
    )

    popularity = models.PositiveIntegerField(
        default=0,
        db_index=True,
    )

    description = models.TextField(
        blank=True,
    )

    poster_url = models.URLField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-popularity", "-rating"]

        indexes = [
            models.Index(
                fields=["release_date", "rating"],
                name="movie_release_rating_idx",
            ),
            models.Index(
                fields=["popularity", "rating"],
                name="movie_pop_rating_idx",
            ),
        ]

    def __str__(self):
        return self.title


class Theater(models.Model):

    name = models.CharField(
        max_length=200,
        db_index=True,
    )

    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="theaters",
    )

    total_seats = models.PositiveIntegerField(
        default=100,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "city"],
                name="unique_theater_city",
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.city.name}"


class Show(models.Model):

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="shows",
    )

    theater = models.ForeignKey(
        Theater,
        on_delete=models.CASCADE,
        related_name="shows",
    )

    show_time = models.DateTimeField(
        db_index=True,
    )

    ticket_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        db_index=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["movie", "show_time"],
                name="show_movie_time_idx",
            ),
            models.Index(
                fields=["theater", "show_time"],
                name="show_theater_time_idx",
            ),
            models.Index(
                fields=["ticket_price", "show_time"],
                name="show_price_time_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.movie.title} - "
            f"{self.theater.name} - "
            f"{self.show_time}"
        )


class Booking(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="movie_bookings",
    )

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    booked_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "booked_at"],
                name="booking_user_date_idx",
            ),
            models.Index(
                fields=["show", "booked_at"],
                name="booking_show_date_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.show.movie.title}"
        )


class RecentlyViewed(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recently_viewed_movies",
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="recent_views",
    )

    viewed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-viewed_at"]

        indexes = [
            models.Index(
                fields=["user", "viewed_at"],
                name="view_user_date_idx",
            ),
            models.Index(
                fields=["movie", "viewed_at"],
                name="view_movie_date_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} viewed "
            f"{self.movie.title}"
        )