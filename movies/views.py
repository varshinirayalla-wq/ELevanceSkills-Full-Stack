from django.shortcuts import render

# Create your views here.
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ReviewForm
from .models import (
    Booking,
    Movie,
    Review,
    ReviewReport,
    ShowSchedule,
)


def movie_list(request):
    movies = (
        Movie.objects
        .filter(is_active=True)
        .prefetch_related("genres", "languages", "posters")
    )

    recently_released = movies.order_by("-release_date")[:6]

    thirty_days_ago = timezone.now() - timedelta(days=30)

    trending = (
        movies
        .filter(
            shows__bookings__booked_at__gte=thirty_days_ago,
            shows__bookings__status="CONFIRMED",
        )
        .annotate(
            booking_count=Count(
                "shows__bookings",
                filter=Q(
                    shows__bookings__booked_at__gte=thirty_days_ago,
                    shows__bookings__status="CONFIRMED",
                ),
                distinct=True,
            )
        )
        .order_by("-booking_count", "-release_date")[:6]
    )

    context = {
        "movies": movies,
        "recently_released": recently_released,
        "trending": trending,
    }

    return render(
        request,
        "movies/movie_list.html",
        context,
    )


def movie_detail(request, pk):
    movie = get_object_or_404(
        Movie.objects
        .prefetch_related(
            "genres",
            "languages",
            "cast_members",
            "posters",
        ),
        pk=pk,
        is_active=True,
    )

    shows = (
        ShowSchedule.objects
        .filter(
            movie=movie,
            starts_at__gte=timezone.now(),
            is_active=True,
        )
        .select_related("theater")
        .order_by("starts_at")
    )

    reviews = (
        movie.reviews
        .filter(is_hidden=False)
        .select_related("user")
    )

    # Find movies sharing either genre or language.
    similar_movies = (
        Movie.objects
        .filter(is_active=True)
        .filter(
            Q(genres__in=movie.genres.all())
            | Q(languages__in=movie.languages.all())
        )
        .exclude(pk=movie.pk)
        .annotate(
            match_count=Count(
                "genres",
                filter=Q(genres__in=movie.genres.all()),
                distinct=True,
            )
        )
        .distinct()
        .order_by("-match_count", "-release_date")[:6]
    )

    thirty_days_ago = timezone.now() - timedelta(days=30)

    trending_movies = (
        Movie.objects
        .filter(
            is_active=True,
            shows__bookings__booked_at__gte=thirty_days_ago,
            shows__bookings__status="CONFIRMED",
        )
        .exclude(pk=movie.pk)
        .annotate(
            booking_count=Count(
                "shows__bookings",
                distinct=True,
            )
        )
        .order_by("-booking_count", "-release_date")[:6]
    )

    recently_released = (
        Movie.objects
        .filter(is_active=True)
        .exclude(pk=movie.pk)
        .order_by("-release_date")[:6]
    )

    user_can_review = False

    if request.user.is_authenticated:
        user_can_review = Booking.objects.filter(
            user=request.user,
            show__movie=movie,
            status="CONFIRMED",
            show__starts_at__lt=timezone.now(),
        ).exists()

    context = {
        "movie": movie,
        "shows": shows,
        "reviews": reviews,
        "similar_movies": similar_movies,
        "trending_movies": trending_movies,
        "recently_released": recently_released,
        "user_can_review": user_can_review,
    }

    return render(
        request,
        "movies/movie_detail.html",
        context,
    )


@login_required
@transaction.atomic
def book_show(request, movie_id, show_id):
    if request.method != "POST":
        return redirect(
            "movie_detail",
            pk=movie_id,
        )

    show = get_object_or_404(
        ShowSchedule.objects.select_for_update(),
        pk=show_id,
        movie_id=movie_id,
        is_active=True,
    )

    if show.starts_at <= timezone.now():
        messages.error(
            request,
            "This show is no longer available for booking.",
        )
        return redirect(
            "movie_detail",
            pk=movie_id,
        )

    if show.available_seats < 1:
        messages.error(
            request,
            "No seats are available.",
        )
        return redirect(
            "movie_detail",
            pk=movie_id,
        )

    Booking.objects.create(
        user=request.user,
        show=show,
        seats=1,
        status="CONFIRMED",
    )

    show.available_seats -= 1
    show.save(update_fields=["available_seats"])

    messages.success(
        request,
        "Your booking was confirmed.",
    )

    return redirect(
        "movie_detail",
        pk=movie_id,
    )


@login_required
def create_review(request, movie_id):
    movie = get_object_or_404(
        Movie,
        pk=movie_id,
        is_active=True,
    )

    has_watched = Booking.objects.filter(
        user=request.user,
        show__movie=movie,
        status="CONFIRMED",
        show__starts_at__lt=timezone.now(),
    ).filter(
        show__starts_at__lte=timezone.now()
    ).exists()

    if not has_watched:
        messages.error(
            request,
            "You can review this movie only after watching a booked show.",
        )
        return redirect(
            "movie_detail",
            pk=movie.pk,
        )

    existing_review = Review.objects.filter(
        user=request.user,
        movie=movie,
    ).first()

    if existing_review:
        messages.info(
            request,
            "You have already reviewed this movie.",
        )
        return redirect(
            "edit_review",
            review_id=existing_review.pk,
        )

    if request.method == "POST":
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.movie = movie
            review.save()

            messages.success(
                request,
                "Your review has been published.",
            )

            return redirect(
                "movie_detail",
                pk=movie.pk,
            )
    else:
        form = ReviewForm()

    return render(
        request,
        "movies/review_form.html",
        {
            "form": form,
            "movie": movie,
            "page_title": "Write Review",
        },
    )


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(
        Review,
        pk=review_id,
        user=request.user,
    )

    if request.method == "POST":
        form = ReviewForm(
            request.POST,
            instance=review,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Your review was updated.",
            )

            return redirect(
                "movie_detail",
                pk=review.movie.pk,
            )
    else:
        form = ReviewForm(instance=review)

    return render(
        request,
        "movies/review_form.html",
        {
            "form": form,
            "movie": review.movie,
            "page_title": "Edit Review",
        },
    )


@login_required
def report_review(request, review_id):
    review = get_object_or_404(
        Review,
        pk=review_id,
        is_hidden=False,
    )

    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()

        if not reason:
            messages.error(
                request,
                "Please provide a reason for reporting the review.",
            )
            return redirect(
                "movie_detail",
                pk=review.movie.pk,
            )

        ReviewReport.objects.get_or_create(
            review=review,
            reported_by=request.user,
            defaults={
                "reason": reason,
            },
        )

        messages.success(
            request,
            "The review has been reported.",
        )

    return redirect(
        "movie_detail",
        pk=review.movie.pk,
    )