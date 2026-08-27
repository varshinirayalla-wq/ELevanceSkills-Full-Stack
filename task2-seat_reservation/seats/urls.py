from django.urls import path

from . import views


urlpatterns = [
    path(
        "<int:show_id>/",
        views.seat_reservation,
        name="seat_reservation",
    ),

    path(
        "<int:show_id>/reserve/",
        views.reserve_seats,
        name="reserve_seats",
    ),

    path(
        "<int:show_id>/modify/",
        views.modify_seats,
        name="modify_seats",
    ),

    path(
        "<int:show_id>/payment/",
        views.complete_payment,
        name="complete_payment",
    ),
]