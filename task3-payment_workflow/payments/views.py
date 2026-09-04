from django.shortcuts import render

# Create your views here.
import json
import hmac
import hashlib
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

import razorpay

from .models import (
    Booking,
    Payment,
    Seat,
    SeatHold,
    Show,
    WebhookEvent,
)
from .services import (
    confirm_payment,
    fail_payment,
    cancel_payment,
    release_payment_holds,
)


def home(request):
    shows = Show.objects.filter(
        is_active=True
    ).order_by("show_time")

    return render(
        request,
        "payments/checkout.html",
        {
            "shows": shows,
        },
    )


@login_required
def create_order(request, show_id):

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required."},
            status=405,
        )

    show = get_object_or_404(
        Show.objects.prefetch_related("seats"),
        pk=show_id,
        is_active=True,
    )

    try:
        seat_numbers = [
            int(value)
            for value in request.POST.getlist("seats")
        ]
    except ValueError:

        return JsonResponse(
            {"error": "Invalid seat selection."},
            status=400,
        )

    seat_numbers = sorted(set(seat_numbers))

    if not seat_numbers:
        return JsonResponse(
            {"error": "Select at least one seat."},
            status=400,
        )

    with transaction.atomic():

        locked_seats = list(
            Seat.objects
            .select_for_update()
            .filter(
                show=show,
                seat_number__in=seat_numbers,
            )
            .order_by("seat_number")
        )

        if len(locked_seats) != len(seat_numbers):

            return JsonResponse(
                {"error": "One or more seats do not exist."},
                status=400,
            )

        # Release holds whose payment attempt has failed,
        # been cancelled, or expired before checking.
        SeatHold.objects.filter(
            seat__show=show,
            status=SeatHold.STATUS_ACTIVE,
            payment__status__in=[
                Payment.STATUS_FAILED,
                Payment.STATUS_CANCELLED,
            ],
        ).update(
            status=SeatHold.STATUS_RELEASED,
            released_at=timezone.now(),
        )

        for seat in locked_seats:

            if seat.status != Seat.STATUS_AVAILABLE:

                return JsonResponse(
                    {
                        "error": (
                            f"Seat {seat.seat_number} "
                            "is not available."
                        )
                    },
                    status=409,
                )

        amount = (
            Decimal(show.ticket_price)
            * Decimal(len(seat_numbers))
        )

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET,
            )
        )

        razorpay_order = client.order.create(
            {
                "amount": int(amount * 100),
                "currency": "INR",
                "receipt": (
                    f"show-{show.id}-"
                    f"user-{request.user.id}-"
                    f"{timezone.now().timestamp()}"
                ),
                "payment_capture": 1,
            }
        )

        payment = Payment.objects.create(
            user=request.user,
            show=show,
            order_id=razorpay_order["id"],
            amount=amount,
            currency="INR",
            status=Payment.STATUS_PENDING,
            selected_seats=seat_numbers,
        )

        for seat in locked_seats:

            seat.status = Seat.STATUS_HELD

            seat.save(
                update_fields=["status"]
            )

            SeatHold.objects.create(
                payment=payment,
                seat=seat,
            )

    return redirect(
        "checkout_page",
        payment_id=payment.id,
    )

@login_required
def payment_success(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required."},
            status=405,
        )

    order_id = request.POST.get(
        "razorpay_order_id"
    )

    payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    signature = request.POST.get(
        "razorpay_signature"
    )

    if not all(
        [
            order_id,
            payment_id,
            signature,
        ]
    ):
        return JsonResponse(
            {"error": "Missing payment verification data."},
            status=400,
        )

    try:

        payment = (
            Payment.objects
            .select_related("user", "show")
            .get(
                order_id=order_id,
                user=request.user,
            )
        )

        confirm_payment(
            order_id=payment.order_id,
            payment_id=payment_id,
            signature=signature,
        )

    except razorpay.errors.SignatureVerificationError:

        return JsonResponse(
            {"error": "Payment signature verification failed."},
            status=400,
        )

    except Payment.DoesNotExist:

        return JsonResponse(
            {"error": "Payment order not found."},
            status=404,
        )

    except Exception as exc:

        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

    return redirect(
        "payment_result",
        order_id=order_id,
    )


@login_required
def payment_failed(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required."},
            status=405,
        )

    order_id = request.POST.get(
        "order_id"
    )

    reason = request.POST.get(
        "reason",
        "Payment failed.",
    )

    if not order_id:
        return JsonResponse(
            {"error": "Order ID required."},
            status=400,
        )

    payment = get_object_or_404(
        Payment,
        order_id=order_id,
        user=request.user,
    )

    fail_payment(
        order_id=payment.order_id,
        reason=reason,
    )

    return redirect(
        "payment_result",
        order_id=order_id,
    )


@login_required
def payment_cancelled(request):

    order_id = request.POST.get(
        "order_id"
    )

    if not order_id:
        messages.error(
            request,
            "Payment order was not found.",
        )

        return redirect("home")

    payment = get_object_or_404(
        Payment,
        order_id=order_id,
        user=request.user,
    )

    cancel_payment(
        payment.order_id
    )

    return redirect(
        "payment_result",
        order_id=order_id,
    )


@login_required
def payment_result(request, order_id):

    payment = get_object_or_404(
        Payment.objects.select_related(
            "show",
            "user",
        ),
        order_id=order_id,
        user=request.user,
    )

    booking = getattr(
        payment,
        "booking",
        None,
    )

    return render(
        request,
        "payments/payment_result.html",
        {
            "payment": payment,
            "booking": booking,
        },
    )


@login_required
def payment_retry(request, payment_id):

    original_payment = get_object_or_404(
        Payment,
        pk=payment_id,
        user=request.user,
    )

    if original_payment.status == Payment.STATUS_SUCCESS:

        messages.info(
            request,
            "This payment was already successful.",
        )

        return redirect(
            "payment_result",
            order_id=original_payment.order_id,
        )

    active_holds = SeatHold.objects.filter(
        payment=original_payment,
        status=SeatHold.STATUS_ACTIVE,
    ).exists()

    if active_holds:

        return redirect(
            "payment_result",
            order_id=original_payment.order_id,
        )

    request.POST = request.POST.copy()

    request.POST.setlist(
        "seats",
        [
            str(seat)
            for seat in original_payment.selected_seats
        ],
    )

    return create_order(
        request,
        original_payment.show_id,
    )


@login_required
def payment_history(request):

    payments = (
        Payment.objects
        .filter(user=request.user)
        .select_related("show")
        .prefetch_related("seat_holds")
        .order_by("-created_at")
    )

    bookings = (
        Booking.objects
        .filter(user=request.user)
        .select_related("show", "payment")
        .order_by("-created_at")
    )

    return render(
        request,
        "payments/payment_history.html",
        {
            "payments": payments,
            "bookings": bookings,
        },
    )

@login_required
def checkout_page(request, payment_id):

    payment = get_object_or_404(
        Payment,
        pk=payment_id,
        user=request.user,
        status=Payment.STATUS_PENDING,
    )

    return render(
        request,
        "payments/razorpay_checkout.html",
        {
            "payment": payment,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "amount_paise": int(
                payment.amount * 100
            ),
        },
    )

@transaction.atomic
def webhook(request):

    if request.method != "POST":

        return HttpResponse(
            "Method not allowed.",
            status=405,
        )

    received_signature = request.headers.get(
        "X-Razorpay-Signature"
    )

    if not received_signature:

        return HttpResponse(
            "Missing signature.",
            status=400,
        )

    raw_body = request.body

    expected_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(
            "utf-8"
        ),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        expected_signature,
        received_signature,
    ):

        return HttpResponse(
            "Invalid signature.",
            status=400,
        )

    try:
        payload = json.loads(
            raw_body.decode("utf-8")
        )

    except (UnicodeDecodeError, json.JSONDecodeError):

        return HttpResponse(
            "Invalid JSON.",
            status=400,
        )

    event_type = payload.get(
        "event",
        ""
    )

    event_id = (
        request.headers.get(
            "X-Razorpay-Event-Id"
        )
        or payload.get("id")
    )

    if not event_id:

        event_id = (
            f"{event_type}-"
            f"{hashlib.sha256(raw_body).hexdigest()}"
        )

    webhook_event, created = (
        WebhookEvent.objects.get_or_create(
            event_id=event_id,
            defaults={
                "event_type": event_type,
                "payload": payload,
            },
        )
    )

    if not created and webhook_event.processed:

        return HttpResponse(
            "Already processed.",
            status=200,
        )

    try:

        payment_entity = (
            payload
            .get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        order_id = payment_entity.get(
            "order_id"
        )

        payment_id = payment_entity.get(
            "id"
        )

        if event_type == "payment.captured" and order_id:

            payment = Payment.objects.get(
                order_id=order_id
            )

            # Webhook itself does not trust the browser.
            # Fetch status from Razorpay API before confirmation.
            client = razorpay.Client(
                auth=(
                    settings.RAZORPAY_KEY_ID,
                    settings.RAZORPAY_KEY_SECRET,
                )
            )

            remote_payment = client.payment.fetch(
                payment_id
            )

            if remote_payment.get("status") == "captured":

                payment.payment_id = payment_id
                payment.transaction_id = payment_id

                payment.save(
                    update_fields=[
                        "payment_id",
                        "transaction_id",
                        "updated_at",
                    ]
                )

                # Browser signature is not used here.
                # Webhook signature + Razorpay API state
                # establish the payment state.
                confirm_payment_from_webhook(
                    payment
                )

        elif event_type == "payment.failed" and order_id:

            fail_payment(
                order_id=order_id,
                payment_id=payment_id,
                reason="Razorpay reported payment failure.",
            )

        elif event_type == "order.paid" and order_id:

            payment = Payment.objects.get(
                order_id=order_id
            )

            payment.payment_id = payment_id
            payment.transaction_id = payment_id

            payment.save(
                update_fields=[
                    "payment_id",
                    "transaction_id",
                    "updated_at",
                ]
            )

        webhook_event.processed = True

        webhook_event.save(
            update_fields=["processed"]
        )

    except Payment.DoesNotExist:

        return HttpResponse(
            "Payment not found.",
            status=404,
        )

    except Exception:

        # Returning a non-2xx tells Razorpay that the
        # event was not processed, allowing retry delivery.
        return HttpResponse(
            "Webhook processing failed.",
            status=500,
        )

    return HttpResponse(
        "OK",
        status=200,
    )


def confirm_payment_from_webhook(payment):

    with transaction.atomic():

        locked_payment = (
            Payment.objects
            .select_for_update()
            .get(
                pk=payment.pk
            )
        )

        if locked_payment.status == Payment.STATUS_SUCCESS:

            return locked_payment

        locked_payment.status = Payment.STATUS_SUCCESS

        locked_payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        holds = list(
            SeatHold.objects
            .select_for_update()
            .select_related("seat")
            .filter(
                payment=locked_payment,
                status=SeatHold.STATUS_ACTIVE,
            )
        )

        if not holds:

            return locked_payment

        booking, _ = Booking.objects.get_or_create(
            payment=locked_payment,
            defaults={
                "user": locked_payment.user,
                "show": locked_payment.show,
                "seats": locked_payment.selected_seats,
                "amount": locked_payment.amount,
                "status": Booking.STATUS_CONFIRMED,
            },
        )

        for hold in holds:

            hold.status = SeatHold.STATUS_BOOKED

            hold.seat.status = Seat.STATUS_BOOKED

            hold.seat.save(
                update_fields=["status"]
            )

            hold.save(
                update_fields=["status"]
            )

        return locked_payment
