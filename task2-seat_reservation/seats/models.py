from django.db import models

# Create your models here.
from datetime import timedelta

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Show(models.Model):
    movie_name = models.CharField(max_length=200)
    theater_name = models.CharField(max_length=200)
    show_time = models.DateTimeField()
    total_seats = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1)],
    )
    ticket_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=200,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.movie_name} - {self.theater_name}"

    @property
    def available_seats(self):
        self.release_expired_reservations()

        return self.total_seats - self.seat_reservations.filter(
            status=SeatReservation.STATUS_RESERVED
        ).count() - self.seat_reservations.filter(
            status=SeatReservation.STATUS_BOOKED
        ).count()

    def release_expired_reservations(self):
        self.seat_reservations.filter(
            status=SeatReservation.STATUS_RESERVED,
            reserved_until__lte=timezone.now(),
        ).update(
            status=SeatReservation.STATUS_RELEASED,
            user=None,
        )


class SeatReservation(models.Model):
    STATUS_RESERVED = "RESERVED"
    STATUS_BOOKED = "BOOKED"
    STATUS_RELEASED = "RELEASED"

    STATUS_CHOICES = [
        (STATUS_RESERVED, "Reserved"),
        (STATUS_BOOKED, "Booked"),
        (STATUS_RELEASED, "Released"),
    ]

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name="seat_reservations",
    )

    seat_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="seat_reservations",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_RESERVED,
    )

    reserved_at = models.DateTimeField(auto_now_add=True)

    reserved_until = models.DateTimeField(
        null=True,
        blank=True,
    )

    booked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["seat_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["show", "seat_number"],
                name="unique_seat_per_show",
            )
        ]

    def __str__(self):
        return (
            f"{self.show.movie_name} - "
            f"Seat {self.seat_number} - "
            f"{self.status}"
        )

    @property
    def is_expired(self):
        return (
            self.status == self.STATUS_RESERVED
            and self.reserved_until is not None
            and self.reserved_until <= timezone.now()
        )

    @property
    def remaining_seconds(self):
        if self.status != self.STATUS_RESERVED:
            return 0

        if not self.reserved_until:
            return 0

        remaining = (
            self.reserved_until - timezone.now()
        ).total_seconds()

        return max(0, int(remaining))