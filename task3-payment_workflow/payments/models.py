from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Show(models.Model):
    movie_name = models.CharField(max_length=200)
    theater_name = models.CharField(max_length=200)
    show_time = models.DateTimeField()
    total_seats = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1)],
    )
    ticket_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return (
            f"{self.movie_name} | "
            f"{self.theater_name} | "
            f"{self.show_time:%d-%m-%Y %I:%M %p}"
        )


class Seat(models.Model):
    STATUS_AVAILABLE = "AVAILABLE"
    STATUS_HELD = "HELD"
    STATUS_BOOKED = "BOOKED"

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, "Available"),
        (STATUS_HELD, "Held"),
        (STATUS_BOOKED, "Booked"),
    ]

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name="seats",
    )

    seat_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_AVAILABLE,
    )

    class Meta:
        ordering = ["seat_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["show", "seat_number"],
                name="unique_show_seat",
            )
        ]

    def __str__(self):
        return f"{self.show.movie_name} - Seat {self.seat_number}"


class Payment(models.Model):
    STATUS_CREATED = "CREATED"
    STATUS_PENDING = "PENDING"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Created"),
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_records",
    )

    show = models.ForeignKey(
        Show,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    order_id = models.CharField(
        max_length=100,
        unique=True,
    )

    payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
    )

    transaction_id = models.CharField(
        max_length=150,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    currency = models.CharField(
        max_length=10,
        default="INR",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
    )

    failure_reason = models.TextField(
        blank=True,
    )

    selected_seats = models.JSONField(
        default=list,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.order_id} - {self.status}"


class SeatHold(models.Model):
    STATUS_ACTIVE = "ACTIVE"
    STATUS_RELEASED = "RELEASED"
    STATUS_BOOKED = "BOOKED"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_RELEASED, "Released"),
        (STATUS_BOOKED, "Booked"),
    ]

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="seat_holds",
    )

    seat = models.ForeignKey(
        Seat,
        on_delete=models.PROTECT,
        related_name="holds",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    released_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["payment", "seat"],
                name="unique_payment_seat_hold",
            )
        ]

    def __str__(self):
        return (
            f"{self.payment.order_id} - "
            f"Seat {self.seat.seat_number} - "
            f"{self.status}"
        )


class Booking(models.Model):
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_bookings",
    )

    payment = models.OneToOneField(
        Payment,
        on_delete=models.PROTECT,
        related_name="booking",
    )

    show = models.ForeignKey(
        Show,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    seats = models.JSONField(
        default=list,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CONFIRMED,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.show.movie_name} - "
            f"{self.user.username} - "
            f"{self.status}"
        )


class WebhookEvent(models.Model):
    event_id = models.CharField(
        max_length=150,
        unique=True,
    )

    event_type = models.CharField(
        max_length=100,
    )

    payload = models.JSONField(
        default=dict,
    )

    processed = models.BooleanField(
        default=False,
    )

    received_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.event_type} - {self.event_id}"