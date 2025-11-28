# character/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Character

@login_required
def character_detail(request):
    character = Character.objects.get(user=request.user)

    if request.method == "POST":
        attr = request.POST.get("attribute")

        valid_attrs = {
            "strength",
            "dexterity",
            "arcane",
            "constitution",
            "courage",
            "luck",
        }

        if attr in valid_attrs and character.attribute_points > 0:
            old_value = getattr(character, attr)
            setattr(character, attr, old_value + 1)
            character.attribute_points -= 1
            character.save()

        return redirect("character_detail")

    return render(request, "character/detail.html", {"character": character})
