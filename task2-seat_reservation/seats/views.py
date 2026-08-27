from django.shortcuts import render

# Create your views here.
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import SeatReservation, Show


RESERVATION_TIME = 2


def release_expired(show):
    SeatReservation.objects.filter(
        show=show,
        status=SeatReservation.STATUS_RESERVED,
        reserved_until__lte=timezone.now(),
    ).update(
        status=SeatReservation.STATUS_RELEASED,
        user=None,
        reserved_until=None,
    )


def seat_reservation(request, show_id):
    show = get_object_or_404(
        Show,
        id=show_id,
        is_active=True,
    )

    release_expired(show)

    reservations = SeatReservation.objects.filter(
        show=show
    ).select_related("user")

    seat_status = {}

    for seat in range(1, show.total_seats + 1):
        reservation = reservations.filter(
            seat_number=seat
        ).first()

        if not reservation:
            seat_status[seat] = "available"

        elif reservation.status == SeatReservation.STATUS_BOOKED:
            seat_status[seat] = "booked"

        elif reservation.status == SeatReservation.STATUS_RESERVED:
            if reservation.user_id == request.user.id:
                seat_status[seat] = "your_reservation"
            else:
                seat_status[seat] = "reserved"

        else:
            seat_status[seat] = "available"

    current_reservations = SeatReservation.objects.filter(
        show=show,
        user=request.user,
        status=SeatReservation.STATUS_RESERVED,
        reserved_until__gt=timezone.now(),
    ).order_by("seat_number")

    context = {
        "show": show,
        "seat_status": seat_status,
        "current_reservations": current_reservations,
        "reservation_seconds": RESERVATION_TIME * 60,
    }

    return render(
        request,
        "seats/seat_reservation.html",
        context,
    )


@login_required
@transaction.atomic
def reserve_seats(request, show_id):
    if request.method != "POST":
        return redirect("seat_reservation", show_id=show_id)

    show = get_object_or_404(
        Show.objects.select_for_update(),
        id=show_id,
        is_active=True,
    )

    release_expired(show)

    seat_numbers = request.POST.getlist("seats")

    if not seat_numbers:
        messages.error(
            request,
            "Please select at least one seat.",
        )
        return redirect("seat_reservation", show_id=show.id)

    try:
        seat_numbers = sorted(
            set(int(seat) for seat in seat_numbers)
        )
    except ValueError:
        messages.error(request, "Invalid seat selection.")
        return redirect("seat_reservation", show_id=show.id)

    if any(
        seat < 1 or seat > show.total_seats
        for seat in seat_numbers
    ):
        messages.error(request, "Invalid seat number.")
        return redirect("seat_reservation", show_id=show.id)

    now = timezone.now()
    reserved_until = now + timedelta(minutes=RESERVATION_TIME)

    # Lock all existing reservation records for selected seats.
    existing = {
        reservation.seat_number: reservation
        for reservation in SeatReservation.objects.select_for_update().filter(
            show=show,
            seat_number__in=seat_numbers,
        )
    }

    # Check that none of the requested seats is already booked
    # or reserved by another user.
    for seat_number in seat_numbers:
        reservation = existing.get(seat_number)

        if not reservation:
            continue

        if reservation.status == SeatReservation.STATUS_BOOKED:
            messages.error(
                request,
                f"Seat {seat_number} is already booked.",
            )
            return redirect(
                "seat_reservation",
                show_id=show.id,
            )

        if (
            reservation.status == SeatReservation.STATUS_RESERVED
            and reservation.user_id != request.user.id
            and reservation.reserved_until
            and reservation.reserved_until > now
        ):
            messages.error(
                request,
                f"Seat {seat_number} is currently reserved.",
            )
            return redirect(
                "seat_reservation",
                show_id=show.id,
            )

    # Reserve/update all selected seats in ONE transaction.
    for seat_number in seat_numbers:
        reservation = existing.get(seat_number)

        if reservation:
            reservation.user = request.user
            reservation.status = SeatReservation.STATUS_RESERVED
            reservation.reserved_until = reserved_until
            reservation.save(
                update_fields=[
                    "user",
                    "status",
                    "reserved_until",
                ]
            )

        else:
            SeatReservation.objects.create(
                show=show,
                seat_number=seat_number,
                user=request.user,
                status=SeatReservation.STATUS_RESERVED,
                reserved_until=reserved_until,
            )

    messages.success(
        request,
        "Seats reserved for 2 minutes. Complete payment before the timer expires.",
    )

    return redirect(
        "seat_reservation",
        show_id=show.id,
    )


@login_required
@transaction.atomic
def modify_seats(request, show_id):

    if request.method != "POST":
        return redirect(
            "seat_reservation",
            show_id=show_id,
        )

    show = get_object_or_404(
        Show.objects.select_for_update(),
        id=show_id,
        is_active=True,
    )

    now = timezone.now()

    # Release expired reservations first.
    SeatReservation.objects.filter(
        show=show,
        status=SeatReservation.STATUS_RESERVED,
        reserved_until__lte=now,
    ).update(
        status=SeatReservation.STATUS_RELEASED,
        user=None,
        reserved_until=None,
    )

    # Get the new selection.
    selected_values = request.POST.getlist("seats")

    try:
        selected_seats = sorted(
            set(int(value) for value in selected_values)
        )
    except ValueError:
        messages.error(
            request,
            "Invalid seat selection.",
        )

        return redirect(
            "seat_reservation",
            show_id=show.id,
        )

    # User must select at least one seat.
    if not selected_seats:
        messages.error(
            request,
            "Please select at least one seat.",
        )

        return redirect(
            "seat_reservation",
            show_id=show.id,
        )

    # Validate seat numbers.
    if any(
        seat < 1 or seat > show.total_seats
        for seat in selected_seats
    ):
        messages.error(
            request,
            "One or more selected seats are invalid.",
        )

        return redirect(
            "seat_reservation",
            show_id=show.id,
        )

    # Lock all existing reservations for the requested seats.
    existing_reservations = {
        reservation.seat_number: reservation
        for reservation in SeatReservation.objects
        .select_for_update()
        .filter(
            show=show,
            seat_number__in=selected_seats,
        )
    }

    # Check whether selected seats belong to somebody else
    # or are already booked.
    for seat_number in selected_seats:

        reservation = existing_reservations.get(
            seat_number
        )

        if not reservation:
            continue

        if reservation.status == SeatReservation.STATUS_BOOKED:

            messages.error(
                request,
                f"Seat {seat_number} is already booked.",
            )

            return redirect(
                "seat_reservation",
                show_id=show.id,
            )

        if (
            reservation.status
            == SeatReservation.STATUS_RESERVED
            and reservation.user_id != request.user.id
            and reservation.reserved_until
            and reservation.reserved_until > now
        ):

            messages.error(
                request,
                f"Seat {seat_number} is reserved by another user.",
            )

            return redirect(
                "seat_reservation",
                show_id=show.id,
            )

    # Lock and get the user's current active reservations.
    current_reservations = list(
        SeatReservation.objects
        .select_for_update()
        .filter(
            show=show,
            user=request.user,
            status=SeatReservation.STATUS_RESERVED,
            reserved_until__gt=now,
        )
    )

    current_seats = {
        reservation.seat_number
        for reservation in current_reservations
    }

    selected_seat_set = set(selected_seats)

    # Release seats that the user removed.
    for reservation in current_reservations:

        if reservation.seat_number not in selected_seat_set:

            reservation.status = (
                SeatReservation.STATUS_RELEASED
            )

            reservation.user = None
            reservation.reserved_until = None

            reservation.save(
                update_fields=[
                    "status",
                    "user",
                    "reserved_until",
                ]
            )

    # Keep or create selected seats.
    new_expiry = (
        now + timedelta(minutes=RESERVATION_TIME)
    )

    for seat_number in selected_seats:

        reservation = SeatReservation.objects.filter(
            show=show,
            seat_number=seat_number,
        ).first()

        if reservation:

            reservation.user = request.user
            reservation.status = (
                SeatReservation.STATUS_RESERVED
            )
            reservation.reserved_until = new_expiry

            reservation.save(
                update_fields=[
                    "user",
                    "status",
                    "reserved_until",
                ]
            )

        else:

            SeatReservation.objects.create(
                show=show,
                seat_number=seat_number,
                user=request.user,
                status=SeatReservation.STATUS_RESERVED,
                reserved_until=new_expiry,
            )

    messages.success(
        request,
        "Your seat selection has been updated.",
    )

    return redirect(
        "seat_reservation",
        show_id=show.id,
    )
def complete_payment(request, show_id):
    if request.method != "POST":
        return redirect("seat_reservation", show_id=show_id)

    show = get_object_or_404(
        Show.objects.select_for_update(),
        id=show_id,
        is_active=True,
    )

    now = timezone.now()

    reservations = list(
        SeatReservation.objects.select_for_update().filter(
            show=show,
            user=request.user,
            status=SeatReservation.STATUS_RESERVED,
            reserved_until__gt=now,
        )
    )

    if not reservations:
        messages.error(
            request,
            "Your reservation has expired. Please select seats again.",
        )
        return redirect(
            "seat_reservation",
            show_id=show.id,
        )

    for reservation in reservations:
        reservation.status = SeatReservation.STATUS_BOOKED
        reservation.booked_at = now
        reservation.save(
            update_fields=[
                "status",
                "booked_at",
            ]
        )

    messages.success(
        request,
        "Payment successful! Your seats are confirmed.",
    )

    return redirect(
        "seat_reservation",
        show_id=show.id,
    )