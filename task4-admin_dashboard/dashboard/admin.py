from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Booking, Movie, Payment, Theater


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("name", "genre")
    search_fields = ("name", "genre")


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "total_seats")
    search_fields = ("name", "location")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "movie",
        "theater",
        "booked_at",
        "seats_booked",
        "amount",
        "status",
    )

    list_filter = (
        "status",
        "theater",
        "movie",
    )

    search_fields = (
        "user__username",
        "movie__name",
        "theater__name",
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "booking",
        "amount",
        "status",
        "refund_amount",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "transaction_id",
        "booking__user__username",
    )