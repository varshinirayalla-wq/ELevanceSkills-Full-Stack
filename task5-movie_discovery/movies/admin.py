from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import (
    Booking,
    City,
    Genre,
    Language,
    Movie,
    RecentlyViewed,
    Show,
    Theater,
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):

    list_display = ("name",)

    search_fields = ("name",)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):

    list_display = ("name",)

    search_fields = ("name",)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):

    list_display = ("name",)

    search_fields = ("name",)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "language",
        "release_date",
        "rating",
        "popularity",
    )

    list_filter = (
        "language",
        "release_date",
    )

    search_fields = (
        "title",
        "description",
    )


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "city",
        "total_seats",
    )

    list_filter = ("city",)

    search_fields = (
        "name",
        "city__name",
    )


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):

    list_display = (
        "movie",
        "theater",
        "show_time",
        "ticket_price",
        "is_active",
    )

    list_filter = (
        "is_active",
        "theater",
    )

    search_fields = (
        "movie__title",
        "theater__name",
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "show",
        "booked_at",
    )

    list_filter = (
        "booked_at",
    )

    search_fields = (
        "user__username",
        "show__movie__title",
    )


@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "movie",
        "viewed_at",
    )

    list_filter = (
        "viewed_at",
    )

    search_fields = (
        "user__username",
        "movie__title",
    )