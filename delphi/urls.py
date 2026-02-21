from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("round/<int:round_id>/", views.round_overview, name="round_overview"),
    path("round/<int:round_id>/submit/", views.submit_round, name="submit_round"),
    path("item/<int:round_item_id>/", views.item_detail, name="item_detail"),
    
    # NEW: Simple token login (permanent, never expires)
    path("login/<uuid:token>/", views.token_login, name="token_login"),
    
    # LEGACY: Magic link login (kept for backward compatibility)
    path("magic/<uuid:token>/", views.magic_login, name="magic_login"),
    
    path("logout/", views.logout_view, name="logout"),
    
    # Admin utilities
    path("setup-admin/", views.setup_admin, name="setup_admin"),
    path("run-migrations/", views.run_migrations, name="run_migrations"),
]