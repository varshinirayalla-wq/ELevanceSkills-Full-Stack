from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .models import Booking


def home(request):
    """
    Send users to booking history.
    Anonymous users are sent to the login page.
    """

    if not request.user.is_authenticated:
        return redirect("login")

    return redirect("booking_history")


@login_required
def booking_history(request):

    bookings = (
        Booking.objects
        .filter(
            user=request.user
        )
        .select_related("ticket")
        .order_by("-created_at")
    )

    return render(
        request,
        "tickets/booking_history.html",
        {
            "bookings": bookings,
        },
    )


@login_required
def download_ticket(
    request,
    booking_id,
):

    try:

        booking = (
            Booking.objects
            .select_related("ticket")
            .get(
                id=booking_id,
                user=request.user,
                status=Booking.STATUS_CONFIRMED,
            )
        )

    except Booking.DoesNotExist:

        raise Http404(
            "Booking not found."
        )

    if not booking.ticket.pdf_file:

        raise Http404(
            "Ticket PDF is not available yet."
        )

    return FileResponse(
        booking.ticket.pdf_file.open("rb"),
        as_attachment=True,
        filename=(
            f"ticket_"
            f"{booking.booking_id}.pdf"
        ),
    )


def verify_ticket(
    request,
    booking_id,
):
    """
    Public ticket verification endpoint.

    The QR code points to this URL.
    """

    booking = get_object_or_404(
        Booking.objects.select_related(
            "user",
            "ticket",
        ),
        booking_id=booking_id,
    )

    is_valid = (
        booking.status
        == Booking.STATUS_CONFIRMED
    )

    return render(
        request,
        "tickets/verify_ticket.html",
        {
            "booking": booking,
            "is_valid": is_valid,
        },
    )