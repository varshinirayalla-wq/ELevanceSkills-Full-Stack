from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class Movie(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    genre = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Theater(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    location = models.CharField(max_length=200, blank=True)
    total_seats = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Booking(models.Model):

    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (CONFIRMED, "Confirmed"),
        (CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_bookings",
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    theater = models.ForeignKey(
        Theater,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    booked_at = models.DateTimeField(db_index=True)

    seats_booked = models.PositiveIntegerField(default=1)

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=CONFIRMED,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
             models.Index(
             fields=["booked_at", "status"],
             name="booking_date_status_idx",
            ),
            models.Index(
            fields=["status", "booked_at"],
            name="booking_status_date_idx",
            ),
            models.Index(
            fields=["theater", "booked_at"],
            name="booking_theater_date_idx",
            ),
            models.Index(
            fields=["movie", "booked_at"],
            name="booking_movie_date_idx",
            ),
            models.Index(
            fields=["user", "booked_at"],
            name="booking_user_date_idx",
            ),
        ]
    def __str__(self):
        return f"Booking #{self.pk}"


class Payment(models.Model):

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

    STATUS_CHOICES = [
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
        (REFUNDED, "Refunded"),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="payment",
    )

    transaction_id = models.CharField(
        max_length=100,
        unique=True,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        db_index=True,
    )

    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "created_at"],
                name="payment_status_date_idx",
            ),
        ]

    def __str__(self):
        return self.transaction_id