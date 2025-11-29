from django.urls import path
from . import views

urlpatterns = [
    path("character/", views.character_detail, name="character_detail"),
    path("ranking/", views.character_ranking, name="ranking"),
    path("character/<int:character_id>/", views.public_character_view, name="public_character"),
]