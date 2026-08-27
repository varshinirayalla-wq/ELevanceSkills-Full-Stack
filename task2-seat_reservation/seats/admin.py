from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import SeatReservation, Show


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = (
        "movie_name",
        "theater_name",
        "show_time",
        "total_seats",
        "ticket_price",
        "is_active",
    )

    list_filter = (
        "is_active",
        "theater_name",
    )

    search_fields = (
        "movie_name",
        "theater_name",
    )


@admin.register(SeatReservation)
class SeatReservationAdmin(admin.ModelAdmin):
    list_display = (
        "show",
        "seat_number",
        "user",
        "status",
        "reserved_until",
        "booked_at",
    )

    list_filter = (
        "status",
        "show",
    )

    search_fields = (
        "show__movie_name",
        "user__username",
    )