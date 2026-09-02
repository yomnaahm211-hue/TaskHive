from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),

    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("tasks/new/", views.create_task, name="create_task"),
    path("tasks/<int:task_id>/", views.task_detail, name="task_detail"),

    path(
        "tasks/<int:task_id>/bid/",
        views.create_bid,
        name="create_bid"
    ),

    path(
        "tasks/<int:task_id>/choose/<int:bid_id>/",
        views.choose_bid,
        name="choose_bid"
    ),
]