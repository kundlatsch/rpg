# combat/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.db import transaction
from combat.engine import run_battle
from combat.utils import create_mock_equipment
from items.models import EquipmentSlot
from character.models import Character
from tasks.models import HuntMonster
from items.models import InventoryItem
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
