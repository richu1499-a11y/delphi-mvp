"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from delphi import views

urlpatterns = [
    path('', include('delphi.urls')),
    path('admin/', admin.site.urls),
    path("load-questions/", views.load_questions_view, name="load_questions_view"),
]