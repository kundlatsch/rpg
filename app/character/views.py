# character/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
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


@login_required
def public_character_view(request, character_id):
    character = get_object_or_404(Character, id=character_id)

    return render(request, "character/public_profile.html", {
        "character": character
    })


@login_required
def character_ranking(request):
    character = Character.objects.get(user=request.user)

    # Filtra apenas jogadores e ordena
    ranking_list = (
        Character.objects
        .filter(type="player")
        .order_by("-level", "-exp")
    )

    # Paginação: 20 por página (pode mudar!)
    paginator = Paginator(ranking_list, 20)

    # pagina atual que vem do GET ?page=2
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "character/ranking.html",
        {
            "character": character,
            "page_obj": page_obj,
        }
    )
