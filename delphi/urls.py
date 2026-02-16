from django.urls import path

from . import views

app_name = "delphi"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/<str:token>/", views.magic_login, name="magic_login"),
    path("logout/", views.logout, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("round/<int:round_id>/", views.round_overview, name="round_overview"),
    path("item/<int:round_item_id>/", views.item_detail, name="item_detail"),
]
