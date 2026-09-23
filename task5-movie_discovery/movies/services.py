from django.db.models import (
    Count,
    Exists,
    ExpressionWrapper,
    F,
    IntegerField,
    Max,
    OuterRef,
    Q,
    Subquery,
    Value,
)
from django.utils import timezone

from .models import Booking, Movie, RecentlyViewed, Show


def build_movie_queryset(filters=None):
    """
    Build the movie-discovery QuerySet.

    Show-related filtering is performed with EXISTS subqueries
    instead of joining the Show table directly into the main
    Movie query. This reduces duplicate movie rows and avoids
    unnecessary DISTINCT/GROUP BY operations.

    The QuerySet remains lazy until evaluated.
    """

    filters = filters or {}

    now = timezone.now()

    # ---------------------------------------------------------
    # Build the subquery representing an eligible show.
    # ---------------------------------------------------------

    matching_shows = Show.objects.filter(
        movie=OuterRef("pk"),
        is_active=True,
        show_time__gte=now,
    )

    # ---------------------------------------------------------
    # City filter
    # ---------------------------------------------------------

    city_id = filters.get("city")

    if city_id:
        matching_shows = matching_shows.filter(
            theater__city_id=city_id
        )

    # ---------------------------------------------------------
    # Theater filter
    # ---------------------------------------------------------

    theater_id = filters.get("theater")

    if theater_id:
        matching_shows = matching_shows.filter(
            theater_id=theater_id
        )

    # ---------------------------------------------------------
    # Show date filter
    # ---------------------------------------------------------

    show_date = filters.get("show_date")

    if show_date:
        matching_shows = matching_shows.filter(
            show_time__date=show_date
        )

    # ---------------------------------------------------------
    # Show time filters
    # ---------------------------------------------------------

    show_time_from = filters.get(
        "show_time_from"
    )

    if show_time_from:
        matching_shows = matching_shows.filter(
            show_time__time__gte=show_time_from
        )

    show_time_to = filters.get(
        "show_time_to"
    )

    if show_time_to:
        matching_shows = matching_shows.filter(
            show_time__time__lte=show_time_to
        )

    # ---------------------------------------------------------
    # Main Movie QuerySet
    # ---------------------------------------------------------

    queryset = (
        Movie.objects
        .select_related("language")
        .prefetch_related("genres")
        .annotate(
            has_matching_show=Exists(
                matching_shows
            )
        )
        .filter(
            has_matching_show=True
        )
    )

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    search = filters.get("search")

    if search:
        queryset = queryset.filter(
            title__icontains=search
        )

    # ---------------------------------------------------------
    # Genre
    # ---------------------------------------------------------

    genre_id = filters.get("genre")

    if genre_id:
        queryset = queryset.filter(
            genres__id=genre_id
        )

    # ---------------------------------------------------------
    # Language
    # ---------------------------------------------------------

    language_id = filters.get("language")

    if language_id:
        queryset = queryset.filter(
            language_id=language_id
        )

    # ---------------------------------------------------------
    # Release date range
    # ---------------------------------------------------------

    release_from = filters.get(
        "release_from"
    )

    if release_from:
        queryset = queryset.filter(
            release_date__gte=release_from
        )

    release_to = filters.get(
        "release_to"
    )

    if release_to:
        queryset = queryset.filter(
            release_date__lte=release_to
        )

    # ---------------------------------------------------------
    # Minimum rating
    # ---------------------------------------------------------

    minimum_rating = filters.get(
        "minimum_rating"
    )

    if minimum_rating:
        queryset = queryset.filter(
            rating__gte=minimum_rating
        )

    # ---------------------------------------------------------
    # Sorting
    # ---------------------------------------------------------

    sort = filters.get(
        "sort",
        "popularity",
    )

    # ---------------------------------------------------------
    # Ticket-price annotations are only needed when the user
    # actually sorts by price.
    # ---------------------------------------------------------

    if sort in (
        "price_low",
        "price_high",
    ):

        minimum_price = (
            matching_shows
            .order_by(
                "ticket_price"
            )
            .values(
                "ticket_price"
            )[:1]
        )

        maximum_price = (
            matching_shows
            .order_by(
                "-ticket_price"
            )
            .values(
                "ticket_price"
            )[:1]
        )

        queryset = queryset.annotate(
            min_ticket_price=Subquery(
                minimum_price
            ),
            max_ticket_price=Subquery(
                maximum_price
            ),
        )

    sort_map = {
        "popularity": (
            "-popularity",
            "-rating",
            "-release_date",
        ),

        "newest": (
            "-release_date",
            "-popularity",
        ),

        "rating": (
            "-rating",
            "-popularity",
            "-release_date",
        ),

        "price_low": (
            "min_ticket_price",
            "-rating",
            "-popularity",
        ),

        "price_high": (
            "-max_ticket_price",
            "-rating",
            "-popularity",
        ),
    }

    queryset = queryset.order_by(
        *sort_map.get(
            sort,
            sort_map["popularity"],
        )
    )

    return queryset


def get_matching_movie_count(filters=None):
    """
    Count matching movies using database-side COUNT().

    No complete movie list is loaded into Python memory.
    """

    queryset = build_movie_queryset(
        filters
    )

    return queryset.count()


def get_recommended_movies(
    user,
    limit=10,
):
    """
    Generate personalized recommendations using:

    1. Booking-history genres.
    2. Recently-viewed genres.
    3. Popularity.
    4. Rating.
    5. Newest release date.

    Previously booked and viewed movies are excluded.

    Filtering and scoring are performed in the database.
    """

    if not user.is_authenticated:
        return Movie.objects.none()

    now = timezone.now()

    # ---------------------------------------------------------
    # Genres from booking history
    # ---------------------------------------------------------

    booked_genres = (
        Booking.objects
        .filter(
            user=user
        )
        .values_list(
            "show__movie__genres__id",
            flat=True,
        )
        .distinct()
    )

    # ---------------------------------------------------------
    # Genres from recently viewed movies
    # ---------------------------------------------------------

    viewed_genres = (
        RecentlyViewed.objects
        .filter(
            user=user
        )
        .values_list(
            "movie__genres__id",
            flat=True,
        )
        .distinct()
    )

    # ---------------------------------------------------------
    # Already booked movies
    # ---------------------------------------------------------

    booked_movie_ids = (
        Booking.objects
        .filter(
            user=user
        )
        .values(
            "show__movie_id"
        )
        .distinct()
    )

    # ---------------------------------------------------------
    # Already viewed movies
    # ---------------------------------------------------------

    viewed_movie_ids = (
        RecentlyViewed.objects
        .filter(
            user=user
        )
        .values(
            "movie_id"
        )
        .distinct()
    )

    # ---------------------------------------------------------
    # Candidate movies
    # ---------------------------------------------------------

    candidates = (
        Movie.objects
        .select_related("language")
        .filter(
            shows__is_active=True,
            shows__show_time__gte=now,
        )
        .filter(
            Q(
                genres__id__in=booked_genres
            )
            |
            Q(
                genres__id__in=viewed_genres
            )
        )
        .exclude(
            id__in=booked_movie_ids
        )
        .exclude(
            id__in=viewed_movie_ids
        )
        .annotate(
            booking_genre_score=Count(
                "genres",
                filter=Q(
                    genres__id__in=booked_genres
                ),
                distinct=True,
            ),

            viewed_genre_score=Count(
                "genres",
                filter=Q(
                    genres__id__in=viewed_genres
                ),
                distinct=True,
            ),
        )
        .annotate(
            recommendation_score=ExpressionWrapper(
                F("booking_genre_score") * Value(2)
                + F("viewed_genre_score"),
                output_field=IntegerField(),
            )
        )
        .distinct()
        .order_by(
            "-recommendation_score",
            "-popularity",
            "-rating",
            "-release_date",
        )
    )

    recommendations = list(
        candidates[:limit]
    )

    # ---------------------------------------------------------
    # Fallback if personalized candidates are insufficient.
    # ---------------------------------------------------------

    if len(recommendations) < limit:

        selected_ids = [
            movie.id
            for movie in recommendations
        ]

        remaining = (
            Movie.objects
            .select_related("language")
            .filter(
                shows__is_active=True,
                shows__show_time__gte=now,
            )
            .exclude(
                id__in=booked_movie_ids
            )
            .exclude(
                id__in=viewed_movie_ids
            )
            .exclude(
                id__in=selected_ids
            )
            .distinct()
            .order_by(
                "-popularity",
                "-rating",
                "-release_date",
            )
        )

        recommendations.extend(
            list(
                remaining[
                    :limit - len(
                        recommendations
                    )
                ]
            )
        )

    return recommendations[:limit]


def get_recently_viewed_movies(
    user,
    limit=10,
):
    """
    Return the user's latest unique viewed movies.

    Uses a correlated subquery so the latest view timestamp
    is resolved by the database.
    """

    if not user.is_authenticated:
        return Movie.objects.none()

    latest_view = (
        RecentlyViewed.objects
        .filter(
            user=user,
            movie=OuterRef("pk"),
        )
        .order_by(
            "-viewed_at"
        )
        .values(
            "viewed_at"
        )[:1]
    )

    return (
        Movie.objects
        .select_related("language")
        .annotate(
            last_viewed=Subquery(
                latest_view
            )
        )
        .filter(
            last_viewed__isnull=False
        )
        .order_by(
            "-last_viewed"
        )[:limit]
    )