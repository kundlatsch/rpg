# character/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Character

@login_required
def character_detail(request):
    character = Character.objects.get(user=request.user)
    return render(request, "character/detail.html", {"character": character})
