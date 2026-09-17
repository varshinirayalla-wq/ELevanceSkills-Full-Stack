from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.db.models.functions import (
    ExtractHour,
    TruncDay,
    TruncMonth,
    TruncWeek,
    TruncYear,
)
from django.utils import timezone

from .models import Booking, Payment


def get_date_range(start_date=None, end_date=None):
    """
    Convert optional date values into timezone-aware datetime boundaries.

    When no dates are supplied, the dashboard uses the previous 365 days
    up to the current local date.
    """

    today = timezone.localdate()

    if start_date is None:
        start_date = today - timedelta(days=365)

    if end_date is None:
        end_date = today

    start_datetime = timezone.make_aware(
        datetime.combine(start_date, time.min)
    )

    end_datetime = timezone.make_aware(
        datetime.combine(end_date, time.max)
    )

    return start_datetime, end_datetime


def filtered_bookings(start_date=None, end_date=None):
    """
    Return a lazy QuerySet for bookings inside the selected date range.

    The QuerySet is not evaluated here, so records are not loaded into
    Python memory unnecessarily.
    """

    start_datetime, end_datetime = get_date_range(
        start_date,
        end_date,
    )

    return Booking.objects.filter(
        booked_at__range=(
            start_datetime,
            end_datetime,
        )
    )


def revenue_summary(start_date=None, end_date=None):
    """
    Return the main revenue KPIs for confirmed bookings.
    """

    bookings = filtered_bookings(
        start_date,
        end_date,
    ).filter(
        status=Booking.CONFIRMED
    )

    result = bookings.aggregate(
        total_revenue=Sum("amount"),
        total_bookings=Count("id"),
        total_seats=Sum("seats_booked"),
    )

    return {
        "total_revenue": result["total_revenue"] or 0,
        "total_bookings": result["total_bookings"] or 0,
        "total_seats": result["total_seats"] or 0,
    }


def revenue_by_period(
    start_date=None,
    end_date=None,
    period="day",
):
    """
    Return revenue and booking totals grouped by day, week, month or year.
    """

    bookings = filtered_bookings(
        start_date,
        end_date,
    ).filter(
        status=Booking.CONFIRMED
    )

    if period == "day":
        truncated = TruncDay("booked_at")

    elif period == "week":
        truncated = TruncWeek("booked_at")

    elif period == "month":
        truncated = TruncMonth("booked_at")

    elif period == "year":
        truncated = TruncYear("booked_at")

    else:
        raise ValueError(
            "Invalid period. Use day, week, month or year."
        )

    return list(
        bookings
        .annotate(period=truncated)
        .values("period")
        .annotate(
            revenue=Sum("amount"),
            bookings=Count("id"),
        )
        .order_by("period")
    )


def booking_trends(start_date=None, end_date=None):
    """
    Return daily booking, confirmed and cancelled counts.
    """

    bookings = filtered_bookings(
        start_date,
        end_date,
    )

    return list(
        bookings
        .annotate(day=TruncDay("booked_at"))
        .values("day")
        .annotate(
            total_bookings=Count("id"),
            confirmed_bookings=Count(
                "id",
                filter=Q(
                    status=Booking.CONFIRMED
                ),
            ),
            cancelled_bookings=Count(
                "id",
                filter=Q(
                    status=Booking.CANCELLED
                ),
            ),
        )
        .order_by("day")
    )


def theater_occupancy(
    start_date=None,
    end_date=None,
):
    """
    Calculate theater occupancy for the selected date range.

    Capacity is calculated as:

        theater seats × number of active booking days

    Occupancy is then:

        confirmed seats booked
        ---------------------- × 100
        available capacity
    """

    bookings = filtered_bookings(
        start_date,
        end_date,
    ).filter(
        status=Booking.CONFIRMED
    )

    day_expression = TruncDay("booked_at")

    rows = list(
        bookings
        .annotate(
            booking_day=day_expression,
        )
        .values(
            "theater__name",
            "theater__total_seats",
        )
        .annotate(
            booked_seats=Sum("seats_booked"),
            active_days=Count(
                "booking_day",
                distinct=True,
            ),
        )
        .order_by("-booked_seats")
    )

    for row in rows:
        total_seats = row["theater__total_seats"] or 0
        active_days = row["active_days"] or 0
        booked_seats = row["booked_seats"] or 0

        total_capacity = total_seats * active_days

        row["total_capacity"] = total_capacity

        if total_capacity:
            row["occupancy_percentage"] = round(
                (
                    booked_seats / total_capacity
                ) * 100,
                2,
            )
        else:
            row["occupancy_percentage"] = 0

    return rows


def most_booked_movies(
    start_date=None,
    end_date=None,
    limit=10,
):
    """
    Return the highest-performing movies by confirmed bookings.
    """

    bookings = filtered_bookings(
        start_date,
        end_date,
    ).filter(
        status=Booking.CONFIRMED
    )

    return list(
        bookings
        .values(
            "movie__name",
        )
        .annotate(
            booking_count=Count("id"),
            seats_booked=Sum("seats_booked"),
            revenue=Sum("amount"),
        )
        .order_by(
            "-booking_count",
            "-seats_booked",
        )[:limit]
    )


def top_theaters(
    start_date=None,
    end_date=None,
    limit=10,
):
    """
    Return the best-performing theaters by revenue.
    """

    bookings = filtered_bookings(
        start_date,
        end_date,
    ).filter(
        status=Booking.CONFIRMED
    )

    return list(
        bookings
        .values(
            "theater__name",
        )
        .annotate(
            booking_count=Count("id"),
            seats_booked=Sum("seats_booked"),
            revenue=Sum("amount"),
        )
        .order_by(
            "-revenue",
            "-booking_count",
        )[:limit]
    )


def peak_booking_hours(
    start_date=None,
    end_date=None,
):
    """
    Return booking counts grouped by hour of the day.
    """

    bookings = filtered_bookings(
        start_date,
        end_date,
    )

    return list(
        bookings
        .annotate(
            hour=ExtractHour("booked_at"),
        )
        .values("hour")
        .annotate(
            booking_count=Count("id"),
        )
        .order_by(
            "-booking_count"
        )
    )


def cancellation_statistics(
    start_date=None,
    end_date=None,
):
    """
    Return total bookings, cancellations and cancellation percentage.
    """

    bookings = filtered_bookings(
        start_date,
        end_date,
    )

    result = bookings.aggregate(
        total=Count("id"),
        cancelled=Count(
            "id",
            filter=Q(
                status=Booking.CANCELLED
            ),
        ),
    )

    total = result["total"] or 0
    cancelled = result["cancelled"] or 0

    cancellation_percentage = (
        (cancelled / total) * 100
        if total
        else 0
    )

    return {
        "total_bookings": total,
        "cancelled_bookings": cancelled,
        "cancellation_percentage": round(
            cancellation_percentage,
            2,
        ),
    }


def refund_statistics(
    start_date=None,
    end_date=None,
):
    """
    Return refund count and refund amount.
    """

    start_datetime, end_datetime = get_date_range(
        start_date,
        end_date,
    )

    payments = Payment.objects.filter(
        created_at__range=(
            start_datetime,
            end_datetime,
        )
    )

    result = payments.aggregate(
        refund_count=Count(
            "id",
            filter=Q(
                status=Payment.REFUNDED
            ),
        ),
        refund_amount=Sum(
            "refund_amount",
            filter=Q(
                status=Payment.REFUNDED
            ),
        ),
    )

    return {
        "refund_count": result["refund_count"] or 0,
        "refund_amount": result["refund_amount"] or 0,
    }


def user_growth(
    start_date=None,
    end_date=None,
):
    """
    Return new users grouped by month.
    """

    start_datetime, end_datetime = get_date_range(
        start_date,
        end_date,
    )

    User = get_user_model()

    return list(
        User.objects
        .filter(
            date_joined__range=(
                start_datetime,
                end_datetime,
            )
        )
        .annotate(
            month=TruncMonth("date_joined"),
        )
        .values("month")
        .annotate(
            new_users=Count("id"),
        )
        .order_by("month")
    )
def revenue_window_totals(reference_date=None):
    """
    Calculate revenue for the day, week, month and year
    containing the selected reference date.
    """

    reference_date = (
        reference_date
        or timezone.localdate()
    )

    daily_revenue = revenue_summary(
        reference_date,
        reference_date,
    )["total_revenue"]

    week_start = (
        reference_date
        - timedelta(
            days=reference_date.weekday()
        )
    )

    weekly_revenue = revenue_summary(
        week_start,
        reference_date,
    )["total_revenue"]

    month_start = reference_date.replace(
        day=1
    )

    monthly_revenue = revenue_summary(
        month_start,
        reference_date,
    )["total_revenue"]

    year_start = reference_date.replace(
        month=1,
        day=1,
    )

    yearly_revenue = revenue_summary(
        year_start,
        reference_date,
    )["total_revenue"]

    return {
        "daily": daily_revenue,
        "weekly": weekly_revenue,
        "monthly": monthly_revenue,
        "yearly": yearly_revenue,
        "reference_date": reference_date,
    }