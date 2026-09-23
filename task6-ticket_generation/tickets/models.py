from django.conf import settings
from django.db import models


class Booking(models.Model):

    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (
            STATUS_CONFIRMED,
            "Confirmed",
        ),
        (
            STATUS_CANCELLED,
            "Cancelled",
        ),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ticket_bookings",
    )

    booking_id = models.CharField(
        max_length=30,
        unique=True,
    )

    movie_title = models.CharField(
        max_length=250,
    )

    theater_name = models.CharField(
        max_length=200,
    )

    screen_name = models.CharField(
        max_length=100,
    )

    show_time = models.DateTimeField(
        db_index=True,
    )

    booked_seats = models.JSONField(
        default=list,
    )

    payment_reference = models.CharField(
        max_length=150,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CONFIRMED,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    def __str__(self):
        return self.booking_id


class Ticket(models.Model):

    EMAIL_PENDING = "PENDING"
    EMAIL_SENT = "SENT"
    EMAIL_FAILED = "FAILED"

    EMAIL_STATUS_CHOICES = [
        (
            EMAIL_PENDING,
            "Pending",
        ),
        (
            EMAIL_SENT,
            "Sent",
        ),
        (
            EMAIL_FAILED,
            "Failed",
        ),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="ticket",
    )

    pdf_file = models.FileField(
        upload_to="tickets/",
        blank=True,
        null=True,
    )

    qr_value = models.CharField(
        max_length=500,
    )

    email_status = models.CharField(
        max_length=20,
        choices=EMAIL_STATUS_CHOICES,
        default=EMAIL_PENDING,
        db_index=True,
    )

    email_attempts = models.PositiveIntegerField(
        default=0,
    )

    last_email_error = models.TextField(
        blank=True,
    )

    generated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    emailed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"Ticket - "
            f"{self.booking.booking_id}"
        )