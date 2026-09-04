from django.contrib import admin

from .models import (
    Booking,
    Payment,
    Seat,
    SeatHold,
    Show,
    WebhookEvent,
)


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
    )

    search_fields = (
        "movie_name",
        "theater_name",
    )


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):

    list_display = (
        "show",
        "seat_number",
        "status",
    )

    list_filter = (
        "status",
        "show",
    )

    search_fields = (
        "show__movie_name",
        "show__theater_name",
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "order_id",
        "user",
        "show",
        "amount",
        "currency",
        "status",
        "payment_id",
        "transaction_id",
        "created_at",
    )

    list_filter = (
        "status",
        "currency",
        "created_at",
    )

    search_fields = (
        "order_id",
        "payment_id",
        "transaction_id",
        "user__username",
        "show__movie_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(SeatHold)
class SeatHoldAdmin(admin.ModelAdmin):

    list_display = (
        "payment",
        "seat",
        "status",
        "created_at",
        "released_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "payment__order_id",
        "seat__show__movie_name",
        "user_search",
    )

    readonly_fields = (
        "created_at",
    )

    @admin.display(description="User")
    def user_search(self, obj):
        return obj.payment.user.username


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "show",
        "display_seats",
        "amount",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "user__username",
        "show__movie_name",
        "show__theater_name",
        "payment__order_id",
        "payment__transaction_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    @admin.display(description="Seats")
    def display_seats(self, obj):
        return ", ".join(
            str(seat)
            for seat in obj.seats
        )


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):

    list_display = (
        "event_id",
        "event_type",
        "processed",
        "received_at",
    )

    list_filter = (
        "event_type",
        "processed",
    )

    search_fields = (
        "event_id",
        "event_type",
    )

    readonly_fields = (
        "received_at",
    )