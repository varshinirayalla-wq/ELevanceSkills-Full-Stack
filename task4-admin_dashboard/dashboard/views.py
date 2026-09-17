import csv
from datetime import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .services import (
    booking_trends,
    cancellation_statistics,
    most_booked_movies,
    peak_booking_hours,
    refund_statistics,
    revenue_by_period,
    revenue_summary,
    revenue_window_totals,
    theater_occupancy,
    top_theaters,
    user_growth,
)


def parse_date(value):
    """
    Convert YYYY-MM-DD into a Python date.
    Return None if the value is invalid.
    """

    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        return None


def build_date_filters(request):
    """
    Read and validate dashboard date filters.
    """

    start_date_text = request.GET.get(
        "start_date",
        "",
    )

    end_date_text = request.GET.get(
        "end_date",
        "",
    )

    start_date = parse_date(
        start_date_text
    )

    end_date = parse_date(
        end_date_text
    )

    if start_date and end_date:
        if start_date > end_date:
            messages.error(
                request,
                "Start date cannot be after end date.",
            )
            start_date = None
            end_date = None

    return (
        start_date,
        end_date,
        start_date_text,
        end_date_text,
    )


@staff_member_required(login_url="login")
@permission_required(
    "dashboard.view_booking",
    raise_exception=True,
)
def dashboard_home(request):

    (
        start_date,
        end_date,
        start_date_text,
        end_date_text,
    ) = build_date_filters(request)

    summary = revenue_summary(
        start_date,
        end_date,
    )

    monthly_revenue = revenue_by_period(
        start_date,
        end_date,
        period="month",
    )

    daily_revenue = revenue_by_period(
        start_date,
        end_date,
        period="day",
    )

    weekly_revenue = revenue_by_period(
        start_date,
        end_date,
        period="week",
    )

    yearly_revenue = revenue_by_period(
        start_date,
        end_date,
        period="year",
    )

    booking_trend_rows = booking_trends(
        start_date,
        end_date,
    )

    occupancy_rows = theater_occupancy(
        start_date,
        end_date,
    )

    movie_rows = most_booked_movies(
        start_date,
        end_date,
        limit=10,
    )

    theater_rows = top_theaters(
        start_date,
        end_date,
        limit=10,
    )

    peak_rows = peak_booking_hours(
        start_date,
        end_date,
    )

    cancellation_stats = cancellation_statistics(
        start_date,
        end_date,
    )

    refund_stats = refund_statistics(
        start_date,
        end_date,
    )

    user_growth_rows = user_growth(
        start_date,
        end_date,
    )

    reference_date = (
        end_date
        if end_date
        else timezone.localdate()
    )

    revenue_windows = revenue_window_totals(
        reference_date
    )

    # -----------------------------
    # Chart data
    # -----------------------------

    monthly_chart = {
        "labels": [
            timezone.localtime(
                row["period"]
            ).strftime("%b %Y")
            for row in monthly_revenue
        ],
        "revenue": [
            float(row["revenue"] or 0)
            for row in monthly_revenue
        ],
    }

    daily_chart = {
        "labels": [
            timezone.localtime(
                row["day"]
            ).strftime("%d %b")
            for row in booking_trend_rows
        ],
        "total": [
            row["total_bookings"]
            for row in booking_trend_rows
        ],
        "confirmed": [
            row["confirmed_bookings"]
            for row in booking_trend_rows
        ],
        "cancelled": [
            row["cancelled_bookings"]
            for row in booking_trend_rows
        ],
    }

    occupancy_chart = {
        "labels": [
            row["theater__name"]
            for row in occupancy_rows
        ],
        "values": [
            row["occupancy_percentage"]
            for row in occupancy_rows
        ],
    }

    movie_chart = {
        "labels": [
            row["movie__name"]
            for row in movie_rows
        ],
        "values": [
            row["booking_count"]
            for row in movie_rows
        ],
    }

    theater_chart = {
        "labels": [
            row["theater__name"]
            for row in theater_rows
        ],
        "values": [
            float(row["revenue"] or 0)
            for row in theater_rows
        ],
    }

    peak_hours = {
        hour: 0
        for hour in range(24)
    }

    for row in peak_rows:
        peak_hours[int(row["hour"])] = row[
            "booking_count"
        ]

    peak_chart = {
        "labels": [
            f"{hour:02d}:00"
            for hour in range(24)
        ],
        "values": [
            peak_hours[hour]
            for hour in range(24)
        ],
    }

    user_growth_chart = {
        "labels": [
            timezone.localtime(
                row["month"]
            ).strftime("%b %Y")
            for row in user_growth_rows
        ],
        "values": [
            row["new_users"]
            for row in user_growth_rows
        ],
    }

    context = {
        "summary": summary,
        "revenue_windows": revenue_windows,

        "daily_revenue": daily_revenue,
        "weekly_revenue": weekly_revenue,
        "monthly_revenue": monthly_revenue,
        "yearly_revenue": yearly_revenue,

        "booking_trends": booking_trend_rows,
        "theater_occupancy": occupancy_rows,
        "most_booked_movies": movie_rows,
        "top_theaters": theater_rows,
        "peak_booking_hours": peak_rows,

        "cancellation_stats": cancellation_stats,
        "refund_stats": refund_stats,

        "user_growth": user_growth_rows,

        "monthly_chart": monthly_chart,
        "daily_chart": daily_chart,
        "occupancy_chart": occupancy_chart,
        "movie_chart": movie_chart,
        "theater_chart": theater_chart,
        "peak_chart": peak_chart,
        "user_growth_chart": user_growth_chart,

        "start_date": start_date_text,
        "end_date": end_date_text,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )


@staff_member_required(login_url="login")
@permission_required(
    "dashboard.view_booking",
    raise_exception=True,
)
def export_csv(request):

    (
        start_date,
        end_date,
        _,
        _,
    ) = build_date_filters(request)

    response = HttpResponse(
        content_type="text/csv"
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; '
        'filename="admin_dashboard_report.csv"'
    )

    writer = csv.writer(response)

    # -----------------------------
    # Report information
    # -----------------------------

    writer.writerow(
        ["ADMIN DASHBOARD REPORT"]
    )

    writer.writerow(
        [
            "Start Date",
            start_date or "Last 365 days",
        ]
    )

    writer.writerow(
        [
            "End Date",
            end_date or timezone.localdate(),
        ]
    )

    writer.writerow([])

    # -----------------------------
    # Summary
    # -----------------------------

    summary = revenue_summary(
        start_date,
        end_date,
    )

    writer.writerow(
        [
            "SUMMARY",
        ]
    )

    writer.writerow(
        [
            "Metric",
            "Value",
        ]
    )

    writer.writerow(
        [
            "Total Revenue",
            summary["total_revenue"],
        ]
    )

    writer.writerow(
        [
            "Confirmed Bookings",
            summary["total_bookings"],
        ]
    )

    writer.writerow(
        [
            "Seats Booked",
            summary["total_seats"],
        ]
    )

    writer.writerow([])

    # -----------------------------
    # Revenue by month
    # -----------------------------

    writer.writerow(
        ["MONTHLY REVENUE"]
    )

    writer.writerow(
        [
            "Month",
            "Bookings",
            "Revenue",
        ]
    )

    for row in revenue_by_period(
        start_date,
        end_date,
        period="month",
    ):
        writer.writerow(
            [
                row["period"],
                row["bookings"],
                row["revenue"],
            ]
        )

    writer.writerow([])

    # -----------------------------
    # Booking trends
    # -----------------------------

    writer.writerow(
        ["BOOKING TRENDS"]
    )

    writer.writerow(
        [
            "Date",
            "Total",
            "Confirmed",
            "Cancelled",
        ]
    )

    for row in booking_trends(
        start_date,
        end_date,
    ):
        writer.writerow(
            [
                row["day"],
                row["total_bookings"],
                row["confirmed_bookings"],
                row["cancelled_bookings"],
            ]
        )

    writer.writerow([])

    # -----------------------------
    # Theater occupancy
    # -----------------------------

    writer.writerow(
        ["THEATER OCCUPANCY"]
    )

    writer.writerow(
        [
            "Theater",
            "Booked Seats",
            "Total Capacity",
            "Occupancy %",
        ]
    )

    for row in theater_occupancy(
        start_date,
        end_date,
    ):
        writer.writerow(
            [
                row["theater__name"],
                row["booked_seats"],
                row["total_capacity"],
                row["occupancy_percentage"],
            ]
        )

    writer.writerow([])

    # -----------------------------
    # Movie performance
    # -----------------------------

    writer.writerow(
        ["MOST BOOKED MOVIES"]
    )

    writer.writerow(
        [
            "Movie",
            "Bookings",
            "Seats",
            "Revenue",
        ]
    )

    for row in most_booked_movies(
        start_date,
        end_date,
    ):
        writer.writerow(
            [
                row["movie__name"],
                row["booking_count"],
                row["seats_booked"],
                row["revenue"],
            ]
        )

    writer.writerow([])

    # -----------------------------
    # Theater performance
    # -----------------------------

    writer.writerow(
        ["TOP PERFORMING THEATERS"]
    )

    writer.writerow(
        [
            "Theater",
            "Bookings",
            "Seats",
            "Revenue",
        ]
    )

    for row in top_theaters(
        start_date,
        end_date,
    ):
        writer.writerow(
            [
                row["theater__name"],
                row["booking_count"],
                row["seats_booked"],
                row["revenue"],
            ]
        )

    writer.writerow([])

    # -----------------------------
    # Peak hours
    # -----------------------------

    writer.writerow(
        ["PEAK BOOKING HOURS"]
    )

    writer.writerow(
        [
            "Hour",
            "Bookings",
        ]
    )

    for row in peak_booking_hours(
        start_date,
        end_date,
    ):
        writer.writerow(
            [
                f'{int(row["hour"]):02d}:00',
                row["booking_count"],
            ]
        )

    writer.writerow([])

    # -----------------------------
    # Cancellation
    # -----------------------------

    cancellation = cancellation_statistics(
        start_date,
        end_date,
    )

    writer.writerow(
        ["CANCELLATION STATISTICS"]
    )

    writer.writerow(
        [
            "Total Bookings",
            cancellation["total_bookings"],
        ]
    )

    writer.writerow(
        [
            "Cancelled Bookings",
            cancellation["cancelled_bookings"],
        ]
    )

    writer.writerow(
        [
            "Cancellation Percentage",
            cancellation[
                "cancellation_percentage"
            ],
        ]
    )

    writer.writerow([])

    # -----------------------------
    # Refunds
    # -----------------------------

    refunds = refund_statistics(
        start_date,
        end_date,
    )

    writer.writerow(
        ["REFUND STATISTICS"]
    )

    writer.writerow(
        [
            "Refund Count",
            refunds["refund_count"],
        ]
    )

    writer.writerow(
        [
            "Refund Amount",
            refunds["refund_amount"],
        ]
    )

    writer.writerow([])

    # -----------------------------
    # User growth
    # -----------------------------

    writer.writerow(
        ["USER GROWTH"]
    )

    writer.writerow(
        [
            "Month",
            "New Users",
        ]
    )

    for row in user_growth(
        start_date,
        end_date,
    ):
        writer.writerow(
            [
                row["month"],
                row["new_users"],
            ]
        )

    return response