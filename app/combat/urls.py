from django.urls import path
from . import views

app_name = "combat"

urlpatterns = [
    path("hunt/<int:monster_id>/", views.hunt, name="hunt"),
    path("arena/", views.arena, name="arena"),
    path("arena/<int:target_id>/", views.arena_fight, name="arena_fight"),
]