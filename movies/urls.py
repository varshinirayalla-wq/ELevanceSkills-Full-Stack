from django.urls import path

from . import views

urlpatterns = [

    path(
        "",
        views.movie_list,
        name="movie_list",
    ),

    path(
        "movie/<int:pk>/",
        views.movie_detail,
        name="movie_detail",
    ),

    path(
        "movie/<int:movie_id>/book/<int:show_id>/",
        views.book_show,
        name="book_show",
    ),

    path(
        "movie/<int:movie_id>/review/",
        views.create_review,
        name="create_review",
    ),

    path(
        "review/<int:review_id>/edit/",
        views.edit_review,
        name="edit_review",
    ),

    path(
        "review/<int:review_id>/report/",
        views.report_review,
        name="report_review",
    ),
]