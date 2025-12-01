from django.urls import path
from . import views

app_name = "combat"

urlpatterns = [
    path("hunt/<int:monster_id>/", views.hunt, name="hunt"),
]