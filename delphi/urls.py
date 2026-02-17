from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("round/<int:round_id>/", views.round_overview, name="round_overview"),
    path("round/<int:round_id>/submit/", views.submit_round, name="submit_round"),
    path("item/<int:round_item_id>/", views.item_detail, name="item_detail"),
    path("magic/<uuid:token>/", views.magic_login, name="magic_login"),
    path("logout/", views.logout_view, name="logout"),
    
    # TEMPORARY - DELETE AFTER CREATING ADMIN USER
    path("setup-admin/", views.setup_admin, name="setup_admin"),
]