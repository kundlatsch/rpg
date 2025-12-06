# combat/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.db import transaction
from combat.engine import run_battle
from items.models import EquipmentSlot
from character.models import Character
from tasks.models import HuntMonster
from items.models import InventoryItem
from .models import ArenaRanking
from .utils import calculate_arena_points
import random


@login_required
def hunt(request, monster_id):
    try:
        character = request.user.character
    except:
        return HttpResponseBadRequest("Usuário não tem personagem.")

    hunt_monster = HuntMonster.objects.get(id=monster_id)
    monster = hunt_monster.monster

    result = run_battle(character, monster)

    xp = getattr(hunt_monster, "xp_drop", 0)
    gold = getattr(hunt_monster, "gold_drop", 0)

    with transaction.atomic():
        character.hp = max(0, int(result["char_state"]["hp"]))
        leveled = character.add_experience(xp)
        character.gold += gold
        character.save()
    
    level_up_text = ""
    if leveled:
        level_up_text = " Você subiu de nível!"

    result["battle_log"].append(f"Você ganhou {gold} ouro e {xp} pontos de experiência. {level_up_text}")
    
    dropped_items = []
    for item in hunt_monster.item_drops.all():
        if hasattr(item, "drop_chance"):
            chance = item.drop_chance
        else:
            chance = 100

        if random.uniform(0, 100) <= chance:
            dropped_items.append(item)
            inv, created = InventoryItem.objects.get_or_create(
                character=character,
                item=item,
                defaults={"quantity": 0},
            )
            inv.quantity += 1
            inv.save()

    drops_text = (
        ", ".join(i.name for i in dropped_items)
        if dropped_items
        else "nenhum item"
    )

    result["battle_log"].append(f"Você encontrou {drops_text}")

    return render(request, "combat/hunt.html", result)


@login_required
def arena(request):
    player = request.user.character
    ranking, created = ArenaRanking.objects.get_or_create(character=player)

    # Todos players com ranking
    all_players = ArenaRanking.objects.exclude(character=player).order_by("points")

    # pegar quem está logo acima / abaixo
    above = list(all_players.filter(points__gt=ranking.points-1).order_by("points")[:4])
    below = list(all_players.filter(points__lt=ranking.points+1).order_by("-points")[:4])
    challenges = list(set(above + below))

    # top 5 geral
    top5 = ArenaRanking.objects.order_by("-points")[:5]

    context = {
        "player": player,
        "ranking": ranking,
        "challenges": challenges,
        "top5": top5,
    }

    return render(request, "combat/arena.html", context)

@login_required
def arena_fight(request, target_id):
    player = request.user.character
    opponent = get_object_or_404(Character, id=target_id)

    if opponent.type != "player":
        raise HttpResponseBadRequest("Você só pode enfrentar jogadores.")
    
    result = run_battle(player, opponent)
    winner = result["winner"]
    
    arena_player = ArenaRanking.objects.get(character=player)
    arena_opponent = ArenaRanking.objects.get(character=opponent)

    gained_player, gained_opponent = calculate_arena_points(
        arena_player.points,
        arena_opponent.points,
        attacker_won=(winner == "character")
    )

    # atualiza pontos
    arena_player.points += gained_player
    arena_opponent.points += gained_opponent
    arena_player.save()
    arena_opponent.save()

    return render(request, "combat/hunt.html", result)