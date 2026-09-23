from django.shortcuts import render
from django.utils import timezone
# Create your views here.
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import City, Genre, Language, Movie, RecentlyViewed, Show, Theater
from .services import (
    build_movie_queryset,
    get_matching_movie_count,
    get_recently_viewed_movies,
    get_recommended_movies,
)


def get_filter_values(request):
    """
    Read filter values from GET parameters.
    """

    return {
        "search": request.GET.get(
            "search",
            ""
        ),

        "genre": request.GET.get(
            "genre",
            ""
        ),

        "language": request.GET.get(
            "language",
            ""
        ),

        "city": request.GET.get(
            "city",
            ""
        ),

        "theater": request.GET.get(
            "theater",
            ""
        ),

        "release_from": request.GET.get(
            "release_from",
            ""
        ),

        "release_to": request.GET.get(
            "release_to",
            ""
        ),

        "minimum_rating": request.GET.get(
            "minimum_rating",
            ""
        ),

        "show_date": request.GET.get(
            "show_date",
            ""
        ),

        "show_time_from": request.GET.get(
            "show_time_from",
            ""
        ),

        "show_time_to": request.GET.get(
            "show_time_to",
            ""
        ),

        "sort": request.GET.get(
            "sort",
            "popularity"
        ),
    }


def movie_list(request):

    filters = get_filter_values(
        request
    )

    queryset = build_movie_queryset(
        filters
    )

    paginator = Paginator(
        queryset,
        12,
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )
    
    context = {
        "movies": page_obj,

        "page_obj": page_obj,

        "genres": Genre.objects.all(),

        "languages": Language.objects.all(),

        "cities": City.objects.all(),

        "theaters": Theater.objects.select_related(
            "city"
        ),

        "filters": filters,

        "matching_count": paginator.count,

        "recommended_movies": (
            get_recommended_movies(
                request.user
            )
            if request.user.is_authenticated
            else Movie.objects.none()
        ),

        "recently_viewed": (
            get_recently_viewed_movies(
                request.user
            )
            if request.user.is_authenticated
            else Movie.objects.none()
        ),
    }

    return render(
        request,
        "movies/movie_list.html",
        context,
    )


def movie_count_api(request):

    filters = get_filter_values(
        request
    )

    count = get_matching_movie_count(
        filters
    )

    return JsonResponse(
        {
            "count": count
        }
    )


def movie_detail(request, movie_id):

    movie = get_object_or_404(
        Movie.objects.select_related(
            "language"
        ).prefetch_related(
            "genres"
        ),
        id=movie_id,
    )

    shows = (
        Show.objects
        .filter(
            movie=movie,
            is_active=True,
        )
        .select_related(
            "theater",
            "theater__city",
        )
        .order_by(
            "show_time"
        )
    )

    if request.user.is_authenticated:

        RecentlyViewed.objects.update_or_create(
            user=request.user,
            movie=movie,
            
        )

    return render(
        request,
        "movies/movie_detail.html",
        {
            "movie": movie,
            "shows": shows,
        },
    )

