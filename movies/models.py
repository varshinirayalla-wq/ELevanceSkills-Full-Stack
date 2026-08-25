

# Create your models here.
from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Avg
from django.utils import timezone


class Genre(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Language(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CastMember(models.Model):
    name = models.CharField(max_length=150)
    biography = models.TextField(blank=True)
    photo_url = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Movie(models.Model):
    CERTIFICATION_CHOICES = [
        ("U", "U"),
        ("UA", "UA"),
        ("A", "A"),
        ("S", "S"),
    ]

    youtube_id_validator = RegexValidator(
        regex=r"^[A-Za-z0-9_-]{11}$",
        message="Enter a valid 11-character YouTube video ID.",
    )

    title = models.CharField(max_length=200)
    genres = models.ManyToManyField(Genre, related_name="movies")
    languages = models.ManyToManyField(Language, related_name="movies")
    cast_members = models.ManyToManyField(
        CastMember,
        related_name="movies",
        blank=True,
    )

    age_certification = models.CharField(
        max_length=5,
        choices=CERTIFICATION_CHOICES,
    )

    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    description = models.TextField()

    release_date = models.DateField()

    trailer_video_id = models.CharField(
        max_length=11,
        validators=[youtube_id_validator],
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-release_date"]

    def __str__(self):
        return self.title

    @property
    def trailer_embed_url(self): 
        if not self.trailer_video_id:
            return "" 
        return f"https://www.youtube.com/embed/{self.trailer_video_id}"

    @property
    def average_rating(self):
        result = self.reviews.aggregate(
            average=Avg("rating")
        )

        return round(result["average"] or 0, 1)

    @property
    def total_reviews(self):
        return self.reviews.count()


class MoviePoster(models.Model):
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="posters",
    )
    image_url = models.URLField()
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "id"]

    def __str__(self):
        return f"{self.movie.title} Poster"


class Theater(models.Model):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    address = models.TextField()
    total_seats = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ["city", "name"]

    def __str__(self):
        return f"{self.name} - {self.city}"


class ShowSchedule(models.Model):
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

    starts_at = models.DateTimeField()

    ticket_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    available_seats = models.PositiveIntegerField()

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return (
            f"{self.movie.title} | "
            f"{self.theater.name} | "
            f"{self.starts_at:%d-%m-%Y %I:%M %p}"
        )

    @property
    def ends_at(self):
        return self.starts_at + timedelta(
            minutes=self.movie.duration_minutes
        )

    @property
    def has_finished(self):
        return timezone.now() >= self.ends_at


class Booking(models.Model):
    STATUS_CHOICES = [
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    show = models.ForeignKey(
        ShowSchedule,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    seats = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="CONFIRMED",
    )

    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-booked_at"]

    def __str__(self):
        return f"{self.user.username} - {self.show.movie.title}"

    @property
    def has_watched(self):
        return (
            self.status == "CONFIRMED"
            and self.show.has_finished
        )


class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )

    title = models.CharField(max_length=150)
    body = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "movie"],
                name="one_review_per_user_movie",
            )
        ]

    def __str__(self):
        return f"{self.movie.title} - {self.user.username}"

    @property
    def is_verified_viewer(self):
        return Booking.objects.filter(
            user=self.user,
            show__movie=self.movie,
            status="CONFIRMED",
            show__starts_at__lte=timezone.now(),
        ).filter(
            show__movie__duration_minutes__isnull=False
        ).exists()


class ReviewReport(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("REVIEWED", "Reviewed"),
        ("DISMISSED", "Dismissed"),
    ]

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="reports",
    )

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_reports",
    )

    reason = models.CharField(max_length=250)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["review", "reported_by"],
                name="one_report_per_user_review",
            )
        ]

    def __str__(self):
        return f"Report #{self.pk}"