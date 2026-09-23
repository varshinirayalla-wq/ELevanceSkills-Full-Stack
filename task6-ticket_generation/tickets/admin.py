from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Booking, Ticket


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = (
        "booking_id",
        "user",
        "movie_title",
        "theater_name",
        "show_time",
        "payment_reference",
        "amount",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "booking_id",
        "user__username",
        "movie_title",
        "payment_reference",
    )

    readonly_fields = (
        "created_at",
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):

    list_display = (
        "booking",
        "email_status",
        "email_attempts",
        "generated_at",
        "emailed_at",
    )

    list_filter = (
        "email_status",
        "generated_at",
        "emailed_at",
    )

    search_fields = (
        "booking__booking_id",
        "booking__user__username",
    )

    readonly_fields = (
        "created_at",
        "generated_at",
        "emailed_at",
    )